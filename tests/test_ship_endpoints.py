
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_helpers import create_sample_harbor as create_harbor
from test_helpers import create_ship, dock_ship 
from test_helpers import create_sample_dock as create_dock
from app.main import app
from app.dependencies import get_db
from app.models import Base, Harbor, Dock, Ship, Docking
import app.enums as enums


# -------------------------------------------------------------------
# SQLite Test Database Setup
# -------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DB_URL,
    connect_args={"check_same_thread": False})

TestingSessionLocal = sessionmaker(
    autocommit=False,autoflush=False,bind=engine)

# Reset schema for clean tests
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
# Tests
# -------------------------------------------------------------------

def test_list_ships_empty():
    response = client.get("/ships/list")
    assert response.status_code == 200
    assert response.json() == []


def test_create_ship():
    db = TestingSessionLocal()
    harbor = create_harbor(db)
    dock = create_dock(db, harbor.id)

    payload = {
        "ship_name": "New Ship",
        "current_cargo": 0,
        "registration_number": "1234",
        "ship_status": enums.ShipStatus.DOCKED,
        "cargo_capacity":1000,
        "ship_size": enums.VesselSize.SMALL
        }

    response = client.post(f"/ships/new?dock_id={dock.id}", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["ship_name"] == "new ship"
    assert data["ship_status"] == enums.ShipStatus.DOCKED


def test_get_ship():
    db = TestingSessionLocal()
    ship = create_ship(db,name="test_ship_get")

    response = client.get(f"/ships/{ship.id}/get")
    assert response.status_code == 200
    assert response.json()["id"] == ship.id


def test_update_undocked_ship():
    db = TestingSessionLocal()
    ship = create_ship(db,name="test_ship_update")


    payload = {
        "ship_name": "Updated Ship",
    }

    response = client.put(f"/ships/{ship.id}/update", json=payload)
    assert response.status_code == 200
    assert response.json()["ship_name"] == "updated ship"


def test_update_ship_while_sailing_fails():
    db = TestingSessionLocal()
    ship = create_ship(db, status=enums.ShipStatus.SAILING,name="update_logic_test_ship")

    payload = {
        "ship_name": "Should Fail",
    }

    response = client.put(f"/ships/{ship.id}/update", json=payload)
    assert response.status_code == 400

    response2 = client.get(f"/ships/{ship.id}/get")
    assert response2.status_code == 200
    assert response2.json()["id"] == ship.id
    assert response2.json()["ship_name"] == "update_logic_test_ship"



#           deleate ship is not working yet need to move to soft del.
"""
def test_delete_ship_requires_docked():
    db = TestingSessionLocal()
    harbor = create_harbor(db)
    dock = create_dock(db,harbor.id)
   
    ship_payload = {
        "ship_name": "old Ship",
        "current_cargo": 0,
        "registration_number": "oild_ship",
        "ship_status": enums.ShipStatus.DOCKED,
        "cargo_capacity":1000,
        "ship_size": enums.VesselSize.SMALL}
    
    ship_response = client.post(f"/ships/new?dock_id={dock.id}", json=ship_payload)
    ship = ship_response.json()

    response = client.delete(f"/ships/{ship["id"]}/delete")
    assert response.status_code == 204

    # verify deletion
    response2 = client.get(f"/ships/{ship["id"]}/get")
    assert response2.status_code == 404
"""

def test_current_docking_lookup():
    db = TestingSessionLocal()
    harbor = create_harbor(db)
    dock = create_dock(db, harbor.id)
    
    ship_payload = {
            "ship_name": "old Ship",
            "current_cargo": 0,
            "registration_number": "4321",
            "ship_status": enums.ShipStatus.DOCKED,
            "cargo_capacity":1000,
            "ship_size": enums.VesselSize.SMALL
            }
    ship_response = client.post(f"/ships/new?dock_id={dock.id}", json=ship_payload)
    ship = ship_response.json()
   
    response = client.get(f"/ships/{ship["id"]}/last_docking")
    assert response.status_code == 200

    data = response.json()
    assert data["dock_id"] == dock.id
    assert data["ship_id"] == ship["id"]
    assert data["departure_date"] is None