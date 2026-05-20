# Backlog 0046: Add Strava OAuth and Token Storage

From version: 0.3.3

Status: Ready

Understanding: 86%

Confidence: 72%

Progress: 0%

Complexity: High

Theme: Backend Security

## Source

- Spec: `docs/specs/0001-strava-b2-backend-responsibilities-and-android-contract.md`
- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Description

Implement OAuth start/callback and secure local token storage for the single-user
B2 backend.

## Scope

In:

- `GET /auth/strava/start`.
- `GET /auth/strava/callback`.
- `POST /auth/strava/refresh`.
- SQLite token persistence.
- Token encryption or documented first-milestone secure storage mechanism.

Out:

- No multi-user auth.
- No Android session auth unless required for local testing.

## Acceptance Criteria

- OAuth flow stores tokens server-side.
- Tokens are not exposed to Android.
- Tokens are not logged.
- Refresh behavior is testable.

## Priority

Priority: Must

Impact: High

Urgency: High

## Task Coverage

- Planning: `docs/tasks/0012-prepare-strava-b2-implementation-plan.md`
- Implementation: `docs/tasks/0015-add-strava-oauth-and-token-storage.md`
