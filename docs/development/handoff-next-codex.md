# Handoff: mapping Paris Current Context

Date: 2026-05-18

Repository: `mapping_Paris`

Remote: `https://github.com/Jilanos/mapping_Paris.git`

Branch: `main`

## Current State

The project is a local-first personal Android app plus PWA tester for manually
tracking completed street segments in Paris intra-muros.

Current latest pushed commit before this handoff:

- `5d8bb5a Link parallel segments as logical blocks`

Generated APK available locally:

- `app/build/outputs/apk/debug/mapping-paris-0.1.0-debug.apk`

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
- `logical_segment_id` is now the user-facing clickable/completion id.
- Parallel same-name carriageways remain visible to avoid holes in boulevards,
  but selection, validation, and statistics use `logical_segment_id`.

## Recent Product Decisions

- The map background should stay close to the current light Carto/OSM style with
  readable street and building context.
- Do not add custom PWA street-label markers; the basemap's own labels are
  sufficient.
- Segment overlays should be transparent red/green ribbons so street names
  remain visible underneath.
- Segment line caps are flat (`butt`) to avoid darker overlap at segment ends.
- After validating/devalidating selected segments, the selection clears by
  default.
- Android statistics are hidden by default behind a `Statistiques` button.
- APK output name remains `mapping-paris-0.1.0-debug.apk`.

## Important Files

Android UI and rendering:

- `app/src/main/java/com/jilanos/mappingparis/ui/MappingParisApp.kt`
- `app/src/main/java/com/jilanos/mappingparis/ui/ParisMapOverlays.kt`
- `app/src/main/java/com/jilanos/mappingparis/ui/MappingParisViewModel.kt`

Android data model:

- `app/src/main/java/com/jilanos/mappingparis/data/StreetSegment.kt`
- `app/src/main/java/com/jilanos/mappingparis/data/SegmentGeoJsonParser.kt`
- `app/src/main/java/com/jilanos/mappingparis/data/SegmentRepository.kt`

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

Icon source:

- `app/src/main/assets/app-icon-source.svg`

## Validation Commands

Use these after pulling:

```powershell
git status --short --branch
py -3 tools\segment_pipeline\validate_segments.py data\generated\paris_segments.geojson
py -3 tools\segment_pipeline\validate_segments.py app\src\main\assets\paris_segments.geojson
node --check pwa\app.js
node --check pwa\service-worker.js
py -3 tools\segment_pipeline\validate_pwa.py
.\gradlew.bat --no-daemon --stacktrace assembleDebug
```

APK verification:

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\build-tools\35.0.0\apksigner.bat" verify --print-certs app\build\outputs\apk\debug\mapping-paris-0.1.0-debug.apk
```

PWA local test:

```powershell
py -3 -m http.server 5173
```

Then open:

```text
http://localhost:5173/pwa/
```

## Known Risks / Next Checks

- Manual mobile test is still needed for the latest APK.
- Check Boulevard Marguerite de Rochechouart and Boulevard de Clichy on device:
  parallel lanes should remain visible and linked as one logical block.
- Because completion now uses `logical_segment_id`, old local Room completion
  rows keyed by visual ids may not carry over perfectly. This is acceptable for
  the current prototype, but should be handled before real user data matters.
- Android currently uses online Carto tiles through osmdroid. Offline map support
  remains a later feature.

## Suggested First Prompt For Next Agent

```text
Je reprends le projet mapping_Paris. Lis docs/development/handoff-next-codex.md.

Objectif immédiat: continuer à tester et corriger le rendu mobile. Le dernier
APK est app/build/outputs/apk/debug/mapping-paris-0.1.0-debug.apk. Le modèle de
segments utilise maintenant logical_segment_id pour lier les voies parallèles:
les géométries restent visibles, mais sélection/validation/statistiques doivent
agir sur le bloc logique. Vérifie d'abord l'état Git, puis travaille uniquement
sur les retours de test mobile les plus récents. Ne régénère pas l'APK sauf si
la correction Android est prête et validée localement.
```
