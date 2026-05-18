# Segment Length Histogram

Date: 2026-05-18

Dataset: `data/generated/paris_segments.geojson`

Generation rule update:

- segments shorter than 10 meters are removed from the generated dataset;
- OSM ways are split at detected street intersections;
- long between-intersection sections are split at existing OSM geometry nodes with a 350 meter target maximum;
- near-parallel same-name carriageways keep their visual geometry but share a `logical_segment_id`, so they are selected and validated as one user-facing block.

Total visual segment geometries: 18,963

Total logical clickable blocks: 18,001

Total visual length: 1418.40 km

Median visual segment length: 59.78 m

Minimum segment length: 10.01 m

Maximum segment length: 459.75 m

## Histogram

| Segment length | Count | Total length |
| --- | ---: | ---: |
| 0-5 m | 0 | 0.00 km |
| 5-10 m | 0 | 0.00 km |
| 10-20 m | 2,709 | 40.04 km |
| 20-50 m | 5,298 | 180.88 km |
| 50-100 m | 5,968 | 432.42 km |
| 100-200 m | 4,211 | 575.64 km |
| 200-350 m | 769 | 186.35 km |
| 350-500 m | 8 | 3.07 km |
| 500-1000 m | 0 | 0.00 km |
| >= 1000 m | 0 | 0.00 km |

```text
0-5 m          0 |
5-10 m         0 |
10-20 m    2,709 | ##############
20-50 m    5,298 | ###########################
50-100 m   5,968 | ##############################
100-200 m  4,211 | #####################
200-350 m    769 | ####
350-500 m      8 |
500-1000 m     0 |
>= 1000 m      0 |
```

## Long Segment Check

No generated segment is longer than 500 meters.

Only 8 generated visual geometries remain above 350 meters.

## Parallel Same-Street Check

The generator now links near-parallel same-name carriageways without removing their visual geometry.

- 1,556 visual geometries carry `merged_parallel_source_count`.
- PWA and Android use `logical_segment_id` for selection, completion, and statistics.
- This keeps both sides of boulevards visible while requiring one validation action from the user.

- Boulevard De Clichy: 27 visual geometries, 14 logical blocks.
- Boulevard Marguerite De Rochechouart: 21 visual geometries, 13 logical blocks.
