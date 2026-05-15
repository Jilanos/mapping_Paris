# ADR 0001: Data Source and Segment Model

## Status

Accepted.

## Context

The project needs a practical street segment dataset for Paris intra-muros. The V1 goal is personal heritage tracking, not exhaustive GIS precision. The Android app should stay simple and should not perform heavy geospatial processing at runtime.

The dataset must exclude the Bois de Boulogne and Bois de Vincennes and include public ways that are reasonably walkable or bikeable.

## Decision

The project will use OpenStreetMap as the street data source.

Street segments will be generated outside the Android app by a dedicated preprocessing pipeline. The Android app will consume a local preprocessed file, probably GeoJSON, containing segments for Paris intra-muros.

User progress will be stored separately inside the Android app, probably with Room. The source segment file must not contain a `completed` field or any other user-specific progress state.

Conceptual segment model:

- stable segment id
- street name
- arrondissement
- length in meters
- geometry as polyline
- metadata about accessibility if available

## Consequences

- Android runtime complexity stays low.
- The segment dataset can be regenerated when the OSM extraction rules improve.
- User progress can survive segment source updates if stable ids are preserved.
- The app can remain local-first with no backend or account system.
- Dataset quality depends on the preprocessing pipeline and OpenStreetMap coverage.

## Alternatives considered

- Generate segments directly in Android: rejected because it would add runtime complexity and make the app harder to maintain.
- Store completion state directly in the GeoJSON source file: rejected because source data and user data must remain separate.
- Use GPS validation in V1: rejected because V1 completion is intentionally manual.
- Build a custom basemap for V1: rejected because an online OSM map is sufficient for the first version.

## Open questions

- What exact OSM tags define public walkable or bikeable ways for V1?
- How should stable segment ids be generated and preserved across dataset refreshes?
- How should arrondissement attribution be handled for segments crossing boundaries?
- What simplification tolerance is acceptable for rendering performance without losing useful street shape?
