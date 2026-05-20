# Task 0014: Add B2 Configuration and Secret Loading

From version: 0.3.3

Status: Ready

Understanding: 88%

Confidence: 76%

Progress: 0%

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

Not started.
