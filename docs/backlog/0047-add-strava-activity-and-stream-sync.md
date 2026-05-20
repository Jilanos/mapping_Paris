# Backlog 0047: Add Strava Activity and Stream Sync

From version: 0.3.3

Status: Ready

Understanding: 86%

Confidence: 72%

Progress: 0%

Complexity: High

Theme: Backend Sync

## Source

- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Description

Synchronize Strava runs and rides, download eligible GPS streams, and record sync
history.

## Scope

In:

- `POST /sync/strava`.
- `GET /sync/status`.
- Activity metadata persistence.
- Stream metadata or payload handling.
- SyncRun and SyncError records.
- Rate limit state handling.

Out:

- No matching implementation in this slice.
- No Android UI.

## Acceptance Criteria

- Runs and rides can be synchronized.
- Stream download can be triggered for eligible activities.
- Sync status is queryable.
- Failures are recorded without corrupting state.

## Priority

Priority: Must

Impact: High

Urgency: Medium

## Task Coverage

- Planning: `docs/tasks/0012-prepare-strava-b2-implementation-plan.md`
- Implementation: `docs/tasks/0016-add-strava-activity-and-stream-sync.md`
