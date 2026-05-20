# Task 0014: Add B2 Configuration and Secret Loading

From version: 0.3.3

Status: In Review

Understanding: 88%

Confidence: 76%

Progress: 90%

Complexity: Medium

Theme: Backend Security

## Goal

Add environment-based configuration for B2 without committing real secrets.

## Links

- Derived from `docs/backlog/0045-add-b2-configuration-and-secret-loading.md`
- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Scope

In:

- Config module.
- Required environment variable validation.
- `.env.example` with fake placeholder values only.
- Documentation for local config.

Out:

- No real Strava credentials.
- No production secret manager.

## Validation

- App starts with valid local fake config where safe.
- App reports missing required config clearly.
- Secret scan finds no real values.

## Report

Implemented and validated locally.

Updated the backend configuration foundation with:

- centralized `Settings` in `backend/app/core/config.py`
- cached `get_settings()`
- optional local `.env` loading
- `APP_NAME`, `APP_VERSION`, `ENV`, `LOG_LEVEL`, `API_BASE_URL`,
  `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REDIRECT_URI`, and
  `DATABASE_URL`
- `strava_configured` helper that is true only when Strava id, secret, and
  redirect URI are present
- complete placeholder-only `.env.example`
- README guidance for local `.env` setup and secret handling
- tests for default settings, Strava readiness, and `/health` secret exposure

Validation passed:

- `python -m compileall backend/app`
- `backend/.venv/Scripts/python.exe -m pytest backend/tests`
- `git diff --check`
- targeted secret scan on modified files

No Strava OAuth, token storage, database models, sync, stream download, segment
matching, or Android runtime changes were implemented.

Pending:

- Manual validation before commit.
