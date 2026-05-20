# Backlog 0050: Expose B2 Proposals API

From version: 0.3.3

Status: Ready

Understanding: 88%

Confidence: 76%

Progress: 0%

Complexity: Medium

Theme: API Contract

## Source

- Spec: `docs/specs/0001-strava-b2-backend-responsibilities-and-android-contract.md`
- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Description

Expose segment proposals to Android through a stable JSON API.

## Scope

In:

- `GET /proposals`.
- `POST /proposals/{proposal_id}/dismiss`.
- Proposal schema.
- Dataset version mismatch warning.
- API tests.

Out:

- No Android client integration.
- No accepted-completion writeback in backend.

## Acceptance Criteria

- Android can fetch proposed logical segment ids.
- Android can dismiss proposals.
- Payload includes evidence and warnings.
- Backend does not mark segments completed.

## Priority

Priority: Must

Impact: High

Urgency: Medium

## Task Coverage

- Planning: `docs/tasks/0012-prepare-strava-b2-implementation-plan.md`
- Implementation: `docs/tasks/0019-expose-b2-proposals-api.md`
