# Backlog 0040: Define Android Proposed Segment Review Flow

From version: 0.3.3

Status: Ready

Understanding: 88%

Confidence: 80%

Progress: 0%

Complexity: Medium

Theme: Android UX

## Source

- Request: `docs/request/0008-strava-b2-backend-integration-for-gps-segment-proposals.md`

## Description

Define how Android should present B2 proposed segments for review, editing,
acceptance, rejection, and rollback while preserving manual confirmation.

## Scope

In:

- Proposal review states.
- Map selection behavior for B2 proposals.
- Accept, reject, and clear behavior.
- Manual override and rollback expectations.
- Interaction with existing Room completion state.

Out:

- No UI implementation.
- No Room schema change unless later task proves it necessary.

## Acceptance Criteria

- Review flow is documented.
- No automatic completion is allowed.
- User confirmation is explicit.
- Rejection and rollback expectations are listed.

## Priority

Priority: Should

Impact: High

Urgency: Medium

## Task Coverage

- `docs/tasks/0011-orchestrate-strava-b2-release-planning.md`
