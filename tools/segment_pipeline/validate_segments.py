from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


FORBIDDEN_SOURCE_FIELDS = {"completed", "validated", "progress", "visited"}
REQUIRED_PROPERTIES = {
    "id",
    "street_name",
    "arrondissement",
    "length_meters",
    "accessibility",
    "source",
    "source_way_id",
    "source_way_index",
    "source_node_count",
    "highway",
}
PARIS_DATA_BBOX = (2.224, 48.815, 2.470, 48.906)


def coordinate_in_bbox(coordinate: list[float]) -> bool:
    lon, lat = coordinate
    min_lon, min_lat, max_lon, max_lat = PARIS_DATA_BBOX
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def validate(path: Path) -> tuple[list[str], dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    features = data.get("features", [])
    ids: list[str] = []
    arrondissement_counts: Counter[str] = Counter()

    if data.get("type") != "FeatureCollection":
        errors.append("Root type must be FeatureCollection")
    if len(features) < 1000:
        errors.append(f"Dataset is not dense enough: {len(features)} features")

    for index, feature in enumerate(features):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        missing = REQUIRED_PROPERTIES - set(properties)
        if missing:
            errors.append(f"Feature {index} missing properties: {sorted(missing)}")
        forbidden = FORBIDDEN_SOURCE_FIELDS & set(properties)
        if forbidden:
            errors.append(f"Feature {index} contains source-state fields: {sorted(forbidden)}")
        segment_id = properties.get("id")
        if segment_id:
            ids.append(segment_id)
        if geometry.get("type") != "LineString":
            errors.append(f"Feature {index} geometry must be LineString")
        coordinates = geometry.get("coordinates", [])
        if len(coordinates) < 2:
            errors.append(f"Feature {index} geometry must contain at least two coordinates")
        for coordinate in coordinates:
            if not coordinate_in_bbox(coordinate):
                errors.append(f"Feature {index} coordinate outside Paris bounds: {coordinate}")
                break
        if properties.get("length_meters", 0) <= 0:
            errors.append(f"Feature {index} length_meters must be positive")
        arrondissement_counts[str(properties.get("arrondissement", "unknown"))] += 1

    duplicate_ids = [segment_id for segment_id, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        errors.append(f"Duplicate ids found: {duplicate_ids[:20]}")

    summary = {
        "feature_count": len(features),
        "arrondissement_counts": dict(sorted(arrondissement_counts.items())),
        "duplicate_id_count": len(duplicate_ids),
    }
    return errors, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate generated Paris segment dataset.")
    parser.add_argument("dataset", nargs="?", default="data/generated/paris_segments.geojson")
    args = parser.parse_args()
    errors, summary = validate(Path(args.dataset))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        print("Validation errors:")
        for error in errors[:100]:
            print(f"- {error}")
        return 1
    print("Segment dataset validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
