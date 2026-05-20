# Backlog 0039: Define Android Backend API Contract

From version: 0.3.3

Status: Ready

Understanding: 88%

Confidence: 76%

Progress: 0%

Complexity: High

Theme: API Contract

## Source

- Request: `docs/request/0008-strava-b2-backend-integration-for-gps-segment-proposals.md`

## Description

Define the Android/B2 API contract for auth status, sync triggering, sync
status, proposed segments, and proposal review handoff.

## Scope

In:

- API responsibilities.
- Request and response shapes at high level.
- Proposed segment output format.
- Error and retry semantics.
- Dataset version compatibility.

Out:

- No API implementation.
- No Android network layer.

## Acceptance Criteria

- Android/backend contract is drafted.
- Proposal payload includes logical segment ids.
- Failure modes are represented.
- Android remains responsible for user confirmation.

## Priority

Priority: Must

Impact: High

Urgency: High

## Task Coverage

- `docs/tasks/0010-orchestrate-strava-b2-contract-security-and-validation.md`
