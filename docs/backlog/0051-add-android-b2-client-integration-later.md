# Backlog 0051: Add Android B2 Client Integration Later

From version: 0.3.3

Status: Ready

Understanding: 82%

Confidence: 68%

Progress: 0%

Complexity: High

Theme: Android Integration

## Source

- Request: `docs/request/0008-strava-b2-backend-integration-for-gps-segment-proposals.md`

## Description

Add Android integration with the B2 proposals API after backend behavior is
validated.

## Scope

In:

- Configure backend URL for local testing.
- Fetch sync status and proposals.
- Display B2 proposals as editable map selections.
- Confirm accepted proposals through existing local completion flow.
- Preserve manual confirmation.

Out:

- No Android implementation until backend contract is stable.
- No automatic completion.
- No Play Store work.

## Acceptance Criteria

- Android can display B2 proposals.
- User can deselect proposals.
- User must explicitly confirm completion.
- Completion remains stored locally in Room.

## Priority

Priority: Should

Impact: High

Urgency: Later

## Task Coverage

- Planning: `docs/tasks/0012-prepare-strava-b2-implementation-plan.md`
- Implementation: `docs/tasks/0020-add-android-b2-client-integration-later.md`
