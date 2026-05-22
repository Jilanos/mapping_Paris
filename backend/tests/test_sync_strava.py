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
        self.activities_by_page: dict[int, list[dict]] = {}
        self.streams: dict[str, dict | Exception] = {}
        self.refresh_calls: list[str] = []
        self.list_calls: list[tuple[str, int, int]] = []

    def list_activities(self, access_token: str, page: int, per_page: int, after=None, before=None):
        self.list_calls.append((access_token, page, per_page))
        if self.activities_by_page:
            return self.activities_by_page.get(page, [])
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
    ):
        monkeypatch.setenv(name, "")
    monkeypatch.setenv("STRAVA_CLIENT_ID", "example-client-id")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "example-client-secret")
    monkeypatch.setenv("STRAVA_REDIRECT_URI", "http://localhost:8000/auth/strava/callback")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
    monkeypatch.setenv("STRAVA_SYNC_PER_PAGE", "30")
    monkeypatch.setenv("STRAVA_SYNC_MAX_PAGES", "1")
    monkeypatch.setenv("STRAVA_SYNC_LOAD_MORE_MAX_PAGES", "5")
    monkeypatch.setenv("STRAVA_SYNC_ABSOLUTE_MAX_PAGES", "10")
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
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", "")
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
    assert payload["pages_requested"] == 1
    assert payload["activities_fetched"] == 3
    assert payload["activities_created"] == 2
    assert payload["skipped_existing_activities"] == 0
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


def test_sync_with_max_pages_requests_later_pages(sync_client) -> None:
    client, session_factory, fake_strava = sync_client
    _store_token(session_factory)
    fake_strava.activities_by_page = {
        1: [_activity(1, "Run"), _activity(2, "Ride")],
        2: [_activity(3, "Run"), _activity(4, "Ride")],
        3: [_activity(5, "Run")],
    }
    fake_strava.streams = {str(activity_id): _stream() for activity_id in range(1, 6)}

    response = client.post("/sync/strava", json={"max_pages": 3, "per_page": 2})

    assert response.status_code == 200
    payload = response.json()
    assert payload["pages_requested"] == 3
    assert payload["activities_fetched"] == 5
    assert payload["activities_created"] == 5
    assert fake_strava.list_calls == [
        ("stored-access-token", 1, 2),
        ("stored-access-token", 2, 2),
        ("stored-access-token", 3, 2),
    ]


def test_sync_skips_existing_activities_with_streams(sync_client) -> None:
    client, session_factory, fake_strava = sync_client
    _store_token(session_factory)
    fake_strava.activities = [_activity(1, "Run"), _activity(2, "Ride")]
    fake_strava.streams = {"1": _stream(), "2": _stream()}
    first = client.post("/sync/strava")
    assert first.status_code == 200

    second = client.post("/sync/strava")

    assert second.status_code == 200
    payload = second.json()
    assert payload["activities_created"] == 0
    assert payload["activities_updated"] == 0
    assert payload["streams_downloaded"] == 0
    assert payload["skipped_existing_activities"] == 2
    with session_factory() as db:
        assert db.query(StravaActivity).count() == 2
        assert db.query(StravaStream).count() == 2


def test_sync_downloads_missing_stream_for_existing_activity(sync_client) -> None:
    client, session_factory, fake_strava = sync_client
    _store_token(session_factory)
    with session_factory() as db:
        db.add(StravaActivity(strava_activity_id="1", sport_type="Run", streams_downloaded=False))
        db.commit()
    fake_strava.activities = [_activity(1, "Run")]
    fake_strava.streams = {"1": _stream()}

    response = client.post("/sync/strava")

    assert response.status_code == 200
    payload = response.json()
    assert payload["activities_created"] == 0
    assert payload["activities_updated"] == 1
    assert payload["streams_downloaded"] == 1
    assert payload["skipped_existing_activities"] == 0


def test_sync_clamps_requested_max_pages(sync_client, monkeypatch) -> None:
    client, session_factory, fake_strava = sync_client
    _store_token(session_factory)
    monkeypatch.setenv("STRAVA_SYNC_ABSOLUTE_MAX_PAGES", "3")
    get_settings.cache_clear()
    fake_strava.activities_by_page = {
        1: [_activity(1, "Run")],
        2: [_activity(2, "Run")],
        3: [_activity(3, "Run")],
    }
    fake_strava.streams = {str(activity_id): _stream() for activity_id in range(1, 4)}

    response = client.post("/sync/strava", json={"max_pages": 99, "per_page": 1})

    assert response.status_code == 200
    assert response.json()["pages_requested"] == 3
    assert [call[1] for call in fake_strava.list_calls] == [1, 2, 3]


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
