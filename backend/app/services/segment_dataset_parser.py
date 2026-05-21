from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


class SegmentDatasetParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedSegment:
    segment_id: str
    logical_segment_id: str
    street_name: str
    arrondissement: str
    length_meters: float
    accessibility: str | None
    geometry: list[list[float]]
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


@dataclass(frozen=True)
class ParsedSegmentDataset:
    source_path: str
    source_file_name: str
    source_file_size_bytes: int
    dataset_hash: str
    segments: list[ParsedSegment]

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    @property
    def logical_segment_count(self) -> int:
        return len({segment.logical_segment_id for segment in self.segments})


class SegmentDatasetParser:
    def parse_file(self, source: str | Path) -> ParsedSegmentDataset:
        path = Path(source)
        raw_bytes = path.read_bytes()
        return self.parse_bytes(raw_bytes, source_path=str(path), source_file_name=path.name)

    def parse_bytes(
        self,
        raw_bytes: bytes,
        source_path: str = "<memory>",
        source_file_name: str = "memory.geojson",
    ) -> ParsedSegmentDataset:
        try:
            root = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SegmentDatasetParseError("Segment dataset must be valid UTF-8 GeoJSON") from exc

        if root.get("type") != "FeatureCollection":
            raise SegmentDatasetParseError("Segment dataset must be a GeoJSON FeatureCollection")
        features = root.get("features")
        if not isinstance(features, list):
            raise SegmentDatasetParseError("Segment dataset must contain a features array")

        segments = [self._parse_feature(feature, index) for index, feature in enumerate(features)]
        return ParsedSegmentDataset(
            source_path=source_path,
            source_file_name=source_file_name,
            source_file_size_bytes=len(raw_bytes),
            dataset_hash=hashlib.sha256(raw_bytes).hexdigest(),
            segments=segments,
        )

    def _parse_feature(self, feature: Any, index: int) -> ParsedSegment:
        if not isinstance(feature, dict):
            raise SegmentDatasetParseError(f"Feature {index} must be an object")
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(properties, dict):
            raise SegmentDatasetParseError(f"Feature {index} is missing properties")
        if not isinstance(geometry, dict):
            raise SegmentDatasetParseError(f"Feature {index} is missing geometry")
        if geometry.get("type") != "LineString":
            raise SegmentDatasetParseError(f"Feature {index} geometry must be LineString")

        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            raise SegmentDatasetParseError(f"Feature {index} must contain at least two coordinates")
        normalized_coordinates = self._normalize_coordinates(coordinates, index)

        segment_id = self._required_string(properties, "id", index)
        logical_segment_id = str(properties.get("logical_segment_id") or segment_id)
        street_name = self._required_string(properties, "street_name", index)
        arrondissement = self._required_string(properties, "arrondissement", index)
        length_meters = self._required_float(properties, "length_meters", index)
        accessibility = properties.get("accessibility")
        lats = [point[1] for point in normalized_coordinates]
        lons = [point[0] for point in normalized_coordinates]

        return ParsedSegment(
            segment_id=segment_id,
            logical_segment_id=logical_segment_id,
            street_name=street_name,
            arrondissement=arrondissement,
            length_meters=length_meters,
            accessibility=str(accessibility) if accessibility is not None else None,
            geometry=normalized_coordinates,
            min_lat=min(lats),
            min_lon=min(lons),
            max_lat=max(lats),
            max_lon=max(lons),
        )

    def _normalize_coordinates(self, coordinates: list[Any], index: int) -> list[list[float]]:
        normalized: list[list[float]] = []
        for point_index, point in enumerate(coordinates):
            if not isinstance(point, list) or len(point) < 2:
                raise SegmentDatasetParseError(
                    f"Feature {index} coordinate {point_index} must contain lon and lat"
                )
            normalized.append([float(point[0]), float(point[1])])
        return normalized

    def _required_string(self, properties: dict[str, Any], key: str, index: int) -> str:
        value = properties.get(key)
        if value is None or str(value).strip() == "":
            raise SegmentDatasetParseError(f"Feature {index} is missing required property {key}")
        return str(value)

    def _required_float(self, properties: dict[str, Any], key: str, index: int) -> float:
        value = properties.get(key)
        if value is None:
            raise SegmentDatasetParseError(f"Feature {index} is missing required property {key}")
        return float(value)
