from datetime import UTC, datetime
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.db.models import (  # noqa: E402
    B2StreetSegment,
    Base,
    SegmentDatasetVersion,
    SegmentMatchProposal,
    StravaActivity,
    StravaStream,
)
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def proposal_client(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'proposals.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setenv("MATCH_MIN_COVERAGE_RATIO", "0.35")
    monkeypatch.setenv("MATCH_MIN_MATCHED_POINTS", "2")
    monkeypatch.setenv("MATCH_MAX_DISTANCE_METERS", "30")
    monkeypatch.setenv("MATCH_MAX_ACTIVITIES_PER_RUN", "20")
    get_settings.cache_clear()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        yield client, TestingSessionLocal
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def _seed_dataset(session_factory, arrondissement: str = "18", street_name: str = "Rue Test") -> int:
    with session_factory() as db:
        version = SegmentDatasetVersion(
            dataset_hash=f"hash-{arrondissement}-{street_name}",
            source_path="fixture.geojson",
            source_file_name="fixture.geojson",
            source_file_size_bytes=123,
            segment_count=1,
            logical_segment_count=1,
            is_active=True,
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        db.add(
            B2StreetSegment(
                dataset_version_id=version.id,
                segment_id=f"seg-{arrondissement}",
                logical_segment_id=f"logical-{arrondissement}",
                street_name=street_name,
                arrondissement=arrondissement,
                length_meters=80.0,
                accessibility="public_walk_cycle",
                geometry_json=json.dumps([[2.0, 48.0], [2.001, 48.0]]),
                min_lat=48.0,
                min_lon=2.0,
                max_lat=48.0,
                max_lon=2.001,
            )
        )
        db.commit()
        return version.id


def _seed_stream(session_factory, activity_id: str = "activity-1", sport_type: str = "Run") -> None:
    with session_factory() as db:
        db.add(
            StravaActivity(
                strava_activity_id=activity_id,
                name="Run",
                sport_type=sport_type,
                type=sport_type,
                start_date=datetime.now(UTC),
                distance_meters=1000.0,
                moving_time_seconds=300,
                elapsed_time_seconds=320,
                streams_downloaded=True,
            )
        )
        db.add(
            StravaStream(
                strava_activity_id=activity_id,
                latlng_json=json.dumps([[48.0, 2.0], [48.0, 2.0005], [48.0, 2.001]]),
                distance_json=json.dumps([0.0, 40.0, 80.0]),
                time_json=json.dumps([0, 20, 40]),
                stream_point_count=3,
            )
        )
        db.commit()


def test_proposal_generation_fails_without_active_dataset(proposal_client) -> None:
    client, _ = proposal_client

    response = client.post("/proposals/generate")

    assert response.status_code == 409
    assert "No active segment dataset" in response.json()["detail"]


def test_proposal_generation_returns_no_proposals_without_streams(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)

    response = client.post("/proposals/generate")

    assert response.status_code == 200
    assert response.json()["proposals_created"] == 0
    assert response.json()["streams_processed"] == 0


def test_proposal_generation_creates_proposal_from_stream(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_stream(session_factory)

    response = client.post("/proposals/generate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["proposals_created"] == 1
    assert payload["candidate_segments_checked"] == 1
    with session_factory() as db:
        proposal = db.query(SegmentMatchProposal).one()
        assert proposal.status == "proposed"
        assert proposal.coverage_ratio >= 0.35


def test_duplicate_generation_does_not_duplicate_proposals(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_stream(session_factory)

    client.post("/proposals/generate")
    second = client.post("/proposals/generate")

    assert second.status_code == 200
    assert second.json()["proposals_updated"] == 1
    with session_factory() as db:
        assert db.query(SegmentMatchProposal).count() == 1


def test_accepted_proposal_is_not_overwritten(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_stream(session_factory)
    client.post("/proposals/generate")
    proposal_id = client.get("/proposals").json()["proposals"][0]["id"]
    client.post(f"/proposals/{proposal_id}/accept")

    response = client.post("/proposals/generate")

    assert response.json()["proposals_skipped"] == 1
    assert client.get("/proposals?status=accepted").json()["proposals"][0]["status"] == "accepted"


def test_dismissed_proposal_is_not_overwritten(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_stream(session_factory)
    client.post("/proposals/generate")
    proposal_id = client.get("/proposals").json()["proposals"][0]["id"]
    client.post(f"/proposals/{proposal_id}/dismiss")

    response = client.post("/proposals/generate")

    assert response.json()["proposals_skipped"] == 1
    assert client.get("/proposals?status=dismissed").json()["proposals"][0]["status"] == "dismissed"


def test_proposals_list_and_filter_by_arrondissement(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory, arrondissement="18", street_name="Rue Lepic")
    _seed_stream(session_factory)
    client.post("/proposals/generate")

    response = client.get("/proposals?arrondissement=18")

    assert response.status_code == 200
    proposals = response.json()["proposals"]
    assert len(proposals) == 1
    assert proposals[0]["street_name"] == "Rue Lepic"
    assert "raw_match" in proposals[0]
    assert proposals[0]["raw_match"] is None


def test_proposals_status_returns_counts(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_stream(session_factory)
    client.post("/proposals/generate")

    response = client.get("/proposals/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_proposals"] == 1
    assert payload["proposed_count"] == 1
    assert payload["activities_with_streams_count"] == 1


def test_accept_and_dismiss_endpoints_update_status(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_stream(session_factory)
    client.post("/proposals/generate")
    proposal_id = client.get("/proposals").json()["proposals"][0]["id"]

    accepted = client.post(f"/proposals/{proposal_id}/accept")
    dismissed = client.post(f"/proposals/{proposal_id}/dismiss")

    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "dismissed"


def test_proposal_endpoints_do_not_expose_tokens_or_secrets(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_stream(session_factory)
    client.post("/proposals/generate")

    for response in (
        client.get("/proposals"),
        client.get("/proposals/status"),
        client.post("/proposals/generate"),
    ):
        body = response.text
        assert "access_token" not in body
        assert "refresh_token" not in body
        assert "TOKEN_ENCRYPTION_KEY" not in body
