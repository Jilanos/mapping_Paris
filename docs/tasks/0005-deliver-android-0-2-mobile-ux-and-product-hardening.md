# Task 0005: Deliver Android 0.2 Mobile UX and Product Hardening

From version: 0.1.0

Status: Implemented

Understanding: 94%

Confidence: 88%

Progress: 95%

Complexity: High

Theme: Android UX

## Goal

Deliver the Android 0.2 app wave by replacing the screen-blocking mobile panel,
adding the top-left menu and contextual map actions, adding import/export,
street search, filters, map modes, the corrected icon, reproducible README
visuals, and the completion-state migration path.

## Links

- Request: `docs/request/0004-prepare-version-0-2-mobile-ux-and-product-hardening.md`
- Derived from `docs/backlog/0019-android-0-2-menu-and-contextual-actions.md`
- Derived from `docs/backlog/0020-android-0-2-import-export-and-progress-safety.md`
- Derived from `docs/backlog/0021-android-0-2-search-and-filter-controls.md`
- Derived from `docs/backlog/0022-android-0-2-map-modes-and-color-polish.md`
- Derived from `docs/backlog/0023-rebuild-android-icon-from-image-1.md`
- Derived from `docs/backlog/0024-readme-mobile-visuals-and-version-0-2-docs.md`
- Derived from `docs/backlog/0025-migrate-completion-state-to-logical-segment-ids.md`
- Product brief: `docs/product/product-brief.md`
- Segment contract: `docs/data/segment-contract.md`
- Android build notes: `docs/development/android-build.md`
- Current handoff: `docs/development/handoff-next-codex.md`

## Context

The 0.1 app has the core local-first tracking model, but the mobile UX still
blocks too much of the map and lacks the tools needed for real progress
management. The next delivery should become version 0.2 and keep Android as the
main focus.

```mermaid
flowchart TD
    A[Current 0.1 app] --> B[Menu and actions]
    B --> C[Import export]
    C --> D[Search and filters]
    D --> E[Map modes and colors]
    E --> F[Icon and docs]
    F --> G[Migration and validation]
    G --> H[Android 0.2 APK]
```

## Scope

In:

- Replace the large always-visible Android bottom panel.
- Add a top-left custom menu for settings and statistics.
- Add a full-screen statistics view.
- Hide empty selection UI when no segment is selected.
- Add a contextual bottom bar for selected-segment actions.
- Add snackbar undo for complete and uncomplete actions.
- Add Android export and import of completed `logical_segment_id` values.
- Add import conflict choices: merge, replace, cancel.
- Add reset-all-progress in settings with confirmation.
- Add Android street search with accent-insensitive partial matches.
- Recenter on search result without auto-selecting segments.
- Add a separate filter icon and hidden filter menu.
- Add light and blue map modes selectable from the menu.
- Polish segment colors using product design judgment.
- Store `[Image #1]` in the repo and rebuild launcher icons from it.
- Bump Gradle version to `0.2.0`.
- Generate `mapping-paris-0.2.0-debug.apk`.
- Capture emulator screenshots and commit README PNG assets.
- Update README dataset counts, version references, screenshots, and 0.2 notes.
- Add or run a migration path from old visual `id` completion rows to
  `logical_segment_id`.

Out:

- GPS validation.
- Backend services.
- User accounts.
- Cloud sync.
- Dedicated color-blind mode.
- Play Store release assets.
- Route planning.
- Regenerating the Paris segment dataset unless a defect requires it.

## Plan

- [x] Wave 1: Android interaction shell
  - [x] Inspect current `MappingParisApp.kt`, `MappingParisViewModel.kt`, and
        `ParisMapOverlays.kt`.
  - [x] Replace the always-visible bottom panel with map-first UI.
  - [x] Add top-left custom menu for settings and statistics.
  - [x] Add full-screen statistics view.
  - [x] Add contextual bottom action bar for selected segments.
  - [x] Remove empty selection UI when no segment is selected.
  - [x] Add snackbar undo for complete and uncomplete actions.
  - [x] Run a targeted Android build after the shell change.
