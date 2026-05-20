from datetime import UTC, datetime, timedelta
import json
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.routes.sync import get_strava_client  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.db.models import Base, StravaActivity, StravaStream, SyncError, SyncRun  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas.strava import StravaTokenResponse  # noqa: E402
from app.services.token_store import TokenStore  # noqa: E402


class FakeStravaSyncClient:
    def __init__(self) -> None:
        self.activities: list[dict] = []
        self.streams: dict[str, dict | Exception] = {}
        self.refresh_calls: list[str] = []
        self.list_calls: list[tuple[str, int, int]] = []

    def list_activities(self, access_token: str, page: int, per_page: int, after=None, before=None):
        self.list_calls.append((access_token, page, per_page))
        return self.activities

    def get_activity_streams(self, access_token: str, activity_id):
        stream = self.streams[str(activity_id)]
        if isinstance(stream, Exception):
            raise stream
        return stream

    def refresh_access_token(self, refresh_token: str) -> StravaTokenResponse:
        self.refresh_calls.append(refresh_token)
        return StravaTokenResponse(
            access_token="refreshed-access-token",
            refresh_token="refreshed-refresh-token",
            expires_at=int((datetime.now(UTC) + timedelta(hours=2)).timestamp()),
            scope="read,activity:read_all",
            token_type="Bearer",
            athlete={"id": 12345},
        )


@pytest.fixture()
def sync_client(tmp_path, monkeypatch):
    database_path = tmp_path / "test-sync.db"
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
        "STRAVA_SYNC_PER_PAGE",
        "STRAVA_SYNC_MAX_PAGES",
        "STRAVA_SYNC_SPORT_TYPES",
        "STRAVA_TOKEN_REFRESH_MARGIN_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("STRAVA_CLIENT_ID", "example-client-id")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "example-client-secret")
    monkeypatch.setenv("STRAVA_REDIRECT_URI", "http://localhost:8000/auth/strava/callback")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
    monkeypatch.setenv("STRAVA_SYNC_PER_PAGE", "30")
    monkeypatch.setenv("STRAVA_SYNC_MAX_PAGES", "1")
    get_settings.cache_clear()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    fake_strava = FakeStravaSyncClient()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_strava_client] = lambda: fake_strava

    client = TestClient(app)
    try:
        yield client, TestingSessionLocal, fake_strava
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def _activity(activity_id: int, sport_type: str) -> dict:
    return {
        "id": activity_id,
        "name": f"Activity {activity_id}",
        "sport_type": sport_type,
        "type": sport_type,
        "start_date": "2026-05-20T08:00:00Z",
        "start_date_local": "2026-05-20T10:00:00Z",
        "timezone": "(GMT+01:00) Europe/Paris",
        "distance": 1234.5,
        "moving_time": 600,
        "elapsed_time": 700,
        "total_elevation_gain": 12.3,
        "private": False,
        "commute": False,
        "trainer": False,
        "manual": False,
        "map": {"summary_polyline": "abc"},
    }


def _stream() -> dict:
    return {
        "latlng": {"data": [[48.88, 2.34], [48.89, 2.35]]},
        "distance": {"data": [0.0, 42.0]},
        "time": {"data": [0, 20]},
    }


def _store_token(session_factory, expires_delta: timedelta = timedelta(hours=2)) -> None:
    with session_factory() as db:
        TokenStore(db, get_settings()).save(
            StravaTokenResponse(
                access_token="stored-access-token",
                refresh_token="stored-refresh-token",
                expires_at=int((datetime.now(UTC) + expires_delta).timestamp()),
                scope="read,activity:read_all",
                token_type="Bearer",
                athlete={"id": 12345},
            )
        )


def test_sync_returns_error_when_no_token_is_connected(sync_client) -> None:
    client, _, _ = sync_client

    response = client.post("/sync/strava")

    assert response.status_code == 404
    assert "No Strava token" in response.json()["detail"]


def test_sync_returns_error_when_encryption_key_missing(sync_client, monkeypatch) -> None:
    client, _, _ = sync_client
    monkeypatch.delenv("TOKEN_ENCRYPTION_KEY", raising=False)
    get_settings.cache_clear()

    response = client.post("/sync/strava")

    assert response.status_code == 503
    assert "TOKEN_ENCRYPTION_KEY" in response.json()["detail"]


def test_sync_stores_run_and_ride_activities_and_streams(sync_client) -> None:
    client, session_factory, fake_strava = sync_client
    _store_token(session_factory)
    fake_strava.activities = [
        _activity(1, "Run"),
        _activity(2, "Ride"),
        _activity(3, "Walk"),
    ]
    fake_strava.streams = {"1": _stream(), "2": _stream()}

    response = client.post("/sync/strava")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["activities_fetched"] == 3
    assert payload["activities_created"] == 2
    assert payload["streams_downloaded"] == 2
    with session_factory() as db:
        activities = db.query(StravaActivity).order_by(StravaActivity.strava_activity_id).all()
        assert [activity.sport_type for activity in activities] == ["Run", "Ride"]
        assert all(activity.streams_downloaded for activity in activities)
        streams = db.query(StravaStream).all()
        assert len(streams) == 2
        assert json.loads(streams[0].latlng_json)[0] == [48.88, 2.34]
        assert json.loads(streams[0].distance_json) == [0.0, 42.0]
        assert json.loads(streams[0].time_json) == [0, 20]
        assert db.query(SyncRun).one().status == "success"


def test_sync_records_partial_failure_when_stream_download_fails(sync_client) -> None:
    client, session_factory, fake_strava = sync_client
    _store_token(session_factory)
    fake_strava.activities = [_activity(1, "Run"), _activity(2, "Ride")]
    fake_strava.streams = {"1": _stream(), "2": RuntimeError("stream unavailable")}

    response = client.post("/sync/strava")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "partial_failure"
    assert payload["streams_downloaded"] == 1
    assert payload["errors_count"] == 1
    with session_factory() as db:
        assert db.query(SyncError).count() == 1
        assert db.query(SyncRun).one().status == "partial_failure"


def test_sync_status_returns_counts_and_no_secrets(sync_client) -> None:
    client, session_factory, fake_strava = sync_client
    _store_token(session_factory)
    fake_strava.activities = [_activity(1, "Run")]
    fake_strava.streams = {"1": _stream()}
    client.post("/sync/strava")

    response = client.get("/sync/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["connected"] is True
    assert payload["stored_activities"] == 1
    assert payload["stored_streams"] == 1
    assert payload["activities_with_streams"] == 1
    body = response.text
    assert "stored-access-token" not in body
    assert "stored-refresh-token" not in body


def test_sync_runs_returns_recent_runs_and_no_secrets(sync_client) -> None:
    client, session_factory, fake_strava = sync_client
    _store_token(session_factory)
    fake_strava.activities = [_activity(1, "Run")]
    fake_strava.streams = {"1": _stream()}
    client.post("/sync/strava")

    response = client.get("/sync/runs")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["runs"]) == 1
    assert payload["runs"][0]["status"] == "success"
    assert "stored-access-token" not in response.text
    assert "stored-refresh-token" not in response.text


def test_sync_refreshes_expired_token(sync_client) -> None:
    client, session_factory, fake_strava = sync_client
    _store_token(session_factory, expires_delta=timedelta(seconds=-1))
    fake_strava.activities = []

    response = client.post("/sync/strava")

    assert response.status_code == 200
    assert fake_strava.refresh_calls == ["stored-refresh-token"]
    assert fake_strava.list_calls[0][0] == "refreshed-access-token"
