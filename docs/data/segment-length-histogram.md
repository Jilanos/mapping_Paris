# Segment Length Histogram

Date: 2026-05-18

Dataset: `data/generated/paris_segments.geojson`

Total segments: 15,295

Total length: 1,430.73 km

Median segment length: 63.37 m

Minimum segment length: 2.02 m

Maximum segment length: 1,220.69 m

## Histogram

| Segment length | Count | Total length |
| --- | ---: | ---: |
| 0-5 m | 281 | 1.06 km |
| 5-10 m | 932 | 7.14 km |
| 10-20 m | 1,943 | 28.63 km |
| 20-50 m | 3,451 | 114.81 km |
| 50-100 m | 3,411 | 249.51 km |
| 100-200 m | 3,501 | 495.91 km |
| 200-500 m | 1,686 | 475.56 km |
| 500-1000 m | 86 | 53.57 km |
| >= 1000 m | 4 | 4.55 km |

```text
0-5 m       281 | ##
5-10 m      932 | #######
10-20 m   1,943 | ################
20-50 m   3,451 | ############################
50-100 m  3,411 | ############################
100-200 m 3,501 | #############################
200-500 m 1,686 | ##############
500-1000 m   86 | #
>= 1000 m     4 | #
```

## Small Segment Finding

There are 1,213 segments shorter than 10 meters.

There are 281 segments shorter than 5 meters.

The short-segment group is visually noisy and should be handled in the next
dataset-generation pass.

Recommended V1 rule:

- remove or merge segments shorter than 5 meters by default;
- merge 5-10 meter segments into a same-street neighbor when they share or nearly
  touch an endpoint;
- keep short segments only when they are the only representation of a named
  street connector.

## Parallel Same-Street Finding

Some Paris boulevards appear as two parallel OSM carriageways because OSM models
separated lanes, medians, tram tracks, or pedestrian refuges as distinct ways.
For this product, those should usually become one clickable street block. The
user should not need to validate both directions of the same boulevard.

Example: `Boulevard de Clichy` currently appears as multiple same-name parallel
and adjacent segments around Place de Clichy.

Recommended V1 rule:

- group candidate segments by normalized street name;
- within each street group, detect near-parallel segments with similar bearing;
- treat segments within roughly 8-18 meters of each other and with overlapping
  projected length as the same logical street block;
- merge each candidate group into one clickable segment/block using a simplified
  centerline or representative geometry;
- keep the source way ids in metadata for traceability.

Open decision:

- choose whether the source GeoJSON should store only the merged clickable
  blocks, or store raw visual lanes plus a shared `logical_segment_id`.
