from dataclasses import dataclass
import json
import math

from app.core.config import Settings
from app.db.models import B2StreetSegment


@dataclass(frozen=True)
class SegmentMatch:
    covered_length_meters: float
    coverage_ratio: float
    min_distance_meters: float
    avg_distance_meters: float
    max_distance_meters: float
    matched_points_count: int
    confidence_score: float
    raw_match: dict


def point_to_segment_distance_meters(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> tuple[float, float]:
    px, py = point
    ax, ay = start
    bx, by = end
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(px - ax, py - ay), 0.0
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    projected = (ax + t * dx, ay + t * dy)
    return math.hypot(px - projected[0], py - projected[1]), t


class SegmentMatcher:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def match(self, stream_latlng: list[list[float]], segment: B2StreetSegment) -> SegmentMatch | None:
        geometry_lonlat = json.loads(segment.geometry_json)
        if len(stream_latlng) < 2 or len(geometry_lonlat) < 2 or segment.length_meters <= 0:
            return None

        origin_lat = geometry_lonlat[0][1]
        origin_lon = geometry_lonlat[0][0]
        polyline = [
            self._to_local_meters(lat=point[1], lon=point[0], origin_lat=origin_lat, origin_lon=origin_lon)
            for point in geometry_lonlat
        ]
        trace = [
            self._to_local_meters(lat=point[0], lon=point[1], origin_lat=origin_lat, origin_lon=origin_lon)
            for point in stream_latlng
        ]
        cumulative = self._cumulative_lengths(polyline)
        total_geometry_length = cumulative[-1]
        if total_geometry_length <= 0:
            return None

        matched_distances: list[float] = []
        matched_positions: list[float] = []
        for point in trace:
            distance, projected_position = self._nearest_projection(point, polyline, cumulative)
            if distance <= self._settings.match_max_distance_meters:
                matched_distances.append(distance)
                matched_positions.append(projected_position)

        if len(matched_distances) < self._settings.match_min_matched_points:
            return None

        covered_geometry_length = max(matched_positions) - min(matched_positions)
        coverage_ratio = min(1.0, covered_geometry_length / total_geometry_length)
        if coverage_ratio < self._settings.match_min_coverage_ratio:
            return None

        covered_length_meters = coverage_ratio * segment.length_meters
        avg_distance = sum(matched_distances) / len(matched_distances)
        confidence_score = self._confidence(coverage_ratio, avg_distance, len(matched_distances))
        return SegmentMatch(
            covered_length_meters=covered_length_meters,
            coverage_ratio=coverage_ratio,
            min_distance_meters=min(matched_distances),
            avg_distance_meters=avg_distance,
            max_distance_meters=max(matched_distances),
            matched_points_count=len(matched_distances),
            confidence_score=confidence_score,
            raw_match={
                "coverage_ratio": coverage_ratio,
                "matched_points_count": len(matched_distances),
                "distance_threshold_meters": self._settings.match_max_distance_meters,
            },
        )

    def _nearest_projection(
        self,
        point: tuple[float, float],
        polyline: list[tuple[float, float]],
        cumulative: list[float],
    ) -> tuple[float, float]:
        best_distance = float("inf")
        best_position = 0.0
        for index in range(len(polyline) - 1):
            distance, t = point_to_segment_distance_meters(point, polyline[index], polyline[index + 1])
            if distance < best_distance:
                segment_length = cumulative[index + 1] - cumulative[index]
                best_distance = distance
                best_position = cumulative[index] + t * segment_length
        return best_distance, best_position

    def _cumulative_lengths(self, polyline: list[tuple[float, float]]) -> list[float]:
        cumulative = [0.0]
        for index in range(len(polyline) - 1):
            ax, ay = polyline[index]
            bx, by = polyline[index + 1]
            cumulative.append(cumulative[-1] + math.hypot(bx - ax, by - ay))
        return cumulative

    def _to_local_meters(
        self,
        lat: float,
        lon: float,
        origin_lat: float,
        origin_lon: float,
    ) -> tuple[float, float]:
        meters_per_lat = 111_320.0
        meters_per_lon = 111_320.0 * math.cos(math.radians(origin_lat))
        return (
            (lon - origin_lon) * meters_per_lon,
            (lat - origin_lat) * meters_per_lat,
        )

    def _confidence(self, coverage_ratio: float, avg_distance: float, matched_points_count: int) -> float:
        coverage_component = min(coverage_ratio, 1.0)
        distance_component = max(
            0.0,
            1.0 - avg_distance / self._settings.match_max_distance_meters,
        )
        points_component = min(matched_points_count / 5.0, 1.0)
        return max(
            0.0,
            min(1.0, 0.55 * coverage_component + 0.35 * distance_component + 0.10 * points_component),
        )
