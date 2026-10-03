from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_api_rejects_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "auth-test-key")

    response = TestClient(app).get("/")

    assert response.status_code == 401


def test_api_accepts_configured_key(monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "auth-test-key")

    response = TestClient(app).get("/", headers={"X-API-Key": "auth-test-key"})

    assert response.status_code == 200