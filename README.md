# mapping_Paris

`mapping_Paris` is a local-first personal app for tracking manually completed
street segments in Paris.

The project deliberately keeps three things separate:

- the source street segment dataset generated from OpenStreetMap;
- the user's completion or validation state;
- the Android app and local PWA inspection tooling.

There is no backend, no account system, no automatic GPS validation, and no
cloud sync in the current scope.

## Current State

The repository now contains:

- an Android Kotlin / Jetpack Compose scaffold;
- a local Room database for user progress persistence;
- an osmdroid map integration in the Android app;
- a generated Paris street segment dataset at
  `data/generated/paris_segments.geojson`;
- the same generated dataset packaged in the Android asset
  `app/src/main/assets/paris_segments.geojson`;
- a local PWA tester in `pwa/` for visual inspection and manual validation;
- a repeatable OSM generation and validation pipeline in
  `tools/segment_pipeline/`;
- a small dependency-free Node dev server exposed through `npm run dev`.

The generated dataset currently contains `18,963` visible street geometries and
`18,001` logical clickable blocks.

## Version 0.2 Preview

Version 0.2 focuses on making the Android app usable as a map-first mobile
tool: a compact top-left menu, contextual bottom actions only when segments are
selected, import/export, search, filters, light/blue map modes, and refreshed
project visuals.

| Map | Menu |
| --- | --- |
| ![Android 0.2 map](docs/assets/readme/android-0-2-map.png) | ![Android 0.2 menu](docs/assets/readme/android-0-2-menu.png) |

| Selection | Statistics |
| --- | --- |
| ![Android 0.2 selected segments](docs/assets/readme/android-0-2-selection.png) | ![Android 0.2 statistics](docs/assets/readme/android-0-2-stats.png) |

## Version 0.3 GPS Preview

Version 0.3 adds foreground GPS assistance to the Android app while keeping the
project local-first and manual-first.

The Android app can now:

- request foreground location permission when GPS is used;
- show the current position and accuracy radius on the map;
- recenter only when the GPS button is pressed;
- keep GPS-assisted behavior disabled by default on first install;
- expose GPS assistance and matching strictness in settings;
- use the foreground GPS path to propose likely covered segments as editable
  selections;
- keep final completion under explicit user control.

GPS data stays local to the device. When GPS assistance is enabled, the app can
keep tracking through a foreground service while the phone is locked. There is
no automatic segment completion, no route upload, and no cloud sync.

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
app\build\outputs\apk\debug\mapping-paris-<version>-debug.apk
```

### Debug Install And Signature Mismatch

Use the local helper to build and install the latest debug APK on a connected
Android device:

```powershell
cmd /c tools\build-and-install-debug-apk.cmd
```

If Android reports `INSTALL_FAILED_UPDATE_INCOMPATIBLE`, the phone already has
`com.jilanos.mappingparis` installed with a different signing key. This commonly
happens when a previous debug APK was built from another machine, another
checkout, or another debug keystore. Android will not update that app in place.

Do not uninstall blindly if the app contains progress you want to keep. First
open the app and export the progression. Then uninstall and reinstall:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" uninstall com.jilanos.mappingparis
cmd /c tools\build-and-install-debug-apk.cmd
```

Uninstalling deletes local Room data, settings, and any progression that has not
been exported.

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
- automatic GPS validation;
- closed-app route history or cloud GPS tracking;
- Play Store publication;
- perfect GIS topology.
