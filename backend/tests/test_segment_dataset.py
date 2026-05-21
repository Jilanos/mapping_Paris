import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.models import Base, B2StreetSegment, SegmentDatasetVersion  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services.segment_dataset_parser import (  # noqa: E402
    SegmentDatasetParseError,
    SegmentDatasetParser,
)
from app.services.segment_dataset_store import SegmentDatasetStore  # noqa: E402


def _feature(
    segment_id: str = "seg-1",
    logical_segment_id: str | None = "logical-1",
    street_name: str = "Rue Test",
    arrondissement: str = "18",
    length_meters: float = 42.5,
) -> dict:
    properties = {
        "id": segment_id,
        "street_name": street_name,
        "arrondissement": arrondissement,
        "length_meters": length_meters,
        "accessibility": "public_walk_cycle",
    }
    if logical_segment_id is not None:
        properties["logical_segment_id"] = logical_segment_id
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": {
            "type": "LineString",
            "coordinates": [[2.3, 48.8], [2.4, 48.9], [2.35, 48.85]],
        },
    }


def _geojson(features: list[dict]) -> bytes:
    return json.dumps({"type": "FeatureCollection", "features": features}).encode("utf-8")


@pytest.fixture()
def segment_client(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'segments.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

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


def test_parser_reads_minimal_feature_collection() -> None:
    parsed = SegmentDatasetParser().parse_bytes(_geojson([_feature()]))

    assert parsed.segment_count == 1
    assert parsed.logical_segment_count == 1
    assert len(parsed.dataset_hash) == 64


def test_parser_preserves_segment_and_logical_ids() -> None:
    parsed = SegmentDatasetParser().parse_bytes(_geojson([_feature()]))
    segment = parsed.segments[0]

    assert segment.segment_id == "seg-1"
    assert segment.logical_segment_id == "logical-1"


def test_parser_falls_back_to_segment_id_when_logical_id_missing() -> None:
    parsed = SegmentDatasetParser().parse_bytes(_geojson([_feature(logical_segment_id=None)]))

    assert parsed.segments[0].logical_segment_id == "seg-1"


def test_parser_computes_bounding_box() -> None:
    segment = SegmentDatasetParser().parse_bytes(_geojson([_feature()])).segments[0]

    assert segment.min_lon == 2.3
    assert segment.max_lon == 2.4
    assert segment.min_lat == 48.8
    assert segment.max_lat == 48.9


def test_parser_uses_length_from_properties() -> None:
    segment = SegmentDatasetParser().parse_bytes(
        _geojson([_feature(length_meters=123.45)])
    ).segments[0]

    assert segment.length_meters == 123.45


def test_parser_rejects_invalid_geojson() -> None:
    with pytest.raises(SegmentDatasetParseError):
        SegmentDatasetParser().parse_bytes(b'{"type":"Feature"}')


def test_ingestion_creates_dataset_version(segment_client) -> None:
    _, session_factory = segment_client
    parsed = SegmentDatasetParser().parse_bytes(_geojson([_feature()]))

    with session_factory() as db:
        version = SegmentDatasetStore(db).ingest(parsed)
        assert version.id is not None
        assert version.segment_count == 1
        assert version.logical_segment_count == 1
        assert db.query(B2StreetSegment).count() == 1


def test_ingestion_does_not_duplicate_same_dataset_hash(segment_client) -> None:
    _, session_factory = segment_client
    parsed = SegmentDatasetParser().parse_bytes(_geojson([_feature()]))

    with session_factory() as db:
        first = SegmentDatasetStore(db).ingest(parsed)
        second = SegmentDatasetStore(db).ingest(parsed)
        assert first.id == second.id
        assert db.query(SegmentDatasetVersion).count() == 1
        assert db.query(B2StreetSegment).count() == 1


def test_new_dataset_version_becomes_active(segment_client) -> None:
    _, session_factory = segment_client
    first = SegmentDatasetParser().parse_bytes(_geojson([_feature(segment_id="seg-1")]))
    second = SegmentDatasetParser().parse_bytes(_geojson([_feature(segment_id="seg-2")]))

    with session_factory() as db:
        first_version = SegmentDatasetStore(db).ingest(first)
        second_version = SegmentDatasetStore(db).ingest(second)
        db.refresh(first_version)
        assert first_version.is_active is False
        assert second_version.is_active is True


def test_segments_status_returns_loaded_false_without_dataset(segment_client) -> None:
    client, _ = segment_client

    response = client.get("/segments/status")

    assert response.status_code == 200
    assert response.json() == {
        "loaded": False,
        "active_dataset_version_id": None,
        "dataset_hash": None,
        "segment_count": None,
        "logical_segment_count": None,
        "created_at": None,
        "source_file_name": None,
    }


def test_segments_status_returns_active_dataset_summary(segment_client) -> None:
    client, session_factory = segment_client
    parsed = SegmentDatasetParser().parse_bytes(_geojson([_feature()]))
    with session_factory() as db:
        SegmentDatasetStore(db).ingest(parsed)

    response = client.get("/segments/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["loaded"] is True
    assert payload["segment_count"] == 1
    assert payload["logical_segment_count"] == 1
    assert payload["source_file_name"] == "memory.geojson"


def test_segments_search_filters_by_arrondissement(segment_client) -> None:
    client, session_factory = segment_client
    parsed = SegmentDatasetParser().parse_bytes(
        _geojson([
            _feature(segment_id="seg-1", arrondissement="18"),
            _feature(segment_id="seg-2", arrondissement="9"),
        ])
    )
    with session_factory() as db:
        SegmentDatasetStore(db).ingest(parsed)

    response = client.get("/segments/search?arrondissement=18")

    assert response.status_code == 200
    assert [segment["segment_id"] for segment in response.json()["segments"]] == ["seg-1"]


def test_segments_search_filters_by_street_name(segment_client) -> None:
    client, session_factory = segment_client
    parsed = SegmentDatasetParser().parse_bytes(
        _geojson([
            _feature(segment_id="seg-1", street_name="Rue Lepic"),
            _feature(segment_id="seg-2", street_name="Rue Test"),
        ])
    )
    with session_factory() as db:
        SegmentDatasetStore(db).ingest(parsed)

    response = client.get("/segments/search?street_name=lepic")

    assert response.status_code == 200
    assert [segment["street_name"] for segment in response.json()["segments"]] == ["Rue Lepic"]


def test_segments_search_respects_limit_and_hides_geometry_by_default(segment_client) -> None:
    client, session_factory = segment_client
    parsed = SegmentDatasetParser().parse_bytes(
        _geojson([_feature(segment_id=f"seg-{index}") for index in range(3)])
    )
    with session_factory() as db:
        SegmentDatasetStore(db).ingest(parsed)

    response = client.get("/segments/search?limit=2")

    assert response.status_code == 200
    segments = response.json()["segments"]
    assert len(segments) == 2
    assert segments[0]["geometry"] is None
    assert "completed" not in segments[0]
    assert "access_token" not in response.text
    assert "refresh_token" not in response.text


def test_segments_search_can_include_geometry(segment_client) -> None:
    client, session_factory = segment_client
    parsed = SegmentDatasetParser().parse_bytes(_geojson([_feature()]))
    with session_factory() as db:
        SegmentDatasetStore(db).ingest(parsed)

    response = client.get("/segments/search?include_geometry=true")

    assert response.status_code == 200
    assert response.json()["segments"][0]["geometry"] == [[2.3, 48.8], [2.4, 48.9], [2.35, 48.85]]


def test_real_android_segment_dataset_can_be_parsed_if_present() -> None:
    source = Path("app/src/main/assets/paris_segments.geojson")
    if not source.exists():
        pytest.skip("Android segment dataset is not present")

    parsed = SegmentDatasetParser().parse_file(source)

    assert parsed.segment_count > 1000
    assert parsed.logical_segment_count > 1000
    assert parsed.segments[0].segment_id
    assert parsed.segments[0].logical_segment_id
