import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402


def test_health_returns_service_status() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "mapping-paris-strava-b2"
    assert payload["version"] == "0.1.0"


def test_health_does_not_expose_secrets() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert "strava_client_id" not in payload
    assert "strava_client_secret" not in payload
    assert "access_token" not in payload
    assert "refresh_token" not in payload
