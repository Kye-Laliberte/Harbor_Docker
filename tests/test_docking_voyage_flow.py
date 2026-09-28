import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from test_helpers import create_sample_dock,create_sample_harbor,create_ship,dock_ship , create_voyage
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
client = TestClient(app)




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
    response = client.post(f"/voyages/{voyage_id}/leave_dock")
    assert response.status_code == 200
    assert response.json()["travel_status"] == enums.VoyageStatus.DEPARTED

    arrival_payload = VoyageArrivalUpdate(arrival_date=datetime(2026, 4, 7, tzinfo=timezone.utc))
    # 4. Ship arrives at destination
    
    response = client.post(f"/voyages/{voyage_id}/arrive", json=arrival_payload.model_dump(mode='json'))
    assert response.status_code == 200
    
    assert response.json()["travel_status"] == enums.VoyageStatus.ARRIVED
    
    dock_stat = db.execute(
    text("SELECT dock_status FROM docks WHERE id = :dock_id"),{"dock_id": dest_dock.id},
    ).scalar_one()

    assert dock_stat == enums.DockStatus.ACTIVE

    # 5. Docking created automatically by arrival logic?
    # If not automatic, create docking manually:


    client.post(f"/{voyage_id}/leave_dock")


    ship_status = db.execute(text("SELECT ship_status from ships WHERE id = :ship_id "),{"ship_id":ship.id}).scalar_one()
    assert ship_status == enums.ShipStatus.SAILING

    doc =DockingCreate(
        ship_id=ship.id,
        dock_id=dest_dock.id,
        arrival_date= datetime(2026, 4, 7, tzinfo=timezone.utc),
        purpose = "testing Arrival Docking")
    

    docking_response = client.post("/dockings/create", json=doc.model_dump(mode='json'))
    assert docking_response.status_code == 201, docking_response.json()
    docking_id = docking_response.json()["id"]
"""
    # 6. Approve docking
    response = client.post(f"/dockings/{docking_id}/approve")
    assert response.status_code == 200
    assert response.json()["ship_clearance_status"] == enums.ShipClearanceStatus.APPROVED

    # 7. Mark docking arrival
    response = client.put(f"/dockings/{docking_id}/arrive/")
    assert response.status_code == 202
    assert response.json()["status"] == "entered"
    
    ship_status = db.execute(text("SELECT ship_status from ships WHERE id = :ship_id "),{"ship_id":ship.id}).scalar_one()
    assert ship_status == enums.ShipStatus.DOCKED
    
    # 8. Cannot delete docking while current
    response = client.delete(f"/dockings/{docking_id}/delete")
    assert response.status_code == 400

    # 9. Set departure_date so deletion is allowed
    docking = db.query(Docking).filter(Docking.id == docking_id).first()
    docking.departure_date = "2024-01-03T00:00:00"
    db.commit()

    response = client.delete(f"/dockings/{docking_id}/delete")
    assert response.status_code == 204"""