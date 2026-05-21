# Task 0017: Add B2 Segment Dataset Ingestion

From version: 0.3.3

Status: In Review

Understanding: 88%

Confidence: 78%

Progress: 90%

Complexity: Medium

Theme: Backend Data

## Goal

Load the Paris logical segment dataset into B2 with version and checksum
tracking.

## Links

- Derived from `docs/backlog/0048-add-segment-dataset-ingestion-for-b2.md`
- Spec: `docs/specs/0002-strava-b2-backend-architecture-and-data-model.md`

## Scope

In:

- Configurable dataset path.
- Dataset checksum.
- SegmentDatasetVersion record.
- Logical segment geometry loader.
- Dataset validation for matching.

Out:

- No dataset regeneration.
- No Android asset changes.

## Validation

- Current segment dataset can be loaded.
- Logical segment ids are available to matching service.
- Dataset version metadata is stored.

## Report

Implemented and validated locally.

Delivered the backend segment dataset ingestion foundation:

- SQLite models for:
  - `SegmentDatasetVersion`
  - `B2StreetSegment`
- GeoJSON parser for the Android dataset schema.
- Preservation of `id` and `logical_segment_id`.
- Fallback to `id` when `logical_segment_id` is missing, matching Android
  parser behavior.
- Storage of geometry as JSON text.
- Per-segment bounding box computation.
- SHA-256 dataset hashing.
- Dataset store that avoids duplicate dataset hashes.
- Active dataset version switching.
- Local ingestion command:
  - `python -m app.tools.ingest_segments --source ../app/src/main/assets/paris_segments.geojson`
- Read-only API routes:
  - `GET /segments/status`
  - `GET /segments/datasets`
  - `GET /segments/search`
- Tests for parser behavior, ingestion, version activation, API responses,
  filtering, geometry hiding, and real Android GeoJSON parsing.

Validation passed:

- `python -m compileall backend/app`
- `backend/.venv/Scripts/python.exe -m pytest backend/tests`
- CLI ingestion against `app/src/main/assets/paris_segments.geojson`
  - segment count: 18963
  - logical segment count: 18001
- `git diff --check`
- staged secret scan before commit

No Android runtime files, source GeoJSON, GPS-to-segment matching, proposal
storage, or proposal API were modified or implemented.

Pending:

- Manual validation after commit/push.
