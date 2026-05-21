import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402
from app.db.models import B2StreetSegment  # noqa: E402
from app.services.segment_matcher import SegmentMatcher, point_to_segment_distance_meters  # noqa: E402


def _segment() -> B2StreetSegment:
    return B2StreetSegment(
        dataset_version_id=1,
        segment_id="seg-1",
        logical_segment_id="logical-1",
        street_name="Rue Test",
        arrondissement="18",
        length_meters=80.0,
        accessibility="public_walk_cycle",
        geometry_json=json.dumps([[2.0, 48.0], [2.001, 48.0]]),
        min_lat=48.0,
        min_lon=2.0,
        max_lat=48.0,
        max_lon=2.001,
    )


def test_point_to_segment_distance_meters() -> None:
    distance, projected = point_to_segment_distance_meters(
        point=(5.0, 3.0),
        start=(0.0, 0.0),
        end=(10.0, 0.0),
    )

    assert distance == 3.0
    assert projected == 0.5


def test_matcher_accepts_stream_close_to_segment() -> None:
    settings = Settings(_env_file=None)
    matcher = SegmentMatcher(settings)

    match = matcher.match([[48.0, 2.0], [48.0, 2.0005], [48.0, 2.001]], _segment())

    assert match is not None
    assert match.coverage_ratio >= settings.match_min_coverage_ratio
    assert 0.0 <= match.confidence_score <= 1.0


def test_matcher_rejects_stream_too_far() -> None:
    matcher = SegmentMatcher(Settings(_env_file=None))

    match = matcher.match([[48.01, 2.0], [48.01, 2.001]], _segment())

    assert match is None


def test_matcher_rejects_low_coverage() -> None:
    settings = Settings(_env_file=None, match_min_coverage_ratio=0.8)
    matcher = SegmentMatcher(settings)

    match = matcher.match([[48.0, 2.0], [48.0, 2.0002]], _segment())

    assert match is None


def test_matcher_respects_minimum_matched_points() -> None:
    settings = Settings(_env_file=None, match_min_matched_points=3)
    matcher = SegmentMatcher(settings)

    match = matcher.match([[48.0, 2.0], [48.0, 2.001]], _segment())

    assert match is None
