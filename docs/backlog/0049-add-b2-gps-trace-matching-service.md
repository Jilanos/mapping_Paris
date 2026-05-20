# Backlog 0049: Add B2 GPS Trace Matching Service

From version: 0.3.3

Status: Ready

Understanding: 86%

Confidence: 70%

Progress: 0%

Complexity: High

Theme: Matching

## Source

- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Description

Implement conservative server-side GPS trace to logical segment matching.

## Scope

In:

- Project GPS points onto segment polylines.
- Compute coverage ratio and matched distance.
- Generate SegmentMatchProposal rows.
- Deduplicate proposals.
- Attach confidence and activity evidence.

Out:

- No automatic completion.
- No Android UI.

## Acceptance Criteria

- Matching outputs logical segment ids.
- Matching is conservative.
- Proposals include evidence metadata.
- Dismissed proposals are not reintroduced without a deliberate reset.

## Priority

Priority: Must

Impact: High

Urgency: Medium

## Task Coverage

- Planning: `docs/tasks/0012-prepare-strava-b2-implementation-plan.md`
- Implementation: `docs/tasks/0018-add-b2-gps-trace-matching-service.md`
