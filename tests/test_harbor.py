import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.dependencies import get_db
from app.models import Base, Harbor, Dock
import app.enums as enums


# -------------------------------------------------------------------
# PostgreSQL Test Database Setup
# -------------------------------------------------------------------

# IMPORTANT:
# This database MUST exist before running tests.
# Your docker-compose should create it automatically.
TEST_DB_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DB_URL,connect_args={"check_same_thread": False},)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables fresh for each test session
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

def create_sample_harbor(db, name="Test Harbor"):
    harbor = Harbor(
        name=name,
        timezone="UTC",
        latitude=10.0,
        longitude=20.0)
    
    db.add(harbor)
    db.commit()
    db.refresh(harbor)
    return harbor


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

def test_create_harbor():
    payload = {
        "name": "New Harbor",
        "timezone": "UTC",
        "latitude": 33.0,
        "longitude": -96.0
    }

    response = client.post("/harbors/new", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == "new harbor"


def test_list_harbors():
    response = client.get("/harbors/home")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_harbor():
    db = TestingSessionLocal()
    harbor = create_sample_harbor(db)

    response = client.get(f"/harbors/{harbor.id}/get")
    assert response.status_code == 200
    assert response.json()["id"] == harbor.id


def test_delete_harbor():
    db = TestingSessionLocal()
    harbor = create_sample_harbor(db)

    response = client.delete(f"/harbors/{harbor.id}")
    assert response.status_code == 204


def test_get_active_docks():
    db = TestingSessionLocal()
    harbor = create_sample_harbor(db)
    create_sample_dock(db, harbor.id)

    response = client.get(f"/harbors/{harbor.id}/active_docks")
    assert response.status_code == 200

    assert len(response.json()) == 1


def test_get_active_docks_not_found():
    db = TestingSessionLocal()
    harbor = create_sample_harbor(db)

    response = client.get(f"/harbors/{harbor.id}/active_docks")
    assert response.status_code == 404


def test_get_docks_above_size():
    db = TestingSessionLocal()
    harbor = create_sample_harbor(db)

    create_sample_dock(db, harbor.id, size=enums.VesselSize.LARGE)

    response = client.get(f"/harbors/{harbor.id}/docks_above_size/{enums.VesselSize.LARGE}/")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_docks_above_size_invalid_enum():
    db = TestingSessionLocal()
    harbor = create_sample_harbor(db)

    response = client.get(f"/harbors/{harbor.id}/docks_above_size/INVALID")
    assert response.status_code == 422
