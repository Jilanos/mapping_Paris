# Task 0004: Polish Android Map Visuals and Interactions

From version: 0.1.0

Status: Ready

Understanding: 92%

Confidence: 84%

Progress: 0%

Complexity: High

Theme: Android UX

## Goal

Turn the Android APK from a dense-dataset proof into a usable personal tracking
app by improving selection performance, adding multi-segment selection, replacing
the detailed OSM background with a simplified blue Paris basemap, applying the
provided app image as the app icon, and producing a clearly versioned APK file.

## Links

- Request: `docs/request/0003-polish-android-map-visuals-and-segment-interaction.md`
- Derived from `docs/backlog/0015-add-android-app-icon-and-apk-naming.md`
- Derived from `docs/backlog/0016-build-simplified-blue-paris-basemap.md`
- Derived from `docs/backlog/0017-add-android-multi-segment-selection.md`
- Derived from `docs/backlog/0018-optimize-android-segment-selection-performance.md`
- Product brief: `docs/product/product-brief.md`
- Segment contract: `docs/data/segment-contract.md`
- Android build notes: `docs/development/android-build.md`
- PWA behavior reference: `docs/development/pwa-segment-tester.md`

## Context

The Android app now packages the accepted generated Paris segment dataset, but
the app still has prototype-level interaction and map presentation. Selection is
slow, only one segment can be selected, the map background is still detailed OSM
tiles, and the APK does not yet carry the provided visual identity or versioned
output name.

```mermaid
flowchart TD
    A[Current Android APK] --> B[Audit selection delay]
    B --> C[Optimize map update path]
    C --> D[Add multi selection]
    D --> E[Build simplified blue basemap]
    E --> F[Add app icon and APK naming]
    F --> G[Validated polished APK]
```

## Scope

In:

- Audit the Android segment selection delay.
- Optimize the map update path so selection feedback is fluid on 15,295
  segments.
- Add tap and long-press multi-segment selection behavior.
- Add batch complete and uncomplete behavior for selected segments.
- Add selected-set UI details: count, total length, and mixed arrondissement
  state.
- Replace the visually dominant detailed OSM background with a simplified blue
  Paris basemap.
- Include Paris outline, Seine, canals, useful street names, parks, train
  stations, churches, Elysee, and similar high-value landmarks where practical.
- Keep the generated segment overlay as the primary interactive layer.
- Store the provided app image in the Android app/project area.
- Generate and wire Android launcher icon assets from that image.
- Configure APK output naming as `mapping-paris-<version>-<buildType>.apk`.
- Produce and validate a debug APK.

Out:

- GPS validation.
- Backend services.
- User accounts.
- Cloud sync.
- Play Store listing graphics.
- Release signing setup.
- Drag or lasso selection in this task.
- Full cartographic accuracy or complete OSM label coverage.

## Plan

- [ ] Wave 1: performance audit and render-path fix
  - [ ] Inspect `MappingParisApp.kt`, `MappingParisViewModel.kt`, and osmdroid
        overlay usage.
  - [ ] Confirm whether selection currently rebuilds all segment overlays.
  - [ ] Add temporary measurement or targeted logging if needed.
  - [ ] Refactor map update behavior to avoid unnecessary `Polyline`
        recreation on selection changes.
  - [ ] Keep completion-state persistence behavior unchanged.
  - [ ] Record the performance finding in this task report.
- [ ] Wave 2: Android multi-segment selection
  - [ ] Replace single selected id state with a selected id set.
  - [ ] Support tap-to-toggle selection.
  - [ ] Support long-press entry into multi-selection mode.
  - [ ] Highlight all selected segments.
  - [ ] Add selected count, total selected length, and mixed arrondissement
        display.
  - [ ] Add selected-set complete and uncomplete behavior.
  - [ ] Add clear selection behavior.
- [ ] Wave 3: simplified blue Paris basemap
  - [ ] Choose the smallest viable basemap strategy for this APK.
  - [ ] Implement a blue-toned background aligned with the app image.
  - [ ] Include Paris outline, Seine, canals, useful street names, and selected
        landmarks.
  - [ ] Ensure the segment network remains readable over the background.
  - [ ] Remove or visually demote detailed OSM tiles.
- [ ] Wave 4: app image, launcher icon, and APK naming
  - [ ] Store the provided image source under the Android app/project folder.
  - [ ] Generate launcher icon resources from the image.
  - [ ] Update manifest/resource references for the app icon.
  - [ ] Configure APK output filename as
        `mapping-paris-<version>-<buildType>.apk`.
  - [ ] Confirm generated debug APK filename includes version and build type.
- [ ] Wave 5: validation and documentation
  - [ ] Update relevant docs and backlog task coverage.
  - [ ] Run dataset validation against the packaged Android asset.
  - [ ] Run Android debug APK build.
  - [ ] Verify the APK contains expected assets.
  - [ ] Document manual device validation steps and any remaining risks.

## Acceptance Criteria

- The source of the original Android selection delay is identified and
  documented.
- Segment selection feedback is visibly faster than the current APK.
- Selection changes do not unnecessarily rebuild thousands of map overlay
  objects.
- The Android app supports selecting multiple segments.
- Tapping a selected segment removes it from the selection.
- Long-pressing a segment enters or supports multi-selection mode.
- The UI displays selected count and total selected length.
- The UI can complete the selected segment set.
- The UI can uncomplete the selected segment set when all selected segments are
  already complete.
- The UI can clear the current selection without changing completion state.
- Completion state remains stored separately from source GeoJSON.
- The Android map background is simplified and blue-toned.
- The simplified background includes Paris outline, Seine, relevant canals, and
  useful orientation labels.
- The segment overlay remains the dominant interactive layer.
- The provided app image is stored in the repository under the Android app area.
- Android launcher icons are generated from the provided app image.
- The APK no longer uses the old default placeholder icon.
- The debug APK output is named with the
  `mapping-paris-<version>-<buildType>.apk` pattern.
- A debug APK builds successfully.

## Validation

Required commands:

```powershell
py -3 tools\segment_pipeline\validate_segments.py app\src\main\assets\paris_segments.geojson
npm run check:pwa
node --check tools\dev-server.mjs
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

APK checks:

```powershell
$sdkRoot = "$env:LOCALAPPDATA\Android\Sdk"
& "$sdkRoot\build-tools\35.0.0\apksigner.bat" verify --print-certs app\build\outputs\apk\debug\mapping-paris-0.1.0-debug.apk
```

Manual checks:

- Install the debug APK on a device.
- Confirm the launcher icon uses the provided image direction.
- Confirm the map background is blue-toned and simplified.
- Confirm Paris outline, waterways, and major labels help with orientation.
- Tap several segments and confirm all remain selected.
- Long-press a segment and confirm multi-selection behavior is discoverable.
- Complete and uncomplete a selected segment set.
- Change selected segments repeatedly and confirm selection feedback is fluid.

## Report

Pending.

## Non-Goals

- Do not add GPS validation, backend, accounts, cloud sync, or Play Store
  publication.
- Do not build drag/lasso selection in this task.
- Do not replace the generated source dataset unless the performance audit
  proves the dataset format is the bottleneck.
- Do not let the basemap visually dominate the segment network.
