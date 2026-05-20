# Task 0018: Add B2 GPS Trace Matching Service

From version: 0.3.3

Status: Ready

Understanding: 86%

Confidence: 70%

Progress: 0%

Complexity: High

Theme: Matching

## Goal

Implement conservative server-side matching from Strava GPS traces to logical
Paris segment proposals.

## Links

- Derived from `docs/backlog/0049-add-b2-gps-trace-matching-service.md`
- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Scope

In:

- Project GPS points onto segment polylines.
- Compute coverage ratio.
- Generate SegmentMatchProposal rows.
- Deduplicate proposals.
- Attach confidence and activity evidence.

Out:

- No automatic completion.
- No Android UI.

## Validation

- Matching outputs logical segment ids.
- Matching is conservative on noisy traces.
- Proposal evidence is present.
- Dismissed proposals are not reintroduced.

## Report

Not started.
