# Initial Backlog

## Define segment data model

Description: Define the canonical segment schema consumed by the Android app and produced by the future OSM pipeline.

Priority: Must

Notes: Keep source segment data separate from user completion state.

## Prepare OSM data pipeline

Description: Design the future offline process that extracts, filters, splits, and exports Paris street segments from OpenStreetMap.

Priority: Must

Notes: Do not implement the pipeline until the model and extraction rules are clear.

## Generate Paris intra-muros segment dataset

Description: Produce the first local segment dataset for Paris intra-muros.

Priority: Must

Notes: Exclude the Bois de Boulogne and Bois de Vincennes. Include public ways walkable or bikeable.

## Create Android project skeleton

Description: Initialize the Android application structure using Kotlin and Jetpack Compose.

Priority: Must

Notes: Keep architecture simple and compatible with MVVM.

## Load local segment dataset

Description: Load the preprocessed local segment file into the Android app.

Priority: Must

Notes: GeoJSON is the likely initial format.

## Display interactive map

Description: Display an online OSM-based 2D map in the Android app.

Priority: Must

Notes: osmdroid is the likely map library for V1.

## Render street segments

Description: Draw the loaded street segments on top of the map.

Priority: Must

Notes: Rendering should distinguish completed and not completed segments.

## Select one segment

Description: Allow the user to tap or otherwise select a single segment.

Priority: Must

Notes: Segment selection should be precise enough for normal map usage.

## Toggle segment completion

Description: Allow the user to mark a selected segment as completed or not completed.

Priority: Must

Notes: Completion is manual in V1.

## Support multi-selection

Description: Allow selecting several segments before applying a completion state.

Priority: Should

Notes: Useful for correcting or recording progress after a walk.

## Store completion state locally

Description: Persist segment completion state on the device.

Priority: Must

Notes: Room is the likely storage option. Do not write completion state into the source dataset.

## Compute global statistics

Description: Compute overall completed distance and completion percentage.

Priority: Should

Notes: Base calculations on segment lengths from the source dataset and completion state from local storage.

## Compute statistics by arrondissement

Description: Compute completion distance and percentage per arrondissement.

Priority: Should

Notes: Requires reliable arrondissement attribution in the segment model.

## Prepare APK generation

Description: Ensure the app can be built and distributed locally as an APK.

Priority: Should

Notes: No Play Store publication is planned.

## Prepare offline map strategy

Description: Define a later strategy for offline map support.

Priority: Could

Notes: Not part of V1 implementation.

## Evaluate future GPS validation

Description: Assess whether GPS-assisted completion validation should be added after V1.

Priority: Could

Notes: GPS is explicitly excluded from V1.
