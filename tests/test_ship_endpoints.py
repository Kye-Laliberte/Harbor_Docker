import app.enums as enums
from app.models import Dock
# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------
class Testship:
    """ship endpoints positive test"""
    def test_list_ships_empty(self,client):
        response = client.get("/ships/list")
        assert response.status_code == 200
        assert response.json() == []


    def test_create_ship(self,client, make_harbor_with_dock):
        _, dock = make_harbor_with_dock(
            dock_size=enums.VesselSize.SMALL,
            cargo_capacity=1000.0,)

        payload = {
            "ship_name": "New Ship",
            "current_cargo": 750,
            "registration_number": "1234",
            "ship_status": enums.ShipStatus.DOCKED,
            "cargo_capacity":1000,
            "ship_size": enums.VesselSize.SMALL}

        ship_info = client.post(f"/ships/new?dock_id={dock.id}", json=payload)
        assert ship_info.status_code == 201 
        assert ship_info.json()["ship_status"] == enums.ShipStatus.DOCKED
        assert ship_info.json()["ship_size"] == enums.VesselSize.SMALL
        assert ship_info.json()["registration_number"] == "1234"

    
        dock_data = client.get(f"/docks/{dock.id}/get")
        assert dock_data.status_code == 200
        assert dock_data.json()["id"] == dock.id
        assert dock_data.json()["dock_status"] == enums.DockStatus.INACTIVE
    
    

    def test_get_ship(self,client, add_docked_ship):
        ship:tuple = add_docked_ship()
        
        response = client.get(f"/ships/{ship[1].id}/get")
        assert response.status_code == 200
        assert response.json()["id"] == ship[1].id


    def test_update_docked_ship(self,client, add_docked_ship):
        
        payload = {
            "ship_name": "Updated Ship",}

        ship:tuple = add_docked_ship(ship_name="test Ship",cargo_capacity=1000,
                    cargo = 0,ship_size = enums.VesselSize.SMALL)

        response = client.put(f"/ships/{ship[1].id}/update", json=payload)
        assert response.status_code == 200
        assert response.json()["ship_name"] == "updated ship"

    def test_update_ship_while_sailing_fails(self,client,make_sailing_ship):
        """Test that updating a ship while it is sailing raises an error."""
        ship, _, _ = make_sailing_ship(ship_name="update_logic_test_ship")
        payload = {"ship_name":"Should Fail",}

        response = client.put(f"/ships/{ship.id}/update", json=payload)
        assert response.status_code == 400
        response2 = client.get(f"/ships/{ship.id}/get")
        assert response2.status_code == 200
        assert response2.json()["id"] == ship.id
        assert response2.json()["ship_name"] == "update_logic_test_ship"
    

    def test_current_docking_search(self,client, make_harbor_with_dock):
        _, dock = make_harbor_with_dock(
            dock_size=enums.VesselSize.SMALL,
            cargo_capacity=1000.0,)
    
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


    def test_delete_ship(self,client,add_docked_ship): 
        """deletes a ship and its docking and releses the dock form inactive to active"""

        _,ship,dock,_=add_docked_ship()

        
        assert client.delete(f"/ships/{ship.id}/delete")
        assert client.get(f"/ships/{ship.id}/get").status_code == 404
       
        respon = client.get(f"/docks/{dock.id}/get")
        assert respon.status_code == 200
        assert respon.json()["dock_status"] == "active"
        remaining_dockings = client.get("/dockings/list").json()
        assert all(docking["ship_id"] != ship.id for docking in remaining_dockings)

    def test_deny_and_redirect_docking(self,db,client,docking_ship):
        ship,harbor,dock = docking_ship()

        second_dock = {"dock_code":12312,
                       "dock_status":enums.DockStatus.ACTIVE,
                       "cargo_capacity":10000,
                       "harbor_id":harbor.id,
                       "dock_size": ship.ship_size
                       }

        dock2=client.post("/docks/newDock", json=second_dock)
        assert dock2.status_code == 201

        respon = client.put(f"/dockings/{ship.id}/deny_and_redirect")
        assert respon.status_code == 200
        assert respon.json()["dock_id"] != dock.id
        
        redirected_dock = db.query(Dock).filter(Dock.id == respon.json()["dock_id"]).first()
        assert redirected_dock.harbor_id == harbor.id
