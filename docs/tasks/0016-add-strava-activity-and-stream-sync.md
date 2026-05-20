# Task 0016: Add Strava Activity and Stream Sync

From version: 0.3.3

Status: Ready

Understanding: 86%

Confidence: 72%

Progress: 0%

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

Not started.
