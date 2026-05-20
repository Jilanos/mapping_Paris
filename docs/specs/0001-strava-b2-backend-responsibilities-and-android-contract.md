# Spec 0001: Strava B2 Backend Responsibilities and Android Contract

Status: Draft

Date: 2026-05-20

Related request: `docs/request/0008-strava-b2-backend-integration-for-gps-segment-proposals.md`

Related ADR: `docs/adr/0002-use-dedicated-strava-b2-backend-for-activity-sync-and-segment-proposals.md`

## Purpose

Define the initial responsibilities and contract boundaries between the future
Strava B2 backend and the existing Android app.

This is a framing spec only. It does not authorize backend implementation yet.

## Current Android Responsibilities

- Load local Paris segment dataset from packaged GeoJSON.
- Use `logicalSegmentId` as the completion and statistics unit.
- Store confirmed completion state locally in Room.
- Render the map and segment overlays.
- Display statistics globally and by arrondissement.
- Let the user manually select and validate segments.
- Use local device GPS to propose editable segment selections.

## B2 Backend Responsibilities

- Handle Strava OAuth at a high level.
- Store Strava access and refresh tokens securely.
- Refresh tokens when required.
- Synchronize Strava running and cycling activities.
- Download activity GPS streams when authorized.
- Maintain sync history and avoid duplicate processing.
- Match GPS traces against the Paris logical segment dataset.
- Return proposed segment ids and supporting metadata to Android.
- Track sync failures and rate limit states.

Initial architecture recommendation:

- FastAPI Python service.
- Single-user first.
- SQLite for the first implementation milestone.
- Environment-variable configuration.
- No committed secrets.
- Android remains the final confirmation surface.

## Authentication Flow

High-level target:

1. Android starts a Strava connect flow or opens a backend-provided auth URL.
2. User authorizes the Strava app.
3. Strava redirects to a backend-controlled callback.
4. Backend exchanges the code for tokens.
5. Backend stores tokens securely.
6. Android receives a connected status, not the Strava client secret.

Default for the first implementation: single-user and locally configured.
Android/B2 session authentication can be deferred until remote deployment or
multi-device access requires it.

## Token Handling

- Strava client secret must not be stored in Android.
- Strava client secret must not be committed to Git.
- Refresh tokens must be encrypted or stored in a secure managed store.
- Access tokens should be short-lived and refreshed server-side.
- Revoked or expired access must be surfaced to Android as an actionable state.

## Activity Sync Responsibilities

B2 should:

- sync runs and rides only by default;
- support initial sync and incremental sync;
- keep Strava activity ids for deduplication;
- track sync status per activity;
- record failure reason and retry eligibility;
- respect Strava API rate limits.

## Stream Import Responsibilities

B2 should:

- request GPS streams only for eligible activities;
- store enough stream metadata to avoid repeated downloads;
- avoid logging raw stream payloads by default;
- decide whether raw streams are stored or discarded after matching.

Open question: whether B2 should store raw GPS streams, simplified traces, or
only derived proposal results.

## Segment Matching Responsibilities

B2 should:

- use the same logical segment ids as Android;
- know the segment dataset version used for matching;
- account for GPS noise and dense Paris street geometry;
- treat parallel same-street logical groups consistently;
- output conservative proposals with confidence or evidence metadata;
- never mark segments completed directly.

Potential proposal evidence:

- matched activity ids;
- coverage ratio;
- matched distance;
- matching threshold;
- first and last matched timestamps;
- confidence level.

## Proposed Segment Output Format

Initial high-level shape:

```json
{
  "schema": "mapping-paris-b2-proposals-v1",
  "segmentDatasetVersion": "unknown",
  "generatedAt": "ISO-8601",
  "syncId": "string",
  "proposals": [
    {
      "logicalSegmentId": "string",
      "activityIds": ["string"],
      "coverageRatio": 0.82,
      "confidence": "medium",
      "reason": "gps_trace_match"
    }
  ],
  "warnings": []
}
```

## Android Review and Confirmation Responsibility

Android should:

- fetch or receive B2 proposals;
- display proposed logical segment ids on the existing map;
- allow the user to deselect incorrect proposals;
- allow the user to confirm selected proposals;
- write only confirmed completions to Room;
- preserve manual override and reset behavior.

Android should not:

- accept proposals silently;
- mark segments completed without user action;
- store Strava client secrets.

## Failure Modes

- Strava authorization denied.
- Strava token expired or revoked.
- Strava API rate limit reached.
- Activity sync partially failed.
- GPS stream unavailable for an activity.
- Segment dataset version mismatch.
- Matching produced no proposals.
- Backend unavailable.
- Android offline while trying to sync.

Each failure should have a user-safe state and should not corrupt local
completion state.

## Rate Limit Handling

B2 should:

- track API usage windows;
- avoid repeated stream downloads;
- allow sync to pause and resume;
- return rate limit state to Android;
- avoid retry loops.

## Privacy Constraints

- Tokens are sensitive.
- GPS traces are sensitive.
- Logs should not contain tokens.
- Logs should avoid raw GPS trace payloads unless explicitly needed for local
  debugging.
- A deletion path for tokens and sync data must be defined before production
  use.

## Open Questions

- Hosting target.
- Token encryption mechanism.
- Segment dataset versioning and update flow.
- Raw GPS stream retention policy.
- Proposal history retention policy.
- Exact confidence scoring model.
- Whether B2 should expose accepted or rejected proposal history.
