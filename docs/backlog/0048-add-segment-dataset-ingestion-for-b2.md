# Backlog 0048: Add Segment Dataset Ingestion for B2

From version: 0.3.3

Status: Ready

Understanding: 88%

Confidence: 78%

Progress: 0%

Complexity: Medium

Theme: Backend Data

## Source

- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Description

Load a versioned Paris logical segment dataset into B2 for matching.

## Scope

In:

- Dataset path config.
- Dataset checksum.
- SegmentDatasetVersion record.
- Logical segment geometry loading.
- Validation that logical segment ids match Android dataset expectations.

Out:

- No dataset regeneration.
- No Android asset change.

## Acceptance Criteria

- B2 can load the current segment dataset.
- Dataset version and checksum are recorded.
- Matching service can consume logical segment geometries.

## Priority

Priority: Must

Impact: High

Urgency: Medium

## Task Coverage

- Planning: `docs/tasks/0012-prepare-strava-b2-implementation-plan.md`
- Implementation: `docs/tasks/0017-add-b2-segment-dataset-ingestion.md`
