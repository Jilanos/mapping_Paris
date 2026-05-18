from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

INCLUDED_HIGHWAYS = {
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "unclassified",
    "living_street",
    "pedestrian",
}

EXCLUDED_ACCESS = {"private", "no", "customers", "delivery", "emergency"}

PARIS_DATA_BBOX = (2.224, 48.815, 2.470, 48.906)

PERIPHERIQUE_POLYGON = [
    (2.255, 48.897),
    (2.300, 48.902),
    (2.365, 48.901),
    (2.405, 48.889),
    (2.418, 48.865),
    (2.414, 48.833),
    (2.392, 48.818),
    (2.320, 48.817),
    (2.270, 48.826),
    (2.248, 48.848),
    (2.246, 48.872),
]

ARRONDISSEMENT_CENTERS = {
    "1": (2.3364, 48.8626),
    "2": (2.3444, 48.8681),
    "3": (2.3600, 48.8629),
    "4": (2.3574, 48.8543),
    "5": (2.3507, 48.8448),
    "6": (2.3327, 48.8493),
    "7": (2.3126, 48.8565),
    "8": (2.3126, 48.8725),
    "9": (2.3375, 48.8770),
    "10": (2.3609, 48.8761),
    "11": (2.3800, 48.8584),
    "12": (2.3910, 48.8396),
    "13": (2.3561, 48.8322),
    "14": (2.3265, 48.8331),
    "15": (2.2923, 48.8401),
    "16": (2.2769, 48.8604),
    "17": (2.3075, 48.8873),
    "18": (2.3431, 48.8925),
    "19": (2.3840, 48.8871),
    "20": (2.3984, 48.8647),
}


def build_query() -> str:
    highway_regex = "|".join(sorted(INCLUDED_HIGHWAYS))
    return f"""
[out:json][timeout:240];
area["ref:INSEE"="75056"]["boundary"="administrative"]["admin_level"="8"]->.paris;
(
  way(area.paris)["highway"~"^({highway_regex})$"]["area"!="yes"]["access"!="private"]["access"!="no"];
);
(._;>;);
out body;
"""


