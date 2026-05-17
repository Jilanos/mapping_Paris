# Segment Data Contract

## Purpose

This contract defines the source segment dataset consumed by the Android app and produced by the future OpenStreetMap preprocessing pipeline.

The source dataset contains street segment facts only. User progress is stored separately in the Android app and must not be written into this file.

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

## Explicitly excluded properties

- `completed`
- `visited`
- `progress`
- any user-specific state

## Segment id rules

Segment ids are stable app references. The first MVP seed uses readable ids such as `paris-001-rivoli-001`.

Future generated ids should remain stable across dataset refreshes whenever the represented segment is unchanged.

## Arrondissement rules

Arrondissement assignment can be approximate or arbitrary for ambiguous or boundary-crossing segments. The purpose is useful progress reporting, not administrative precision.

## Geometry rules

Geometry can be simplified. The rendered Paris street network must remain understandable at normal map zoom levels, but the line does not need to reproduce the exact shape of every street.

## Example

```json
{
  "type": "Feature",
  "properties": {
    "id": "paris-001-rivoli-001",
    "street_name": "Rue de Rivoli",
    "arrondissement": "1",
    "length_meters": 620,
    "accessibility": "public_walk_cycle"
  },
  "geometry": {
    "type": "LineString",
    "coordinates": [[2.3297, 48.8609], [2.3364, 48.8616]]
  }
}
```
