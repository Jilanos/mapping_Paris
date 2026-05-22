# Task 0026 - Fix Strava B2 proposal pagination and review loading

## Goal

Prevent the Strava B2 proposal screen from getting stuck when the first backend
proposal page contains only hidden proposals.

## Root Cause

Android loaded only the first 100 raw backend proposals, then filtered them
locally. If those 100 proposals were already completed locally or not
recognized, the review list became empty even though later backend pages could
contain reviewable local segments.

## Scope

- Add `limit`/`offset` pagination metadata to `GET /proposals`.
- Keep the existing `proposals` response wrapper for compatibility.
- Update Android to scan backend proposal pages until it finds enough unique
  reviewable local logical segments, reaches the backend end, or hits a safe
  scan cap.
- Add `Charger plus de propositions` to continue scanning existing backend
  proposals without syncing older Strava activities.
- Improve diagnostics around total backend proposals, analyzed proposals, pages
  analyzed, and whether the end was reached.

## Acceptance Criteria

- Android no longer stops at the first 100 hidden proposals.
- `A examiner` is based on unique reviewable local logical segments.
- Orange highlights still match only reviewable proposals.
- Accepted/dismissed backend proposals do not reappear.
- Completed local segments remain hidden.
- Non-recognized proposals remain hidden.
- Backend tests and Android build pass.

## Validation

- `python -m compileall backend/app`
- `backend\\.venv\\Scripts\\python.exe -m pytest backend\\tests`
- `.\\gradlew.bat testDebugUnitTest`
- `.\\gradlew.bat assembleDebug`
- `git diff --check`

## Result

Implemented. Automated validation passed.
