# Task 0019: Expose B2 Proposals API

From version: 0.3.3

Status: In Review

Understanding: 88%

Confidence: 76%

Progress: 90%

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

Implemented and validated locally.

Delivered the proposals API foundation:

- SQLite model `SegmentMatchProposal`.
- `POST /proposals/generate`
- `GET /proposals`
- `GET /proposals/status`
- `POST /proposals/{proposal_id}/dismiss`
- `POST /proposals/{proposal_id}/accept`
- Query filters by status, arrondissement, and street name.
- Optional raw match output through `include_raw`.
- Safe proposal status updates without deleting proposals.
- Backend `accepted` status is only a B2 acknowledgement; it does not update
  Android completion state.
- Tests verify proposal generation, idempotence, filters, counts,
  accept/dismiss behavior, and absence of tokens/secrets in responses.

Validation passed:

- `python -m compileall backend/app`
- `backend/.venv/Scripts/python.exe -m pytest backend/tests`
- `git diff --check`
- staged secret scan before commit

No Android integration was implemented.

Pending:

- Manual validation after commit/push.
