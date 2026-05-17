# OSM Dataset Generation Notes

## Current MVP dataset

The current app includes a compact seed dataset at:

- `app/src/main/assets/paris_segments_seed.geojson`

This file is intentionally small. It validates the Android MVP loop: local loading, map rendering, segment selection, manual completion, persistence, and statistics.

It is not the final full Paris dataset.

## Target generation approach

The future dataset should be generated outside Android from OpenStreetMap.

The first pragmatic rules should:

- keep Paris intra-muros only;
- exclude the Bois de Boulogne and the Bois de Vincennes;
- keep normal streets, pedestrian streets, paths, and cycleable ways useful for personal traversal;
- exclude clearly private, inaccessible, service-only, or irrelevant ways;
- split ways into segments between intersections when practical;
- assign stable ids before Android integration;
- assign arrondissement metadata pragmatically;
- export GeoJSON matching `docs/data/segment-contract.md`.

## Candidate OSM filtering direction

Start with OSM `highway` values that usually describe public street traversal:

- `primary`
- `secondary`
- `tertiary`
- `residential`
- `living_street`
- `pedestrian`
- `unclassified`
- `service` only when it represents a meaningful public passage
- `cycleway`
- `path`
- `footway`

Exclude or review carefully:

- `access=private`
- `access=no`
- internal parking aisles;
- service roads that are not useful for the personal tracking goal;
- ways outside Paris intra-muros;
- ways inside the excluded woods.

## Repeatability requirement

When the full OSM pipeline is implemented, it should document:

- input OSM extract source;
- filtering rules;
- Paris boundary source;
- woods exclusion method;
- segment splitting logic;
- id generation logic;
- export command;
- visual inspection steps.
