# Task 0028 - Add async Strava B2 proposal generation progress

## Goal

Prevent Android timeouts during Strava B2 proposal generation by moving the
long proposal analysis step behind a backend job API and polling progress from
Android.

## Scope

- Add backend proposal generation job persistence.
- Add non-blocking proposal generation job endpoints.
- Keep the existing synchronous `POST /proposals/generate` endpoint.
- Update Android `Importer mes activites Strava` to start a job and poll it.
- Fix the progress indicator so unknown progress is indeterminate.
- Bump Android to `versionName=0.3.6`.

## Files changed

- `backend/app/db/models.py`
- `backend/app/schemas/proposals.py`
- `backend/app/services/proposal_service.py`
- `backend/app/api/routes/proposals.py`
- `backend/tests/test_proposals.py`
- `backend/README.md`
- `app/build.gradle.kts`
- `app/src/main/java/com/jilanos/mappingparis/b2/B2ApiClient.kt`
- `app/src/main/java/com/jilanos/mappingparis/b2/B2Models.kt`
- `app/src/main/java/com/jilanos/mappingparis/ui/MappingParisViewModel.kt`
- `app/src/main/java/com/jilanos/mappingparis/ui/MappingParisApp.kt`

## Acceptance criteria

- [x] Android no longer waits on one long synchronous proposal generation request.
- [x] Backend exposes proposal generation job start and status endpoints.
- [x] Job counters are persisted and safe to poll.
- [x] Existing synchronous proposal generation remains available.
- [x] Android shows stage labels and handles job failure or polling timeout.
- [x] The progress bar uses an indeterminate state when exact progress is unknown.
- [x] No Strava token, client secret, encryption key, local DB, or APK is committed.

## Validation steps

- `python -m compileall backend/app`
- `backend\.venv\Scripts\python.exe -m pytest backend\tests`
- `.\gradlew.bat testDebugUnitTest`
- `.\gradlew.bat assembleDebug`
- `git diff --check`
- Install debug APK on connected phone if available.

## Non-goals

- No backend deployment.
- No matching threshold changes.
- No segment dataset changes.
- No automatic completion without explicit Android confirmation.
