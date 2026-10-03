import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from test_helpers import authenticated_client, create_sample_dock,create_sample_harbor,create_ship,dock_ship,get_dock_stat,get_ship_stat
from app.main import app
from app.dependencies import get_db
from app.models import Base, Harbor, Dock, Ship, Voyage, Docking
import app.enums as enums
from app.schemas import VoyageCreate,VoyageArrivalUpdate,DockingCreate

# -------------------------------------------------------------------
# SQLite Test Database Setup
# -------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = authenticated_client(app)




# -------------------------------------------------------------------
# FULL WORKFLOW TEST
# -------------------------------------------------------------------

def test_full_voyage_docking_workflow():
    db = TestingSessionLocal()

    # Create harbors, dock, ship
    origin = create_sample_harbor(db, "Origin Harbor", 10.0, 20.0)
    dest = create_sample_harbor(db, "Destination Harbor", 30.0, 40.0)
    dest_dock = create_sample_dock(db, dest.id,size=enums.VesselSize.SMALL, active=enums.DockStatus.ACTIVE)
    origin_dock = create_sample_dock(db, origin.id,size=enums.VesselSize.SMALL, active=enums.DockStatus.INACTIVE)
    ship = create_ship(db,name="full_voyage",ship_size=enums.VesselSize.SMALL)
    
    first_dockig = dock_ship(db,ship_id=ship.id,dock_id=origin_dock.id)
    


    # 1. Create voyage
    voy = VoyageCreate(ship_id=ship.id, departure_date=datetime(2026,4,3, tzinfo=timezone.utc),
                 departure_harbor_id=origin.id,destination_harbor_id=dest.id)
    

    response = client.post("/voyages/create", json=voy.model_dump(mode='json'))
    assert response.status_code == 201
    assert response.json()["travel_status"] == enums.VoyageStatus.SCHEDULED
    voyage_id = response.json()["id"]

    # 2. Approve voyage
    response = client.post(f"/voyages/{voyage_id}/approve")
    assert response.status_code == 200
    assert response.json()["travel_status"] == enums.VoyageStatus.APPROVED

    # 3. Ship leaves dock
    response = client.post(f"/voyages/{ship.id}/leave_dock")
    assert response.status_code == 200
    assert response.json()["travel_status"] == enums.VoyageStatus.DEPARTED
    ship_status = get_ship_stat(db=db,ship_id=ship.id)
    assert ship_status == enums.ShipStatus.SAILING
    dock_stat = get_dock_stat(db=db, dock_id=origin_dock.id)
    assert dock_stat == enums.DockStatus.ACTIVE

    arrival_payload = VoyageArrivalUpdate(arrival_date=datetime(2026, 4, 7, tzinfo=timezone.utc))
    # 4. Ship arrives at destination
    
    response = client.post(f"/voyages/{voyage_id}/arrive", json=arrival_payload.model_dump(mode='json'))
    assert response.status_code == 200
    assert response.json()["travel_status"] == enums.VoyageStatus.ARRIVED
    

    # 5. Docking created automatically by arrival logic?
    # If not automatic, create docking manually:

    doc =DockingCreate(
        ship_id=ship.id,
        dock_id=dest_dock.id,
        arrival_date= datetime(2026, 4, 7, tzinfo=timezone.utc),
        purpose = "testing Arrival Docking")
    

    docking_response = client.post("/dockings/create", json=doc.model_dump(mode='json'))
    assert docking_response.status_code == 201, docking_response.json()
    docking_id = docking_response.json()["id"]
    
    # 6. Approve docking
    response = client.post(f"/dockings/{docking_id}/approve")
    assert response.status_code == 200
    assert response.json()["ship_clearance_status"] == enums.ShipClearanceStatus.APPROVED

    # 7. Mark docking arrival
    response = client.put(f"/dockings/{docking_id}/arrive/")
    assert response.status_code == 202
    
    dock_stat = get_dock_stat(db,dest_dock.id)
    assert dock_stat == enums.DockStatus.INACTIVE

    ship_status = get_ship_stat(db,ship.id)
    assert ship_status == enums.ShipStatus.DOCKED

    # 8. Cannot delete docking while current
    response = client.delete(f"/dockings/{docking_id}/delete")
    assert response.status_code == 400

    # 9. Set departure_date so deletion is allowed
    docking = db.query(Docking).filter(Docking.id == docking_id).first()
    docking.departure_date =  datetime(2026, 4, 8, tzinfo=timezone.utc)
    db.commit()

    response = client.delete(f"/dockings/{docking_id}/delete")
    assert response.status_code == 204
    