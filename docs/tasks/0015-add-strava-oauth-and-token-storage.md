# Task 0015: Add Strava OAuth and Token Storage

From version: 0.3.3

Status: Ready

Understanding: 86%

Confidence: 72%

Progress: 0%

Complexity: High

Theme: Backend Security

## Goal

Implement Strava OAuth start/callback/refresh and secure single-user token
storage.

## Links

- Derived from `docs/backlog/0046-add-strava-oauth-and-token-storage.md`
- ADR: `docs/adr/0002-use-dedicated-strava-b2-backend-for-activity-sync-and-segment-proposals.md`
- Spec: `docs/specs/0001-strava-b2-backend-responsibilities-and-android-contract.md`

## Scope

In:

- `GET /auth/strava/start`.
- `GET /auth/strava/callback`.
- `POST /auth/strava/refresh`.
- SQLite token persistence.
- Token encryption or documented first-milestone secure storage.

Out:

- No multi-user auth.
- No Android integration.

## Validation

- OAuth flow can store server-side tokens.
- Tokens are not returned to Android.
- Tokens are not logged.
- Refresh flow is testable.

## Report

Not started.
