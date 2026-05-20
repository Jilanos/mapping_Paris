# Backlog 0038: Define GPS Trace to Segment Matching Strategy

From version: 0.3.3

Status: Ready

Understanding: 90%

Confidence: 78%

Progress: 0%

Complexity: High

Theme: Matching

## Source

- Request: `docs/request/0008-strava-b2-backend-integration-for-gps-segment-proposals.md`

## Description

Define how B2 should match Strava GPS traces against Paris logical street
segments and produce conservative proposals.

## Scope

In:

- Matching input format.
- Segment dataset versioning requirement.
- Distance and coverage thresholds.
- Handling noisy GPS traces.
- Handling parallel streets and logical segment groups.
- Proposal confidence metadata.

Out:

- No matching implementation.
- No dataset regeneration.

## Acceptance Criteria

- Matching strategy is documented.
- Logical segment id remains the proposal unit.
- Conservative proposal behavior is explicit.
- Known edge cases are listed.

## Priority

Priority: Must

Impact: High

Urgency: High

## Task Coverage

- `docs/tasks/0010-orchestrate-strava-b2-contract-security-and-validation.md`
