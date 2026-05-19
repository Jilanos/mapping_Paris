# Handoff: mapping Paris Current Context

Date: 2026-05-19

Repository: `mapping_Paris`

Remote: `https://github.com/Jilanos/mapping_Paris.git`

Branch: `main`

## Current State

The project is a local-first personal Android app plus PWA tester for manually
tracking completed street segments in Paris intra-muros.

Current latest pushed commit before GPS 0.3 work:

- `9737c80 Document release 0.2.4`

Generated APK available locally:

- `app/build/outputs/apk/debug/mapping-paris-0.3.0-debug.apk`

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

- Android `versionName` was `0.2.4`.
- Android `versionCode` was `6`.
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

## Version 0.3 GPS State

- Android `versionName` is `0.3.0`.
- Android `versionCode` is `7`.
- Foreground location permissions are declared for fine and coarse location.
- GPS-assisted behavior is stored in local settings and disabled by default on
  first install.
- The map has an always-visible GPS button below the filter button.
- Pressing the GPS button requests permission if needed and recenters only when
  a current position is available.
- Current position is drawn as a compact marker with an accuracy radius.
- GPS loading, denied, and unavailable states are shown as non-blocking map
  chips and settings labels.
- Settings includes GPS-assisted behavior plus strict, balanced, and wide
  matching strictness.
- While GPS assistance is enabled and the app is open, path points are kept in
  memory only.
- GPS path matching proposes likely nearby logical segments conservatively.
- GPS proposals are selected for review and use a distinct temporary style.
- The user can deselect proposed segments before validation.
- Segments are never completed automatically from GPS.
- Captured GPS path data is discarded when the app closes.

## Latest Mobile Feedback Implemented

- Launcher icon uses the provided raster image source and generated mipmap PNGs.
- Settings displays the real installed app version.
- Statistics is a safe-area compliant screen with global and arrondissement
  progress cards.
- Filters use status checkboxes plus arrondissement checkboxes from 1 to 20.
- The street-name filter field was removed from filters; street search remains
  available through the search panel.
- Segment width is zoom-dependent and much thicker from zoom 15 upward.
- Completed and uncompleted segment ribbons use the same width and opacity;
  only their color differs.
- Uncompleted segments are a stronger red, completed segments remain teal.
- Map debug markers can be enabled in settings to show zoom, screen size, and a
  48 px ruler.
- Pinch zoom has an additional osmdroid gesture amplifier.
- Segment endpoints are rounded.
- Unselected segments are rendered into an isolated layer using source
  replacement so same-color overlaps do not become visually darker.
- Visual segments shorter than 20 m are filtered out at load time.

## Important Files

Android UI and rendering:

- `app/src/main/java/com/jilanos/mappingparis/ui/MappingParisApp.kt`
- `app/src/main/java/com/jilanos/mappingparis/ui/ParisMapOverlays.kt`
- `app/src/main/java/com/jilanos/mappingparis/ui/MappingParisViewModel.kt`
- `app/build.gradle.kts`
- `app/src/main/AndroidManifest.xml`

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

0.3 GPS planning and report:

- `docs/request/0006-show-gps-position-on-map-0-3.md`
- `docs/backlog/0027-android-0-3-foreground-gps-position.md`
- `docs/backlog/0028-android-0-3-gps-path-segment-proposals.md`
- `docs/backlog/0029-android-0-3-gps-settings-and-states.md`
- `docs/backlog/0030-version-0-3-gps-release-docs-and-validation.md`
- `docs/tasks/0007-deliver-android-0-3-gps-position-and-segment-proposals.md`
- `docs/releases/RELEASE_0.3.0.md`

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
& "$env:LOCALAPPDATA\Android\Sdk\build-tools\35.0.0\apksigner.bat" verify --print-certs app\build\outputs\apk\debug\mapping-paris-0.3.0-debug.apk
```

APK asset inspection:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\build-tools\35.0.0\aapt.exe" list app\build\outputs\apk\debug\mapping-paris-0.3.0-debug.apk
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
- `.\gradlew.bat --no-daemon --stacktrace :app:compileDebugKotlin --rerun-tasks`
  - BUILD SUCCESSFUL after GPS 0.3 code changes.
- APK signature verification with `apksigner`
  - OK: Android Debug certificate.
- APK asset inspection with `aapt`
  - Verified: `assets/paris_segments.geojson`, `assets/image-1-source.png`,
    and launcher resources are packaged.
- `cmd /c tools\build-and-install-debug-apk.cmd`
  - BUILD SUCCESSFUL for `mapping-paris-0.3.0-debug.apk`.
  - Connected device: `37290DLJH004PP`.
  - Initial install blocked: `INSTALL_FAILED_UPDATE_INCOMPATIBLE`.
  - Existing installed package had a different signature.
  - After user approval, the existing package was uninstalled and 0.3.0 was
    installed successfully.
  - Follow-up GPS permission fix was rebuilt and installed successfully.
  - Installed package confirmed: `versionName=0.3.0`, `versionCode=7`.
- `git diff --check`
  - OK after the 0.3 GPS changes, with only expected CRLF conversion warnings.

## Known Risks / Next Checks

- User confirmed current GPS position display works on the Pixel 8.
- Still check first-install GPS-off state, permission denial, Android location
  disabled state, GPS button recentering, and no continuous camera lock.
- Walk with the app open and verify that GPS-proposed segments are conservative,
  editable, visually distinct, and not completed until explicit validation.
- Check strict, balanced, and wide matching settings on real streets.
- Re-run APK signature verification for `mapping-paris-0.3.0-debug.apk`.
- Check Boulevard Marguerite de Rochechouart and Boulevard de Clichy on device:
  parallel lanes should remain visible and linked as one logical block.
- Check whether filtering visual segments shorter than 20 m removes too many
  meaningful tiny streets. If it does, move this rule into the data pipeline
  and merge tiny geometries instead of filtering them at app load time.
- Check high zoom around Pigalle / Boulevard de Clichy / Rue Lepic:
  endpoints should look rounded, gaps should be reduced, and same-color
  overlaps should not create darker red spots.
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

Objectif immediat: tester le nouvel APK 0.3 sur mobile. Le dernier APK est
app/build/outputs/apk/debug/mapping-paris-0.3.0-debug.apk. Verifie en priorite
le GPS: off par defaut, demande de permission, affichage position et rayon de
precision, bouton recenter sans verrouiller la camera, et propositions de
segments GPS editables/non validees. Verifie aussi light/blue mode, selection,
validation manuelle, settings, search, filters, import/export et statistiques.
Verifie d'abord l'etat Git, puis travaille uniquement sur les retours de test
mobile les plus recents.
```
