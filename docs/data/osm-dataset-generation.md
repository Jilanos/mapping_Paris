# OSM Dataset Generation Notes

## Current MVP dataset

The current app includes a compact seed dataset at:

- `app/src/main/assets/paris_segments_seed.geojson`

This file is intentionally small. It validates the Android MVP loop: local loading, map rendering, segment selection, manual completion, persistence, and statistics.

It is not the final full Paris dataset.

## Target generation approach

The future dataset should be generated outside Android from OpenStreetMap.

The first pragmatic rules should:

- keep streets inside the Boulevard Peripherique;
- use the Peripherique boundary instead of broad Bois de Boulogne / Bois de Vincennes exclusion boxes;
- keep normal streets and pedestrian streets first;
- exclude sidewalk-like and internal pedestrian geometry in the first inspection pass;
- exclude clearly private, inaccessible, service-only, or irrelevant ways;
- split ways into segments between intersections when practical;
- assign stable ids before Android integration;
- assign arrondissement metadata pragmatically;
- export GeoJSON matching `docs/data/segment-contract.md`.

## Candidate OSM filtering direction

Start with OSM `highway` values that usually describe public street traversal without duplicating sidewalks and internal paths:

- `primary`
- `secondary`
- `tertiary`
- `residential`
- `living_street`
- `pedestrian`
- `unclassified`

Exclude or review carefully:

- `access=private`
- `access=no`
- `footway`, because Paris OSM often maps both sidewalks separately from the street;
- `path`, because it pulls in many park, station, library, and building-internal paths;
- `steps`, because it pulls in many micro-segments;
- `cycleway`, until a later pass decides whether separate bike lanes are useful tracking targets;
- internal parking aisles;
- service roads that are not useful for the personal tracking goal;
- ways outside the Boulevard Peripherique.

## Repeatability requirement

When the full OSM pipeline is implemented, it should document:

- input OSM extract source;
- filtering rules;
- Paris boundary source;
- Peripherique polygon method;
- segment splitting logic;
- id generation logic;
- export command;
- visual inspection steps.
