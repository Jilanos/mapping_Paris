# Task 0016: Add Strava Activity and Stream Sync

From version: 0.3.3

Status: In Review

Understanding: 86%

Confidence: 72%

Progress: 90%

Complexity: High

Theme: Backend Sync

## Goal

Synchronize Strava runs and rides, download eligible GPS streams, and store sync
history.

## Links

- Derived from `docs/backlog/0047-add-strava-activity-and-stream-sync.md`
- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Scope

In:

- `POST /sync/strava`.
- `GET /sync/status`.
- Activity metadata persistence.
- Stream metadata or payload handling.
- SyncRun and SyncError persistence.
- Rate limit state handling.

Out:

- No segment matching.
- No Android UI.

## Validation

- Runs and rides are filtered.
- Sync status is queryable.
- Failures are stored and retry-safe.
- Rate limit state is represented.

## Report

Implemented and validated locally.

Delivered the backend Strava activity and stream sync foundation:

- SQLite models for:
  - `StravaActivity`
  - `StravaStream`
  - `SyncRun`
  - `SyncError`
- Strava client methods for:
  - activity listing
  - GPS stream download
  - safe token refresh reuse
  - rate-limit header parsing when present
- Sync service that:
  - loads encrypted stored tokens
  - refreshes tokens when expired or near expiry
  - fetches recent activities with bounded pagination
  - stores `Run` and `Ride` activities
  - ignores unsupported sport types
  - downloads `latlng`, `distance`, and `time` streams
  - records `SyncRun` success, partial failure, or failure
  - records `SyncError` rows for per-activity stream failures
- API routes:
  - `POST /sync/strava`
  - `GET /sync/status`
  - `GET /sync/runs`
- README updates for sync settings and routes.
- Mocked tests for sync behavior and client request construction.

Validation passed:

- `python -m compileall backend/app`
- `backend/.venv/Scripts/python.exe -m pytest backend/tests`
- `git diff --check`
- staged secret scan before commit

No segment dataset ingestion, GPS-to-segment matching, proposal API, background
jobs, Alembic migrations, Docker setup, or Android runtime changes were
implemented.

Pending:

- Manual validation after commit/push.
