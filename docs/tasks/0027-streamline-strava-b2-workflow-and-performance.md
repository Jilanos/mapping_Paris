# Task 0027 - Streamline Strava B2 workflow and performance

## Goal

Make the Strava B2 Android flow simpler, clearer, and safer under large
proposal volumes.

## Scope

- Replace the normal multi-button Strava workflow with one guided action:
  `Importer mes activites Strava`.
- Keep low-level sync/generate/load actions in an advanced section.
- Add stage labels and a progress bar for long Strava operations.
- Track proposal processing per Strava activity and dataset version.
- Add a backend reset route for processed activity markers.
- Add Android reset action with confirmation.
- Add a map highlight toggle for Strava proposals.
- Disable orange highlights automatically when too many reviewable proposals
  would be rendered.
- Open settings directly from the main menu button.
- Bump Android version to `0.3.5`.

## Acceptance Criteria

- Manual map completion remains unchanged.
- Backend proposals still do not mutate Android progress without explicit
  Android validation.
- Proposal generation skips already processed Strava activities by default.
- Processing reset does not delete activities, streams, or proposals by
  default.
- Accepted and dismissed proposals stay protected.
- Large Strava proposal batches can be reviewed with map highlights disabled.
- Backend tests and Android build pass.

## Validation

- `python -m compileall backend/app`
- `backend\\.venv\\Scripts\\python.exe -m pytest backend\\tests`
- `.\\gradlew.bat testDebugUnitTest`
- `.\\gradlew.bat assembleDebug`
- `git diff --check`

## Result

Implemented. Automated validation passed.
