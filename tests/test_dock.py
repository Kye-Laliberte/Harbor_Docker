import app.enums as enums


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

def test_list_docks_empty(client):
    response = client.get("/docks/getall")
    assert response.status_code == 200
    assert response.json() == []


def test_create_dock(client, make_harbor):
    harbor = make_harbor()
    payload = {
        "dock_code": harbor.id * 100,
        "harbor_id": harbor.id,
        "dock_status": enums.DockStatus.ACTIVE,
        "dock_size": 2,
        "cargo_capacity": 500.0}

    response = client.post("/docks/newDock", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["dock_code"]  == harbor.id * 100
    assert data["harbor_id"] == harbor.id
    assert data["dock_status"] == enums.DockStatus.ACTIVE
    assert data["dock_size"] == 2


def test_get_dock(client, make_harbor_with_dock):
    _, dock = make_harbor_with_dock()

    response = client.get(f"/docks/{dock.id}/get")
    assert response.status_code == 200
    assert response.json()["id"] == dock.id


def test_update_dock(client, make_harbor_with_dock):
    _, dock = make_harbor_with_dock()

    payload = {
        "dock_status": enums.DockStatus.INACTIVE,
        "dock_size": 3,
        "cargo_capacity": 2000.0
        }

    response = client.put(f"/docks/{dock.id}/update", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["dock_status"] == enums.DockStatus.INACTIVE
    assert data["dock_size"] == 3
    assert data["cargo_capacity"] == 2000.0


def test_delete_dock(client, make_harbor_with_dock):
    _, dock = make_harbor_with_dock()

    response = client.delete(f"/docks/{dock.id}/delete")
    assert response.status_code == 204

    # verify deletion
    response2 = client.get(f"/docks/{dock.id}/get")
    assert response2.status_code == 404