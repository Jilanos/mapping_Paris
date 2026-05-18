# Handoff: mapping Paris Current Context

Date: 2026-05-18

Repository: `mapping_Paris`

Remote: `https://github.com/Jilanos/mapping_Paris.git`

Branch: `main`

## Current State

The project is a local-first personal Android app plus PWA tester for manually
tracking completed street segments in Paris intra-muros.

Current latest pushed commit before the 0.2 implementation:

- `a7ecedb Plan Android 0.2 UX hardening`

Generated APK available locally:

- `app/build/outputs/apk/debug/mapping-paris-0.2.0-debug.apk`

Current datasets:

- Source/tester dataset: `data/generated/paris_segments.geojson`
- Android packaged asset: `app/src/main/assets/paris_segments.geojson`

Dataset state:

- 18,963 visible segment geometries.
- 18,001 logical clickable blocks.
- 1,556 geometries are linked into parallel same-street groups.
- 0 segments shorter than 10 m.
- 0 segments longer than 500 m.

Key model decision:

- `id` remains the visual/source geometry id.
- `logical_segment_id` is the user-facing clickable/completion id.
- Parallel same-name carriageways remain visible to avoid holes in boulevards,
  but selection, validation, and statistics use `logical_segment_id`.

## Version 0.2 State

- Android `versionName` is `0.2.0`.
- The map is now map-first: no permanent empty bottom panel when no segment is
  selected.
- A custom top-left menu opens settings, statistics, and light/blue map mode
  selection.
- Main selected-segment actions use a contextual bottom bar.
- Complete/uncomplete actions provide a snackbar undo.
- Settings contains import, export, and reset-all-progress.
- Import conflict choices are merge, replace, and cancel.
- Street search supports accent-insensitive partial matching and recenters the
  map without auto-selecting segments.
- Filters are hidden behind a separate filter icon and are shown only when that
  icon is pressed.
- The map supports both light Carto/OSM mode and a blue local overlay mode.
- A visual-id to `logical_segment_id` migration path runs on startup for old
  local Room rows.
- The icon direction is stored as a raster source asset and launcher vectors
  were refreshed to stay close to Image #1.
- README now includes committed 0.2 visual PNGs.

## Important Files

Android UI and rendering:

- `app/src/main/java/com/jilanos/mappingparis/ui/MappingParisApp.kt`
- `app/src/main/java/com/jilanos/mappingparis/ui/ParisMapOverlays.kt`
- `app/src/main/java/com/jilanos/mappingparis/ui/MappingParisViewModel.kt`

Android data model:

- `app/src/main/java/com/jilanos/mappingparis/data/StreetSegment.kt`
- `app/src/main/java/com/jilanos/mappingparis/data/SegmentGeoJsonParser.kt`
- `app/src/main/java/com/jilanos/mappingparis/data/SegmentRepository.kt`
- `app/src/main/java/com/jilanos/mappingparis/data/SegmentCompletionDao.kt`

PWA tester:

- `pwa/index.html`
- `pwa/app.js`
- `pwa/styles.css`
- `pwa/service-worker.js`

Dataset pipeline and reports:

- `tools/segment_pipeline/generate_paris_segments.py`
- `tools/segment_pipeline/validate_segments.py`
- `docs/data/generated-segment-summary.md`
- `docs/data/segment-length-histogram.md`

Icon and README visual assets:

- `app/src/main/assets/image-1-source.png`
- `docs/assets/icon/image-1-source.png`
- `docs/assets/readme/android-0-2-map.png`
- `docs/assets/readme/android-0-2-menu.png`
- `docs/assets/readme/android-0-2-selection.png`
- `docs/assets/readme/android-0-2-stats.png`

0.2 planning and report:

- `docs/request/0004-prepare-version-0-2-mobile-ux-and-product-hardening.md`
- `docs/tasks/0005-deliver-android-0-2-mobile-ux-and-product-hardening.md`

## Validation Commands

Use these after pulling:

```powershell
git status --short --branch
py -3 tools\segment_pipeline\validate_segments.py data\generated\paris_segments.geojson
py -3 tools\segment_pipeline\validate_segments.py app\src\main\assets\paris_segments.geojson
npm run check:pwa
py -3 tools\segment_pipeline\validate_pwa.py
node --check tools\dev-server.mjs
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

APK verification:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\build-tools\35.0.0\apksigner.bat" verify --print-certs app\build\outputs\apk\debug\mapping-paris-0.2.0-debug.apk
```

APK asset inspection:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\build-tools\35.0.0\aapt.exe" list app\build\outputs\apk\debug\mapping-paris-0.2.0-debug.apk
```

PWA local test:

```powershell
py -3 -m http.server 5173
```

Then open:

```text
http://localhost:5173/pwa/
```

## Validation Already Run

- `py -3 tools\segment_pipeline\validate_segments.py data\generated\paris_segments.geojson`
  - OK: 18,963 features, duplicate_id_count 0.
- `py -3 tools\segment_pipeline\validate_segments.py app\src\main\assets\paris_segments.geojson`
  - OK: 18,963 features, duplicate_id_count 0.
- `npm run check:pwa`
  - OK.
- `py -3 tools\segment_pipeline\validate_pwa.py`
  - OK.
- `node --check tools\dev-server.mjs`
  - OK.
- `.\gradlew.bat --no-daemon --stacktrace assembleDebug`
  - BUILD SUCCESSFUL.
- APK signature verification with `apksigner`
  - OK: Android Debug certificate.
- APK asset inspection with `aapt`
  - Verified: `assets/paris_segments.geojson`, `assets/image-1-source.png`,
    and launcher resources are packaged.

## Known Risks / Next Checks

- Manual mobile test is still needed for the 0.2 APK, ideally on Google Pixel 8
  with the latest Android version available for that device.
- Check Boulevard Marguerite de Rochechouart and Boulevard de Clichy on device:
  parallel lanes should remain visible and linked as one logical block.
- Check import/export on a real device, including merge, replace, and cancel.
- Check search, filters, light/blue mode, snackbar undo, settings, and
  full-screen statistics on the real device.
- Android currently uses online Carto tiles through osmdroid for light mode.
  Offline map support remains a later feature.
- No Android emulator or AVD is installed on this machine. README visuals are
  reproducible local PNGs, not true emulator screenshots.

## Suggested First Prompt For Next Agent

```text
Je reprends le projet mapping_Paris. Lis docs/development/handoff-next-codex.md.

Objectif immediat: tester le nouvel APK 0.2 sur mobile. Le dernier APK est
app/build/outputs/apk/debug/mapping-paris-0.2.0-debug.apk. Verifie le menu
top-left, les settings/statistiques, la bottom bar contextuelle, import/export,
search, filters, light/blue mode, snackbar undo et la migration
logical_segment_id. Verifie d'abord l'etat Git, puis travaille uniquement sur
les retours de test mobile les plus recents.
```
