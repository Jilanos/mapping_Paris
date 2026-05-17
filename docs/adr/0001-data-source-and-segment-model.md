# ADR 0001: Data Source and Segment Model

## Status

Accepted.

## Context

The project needs a practical street segment dataset for Paris intra-muros. The V1 goal is personal heritage tracking, not exhaustive GIS precision. The Android app should stay simple and should not perform heavy geospatial processing at runtime.

The dataset must exclude the Bois de Boulogne and Bois de Vincennes. It should focus on ways that represent streets, paths, or cycleable/walkable public passages useful for the personal tracking goal. The exact OpenStreetMap filtering rules can stay pragmatic and may be refined later.

The current target dataset is a dense generated segment mesh, not a small representative seed. The Chrome PWA tester is the validation surface for inspecting this mesh before Android import.

## Decision

The project will use OpenStreetMap as the street data source.

Street segments will be generated outside the Android app by a dedicated preprocessing pipeline. The first generated dataset is a GeoJSON file containing a dense Paris intra-muros segment mesh.

User progress will be stored separately inside the Android app, probably with Room. The source segment file must not contain a `completed` field or any other user-specific progress state.

Segment ids will be defined before app integration and used as stable references by the PWA tester and later Android app. Arrondissement attribution may be arbitrary for ambiguous or boundary-crossing segments. Geometry may be simplified: the goal is to represent Paris street segments clearly enough for personal tracking, not to preserve the exact shape of every street.

The first dense generation pass treats each filtered OSM way as a clickable segment and keeps validation state in the PWA separate from the source dataset.

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
- Some arrondissement and geometry details may be approximate by design.
- The PWA tester becomes the first gate for visual segment quality before Android import.

## Alternatives considered

- Generate segments directly in Android: rejected because it would add runtime complexity and make the app harder to maintain.
- Store completion state directly in the GeoJSON source file: rejected because source data and user data must remain separate.
- Use GPS validation in V1: rejected because V1 completion is intentionally manual.
- Build a custom basemap for V1: rejected because an online OSM map is sufficient for the first version.

## Open questions

- Which simple OpenStreetMap filtering rules should be used first to keep normal streets, pedestrian ways, and cycleable paths while excluding clearly private, inaccessible, or irrelevant ways?
