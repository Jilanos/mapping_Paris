# PWA Segment Tester

## Purpose

The PWA tester is the local Chrome tool used to inspect the generated Paris segment mesh before it is imported into Android.

It is not the final Android app.

## Run locally

From the repository root:

```powershell
npm run dev
```

Then open:

```text
http://localhost:5173/pwa/
```

## What it loads

The tester loads:

```text
data/generated/paris_segments.geojson
```

## Behavior

- Displays the generated Paris segment mesh.
- Uses canvas rendering through Leaflet for a dense dataset.
- Lets the user click one or more segments.
- Shows single-segment metadata or multi-segment summary details.
- Lets the user validate or unvalidate the selected segment set.
- Stores validation state in browser local storage.
- Allows exporting validation state to a JSON file.

## Validation

Run:

```powershell
py -3 tools/segment_pipeline/validate_pwa.py
npm run check:pwa
```
