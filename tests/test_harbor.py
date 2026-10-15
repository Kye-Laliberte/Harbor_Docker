import app.enums as enums


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

def test_create_harbor(client):
    payload = {
        "name": "New Harbor",
        "timezone": "UTC",
        "latitude": 33.0,
        "longitude": -96.0
    }

    response = client.post("/harbors/new", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == "new harbor"


def test_list_harbors(client):
    response = client.get("/harbors/home")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_harbor(client, make_harbor):
    harbor = make_harbor()
    response = client.get(f"/harbors/{harbor.id}/get")
    assert response.status_code == 200
    assert response.json()["id"] == harbor.id


def test_delete_harbor(client, make_harbor):
    harbor = make_harbor()

    response = client.delete(f"/harbors/{harbor.id}/delete")
    assert response.status_code == 204


def test_get_active_docks(client, make_harbor_with_dock):
    harbor, dock = make_harbor_with_dock()

    response = client.get(f"/harbors/{harbor.id}/active_docks")
    assert response.status_code == 200

    assert [item["id"] for item in response.json()] == [dock.id]


def test_get_active_docks_not_found(client, make_harbor):
    harbor = make_harbor()

    response = client.get(f"/harbors/{harbor.id}/active_docks")
    assert response.status_code == 404


def test_get_docks_above_size(client, make_harbor_with_dock):
    harbor, dock = make_harbor_with_dock(dock_size=enums.VesselSize.LARGE)

    response = client.get(f"/harbors/{harbor.id}/docks_above_size/{enums.VesselSize.LARGE}/")
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [dock.id]


def test_get_docks_above_size_invalid_enum(client, make_harbor):
    harbor = make_harbor()

    response = client.get(f"/harbors/{harbor.id}/docks_above_size/INVALID")
    assert response.status_code == 422