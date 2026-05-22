import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.routes.auth_strava import get_strava_client  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db.models import Base, StravaToken  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas.strava import StravaTokenResponse  # noqa: E402


class FakeStravaClient:
    def __init__(self) -> None:
        self.exchange_calls: list[str] = []
        self.refresh_calls: list[str] = []

    def exchange_code_for_token(self, code: str) -> StravaTokenResponse:
        self.exchange_calls.append(code)
        return StravaTokenResponse(
            access_token="mock-access-token",
            refresh_token="mock-refresh-token",
            expires_at=1893456000,
            scope="read,activity:read_all",
            token_type="Bearer",
            athlete={"id": 12345},
        )

    def refresh_access_token(self, refresh_token: str) -> StravaTokenResponse:
        self.refresh_calls.append(refresh_token)
        return StravaTokenResponse(
            access_token="refreshed-access-token",
            refresh_token="refreshed-refresh-token",
            expires_at=1893542400,
            scope="read,activity:read_all",
            token_type="Bearer",
            athlete={"id": 12345},
        )


@pytest.fixture()
def auth_client(tmp_path, monkeypatch):
    database_path = tmp_path / "test-auth.db"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    for name in (
        "STRAVA_CLIENT_ID",
        "STRAVA_CLIENT_SECRET",
        "STRAVA_REDIRECT_URI",
        "TOKEN_ENCRYPTION_KEY",
    ):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("STRAVA_SCOPES", "read,activity:read_all")
    monkeypatch.setenv("AUTH_STATE_TTL_SECONDS", "600")
    get_settings.cache_clear()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fake_strava = FakeStravaClient()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_strava_client] = lambda: fake_strava

    client = TestClient(app)
    try:
        yield client, TestingSessionLocal, fake_strava
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def configure_strava(monkeypatch, with_secret: bool = True) -> None:
    monkeypatch.setenv("STRAVA_CLIENT_ID", "example-client-id")
    monkeypatch.setenv("STRAVA_REDIRECT_URI", "http://localhost:8000/auth/strava/callback")
    if with_secret:
        monkeypatch.setenv("STRAVA_CLIENT_SECRET", "example-client-secret")
        monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
    get_settings.cache_clear()


def test_auth_status_returns_configured_false_without_strava_config(auth_client) -> None:
    client, _, _ = auth_client

    response = client.get("/auth/strava/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "configured": False,
        "connected": False,
        "expires_at": None,
        "scope": None,
    }


def test_auth_start_returns_clear_error_when_config_missing(auth_client) -> None:
    client, _, _ = auth_client

    response = client.get("/auth/strava/start")

    assert response.status_code == 503
    assert "STRAVA_CLIENT_ID" in response.json()["detail"]


def test_auth_start_redirects_when_config_present(auth_client, monkeypatch) -> None:
    client, _, _ = auth_client
    configure_strava(monkeypatch, with_secret=False)

    response = client.get("/auth/strava/start", follow_redirects=False)

    assert response.status_code == 307
    location = response.headers["location"]
    parsed = urlparse(location)
    params = parse_qs(parsed.query)
    assert parsed.netloc == "www.strava.com"
    assert params["client_id"] == ["example-client-id"]
    assert params["redirect_uri"] == ["http://localhost:8000/auth/strava/callback"]
    assert params["scope"] == ["read,activity:read_all"]
    assert "state" in params


def test_callback_rejects_invalid_state(auth_client, monkeypatch) -> None:
    client, _, _ = auth_client
    configure_strava(monkeypatch)

    response = client.get("/auth/strava/callback?code=example-code&state=invalid")

    assert response.status_code == 400
    assert "state" in response.json()["detail"].lower()


def test_callback_stores_encrypted_tokens(auth_client, monkeypatch) -> None:
    client, session_factory, fake_strava = auth_client
    configure_strava(monkeypatch)
    start = client.get("/auth/strava/start", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]

    response = client.get(f"/auth/strava/callback?code=example-code&state={state}")

    assert response.status_code == 200
    assert response.json() == {"status": "connected", "connected": True}
    assert fake_strava.exchange_calls == ["example-code"]
    with session_factory() as db:
        token = db.query(StravaToken).one()
        assert token.access_token_encrypted != "mock-access-token"
        assert token.refresh_token_encrypted != "mock-refresh-token"
        assert token.athlete_id == "12345"


def test_status_connected_true_after_successful_callback(auth_client, monkeypatch) -> None:
    client, _, _ = auth_client
    configure_strava(monkeypatch)
    start = client.get("/auth/strava/start", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    client.get(f"/auth/strava/callback?code=example-code&state={state}")

    response = client.get("/auth/strava/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is True
    assert payload["connected"] is True
    assert payload["scope"] == "read,activity:read_all"
    assert "access_token" not in payload
    assert "refresh_token" not in payload


def test_refresh_updates_stored_encrypted_tokens(auth_client, monkeypatch) -> None:
    client, session_factory, fake_strava = auth_client
    configure_strava(monkeypatch)
    start = client.get("/auth/strava/start", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    client.get(f"/auth/strava/callback?code=example-code&state={state}")

    response = client.post("/auth/strava/refresh")

    assert response.status_code == 200
    assert response.json() == {"status": "refreshed", "connected": True}
    assert fake_strava.refresh_calls == ["mock-refresh-token"]
    with session_factory() as db:
        token = db.query(StravaToken).one()
        assert token.access_token_encrypted != "refreshed-access-token"
        assert token.refresh_token_encrypted != "refreshed-refresh-token"


def test_callback_fails_without_token_encryption_key(auth_client, monkeypatch) -> None:
    client, _, _ = auth_client
    monkeypatch.setenv("STRAVA_CLIENT_ID", "example-client-id")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "example-client-secret")
    monkeypatch.setenv("STRAVA_REDIRECT_URI", "http://localhost:8000/auth/strava/callback")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "")
    get_settings.cache_clear()
    start = client.get("/auth/strava/start", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]

    response = client.get(f"/auth/strava/callback?code=example-code&state={state}")

    assert response.status_code == 503
    assert "TOKEN_ENCRYPTION_KEY" in response.json()["detail"]


def test_auth_responses_do_not_expose_raw_secrets(auth_client, monkeypatch) -> None:
    client, _, _ = auth_client
    configure_strava(monkeypatch)
    start = client.get("/auth/strava/start", follow_redirects=False)
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
    callback = client.get(f"/auth/strava/callback?code=example-code&state={state}")
    status = client.get("/auth/strava/status")
    refresh = client.post("/auth/strava/refresh")

    for response in (callback, status, refresh):
        body = response.text
        assert "mock-access-token" not in body
        assert "mock-refresh-token" not in body
        assert "example-client-secret" not in body
        assert "TOKEN_ENCRYPTION_KEY" not in body
