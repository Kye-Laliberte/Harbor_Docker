import datetime
import os
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app.core.config import settings
from app.dependencies import get_db
from app.enums import DockStatus, ShipStatus, VesselSize, VoyageStatus
from app.main import app
from app.models import Base, Dock, Docking, Harbor, Ship, Voyage
from app.schemas import DockingCreate, VoyageCreate
from app.services.docking_service import sev_create_docking
from app.services.voyage_service import VoyageService



TEST_DATABASE_NAME = "harbor_test"


def _database_target(database_url):
    host = database_url.host
    if host is not None:
        host = host.lower()
        if host in {
            "localhost",
            "127.0.0.1",
            "::1",
            "postgres",
            "harbor-postgres",
        }:
            host = "local-postgres"

    return host, database_url.port or 5432, database_url.database


@pytest.fixture(scope="session")
def test_engine():
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.fail("Set TEST_DATABASE_URL to a dedicated PostgreSQL test database.")

    test_url = make_url(database_url)
    app_url = make_url(settings.DATABASE_URL)
    if test_url.get_backend_name() != "postgresql":
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL.")
    if app_url.get_backend_name() != "postgresql":
        pytest.fail("DATABASE_URL must use PostgreSQL.")
    if _database_target(test_url) == _database_target(app_url):
        pytest.fail(
            "TEST_DATABASE_URL must not point to the same PostgreSQL server "
            "address and database as DATABASE_URL."
        )
    if test_url.database != TEST_DATABASE_NAME:
        pytest.fail(
            f"TEST_DATABASE_URL must use the dedicated {TEST_DATABASE_NAME} database."
        )
    if test_url.database == app_url.database:
        pytest.fail("TEST_DATABASE_URL must not point to the application's database.")

    engine = create_engine(database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def cleanup_test_database(test_engine):
    existing_tables = set(inspect(test_engine).get_table_names())
    model_tables = set(Base.metadata.tables)
    if existing_tables.intersection(model_tables):
        pytest.fail(
            "TEST_DATABASE_URL must point to an empty database without "
            "application tables.")
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_connection(test_engine, cleanup_test_database):
    connection = test_engine.connect()
    transaction = connection.begin()
    try:
        existing_tables = set(inspect(connection).get_table_names())
        model_tables = set(Base.metadata.tables)
        if existing_tables.intersection(model_tables):
            pytest.fail(
                "TEST_DATABASE_URL must point to an empty database without "
                "application tables."
            )

        Base.metadata.create_all(bind=connection)
        yield connection
    finally:
        try:
            transaction.rollback()
        finally:
            connection.close()


@pytest.fixture
def db(test_connection):
    transaction = test_connection.begin_nested()
    session = Session(
        bind=test_connection,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        try:
            session.close()
        finally:
            transaction.rollback()


@pytest.fixture
def client(db:Session):
    previous_override = app.dependency_overrides.get(get_db)
    previous_api_key = settings.API_KEY

    def authenticated_client(app):
        from fastapi.testclient import TestClient
        settings.API_KEY = "test-api-key"
        return TestClient(app, headers={"X-API-Key": settings.API_KEY})


    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with authenticated_client(app) as started_client:
            yield started_client
    finally:
        settings.API_KEY = previous_api_key
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override

@pytest.fixture
def make_harbor(db:Session) -> Harbor:
    def factory(harbor_name="test_harbor", tz="UTC", lat=33.0, lon=-96.0):
        harbor = Harbor(name=harbor_name,
                        timezone=tz,latitude=lat,
                        longitude=lon,)
        db.add(harbor)
        db.commit()
        db.refresh(harbor)
        return harbor

    return factory


@pytest.fixture
def make_harbor_with_dock(db:Session, make_harbor) -> tuple[Harbor,Dock]:
    def factory(
        harbor_name="test_harbor",
        tz="UTC",
        lat=33.0,
        lon=-96.0,
        dock_status=DockStatus.ACTIVE,
        dock_size=VesselSize.SMALL,
        cargo_capacity=1000.0,
    ):
        harbor = make_harbor(
            harbor_name=harbor_name,
            tz=tz,
            lat=lat,
            lon=lon,
        )
        dock = Dock(
            dock_code=harbor.id * 100,
            harbor_id=harbor.id,
            dock_status=dock_status,
            dock_size=int(dock_size),
            cargo_capacity=cargo_capacity,
        )
        db.add(dock)
        db.commit()
        db.refresh(dock)
        return harbor, dock

    return factory

@pytest.fixture
def make_sailing_ship(db:Session, add_docked_ship, make_harbor_with_dock) -> tuple[Dock,Harbor,Voyage]:
    """Fixture to create a ship that is currently sailing."""
    
    def factory(
        ship_name="Sailing Ship",
        cargo_capacity=500,
        cargo=1,
        ship_size=VesselSize.SMALL,):

        # Create a docked ship first
        docking_tupel = add_docked_ship(
            ship_name=ship_name,
            cargo_capacity=cargo_capacity,
            cargo=cargo,
            ship_size=ship_size,)
        
        destination_harbor,_ = make_harbor_with_dock(harbor_name="Destination Harbor",dock_size=ship_size)
         
        # Create a voyage for the ship to mark it as sailing
        voyage = VoyageService(db=db,v_id=None).create_voyage(payload=VoyageCreate(ship_id=docking_tupel[1].id,
                                                                                   departure_harbor_id=docking_tupel[0].id,
                                                                                   destination_harbor_id=destination_harbor.id,
                                                                                   departure_date = datetime.datetime.now(datetime.timezone.utc),
                                                                                   arrival_date=None,travel_status= VoyageStatus.APPROVED))
        #leave dock 
        db.add(voyage)
        VoyageService(db,v_id=voyage.id).leave_dock()

        
        db.commit()
        db.refresh(voyage)
        out:tuple = [docking_tupel[1], destination_harbor, voyage]
        return out

    return factory

@pytest.fixture
def add_docked_ship(db:Session, make_harbor_with_dock) -> tuple[Harbor,Ship,Dock,Docking]:
    """Fixture to create a docked ship with an initial docking."""
    def factory(
        ship_name="Docked testing Ship",
        status = ShipStatus.DOCKED,
        cargo_capacity=500,
        cargo=1,
        ship_size=VesselSize.SMALL,):

        harbor, dock = make_harbor_with_dock(dock_size=ship_size)
        ship = Ship(
            ship_name=ship_name,
            current_cargo=cargo,
            ship_status=status,
            registration_number=ship_name,
            cargo_capacity=cargo_capacity,
            ship_size=ship_size,
        )
        db.add(ship)
        db.flush() 

        # Create an initial docking for the ship
        docking = sev_create_docking(db
                ,payload=DockingCreate(
                ship_id=ship.id,
                dock_id=dock.id,
                arrival_date=datetime.datetime.now(datetime.timezone.utc),
                purpose="initial docking",
            ),
            allow_initial_docking=True)

        db.add(docking)
        db.commit()
        db.refresh(ship)
        db.refresh(docking)
        out:tuple=[harbor,ship,dock,docking]
        return out

    return factory


@pytest.fixture
def docking_ship(db:Session, make_sailing_ship) -> tuple[Ship,Harbor,Dock]:
    """"""
    def factory():
        ship = make_sailing_ship()
        
        dock = db.query(Dock).filter(Dock.dock_size <= ship[0].ship_size, Dock.harbor_id == ship[1].id).first()
        if not dock:
            raise
        sev_create_docking(db,payload=DockingCreate(
                ship_id=ship[0].id,
                dock_id=dock.id,
                arrival_date=datetime.datetime.now(datetime.timezone.utc),
                purpose="pending docking",))
        
        return ship[0], ship[1], ship[2]

    return factory 

