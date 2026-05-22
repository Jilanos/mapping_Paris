# Task 0024 - Add Strava B2 load more activities flow

## Goal

Allow Android to fetch older Strava Run/Ride activities when the current synced
activities no longer produce new local segments to review.

## Scope

- Extend `POST /sync/strava` with optional `max_pages` and `per_page`.
- Keep the default sync behavior unchanged.
- Clamp requested pages and page size to safe limits.
- Skip already stored eligible activities that already have streams.
- Add Android action `Charger plus d'activites`.
- After load-more sync, generate proposals and reload the filtered review list.
- Do not change matching thresholds, Android manual completion, or the segment
  dataset.

## Acceptance Criteria

- Normal `Synchroniser Strava` still uses the default one-page sync.
- `Charger plus d'activites` progressively requests deeper Strava page windows.
- Sync summaries report requested pages and skipped existing activities.
- Existing accepted/ignored proposals remain hidden from Android review.
- Already completed local segments remain hidden from Android review.
- Backend and Android tests/build pass.
- No secrets, local DB, APK, or dataset changes are committed.

## Validation

- `python -m compileall backend/app`
- `backend\\.venv\\Scripts\\python.exe -m pytest backend\\tests`
- `.\\gradlew.bat testDebugUnitTest`
- `.\\gradlew.bat assembleDebug`
- `git diff --check`

## Result

Implemented and validated in version `0.3.4`.

- Backend accepts optional sync depth parameters and reports skipped existing
  activities.
- Android adds `Charger plus d'activites`, then runs sync, proposal generation,
  and proposal reload.
- Debug APK installed successfully on connected device `37290DLJH004PP`.
