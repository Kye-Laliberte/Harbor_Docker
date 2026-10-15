from test_helpers import create_ship
import app.enums as enums


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

def test_list_ships_empty(client):
    response = client.get("/ships/list")
    assert response.status_code == 200
    assert response.json() == []


def test_create_ship(client, make_harbor_with_dock):
    _, dock = make_harbor_with_dock(
        dock_size=enums.VesselSize.SMALL,
        cargo_capacity=1000.0,
    )

    payload = {
        "ship_name": "New Ship",
        "current_cargo": 750,
        "registration_number": "1234",
        "ship_status": enums.ShipStatus.DOCKED,
        "cargo_capacity":1000,
        "ship_size": enums.VesselSize.SMALL
        }

    response = client.post(f"/ships/new?dock_id={dock.id}", json=payload)
    assert response.status_code == 201
    
    dock_data = client.get(f"/docks/{dock.id}/get")
    assert dock_data.status_code == 200
    assert dock_data.json()["id"] == dock.id
    assert dock_data.json()["dock_status"] == enums.DockStatus.INACTIVE
    
    data = response.json()

    assert data["ship_name"] == "new ship"
    assert data["ship_status"] == enums.ShipStatus.DOCKED
    assert data["current_cargo"] == 750
    

def test_get_ship(client, db):
    ship = create_ship(db,name="test_ship_get")

    response = client.get(f"/ships/{ship.id}/get")
    assert response.status_code == 200
    assert response.json()["id"] == ship.id


def test_update_docked_ship(client, make_harbor_with_dock):
    _, dock = make_harbor_with_dock(
        dock_size=enums.VesselSize.SMALL,
        cargo_capacity=1000.0,)
    
    ship_payload = {
        "ship_name": "test Ship",
        "current_cargo": 0,
        "registration_number": "12345",
        "ship_status": enums.ShipStatus.DOCKED,
        "cargo_capacity":1000,
        "ship_size": enums.VesselSize.SMALL
        }
    ship_response = client.post(f"/ships/new?dock_id={dock.id}", json=ship_payload)
    assert ship_response.status_code == 201
    
    ship = ship_response.json()
    assert ship["ship_name"] == "test ship"
    assert ship["ship_status"] == enums.ShipStatus.DOCKED


    payload = {
        "ship_name": "Updated Ship",
    }

    response = client.put(f"/ships/{ship["id"]}/update", json=payload)
    assert response.status_code == 200
    assert response.json()["ship_name"] == "updated ship"


def test_update_ship_while_sailing_fails(client, db):
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

def test_current_docking_search(client, make_harbor_with_dock):
    _, dock = make_harbor_with_dock(
        dock_size=enums.VesselSize.SMALL,
        cargo_capacity=1000.0,
    )
    
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


def test_delete_ship(client,make_harbor_with_dock,): 
    """deletes a ship and its docking and releses the dock form inactive to active"""
    _, dock = make_harbor_with_dock(
        harbor_name="ship-delete-harbor",
        dock_size=enums.VesselSize.SMALL,
        cargo_capacity=1000.0,
    )
    ship_payload = {
        "ship_name": "ship for delete test",
        "current_cargo": 0,
        "registration_number": "ship-delete-test",
        "ship_status": enums.ShipStatus.DOCKED,
        "cargo_capacity": 1000,
        "ship_size": enums.VesselSize.SMALL,
    }
    ship_response = client.post(
        f"/ships/new?dock_id={dock.id}",
        json=ship_payload,
    )
    assert ship_response.status_code == 201
    ship_id = ship_response.json()["id"]

    response = client.delete(f"/ships/{ship_id}/delete")

    assert response.status_code == 200
    assert client.get(f"/ships/{ship_id}/get").status_code == 404
    assert client.get(f"/docks/{dock.id}/get").json()["dock_status"] == "active"
    remaining_dockings = client.get("/dockings/list").json()
    assert all(docking["ship_id"] != ship_id for docking in remaining_dockings)