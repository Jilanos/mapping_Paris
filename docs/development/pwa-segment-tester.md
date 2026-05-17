# PWA Segment Tester

## Purpose

The PWA tester is the local Chrome tool used to inspect the generated Paris segment mesh before it is imported into Android.

It is not the final Android app.

## Run locally

From the repository root:

```powershell
py -3 -m http.server 5173
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
- Lets the user click one segment.
- Shows segment metadata.
- Lets the user validate or unvalidate the selected segment.
- Stores validation state in browser local storage.
- Allows exporting validation state to a JSON file.

## Validation

Run:

```powershell
py -3 tools/segment_pipeline/validate_pwa.py
node --check pwa/app.js
```