def download_overpass(output_path: Path) -> None:
    query = build_query()
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(
        OVERPASS_URL,
        data=data,
        headers={"User-Agent": "mapping_Paris segment generator"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=420) as response:
        output_path.write_bytes(response.read())


def load_osm(path: Path, refresh: bool) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if refresh or not path.exists():
        download_overpass(path)
    return json.loads(path.read_text(encoding="utf-8"))


def midpoint(points: list[tuple[float, float]]) -> tuple[float, float]:
    lon = sum(point[0] for point in points) / len(points)
    lat = sum(point[1] for point in points) / len(points)
    return lon, lat


def in_bbox(point: tuple[float, float], bbox: tuple[float, float, float, float]) -> bool:
    lon, lat = point
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    lon, lat = point
    inside = False
    previous_lon, previous_lat = polygon[-1]
    for current_lon, current_lat in polygon:
        intersects = (current_lat > lat) != (previous_lat > lat)
        if intersects:
            crossing_lon = (previous_lon - current_lon) * (lat - current_lat) / (
                previous_lat - current_lat
            ) + current_lon
            if lon < crossing_lon:
                inside = not inside
        previous_lon, previous_lat = current_lon, current_lat
    return inside


def haversine_meters(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = a
    lon2, lat2 = b
    radius = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    h = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def nearest_arrondissement(point: tuple[float, float]) -> str:
    lon, lat = point
    best = None
    for arrondissement, center in ARRONDISSEMENT_CENTERS.items():
        distance = haversine_meters((lon, lat), center)
        if best is None or distance < best[1]:
            best = (arrondissement, distance)
    return best[0] if best else "unknown"


def stable_segment_id(
    way_id: int,
    index: int,
    name: str,
    a: tuple[float, float],
    b: tuple[float, float],
) -> str:
    payload = f"{way_id}|{index}|{name}|{a[0]:.7f},{a[1]:.7f}|{b[0]:.7f},{b[1]:.7f}"
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    return f"paris-seg-{digest}"


def normalize_street_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().casefold())


def perpendicular_distance_meters(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    lon, lat = point
    lon1, lat1 = start
    lon2, lat2 = end
    if start == end:
        return haversine_meters(point, start)
    x0 = lon
    y0 = lat
    x1 = lon1
    y1 = lat1
    x2 = lon2
    y2 = lat2
    numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
    denominator = math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
    degrees = numerator / denominator
    return degrees * 111_320


def simplify_polyline(
    points: list[tuple[float, float]],
    tolerance_meters: float,
) -> list[tuple[float, float]]:
    if len(points) <= 2:
        return points
    start = points[0]
    end = points[-1]
    max_distance = -1.0
    max_index = 0
    for index in range(1, len(points) - 1):
        distance = perpendicular_distance_meters(points[index], start, end)
        if distance > max_distance:
            max_distance = distance
            max_index = index
    if max_distance > tolerance_meters:
        left = simplify_polyline(points[: max_index + 1], tolerance_meters)
        right = simplify_polyline(points[max_index:], tolerance_meters)
        return left[:-1] + right
    return [start, end]


def split_indexes_for_way(
    node_ids: list[int],
    nodes: dict[int, tuple[float, float]],
    node_usage: Counter[int],
    max_length_meters: float,
) -> list[int]:
    split_indexes = {0, len(node_ids) - 1}
    for index, node_id in enumerate(node_ids[1:-1], start=1):
        if node_usage[node_id] > 1:
            split_indexes.add(index)

    ordered = sorted(split_indexes)
    expanded = set(ordered)
    for start_index, end_index in zip(ordered, ordered[1:]):
        path = [nodes[node_id] for node_id in node_ids[start_index : end_index + 1]]
        length_meters = sum(haversine_meters(a, b) for a, b in zip(path, path[1:]))
        if length_meters <= max_length_meters:
            continue
        split_count = max(2, math.ceil(length_meters / max_length_meters))
        target_step = length_meters / split_count
        cumulative = 0.0
        target = target_step
        for local_index in range(1, len(path) - 1):
            cumulative += haversine_meters(path[local_index - 1], path[local_index])
            if cumulative >= target:
                expanded.add(start_index + local_index)
                target += target_step
    return sorted(expanded)


def should_keep_way(tags: dict[str, str]) -> bool:
    highway = tags.get("highway")
    if highway not in INCLUDED_HIGHWAYS:
        return False
    access = tags.get("access")
    foot = tags.get("foot")
    bicycle = tags.get("bicycle")
    if access in EXCLUDED_ACCESS or foot in EXCLUDED_ACCESS or bicycle in EXCLUDED_ACCESS:
        return False
    if tags.get("service") in {"parking_aisle", "driveway", "drive-through", "emergency_access"}:
        return False
    return True


def build_features(
    osm: dict[str, Any],
    min_length_meters: float,
    simplify_tolerance_meters: float,
    max_length_meters: float,
) -> list[dict[str, Any]]:
    nodes: dict[int, tuple[float, float]] = {}
    ways: list[dict[str, Any]] = []

    for element in osm.get("elements", []):
        if element.get("type") == "node":
            nodes[element["id"]] = (element["lon"], element["lat"])
        elif element.get("type") == "way":
            ways.append(element)

    node_usage: Counter[int] = Counter()
    for way in ways:
        tags = way.get("tags", {})
        if not should_keep_way(tags):
            continue
        for node_id in way.get("nodes", []):
            if node_id in nodes:
                node_usage[node_id] += 1

    features: list[dict[str, Any]] = []
    seen_geometry: set[str] = set()

    for way in ways:
        tags = way.get("tags", {})
        if not should_keep_way(tags):
            continue
        node_ids = [node_id for node_id in way.get("nodes", []) if node_id in nodes]
        if len(node_ids) < 2:
            continue
        street_name = tags.get("name") or tags.get("ref") or "Unnamed way"
        highway = tags.get("highway", "unknown")
        ordered_split_indexes = split_indexes_for_way(
            node_ids=node_ids,
            nodes=nodes,
            node_usage=node_usage,
            max_length_meters=max_length_meters,
        )

        for split_index, (start_index, end_index) in enumerate(zip(ordered_split_indexes, ordered_split_indexes[1:])):
            path = [nodes[node_id] for node_id in node_ids[start_index : end_index + 1]]
            if len(path) < 2:
                continue
            mid = midpoint(path)
            if not in_bbox(mid, PARIS_DATA_BBOX):
                continue
            if not in_polygon(mid, PERIPHERIQUE_POLYGON):
                continue
            length_meters = sum(haversine_meters(a, b) for a, b in zip(path, path[1:]))
            if length_meters < min_length_meters:
                continue
            simplified_path = simplify_polyline(path, simplify_tolerance_meters)
            a = simplified_path[0]
            b = simplified_path[-1]

            geometry_key = "|".join(
                sorted(
                    [
                        f"{a[0]:.7f},{a[1]:.7f}",
                        f"{b[0]:.7f},{b[1]:.7f}",
                    ]
                )
            )
            if geometry_key in seen_geometry:
                continue
            seen_geometry.add(geometry_key)

            segment_id = stable_segment_id(way["id"], split_index, street_name, a, b)
            arrondissement = nearest_arrondissement(mid)
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "id": segment_id,
                        "street_name": street_name,
                        "arrondissement": arrondissement,
                        "length_meters": round(length_meters, 2),
                        "accessibility": accessibility_label(highway, tags),
                        "source": "openstreetmap",
                        "source_way_id": way["id"],
                        "source_way_index": split_index,
                        "source_node_count": len(path),
                        "highway": highway,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [round(point[0], 7), round(point[1], 7)]
                            for point in simplified_path
                        ],
                    },
                }
            )
    return remove_parallel_same_street_duplicates(features)


