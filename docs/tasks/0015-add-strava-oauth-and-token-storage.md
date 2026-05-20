# Task 0015: Add Strava OAuth and Token Storage

From version: 0.3.3

Status: In Review

Understanding: 86%

Confidence: 72%

Progress: 90%

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

Implemented and validated locally.

Delivered a first Strava B2 OAuth and encrypted token foundation:

- SQLite database foundation with automatic local table creation.
- `AuthState` model for OAuth state persistence and expiry.
- `StravaToken` model for encrypted token storage.
- Fernet-based token encryption via `TOKEN_ENCRYPTION_KEY`.
- Strava API client foundation for token exchange and token refresh.
- OAuth routes:
  - `GET /auth/strava/start`
  - `GET /auth/strava/callback`
  - `POST /auth/strava/refresh`
  - `GET /auth/strava/status`
- Safe config failures when Strava settings or encryption key are missing.
- README updates for SQLite, OAuth routes, and token encryption setup.
- Tests for crypto, Strava client, auth routes, safe status responses, and
  encrypted token persistence.

Validation passed:

- `python -m compileall backend/app`
- `backend/.venv/Scripts/python.exe -m pytest backend/tests`
- `git diff --check`
- staged secret scan before commit

No activity sync, stream download, segment dataset ingestion, GPS matching,
proposal API, or Android runtime changes were implemented.

Pending:

- Manual validation after commit/push.
