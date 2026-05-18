# Segment Length Histogram

Date: 2026-05-18

Dataset: `data/generated/paris_segments.geojson`

Generation rule update:

- segments shorter than 10 meters are removed from the generated dataset;
- OSM ways are split at detected street intersections;
- long between-intersection sections are split at existing OSM geometry nodes
  with a 350 meter target maximum;
- near-parallel same-name carriageways are deduplicated when they overlap, so a
  boulevard is not treated as two different streets only because OSM stores both
  traffic directions separately.

Total segments: 18,154

Total length: 1,355.51 km

Median segment length: 59.65 m

Minimum segment length: 10.01 m

Maximum segment length: 459.75 m

## Histogram

| Segment length | Count | Total length |
| --- | ---: | ---: |
| 0-5 m | 0 | 0.00 km |
| 5-10 m | 0 | 0.00 km |
| 10-20 m | 2,709 | 40.04 km |
| 20-50 m | 4,978 | 170.35 km |
| 50-100 m | 5,696 | 412.57 km |
| 100-200 m | 4,024 | 549.99 km |
| 200-350 m | 739 | 179.48 km |
| 350-500 m | 8 | 3.07 km |
| 500-1000 m | 0 | 0.00 km |
| >= 1000 m | 0 | 0.00 km |

```text
0-5 m         0 |
5-10 m        0 |
10-20 m   2,709 | ##############
20-50 m   4,978 | ##########################
50-100 m  5,696 | ##############################
100-200 m 4,024 | #####################
200-350 m   739 | ####
350-500 m     8 | #
500-1000 m    0 |
>= 1000 m     0 |
```

## Long Segment Check

No generated segment is longer than 500 meters.

Only 8 generated segments remain above 350 meters. These are cases where the
source OSM geometry has too few usable intermediate nodes to split cleanly
without inventing new geometry points.

Examples:

- Allée des Fortifications: 459.75 m
- Cours Albert-Ier: 435.23 m
- Chemin de l'Ancienne Écluse: 379.83 m
- Allée de Longchamp: 371.94 m
- Avenue Foch: 364.22 m

## Parallel Same-Street Check

The generator now deduplicates near-parallel same-name carriageways.

Current result:

- 633 generated segments carry `merged_parallel_source_count`, meaning they
  represent one logical clickable segment built from multiple near-parallel OSM
  source ways.
- `Boulevard de Clichy` went from 27 generated same-name segments after the
  intersection split to 17 generated same-name segments after parallel
  deduplication.

This is a heuristic V1. It reduces the "validate both directions" problem
without trying to build a full GIS conflation engine.
