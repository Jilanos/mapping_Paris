# mapping_Paris

`mapping_Paris` is a local-first personal app for tracking manually completed
street segments in Paris.

The project deliberately keeps three things separate:

- the source street segment dataset generated from OpenStreetMap;
- the user's completion or validation state;
- the Android app and local PWA inspection tooling.

There is no backend, no account system, no GPS validation, and no cloud sync in
the current scope.

## Current State

The repository now contains:

- an Android Kotlin / Jetpack Compose scaffold;
- a local Room database for future user progress persistence;
- an osmdroid map integration in the Android app;
- a generated Paris street segment dataset at
  `data/generated/paris_segments.geojson`;
- a local PWA tester in `pwa/` for visual inspection and manual validation;
- a repeatable OSM generation and validation pipeline in
  `tools/segment_pipeline/`;
- a small dependency-free Node dev server exposed through `npm run dev`.

The generated dataset currently contains `15,295` street segments and about
`1,430.73 km` of total segment length.

## Segment Dataset

The current V1 dataset is generated from OpenStreetMap and keeps streets whose
midpoint falls inside a pragmatic Boulevard Peripherique polygon.

Included OSM `highway` values:

- `primary`
- `secondary`
- `tertiary`
- `residential`
- `unclassified`
- `living_street`
- `pedestrian`

Excluded in the first inspection pass:

- `footway`
- `path`
- `steps`
- `cycleway`
- private, inaccessible, service-only, or irrelevant ways

This keeps the map close to the street network instead of tripling most streets
with separately mapped sidewalks or internal park/building paths. Private alleys
such as `Square de Port-Royal` and `Impasse de la Santé` are intentionally not
included while they remain tagged as private service alleys in OSM.

Regenerate the dataset:

```powershell
py -3 tools\segment_pipeline\generate_paris_segments.py --refresh
```

Validate the dataset:

```powershell
py -3 tools\segment_pipeline\validate_segments.py
```

## PWA Tester

The PWA is the current inspection surface for the generated segment mesh before
Android import.

Run it locally:

```powershell
npm run dev
```

Then open the URL printed by the server, normally:

```text
http://localhost:5173/pwa/
```

If port `5173` is already in use, the dev server automatically tries the next
available port and prints the final URL.

The tester supports:

- Leaflet canvas rendering of the full segment mesh;
- startup zoom directly on Paris;
- map bounds constrained around Paris / Ile-de-France;
- click-to-select one or more segments;
- validate or unvalidate the selected segment set;
- localStorage persistence for validation state;
- export of validated segment ids to JSON.

PWA checks:

```powershell
npm run check:pwa
py -3 tools\segment_pipeline\validate_pwa.py
```

## Android APK Build

The local machine has been prepared with:

- JDK 17 Temurin;
- Android SDK command line tools;
- `platform-tools`;
- `platforms;android-35`;
- `build-tools;35.0.0`.

The expected environment variables are:

```text
JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.19.10-hotspot
ANDROID_HOME=C:\Users\Pmondou\AppData\Local\Android\Sdk
ANDROID_SDK_ROOT=C:\Users\Pmondou\AppData\Local\Android\Sdk
```

Build a debug APK:

```powershell
.\gradlew.bat assembleDebug
```

If a reused Gradle daemon hangs, use:

```powershell
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

Expected output:

```text
app\build\outputs\apk\debug\app-debug.apk
```

## Validation Commands

Useful project checks:

```powershell
py -3 tools\segment_pipeline\validate_segments.py
py -3 tools\segment_pipeline\validate_pwa.py
npm run check:pwa
node --check tools\dev-server.mjs
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

## Documentation

Project documentation lives under `docs/`:

- `docs/product/` for product intent and scope;
- `docs/adr/` for architecture decisions;
- `docs/request/` for high-level requests;
- `docs/backlog/` for delivery slices;
- `docs/tasks/` for executable task tracking;
- `docs/data/` for dataset contracts and generation notes;
- `docs/development/` for local build and development notes.

## Non-Goals

The current V1 does not target:

- backend services;
- user accounts;
- cloud sync;
- GPS validation;
- Play Store publication;
- perfect GIS topology.