- [x] Wave 2: progress safety
  - [x] Add export JSON for completed `logical_segment_id` values.
  - [x] Add import JSON from a previous export.
  - [x] Place import/export in settings.
  - [x] Add merge, replace, and cancel import conflict choices.
  - [x] Add reset-all-progress with confirmation.
  - [x] Document export schema or behavior.
  - [x] Run Android build and relevant manual checks.
- [x] Wave 3: search and filters
  - [x] Add accent-insensitive partial street search.
  - [x] Recenter on selected search result without auto-selection.
  - [x] Add filter icon and hidden filter menu.
  - [x] Add practical filters for completed, not completed, selected,
        arrondissement, and street.
  - [x] Keep filters hidden when the filter menu is closed.
  - [x] Verify map performance remains acceptable.
- [x] Wave 4: map modes and color polish
  - [x] Add light and blue map mode choices in the menu.
  - [x] Start blue mode as a blue-tinted treatment if labels stay readable.
  - [x] Tune selected, completed, and not completed colors.
  - [x] Check readability over both map modes.
  - [x] Keep no dedicated color-blind mode.
- [x] Wave 5: icon and version
  - [x] Store the `[Image #1]` source asset in the repo.
  - [x] Regenerate Android launcher resources from the image.
  - [x] Preserve only minor adaptations for Android launcher constraints.
  - [x] Bump Android `versionName` to `0.2.0`.
  - [x] Confirm APK naming produces `mapping-paris-0.2.0-debug.apk`.
- [x] Wave 6: logical id migration
  - [x] Detect old completion rows keyed by visual segment `id`.
  - [x] Map them to `logical_segment_id` values from the packaged dataset.
  - [x] Deduplicate rows that map to the same logical segment.
  - [x] Keep migration safe to run more than once.
  - [x] Document limitations for unrecoverable old ids.
- [x] Wave 7: README visuals and docs
  - [x] Add reproducible README visuals for normal map, menu open, selected
        segments, and stats or progress view.
  - [x] Add search or filter screenshot if implemented visually.
  - [x] Commit screenshot PNG files under a stable docs assets folder.
  - [x] Update README counts to the current dataset.
  - [x] Add compact Version 0.2 README section.
  - [x] Update handoff or development notes if needed.
- [x] Wave 8: final validation
  - [x] Run dataset validation for source and Android asset.
  - [x] Run PWA static validation.
  - [x] Build the Android debug APK.
  - [x] Verify APK signature and output name.
  - [x] Record manual validation expectations for Google Pixel 8 with latest
        available Android version.
  - [x] Update this task report with implementation and validation results.

## Acceptance Criteria

- The Android app version is `0.2.0`.
- The debug APK is named `mapping-paris-0.2.0-debug.apk`.
- The Android map is not blocked by a large always-visible bottom panel.
- No empty selection panel is shown when no segment is selected.
- A top-left custom menu opens settings and the full-screen statistics view.
- Main map actions use a contextual bottom bar.
- Complete and uncomplete actions provide snackbar undo.
- Android can export completion state.
- Android can import completion state.
- Import conflict handling offers merge, replace, and cancel.
- Reset all progress exists in settings and requires confirmation.
- Street search is available and recenters without auto-selecting.
- A separate filter icon opens a hidden filter menu.
- Light and blue map modes are selectable.
- Segment colors are readable in both map modes.
- Launcher icon resources are rebuilt from `[Image #1]` with only minor
  adaptations.
- README includes committed emulator screenshots.
- README dataset counts and version references are updated.
- Old visual `id` completion rows are migrated or safely handled.
- Source segment geometry remains separate from user completion state.
- Required validation commands pass.

## Validation

Required commands:

```powershell
git status --short --branch
py -3 tools\segment_pipeline\validate_segments.py data\generated\paris_segments.geojson
py -3 tools\segment_pipeline\validate_segments.py app\src\main\assets\paris_segments.geojson
npm run check:pwa
py -3 tools\segment_pipeline\validate_pwa.py
node --check tools\dev-server.mjs
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

APK checks:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\build-tools\35.0.0\apksigner.bat" verify --print-certs app\build\outputs\apk\debug\mapping-paris-0.2.0-debug.apk
```

