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


def _seed_duplicate_logical_dataset(session_factory) -> int:
    with session_factory() as db:
        version = SegmentDatasetVersion(
            dataset_hash="hash-duplicate-logical",
            source_path="fixture.geojson",
            source_file_name="fixture.geojson",
            source_file_size_bytes=456,
            segment_count=2,
            logical_segment_count=1,
            is_active=True,
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        shared = {
            "dataset_version_id": version.id,
            "logical_segment_id": "logical-duplicate",
            "street_name": "Boulevard de la Chapelle",
            "arrondissement": "18",
            "length_meters": 80.0,
            "accessibility": "public_walk_cycle",
            "min_lon": 2.0,
            "max_lon": 2.001,
        }
        db.add_all(
            [
                B2StreetSegment(
                    **shared,
                    segment_id="seg-weaker-offset",
                    geometry_json=json.dumps([[2.0, 48.00008], [2.001, 48.00008]]),
                    min_lat=48.00008,
                    max_lat=48.00008,
                ),
                B2StreetSegment(
                    **shared,
                    segment_id="seg-best-exact",
                    geometry_json=json.dumps([[2.0, 48.0], [2.001, 48.0]]),
                    min_lat=48.0,
                    max_lat=48.0,
                ),
            ]
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


def _seed_many_streams(session_factory, count: int, start_id: int = 1) -> None:
    for activity_id in range(start_id, start_id + count):
        _seed_stream(session_factory, activity_id=f"activity-{activity_id}", sport_type="Run")


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
    assert response.json()["activities_with_streams_total"] == 0
    assert response.json()["proposals_created"] == 0
    assert response.json()["streams_processed"] == 0


def test_proposal_generation_creates_proposal_from_stream(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_stream(session_factory)

    response = client.post("/proposals/generate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["activities_with_streams_total"] == 1
    assert payload["activities_without_existing_proposals"] == 1
    assert payload["activities_processed"] == 1
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
    assert second.json()["activities_already_had_proposals"] == 1
    assert second.json()["activities_already_processed"] == 1
    assert second.json()["proposals_updated"] == 0
    assert second.json()["proposals_skipped"] == 0
    with session_factory() as db:
        assert db.query(SegmentMatchProposal).count() == 1


def test_generation_prioritizes_unprocessed_streams_after_first_batch(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_many_streams(session_factory, count=30)

    first = client.post("/proposals/generate")

    assert first.status_code == 200
    assert first.json()["activities_processed"] == 20
    assert first.json()["proposals_created"] == 20

    second = client.post(
        "/proposals/generate",
        json={"only_unprocessed": True, "max_activities": 100},
    )

    assert second.status_code == 200
    payload = second.json()
    assert payload["activities_with_streams_total"] == 30
    assert payload["activities_already_had_proposals"] == 20
    assert payload["activities_without_existing_proposals"] == 10
    assert payload["activities_processed"] == 10
    assert payload["proposals_created"] == 10
    assert payload["activities_skipped_already_processed"] == 20
    with session_factory() as db:
        assert db.query(SegmentMatchProposal).count() == 30


def test_generation_only_unprocessed_does_not_reprocess_existing_batch(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_many_streams(session_factory, count=3)
    client.post("/proposals/generate", json={"only_unprocessed": True, "max_activities": 10})

    second = client.post("/proposals/generate", json={"only_unprocessed": True, "max_activities": 10})

    assert second.status_code == 200
    payload = second.json()
    assert payload["activities_processed"] == 0
    assert payload["streams_processed"] == 0
    assert payload["activities_skipped_already_processed"] == 3
    assert payload["proposals_created"] == 0
    with session_factory() as db:
        assert db.query(SegmentMatchProposal).count() == 3


def test_reset_processing_allows_reprocessing_without_deleting_proposals(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_stream(session_factory)
    client.post("/proposals/generate")

    reset = client.post("/proposals/processing/reset")
    second = client.post("/proposals/generate")

    assert reset.status_code == 200
    assert reset.json()["processing_records_reset"] == 1
    assert reset.json()["proposals_deleted"] == 0
    assert second.status_code == 200
    assert second.json()["activities_processed"] == 1
    assert second.json()["proposals_created"] == 0
    with session_factory() as db:
        assert db.query(StravaActivity).count() == 1
        assert db.query(StravaStream).count() == 1
        assert db.query(SegmentMatchProposal).count() == 1


def test_reset_processing_keeps_accepted_proposals_protected(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_stream(session_factory)
    client.post("/proposals/generate")
    proposal_id = client.get("/proposals").json()["proposals"][0]["id"]
    client.post(f"/proposals/{proposal_id}/accept")

    reset = client.post("/proposals/processing/reset")
    second = client.post("/proposals/generate")

    assert reset.status_code == 200
    assert second.json()["proposals_skipped"] == 1
    with session_factory() as db:
        assert db.query(SegmentMatchProposal).one().status == "accepted"


def test_duplicate_logical_segments_keep_best_candidate(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_duplicate_logical_dataset(session_factory)
    _seed_stream(session_factory, activity_id="activity-duplicate")

    response = client.post("/proposals/generate")

    assert response.status_code == 200
    assert response.json()["proposals_created"] == 1
    with session_factory() as db:
        proposals = db.query(SegmentMatchProposal).all()
        assert len(proposals) == 1
        proposal = proposals[0]
        assert proposal.logical_segment_id == "logical-duplicate"
        assert proposal.segment_id == "seg-best-exact"
        assert proposal.confidence_score > 0.9

    second = client.post("/proposals/generate")

    assert second.status_code == 200
    with session_factory() as db:
        assert db.query(SegmentMatchProposal).count() == 1


def test_existing_proposed_proposal_updates_only_when_candidate_is_better(proposal_client) -> None:
    client, session_factory = proposal_client
    dataset_version_id = _seed_dataset(session_factory)
    _seed_stream(session_factory)
    with session_factory() as db:
        db.add(
            SegmentMatchProposal(
                dataset_version_id=dataset_version_id,
                strava_activity_id="activity-1",
                segment_id="old-seg",
                logical_segment_id="logical-18",
                street_name="Old",
                arrondissement="18",
                segment_length_meters=80.0,
                covered_length_meters=20.0,
                coverage_ratio=0.25,
                min_distance_meters=20.0,
                avg_distance_meters=20.0,
                max_distance_meters=20.0,
                matched_points_count=2,
                confidence_score=0.2,
                status="proposed",
            )
        )
        db.commit()

    response = client.post("/proposals/generate")

    assert response.status_code == 200
    assert response.json()["proposals_updated"] == 1
    with session_factory() as db:
        proposal = db.query(SegmentMatchProposal).one()
        assert proposal.segment_id == "seg-18"
        assert proposal.confidence_score > 0.2

    second = client.post("/proposals/generate")

    assert second.status_code == 200
    assert second.json()["proposals_updated"] == 0
    assert second.json()["proposals_skipped"] == 0
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

    assert response.json()["activities_already_processed"] == 1
    assert response.json()["proposals_skipped"] == 0
    assert client.get("/proposals?status=accepted").json()["proposals"][0]["status"] == "accepted"
    with session_factory() as db:
        assert db.query(SegmentMatchProposal).one().status == "accepted"


def test_dismissed_proposal_is_not_overwritten(proposal_client) -> None:
    client, session_factory = proposal_client
    _seed_dataset(session_factory)
    _seed_stream(session_factory)
    client.post("/proposals/generate")
    proposal_id = client.get("/proposals").json()["proposals"][0]["id"]
    client.post(f"/proposals/{proposal_id}/dismiss")

    response = client.post("/proposals/generate")

    assert response.json()["activities_already_processed"] == 1
    assert response.json()["proposals_skipped"] == 0
    assert client.get("/proposals?status=dismissed").json()["proposals"][0]["status"] == "dismissed"
    with session_factory() as db:
        assert db.query(SegmentMatchProposal).one().status == "dismissed"


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
    assert response.json()["total"] == 1
    assert response.json()["returned"] == 1
    assert response.json()["has_more"] is False


def test_proposals_pagination_returns_metadata_and_distinct_pages(proposal_client) -> None:
    client, session_factory = proposal_client
    dataset_version_id = _seed_dataset(session_factory)
    with session_factory() as db:
        for index in range(3):
            db.add(
                SegmentMatchProposal(
                    dataset_version_id=dataset_version_id,
                    strava_activity_id=f"activity-page-{index}",
                    segment_id=f"seg-page-{index}",
                    logical_segment_id=f"logical-page-{index}",
                    street_name=f"Rue Page {index}",
                    arrondissement="18",
                    segment_length_meters=80.0,
                    covered_length_meters=80.0,
                    coverage_ratio=1.0,
                    min_distance_meters=0.0,
                    avg_distance_meters=float(index),
                    max_distance_meters=1.0,
                    matched_points_count=3,
                    confidence_score=1.0 - (index * 0.01),
                    status="proposed",
                )
            )
        db.commit()

    first = client.get("/proposals?limit=2&offset=0")
    second = client.get("/proposals?limit=2&offset=2")

    assert first.status_code == 200
    assert second.status_code == 200
    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["total"] == 3
    assert first_payload["returned"] == 2
    assert first_payload["has_more"] is True
    assert first_payload["next_offset"] == 2
    assert second_payload["total"] == 3
    assert second_payload["returned"] == 1
    assert second_payload["has_more"] is False
    assert first_payload["proposals"][0]["id"] != second_payload["proposals"][0]["id"]
    assert "access_token" not in first.text
    assert "refresh_token" not in first.text


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
