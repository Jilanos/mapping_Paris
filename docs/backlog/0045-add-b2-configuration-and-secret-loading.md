# Backlog 0045: Add B2 Configuration and Secret Loading

From version: 0.3.3

Status: Ready

Understanding: 88%

Confidence: 76%

Progress: 0%

Complexity: Medium

Theme: Backend Security

## Source

- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Description

Add environment-based configuration for B2 without committing real secrets.

## Scope

In:

- Config module.
- Required environment variables.
- Local `.env.example` with fake placeholder values only.
- Secret validation at startup.

Out:

- No real Strava credentials.
- No production secret manager integration.

## Acceptance Criteria

- App refuses invalid required config where appropriate.
- Real secrets are not committed.
- `.env` remains ignored.

## Priority

Priority: Must

Impact: High

Urgency: High

## Task Coverage

- Planning: `docs/tasks/0012-prepare-strava-b2-implementation-plan.md`
- Implementation: `docs/tasks/0014-add-b2-configuration-and-secret-loading.md`
