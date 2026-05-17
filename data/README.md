# Data Artifacts

## Generated dataset

The full Paris segment mesh is generated into:

- `data/generated/paris_segments.geojson`

The generated dataset is source geometry only. It must not contain `completed`, `validated`, `visited`, or user progress fields.

## Raw OSM cache

The pipeline downloads the Overpass response into:

- `data/raw/paris_osm_highways.json`

This raw cache is ignored by Git. Rebuild it with:

```powershell
py -3 tools/segment_pipeline/generate_paris_segments.py --refresh
```

## Validation

Run:

```powershell
py -3 tools/segment_pipeline/validate_segments.py
```
