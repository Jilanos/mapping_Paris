# Task 0019: Expose B2 Proposals API

From version: 0.3.3

Status: Ready

Understanding: 88%

Confidence: 76%

Progress: 0%

Complexity: Medium

Theme: API Contract

## Goal

Expose B2 segment proposals through a stable JSON API for later Android review.

## Links

- Derived from `docs/backlog/0050-expose-b2-proposals-api.md`
- Spec: `docs/specs/0001-strava-b2-backend-responsibilities-and-android-contract.md`
- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Scope

In:

- `GET /proposals`.
- `POST /proposals/{proposal_id}/dismiss`.
- Proposal response schema.
- Dataset version mismatch warnings.
- API tests.

Out:

- No Android client integration.
- No backend completion writeback.

## Validation

- Android-compatible proposal payload is returned.
- Proposal dismissal is persisted.
- Backend never marks segments completed.

## Report

Not started.
