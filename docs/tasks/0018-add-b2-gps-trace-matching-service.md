# Task 0018: Add B2 GPS Trace Matching Service

From version: 0.3.3

Status: In Review

Understanding: 86%

Confidence: 70%

Progress: 90%

Complexity: High

Theme: Matching

## Goal

Implement conservative server-side matching from Strava GPS traces to logical
Paris segment proposals.

## Links

- Derived from `docs/backlog/0049-add-b2-gps-trace-matching-service.md`
- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Scope

In:

- Project GPS points onto segment polylines.
- Compute coverage ratio.
- Generate SegmentMatchProposal rows.
- Deduplicate proposals.
- Attach confidence and activity evidence.

Out:

- No automatic completion.
- No Android UI.

## Validation

- Matching outputs logical segment ids.
- Matching is conservative on noisy traces.
- Proposal evidence is present.
- Dismissed proposals are not reintroduced.

## Report

Implemented and validated locally.

Delivered the backend GPS-to-segment matching foundation:

- Local point-to-polyline distance and projection logic.
- Approximate lat/lon to meters conversion without heavy geospatial
  dependencies.
- Candidate segment filtering by active dataset bounding boxes plus buffer.
- Coverage ratio estimation from projected matched GPS points.
- Configurable matching settings:
  - `MATCH_MAX_DISTANCE_METERS`
  - `MATCH_MIN_COVERAGE_RATIO`
  - `MATCH_MIN_MATCHED_POINTS`
  - `MATCH_MAX_ACTIVITIES_PER_RUN`
  - `MATCH_CANDIDATE_BBOX_BUFFER_METERS`
- Deterministic confidence score from coverage, average distance, and matched
  points.
- Proposal generation from stored `StravaStream` rows and active
  `B2StreetSegment` rows.
- Idempotent handling of duplicate activity/segment/logical id proposals.
- Accepted and dismissed proposals are not overwritten by later generation.

Validation passed:

- `python -m compileall backend/app`
- `backend/.venv/Scripts/python.exe -m pytest backend/tests`
- `git diff --check`
- staged secret scan before commit

No Android runtime files were modified and no Android completion state is
written by the backend.

Pending:

- Manual validation after commit/push.
