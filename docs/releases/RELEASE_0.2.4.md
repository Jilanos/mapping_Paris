# Release 0.2.4: Android Map Readability and Mobile UX Hardening

Date: 2026-05-19

Version: `0.2.4`

Version code: `6`

Branch: `main`

APK:

- `app/build/outputs/apk/debug/mapping-paris-0.2.4-debug.apk`

## Summary

Release 0.2.4 is the current Android usability release for `mapping_Paris`.
It keeps the app local-first and manual, while making the mobile map easier to
use at high zoom and replacing the README preview images with real cleaned
mobile captures.

The release focuses on:

- map-first Android navigation;
- clearer segment rendering at high zoom;
- more faithful launcher icon assets;
- safer local progress handling;
- current README visuals based on the real app.

## User-Facing Changes

- Added the Android 0.2 map-first workflow:
  - top-left custom menu;
  - contextual bottom bar only when segments are selected;
  - no empty selection panel when no segment is selected.
- Added full-screen statistics.
- Added settings actions for:
  - export progress;
  - import progress;
  - reset local progress.
- Import supports three choices:
  - merge;
  - replace;
  - cancel.
- Added street search with accent-insensitive partial matching.
- Added filters behind a dedicated filter button.
- Added light and blue map modes.
- Added snackbar undo for complete and uncomplete actions.
- Improved high-zoom segment readability:
  - thicker segments at high zoom;
  - rounded segment endpoints;
  - reduced visual gaps;
  - same-color overlaps avoid darker red hot spots;
  - completed and uncompleted ribbons use matching width and opacity.
- Filtered visual segments shorter than 20 m at app load time.
- Updated launcher icon assets to stay closer to the provided app icon source.
- README screenshots now use cleaned real mobile captures with phone status
  information removed.

## Data Model

- Source GeoJSON remains separate from user progress.
- `id` remains the visual/source geometry id.
- `logical_segment_id` remains the user-facing clickable/completion id.
- Completion state is stored locally in Room.
- A startup migration path maps older visual-id completion rows to
  `logical_segment_id` where possible.

## Dataset State

- Source dataset: `data/generated/paris_segments.geojson`
- Android packaged dataset: `app/src/main/assets/paris_segments.geojson`
- Visible source geometries: `18,963`
- Logical clickable blocks: `18,001`
- Parallel same-street linked geometries: `1,556`
- Duplicate ids: `0`

## README Visuals

Updated files:

- `docs/assets/readme/android-0-2-map.png`
- `docs/assets/readme/android-0-2-menu.png`
- `docs/assets/readme/android-0-2-selection.png`
- `docs/assets/readme/android-0-2-stats.png`

Source captures came from:

- `C:\Users\Pmondou\OneDrive - Circle SAS\Images\Perso`

Processing:

- Removed Android status bar information such as time, network, and battery.
- Removed the bottom gesture/navigation bar.
- Preserved the app content at mobile portrait ratio.

## Validation

Commands run successfully:

```powershell
py -3 tools\segment_pipeline\validate_segments.py data\generated\paris_segments.geojson
py -3 tools\segment_pipeline\validate_segments.py app\src\main\assets\paris_segments.geojson
npm run check:pwa
py -3 tools\segment_pipeline\validate_pwa.py
node --check tools\dev-server.mjs
.\gradlew.bat --no-daemon --stacktrace assembleDebug
git diff --check
```

APK verification:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\build-tools\35.0.0\apksigner.bat" verify --print-certs app\build\outputs\apk\debug\mapping-paris-0.2.4-debug.apk
```

Result:

- Build successful.
- APK generated successfully.
- Debug signature verified successfully.
- Dataset validation passed for both source and Android asset.
- PWA static validation passed.

## Manual Test Checklist

Recommended device:

- Google Pixel 8
- Latest Android version available for that device

Check:

- App launches with the refreshed launcher icon.
- Map opens without a permanent bottom panel.
- Top-left menu opens and closes.
- Settings displays the installed app version.
- Statistics opens full screen and scrolls correctly.
- Street search recenters without auto-selecting.
- Filters open only from the filter icon.
- Light and blue map modes both render correctly.
- Selected segments show the contextual bottom bar.
- Complete/uncomplete works.
- Snackbar undo restores the previous state.
- Import/export works with merge, replace, and cancel.
- High zoom around Pigalle, Boulevard de Clichy, Rue Lepic:
  - endpoints are rounded;
  - gaps are reduced;
  - red overlaps do not become visually over-dark;
  - selected segments remain readable.

## Known Limits

- Offline map tiles are not part of this release.
- GPS validation is not part of this release.
- Cloud sync and accounts are not part of this release.
- Segments shorter than 20 m are filtered at app load time. If meaningful tiny
  streets disappear, this should move into the generation pipeline with a proper
  merge strategy instead of app-side filtering.
- README screenshots are cleaned real mobile captures, not emulator-generated
  screenshots. No Android AVD is currently installed on this machine.

## Release Notes For Handoff

The next work should start from the latest handoff:

- `docs/development/handoff-next-codex.md`

Primary follow-up is manual mobile validation of the 0.2.4 APK, especially map
rendering at high zoom and progress import/export behavior.
