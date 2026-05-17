# mapping_Paris

`mapping_Paris` is a personal Android application project for tracking which street segments have been completed in Paris intra-muros.

The repository will contain two future parts:

- an Android app used to display a 2D map of Paris, select street segments, and mark them as completed or not completed;
- an offline data preparation pipeline used to generate a local street segment dataset from OpenStreetMap before it is bundled into the app.

The project is local-first, personal-use only, and intended for APK distribution. It does not target Play Store publication, backend services, user accounts, or cloud synchronization.

## Documentation logic

The repository starts with a lightweight Logics Manager style documentation base:

- `docs/product/` captures product intent, scope, user value, and success criteria.
- `docs/adr/` records architecture decisions and their consequences.
- `docs/request/` captures high-level product requests before they are split into delivery work.
- `docs/backlog/` lists prioritized delivery slices.
- `docs/tasks/` tracks executable tasks and validation evidence.

This structure is intentionally small so future Codex tasks can be driven from clear, maintainable documents.

## Current status

The project has an MVP Android scaffold with:

- a Kotlin/Jetpack Compose app structure;
- an online OSM map integration through osmdroid;
- a local GeoJSON seed dataset for Paris segments;
- manual single-segment selection and completion state;
- local Room persistence for progress;
- global and arrondissement statistics.

APK validation is pending because the local shell does not currently expose a JDK, Gradle, or Android SDK.
