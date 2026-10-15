import os

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies import get_db
from app.main import app
from app.models import Base
from test_helpers import authenticated_client


@pytest.fixture(scope="session")
def test_engine():
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.fail("Set TEST_DATABASE_URL to a dedicated PostgreSQL test database.")

    test_url = make_url(database_url)
    app_url = make_url(settings.DATABASE_URL)
    if test_url.get_backend_name() != "postgresql":
        pytest.fail("TEST_DATABASE_URL must use PostgreSQL.")
    if test_url.database == app_url.database:
        pytest.fail("TEST_DATABASE_URL must not point to the application's database.")

    engine = create_engine(database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def test_connection(test_engine):
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
def client(db):
    previous_override = app.dependency_overrides.get(get_db)
    previous_api_key = settings.API_KEY

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