def remove_parallel_same_street_duplicates(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for feature in features:
        name = feature["properties"].get("street_name", "")
        grouped.setdefault(normalize_street_name(name), []).append(feature)

    result: list[dict[str, Any]] = []
    for name, group in grouped.items():
        if name in {"", "unnamed way"} or len(group) == 1:
            result.extend(group)
            continue
        kept: list[dict[str, Any]] = []
        for feature in sorted(group, key=lambda item: item["properties"]["length_meters"], reverse=True):
            duplicate_of = next(
                (candidate for candidate in kept if is_parallel_duplicate(feature, candidate)),
                None,
            )
            if duplicate_of is None:
                kept.append(feature)
            else:
                duplicate_of["properties"]["merged_parallel_source_count"] = (
                    duplicate_of["properties"].get("merged_parallel_source_count", 1) + 1
                )
        result.extend(kept)
    return result


def is_parallel_duplicate(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_points = [tuple(point) for point in left["geometry"]["coordinates"]]
    right_points = [tuple(point) for point in right["geometry"]["coordinates"]]
    if len(left_points) < 2 or len(right_points) < 2:
        return False

    left_line = line_metrics(left_points)
    right_line = line_metrics(right_points)
    if left_line["length"] < 20 or right_line["length"] < 20:
        return False
    angle_delta = abs(left_line["angle"] - right_line["angle"])
    angle_delta = min(angle_delta, 180 - angle_delta)
    if angle_delta > 14:
        return False

    distance = point_to_segment_distance_meters(
        right_line["midpoint"],
        left_line["start"],
        left_line["end"],
    )
    if distance > 32:
        return False

    overlap = interval_overlap(left_line["range"], project_interval(right_points, left_line))
    shortest = min(left_line["length"], right_line["length"])
    return shortest > 0 and overlap / shortest >= 0.22


def line_metrics(points: list[tuple[float, float]]) -> dict[str, Any]:
    start = points[0]
    end = points[-1]
    midpoint_value = midpoint(points)
    dx = (end[0] - start[0]) * 111_320 * math.cos(math.radians(midpoint_value[1]))
    dy = (end[1] - start[1]) * 111_320
    angle = math.degrees(math.atan2(dy, dx)) % 180
    projected = project_interval(points, {"start": start, "end": end})
    return {
        "start": start,
        "end": end,
        "midpoint": midpoint_value,
        "angle": angle,
        "length": max(haversine_meters(start, end), 0.001),
        "range": projected,
    }


def project_interval(points: list[tuple[float, float]], line: dict[str, Any]) -> tuple[float, float]:
    start = line["start"]
    end = line["end"]
    mid_lat = (start[1] + end[1]) / 2
    sx, sy = lonlat_to_xy(start, mid_lat)
    ex, ey = lonlat_to_xy(end, mid_lat)
    dx = ex - sx
    dy = ey - sy
    denominator = dx * dx + dy * dy
    if denominator == 0:
        return (0.0, 0.0)
    values = []
    for point in points:
        px, py = lonlat_to_xy(point, mid_lat)
        values.append(((px - sx) * dx + (py - sy) * dy) / math.sqrt(denominator))
    return min(values), max(values)


def lonlat_to_xy(point: tuple[float, float], reference_lat: float) -> tuple[float, float]:
    lon, lat = point
    return (
        lon * 111_320 * math.cos(math.radians(reference_lat)),
        lat * 111_320,
    )


def point_to_segment_distance_meters(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    mid_lat = (start[1] + end[1]) / 2
    px, py = lonlat_to_xy(point, mid_lat)
    sx, sy = lonlat_to_xy(start, mid_lat)
    ex, ey = lonlat_to_xy(end, mid_lat)
    dx = ex - sx
    dy = ey - sy
    if dx == 0 and dy == 0:
        return math.hypot(px - sx, py - sy)
    t = ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    projected_x = sx + t * dx
    projected_y = sy + t * dy
    return math.hypot(px - projected_x, py - projected_y)


def interval_overlap(left: tuple[float, float], right: tuple[float, float]) -> float:
    return max(0.0, min(left[1], right[1]) - max(left[0], right[0]))


def accessibility_label(highway: str, tags: dict[str, str]) -> str:
    if highway in {"footway", "pedestrian", "steps"}:
        return "public_walk"
    if highway == "cycleway":
        return "public_cycle"
    if tags.get("bicycle") in {"yes", "designated"}:
        return "public_walk_cycle"
    return "public_walk_cycle"


def write_geojson(features: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    collection = {
        "type": "FeatureCollection",
        "name": "mapping_paris_generated_segments",
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scope": "Paris intra-muros street segment mesh",
            "source": "OpenStreetMap via Overpass API",
            "boundary": "Approximate Boulevard Peripherique polygon",
            "excluded": ["ways outside the Boulevard Peripherique"],
            "notes": [
                "Segments are generated as individual clickable elements.",
                "Validation/completion state is intentionally excluded from source data.",
                "Arrondissement assignment is nearest-center approximation for this first generated mesh.",
            ],
        },
        "features": features,
    }
    output_path.write_text(
        json.dumps(collection, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def write_summary(features: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    arrondissement_counts = Counter(
        feature["properties"].get("arrondissement", "unknown") for feature in features
    )
    highway_counts = Counter(feature["properties"].get("highway", "unknown") for feature in features)
    total_meters = sum(feature["properties"].get("length_meters", 0) for feature in features)
    lines = [
        "# Generated Segment Dataset Summary",
        "",
        f"Generated at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "",
        f"Total segments: {len(features)}",
        f"Total length: {total_meters / 1000:.2f} km",
        "",
        "## Segments by Arrondissement",
        "",
    ]
    for arrondissement, count in sorted(arrondissement_counts.items(), key=lambda item: item[0]):
        lines.append(f"- {arrondissement}: {count}")
    lines.extend(["", "## Segments by Highway Type", ""])
    for highway, count in sorted(highway_counts.items(), key=lambda item: item[0]):
        lines.append(f"- {highway}: {count}")
    lines.extend(
        [
            "",
            "## Known Limitations",
            "",
            "- Arrondissement assignment uses nearest arrondissement center approximation.",
            "- Intra-muros filtering uses a pragmatic hand-drawn Boulevard Peripherique polygon.",
            "- The first street-only mesh excludes footways, paths, steps, and cycleways to avoid sidewalk/internal-path duplication.",
            "- Geometry is generated from filtered OSM ways and simplified for visual inspection in the PWA.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Paris street segments from OSM.")
    parser.add_argument("--raw", default="data/raw/paris_osm_highways.json")
    parser.add_argument("--out", default="data/generated/paris_segments.geojson")
    parser.add_argument("--summary", default="docs/data/generated-segment-summary.md")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--min-length-meters", type=float, default=10.0)
    parser.add_argument("--simplify-tolerance-meters", type=float, default=4.0)
    parser.add_argument("--max-length-meters", type=float, default=350.0)
    args = parser.parse_args()

    raw_path = Path(args.raw)
    output_path = Path(args.out)
    summary_path = Path(args.summary)

    osm = load_osm(raw_path, refresh=args.refresh)
    features = build_features(
        osm,
        min_length_meters=args.min_length_meters,
        simplify_tolerance_meters=args.simplify_tolerance_meters,
        max_length_meters=args.max_length_meters,
    )
    if len(features) < 1000:
        print(f"Generated only {len(features)} segments; expected dense Paris mesh.", file=sys.stderr)
        return 2
    write_geojson(features, output_path)
    write_summary(features, summary_path)
    print(f"Generated {len(features)} segments")
    print(f"Wrote {output_path}")
    print(f"Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
