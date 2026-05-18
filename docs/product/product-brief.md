# Product Brief

## Product vision

Create a simple personal Android app to track walking or cycling progress across Paris street segments. The app helps build a reliable heritage-style record of streets already covered in Paris intra-muros.

## User problem

The user wants a practical way to know which Paris streets have already been covered and which remain to be explored. Existing map tools do not provide a lightweight personal completion layer based on manually selected street segments.

## Target user

The primary user is the project owner. The app is personal, local-first, and distributed only as an APK.

## MVP scope

- Display an online OpenStreetMap-based 2D map of Paris intra-muros.
- Load a local preprocessed segment dataset generated from OpenStreetMap.
- Represent a segment as a portion of street between two intersections.
- Allow manual selection of one or more segments.
- Mark selected segments as completed or not completed.
- Store completion state locally on the device.
- Show global completion statistics and statistics by arrondissement.
- Keep the V1 street dataset inside the Boulevard Peripherique, excluding the Bois de Boulogne and Bois de Vincennes without cutting into valid intra-muros neighborhoods.
- Include public ways that are reasonably walkable or bikeable.

## Out of scope for V1

- GPS-based validation.
- Automatic route tracking.
- User accounts.
- Backend services.
- Cloud synchronization.
- Play Store release.
- Offline map tiles.
- Perfect GIS completeness or survey-grade accuracy.

## Core user flows

- Open the app and view Paris intra-muros on a 2D map.
- Inspect rendered street segments.
- Select one segment and toggle its completion state.
- Select multiple segments and toggle their completion state together.
- Review completion progress globally and by arrondissement.

## Data principles

- OpenStreetMap is the source for street geometry.
- Segment source data and user progress data are separate.
- The source segment dataset must not contain user completion state.
- Completion state is local user data stored in the Android app.
- Data quality should be sufficient for personal heritage tracking, not perfect GIS accuracy.
- Segment ids are defined before app integration and treated as stable app references.
- Arrondissement assignment can be approximate or arbitrary when a segment is ambiguous.
- Street geometry can be simplified as long as the rendered Paris segment network remains understandable.

## Technical principles

- Keep the V1 Android app simple, robust, and maintainable.
- Prefer Kotlin, Jetpack Compose, a simple MVVM structure, osmdroid for the map, and Room for local progress.
- Generate street segments outside Android through a dedicated preprocessing pipeline.
- Use a local preprocessed dataset, probably GeoJSON, for app consumption.
- Keep offline map support and GPS validation as later evolutions.

## Success criteria

- The user can clearly see Paris intra-muros street segments on a map.
- The user can manually mark segments as completed or not completed.
- Progress persists locally between app launches.
- Statistics are understandable and useful for personal tracking.
- The V1 remains limited, maintainable, and aligned with manual validation.