Manual checks:

- Install the 0.2 debug APK on a Google Pixel 8 with the latest Android version
  available for that device.
- Confirm the map is usable without the old bottom panel.
- Open and close the top-left menu.
- Open settings and statistics.
- Switch between light and blue map modes.
- Open and close the filter menu from the filter icon.
- Search for a street and confirm the map recenters without selecting.
- Select one segment and several segments.
- Complete and uncomplete selected segments.
- Undo a completion or uncompletion from the snackbar.
- Export completion state.
- Import completion state and test merge, replace, and cancel.
- Confirm the launcher icon resembles `[Image #1]`.
- Confirm README screenshots match the current app.

## Report

Implemented on 2026-05-18.

Implementation:

- Reworked `MappingParisApp.kt` into a map-first Android UI.
- Added top-left custom menu for settings, statistics, and map mode selection.
- Added full-screen settings and statistics views.
- Removed the always-visible empty selection panel.
- Added a contextual bottom action bar that appears only when segments are
  selected.
- Added snackbar undo for complete and uncomplete actions.
- Added completion export and import through Android document contracts.
- Import supports merge, replace, and cancel conflict choices.
- Added reset-all-progress in settings with confirmation.
- Added accent-insensitive street search that recenters without auto-selecting.
- Added a separate filter icon and hidden filter panel for completed, not
  completed, selected, arrondissement, and street filters.
- Added light and blue map modes.
- Tuned segment colors for clearer light and blue mode readability.
- Added a safe visual-id to `logical_segment_id` migration path for old Room
  completion rows.
- Bumped Android version to `0.2.0`, producing
  `mapping-paris-0.2.0-debug.apk`.
- Stored the icon source direction under `docs/assets/icon/image-1-source.png`
  and `app/src/main/assets/image-1-source.png`.
- Refreshed launcher vector resources to stay closer to `[Image #1]`.
- Added README visuals under `docs/assets/readme/`.
- Updated README counts and added a compact Version 0.2 preview section.
- Updated the next-agent handoff.

Validation results:

```powershell
py -3 tools\segment_pipeline\validate_segments.py data\generated\paris_segments.geojson
# OK: 18,963 features, duplicate_id_count 0

py -3 tools\segment_pipeline\validate_segments.py app\src\main\assets\paris_segments.geojson
# OK: 18,963 features, duplicate_id_count 0

npm run check:pwa
# OK

py -3 tools\segment_pipeline\validate_pwa.py
# PWA static validation: OK

node --check tools\dev-server.mjs
# OK

.\gradlew.bat --no-daemon --stacktrace assembleDebug
# BUILD SUCCESSFUL

& "$env:LOCALAPPDATA\Android\Sdk\build-tools\35.0.0\apksigner.bat" verify --print-certs app\build\outputs\apk\debug\mapping-paris-0.2.0-debug.apk
# OK: Android Debug certificate

& "$env:LOCALAPPDATA\Android\Sdk\build-tools\35.0.0\aapt.exe" list app\build\outputs\apk\debug\mapping-paris-0.2.0-debug.apk
# Verified: assets/paris_segments.geojson, assets/image-1-source.png, launcher resources
```

APK output:

- `app/build/outputs/apk/debug/mapping-paris-0.2.0-debug.apk`

Known limitation:

- No Android emulator or AVD is installed on this machine, so true emulator
  screenshots could not be captured. README visual PNGs were generated
  reproducibly as app-style documentation visuals and committed under
  `docs/assets/readme/`.
- Manual validation on Google Pixel 8 with the latest Android version available
  for it remains the required device check.

## Non-Goals

- Do not add GPS validation, backend, accounts, cloud sync, route planning, or
  Play Store publication.
- Do not add a dedicated color-blind mode.
- Do not regenerate the dataset unless required by a defect found during the
  work.
