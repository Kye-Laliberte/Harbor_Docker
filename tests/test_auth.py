from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import require_api_key
from app.main import app


def test_api_rejects_missing_key(patch):
    patch.setattr(settings, "API_KEY", "auth-test-key")

    response = TestClient(app).get("/")

    assert response.status_code == 401


def test_api_accepts_configured_key(patch):
    patch.setattr(settings, "API_KEY", "auth-test-key")
    response = TestClient(app).get("/", headers={"X-API-Key": "auth-test-key"})
    assert response.status_code == 200

def test_api_rejects_unconfigured_key(patch):
    patch.setattr(settings, "API_KEY", None)
    response = TestClient(app).get("/")
    assert response.status_code == 503

def test_api_key_supports_non_ascii_value(patch):
    patch.setattr(settings, "API_KEY", "clé-de-test")
    require_api_key("clé-de-test")

def test_incorect_api_key(patch):
    patch.setattr(settings, "API_KEY", "auth-test-key")
    response = TestClient(app).get("/", headers={"X-API-Key": "incorrect-key"})
    assert response.status_code == 401