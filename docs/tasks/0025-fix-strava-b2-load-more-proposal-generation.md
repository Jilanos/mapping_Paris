# Task 0025 - Fix Strava B2 load-more proposal generation

## Goal

Ensure older Strava activities imported by `Charger plus d'activites` are
actually processed by proposal generation.

## Root Cause

Proposal generation used a fixed activity limit and a stable stream ordering.
After the first successful generation, subsequent runs could keep selecting the
same already-processed streams instead of the newly imported older streams.

## Scope

- Add an optional proposal generation request with `only_unprocessed` and
  `max_activities`.
- Prioritize streams whose Strava activity has no proposal for the active
  segment dataset.
- Keep existing empty-body `POST /proposals/generate` behavior compatible and
  idempotent.
- Update Android load-more to call proposal generation in unprocessed mode.
- Surface clearer generation diagnostics in the Android B2 panel.

## Acceptance Criteria

- Load-more sync still imports older activities and streams.
- Proposal generation processes streams that do not already have proposals.
- Accepted and dismissed proposals are not overwritten.
- Duplicate proposals are not created.
- Android distinguishes synced activities from activities processed for
  proposals.
- If no reviewable segment appears, the UI explains the likely reason.
- Backend tests and Android build pass.

## Validation

- `python -m compileall backend/app`
- `backend\\.venv\\Scripts\\python.exe -m pytest backend\\tests`
- `.\\gradlew.bat testDebugUnitTest`
- `.\\gradlew.bat assembleDebug`
- `git diff --check`

## Result

Implemented. Automated validation passed.
