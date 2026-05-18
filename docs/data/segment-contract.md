# Segment Data Contract

## Purpose

This contract defines the source segment dataset produced by the OpenStreetMap preprocessing pipeline and inspected in the Chrome PWA tester before Android import.

The source dataset contains street segment facts only. User progress is stored separately in the Android app and must not be written into this file.

The target dataset is a dense Paris street mesh inside the Boulevard Peripherique. It is not a one-segment-per-arrondissement sample.

## Format

Initial format: GeoJSON `FeatureCollection`.

Geometry type: `LineString`.

Coordinates follow GeoJSON order: longitude, latitude.

## Required properties

- `id`: stable segment id, predefined before app integration.
- `street_name`: human-readable street name.
- `arrondissement`: arrondissement label used for statistics.
- `length_meters`: segment length in meters.
- `accessibility`: pragmatic metadata when available.
- `source`: original data source, currently `openstreetmap`.
- `source_way_id`: OSM way id used to generate the segment.
- `source_way_index`: index of the generated segment inside the source way.
- `source_node_count`: count of OSM nodes used before simplification.
- `highway`: OSM highway type.

## Explicitly excluded properties

- `completed`
- `visited`
- `progress`
- `validated`
- any user-specific state

## Segment id rules

Segment ids are stable app references. Generated ids use a deterministic hash prefix such as `paris-seg-...`.

Future generated ids should remain stable across dataset refreshes whenever the represented segment is unchanged.

## Arrondissement rules

Arrondissement assignment can be approximate or arbitrary for ambiguous or boundary-crossing segments. The purpose is useful progress reporting, not administrative precision.

## Geometry rules

Geometry can be simplified. The rendered Paris street network must remain understandable at normal map zoom levels, but the line does not need to reproduce the exact shape of every street.

The first generated mesh treats each filtered OSM street way as a clickable segment and simplifies its polyline with a documented tolerance. It keeps ways whose midpoint falls inside a pragmatic Boulevard Peripherique polygon, which is simpler than subtracting the two Bois areas manually and preserves neighborhoods such as Auteuil and Bel-Air. It intentionally excludes OSM `footway`, `path`, `steps`, and `cycleway` values in the first inspection pass to avoid duplicated sidewalks and internal park/building paths.

## Example

```json
{
  "type": "Feature",
  "properties": {
    "id": "paris-seg-4f0b998f01d3",
    "street_name": "Rue de Rivoli",
    "arrondissement": "1",
    "length_meters": 620,
    "accessibility": "public_walk_cycle",
    "source": "openstreetmap",
    "source_way_id": 123456,
    "source_way_index": 0,
    "source_node_count": 8,
    "highway": "residential"
  },
  "geometry": {
    "type": "LineString",
    "coordinates": [[2.3297, 48.8609], [2.3364, 48.8616]]
  }
}
```
