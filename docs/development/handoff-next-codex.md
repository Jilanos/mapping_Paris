# Handoff: Android Map Polish Work

Date: 2026-05-18

Repository: `mapping_Paris`

Remote: `https://github.com/Jilanos/mapping_Paris.git`

Branch: `main`

## Current Repository State

The project is a local-first personal Android app for manually tracking completed
street segments in Paris.

Recent completed work:

- The generated Paris street dataset is accepted as good enough for the next
  Android phase.
- The Android APK now packages the dense generated dataset instead of the old
  seed sample.
- Current Android asset:
  `app/src/main/assets/paris_segments.geojson`
- Current generated source dataset:
  `data/generated/paris_segments.geojson`
- Dataset size: `15,295` segments.
- The old one-segment-per-arrondissement style asset was removed.
- `npm run dev` serves the PWA tester.
- `app/build/outputs/apk/debug/app-debug.apk` builds locally on the previous PC.

Last pushed commits before this handoff:

- `9a41c82 Package generated Paris segments in Android app`
- `a44e034 Refine Paris segments and document APK workflow`

## Planning Docs Created For Next Work

Request:

- `docs/request/0003-polish-android-map-visuals-and-segment-interaction.md`

Backlog items:

- `docs/backlog/0015-add-android-app-icon-and-apk-naming.md`
- `docs/backlog/0016-build-simplified-blue-paris-basemap.md`
- `docs/backlog/0017-add-android-multi-segment-selection.md`
- `docs/backlog/0018-optimize-android-segment-selection-performance.md`

Task:

- `docs/tasks/0004-polish-android-map-visuals-and-interactions.md`

The task intentionally covers the four backlog items in one orchestration flow.
The planned order is:

1. performance audit and render-path fix;
2. Android multi-segment selection;
3. simplified blue Paris basemap;
4. app image, launcher icon, and APK naming;
5. validation and documentation.

## Product Direction For Task 0004

The user wants the Android app to feel like the real tracking app, not a
prototype.

Requirements:

- Use the provided app image as the app icon/visual source.
- The image can be cropped or adapted for Android adaptive icons.
- Store the source image under the Android app/project folder so it is not lost
  if downloads are deleted.
- Replace the detailed OSM-looking map background with a simplified Paris map.
- The simplified map should be blue-toned, in the style of the provided icon.
- Show Paris outline.
- Show the Seine and canals clearly.
- Show useful street names.
- Show major landmarks and orientation anchors with names, such as churches,
  train stations, parks, Elysee, and recognizable monuments.
- Keep the colored segment network as the main visual layer.
- Implement multi-segment selection in Android.
- Supported selection interactions:
  - taps successifs to add/remove segments;
  - long-press on a segment to enter or support multi-selection mode.
- Support batch complete/uncomplete of the selected segment set.
- Fix the long delay before selection feedback or selected segment changes.
- Audit and document the source of the delay before optimizing.
- Generated APK files should be named:
  `mapping-paris-<version>-<buildType>.apk`
  for example `mapping-paris-0.1.0-debug.apk`.

## Current Suspected Performance Issue

The Android map likely rebuilds too many osmdroid overlays during selection.
Check first:

- `app/src/main/java/com/jilanos/mappingparis/ui/MappingParisApp.kt`
- `SegmentMap(...)`
- `AndroidView(update = { ... })`

Likely issue:

- `mapView.overlays.clear()`
- then recreating one `Polyline` per segment every update
- with 15,295 segments, selection changes are expensive

Task 0004 asks to prove this before optimizing.

## Useful Commands

After pulling on the next PC:

```powershell
git status --short --branch
py -3 tools\segment_pipeline\validate_segments.py app\src\main\assets\paris_segments.geojson
npm run check:pwa
node --check tools\dev-server.mjs
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

If Android tooling is not installed on the next PC, install/configure:

- JDK 17
- Android SDK command line tools
- `platform-tools`
- `platforms;android-35`
- `build-tools;35.0.0`

Reference doc:

- `docs/development/android-build.md`

## Initial Prompt For Codex On The Next PC

Copy/paste this as the first message after pulling the repo:

```text
Je reprends le projet mapping_Paris sur un autre PC. Lis d'abord docs/development/handoff-next-codex.md, puis docs/tasks/0004-polish-android-map-visuals-and-interactions.md.

Objectif: implémenter la task 0004 de bout en bout. Commence par l'audit perf Android: vérifie si MappingParisApp.kt reconstruit toutes les overlays osmdroid à chaque sélection, optimise le rendu pour que la sélection soit fluide avec les 15 295 segments, puis ajoute la sélection multiple Android, le fond de carte Paris bleu simplifié, l'icône depuis l'image fournie, et le nommage APK mapping-paris-<version>-<buildType>.apk.

Respecte les docs request/backlog/task déjà créées. Garde le dataset source séparé de l'état utilisateur. À la fin, reconstruis l'APK debug, vérifie son contenu/nom, mets à jour les docs de validation, commit et push sur main.
```

## Notes For The Next Agent

- Do not restore the old `paris_segments_seed.geojson`.
- The Android app should keep loading `app/src/main/assets/paris_segments.geojson`.
- The PWA already supports multi-selection and can be used as a behavior
  reference.
- The source app image was provided in chat as `[Image #1]`; if it is not
  available in the new session, ask the user to attach it again before icon work.
- Do performance work before adding multi-selection, otherwise multi-selection
  may amplify the current selection delay.
