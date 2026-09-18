import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_harbor import create_sample_harbor
from app.main import app
from app.dependencies import get_db
from app.models import Base, Harbor, Dock
import app.enums as enums


# -------------------------------------------------------------------
# SQLite Test Database Setup
# -------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DB_URL,
    connect_args={"check_same_thread": False})

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine)

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
# Helpers
# -------------------------------------------------------------------


def create_sample_dock(db, harbor_id,size=enums.VesselSize.MEDIUM, active=enums.DockStatus.ACTIVE):
    dock = Dock(
        dock_code = str(harbor_id),
        harbor_id=harbor_id,
        dock_size=size,
        dock_status=active,
        cargo_capacity = size*1000)

    db.add(dock)
    db.commit()
    db.refresh(dock)
    return dock

# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

def test_list_docks_empty():
    response = client.get("/docks/getall")
    assert response.status_code == 200
    assert response.json() == []


def test_create_dock():
    db = TestingSessionLocal()
    harbor = create_sample_harbor(db)

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


def test_get_dock():
    db = TestingSessionLocal()
    harbor = create_sample_harbor(db)
    dock = create_sample_dock(db, harbor.id)

    response = client.get(f"/docks/{dock.id}/get")
    assert response.status_code == 200
    assert response.json()["id"] == dock.id


def test_update_dock():
    db = TestingSessionLocal()
    harbor = create_sample_harbor(db)
    dock = create_sample_dock(db, harbor.id)

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


def test_delete_dock():
    db = TestingSessionLocal()
    harbor = create_sample_harbor(db)
    dock = create_sample_dock(db, harbor.id)

    response = client.delete(f"/docks/{dock.id}/delete")
    assert response.status_code == 204

    # verify deletion
    response2 = client.get(f"/docks/{dock.id}/get")
    assert response2.status_code == 404