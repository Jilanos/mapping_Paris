# Spec 0002: Strava B2 Backend Architecture and Data Model

Status: Draft

Date: 2026-05-20

Related request: `docs/request/0008-strava-b2-backend-integration-for-gps-segment-proposals.md`

Related ADR: `docs/adr/0002-use-dedicated-strava-b2-backend-for-activity-sync-and-segment-proposals.md`

## Recommendation

Build the first B2 implementation as a Python FastAPI backend with SQLite,
single-user first, and environment-variable configuration.

Keep a clean path toward PostgreSQL and multi-user support, but do not implement
multi-user behavior in the first milestone.

## Architecture Decision Matrix

| Option | Strengths | Weaknesses | Fit |
| --- | --- | --- | --- |
| Direct Strava in APK | No backend to host, simple user flow | Secrets and refresh tokens in APK are risky; sync and matching are harder to evolve | Reject |
| B1 token proxy | Keeps secret out of APK, smaller backend | Does not own sync, stream ingestion, matching, history, or proposals | Not enough |
| B2 FastAPI | Good fit for matching, clear API, easy local dev, Python geospatial path | Requires hosting and backend operations | Recommended |
| B2 Node Express | Good REST API ergonomics | Less natural for GPS matching and segment tooling | Viable fallback |
| Cloudflare Worker | Lightweight hosting | Awkward for GPS stream processing and dataset matching | Not first target |
| Desktop JSON sync | No hosted backend | Manual workflow, poor Android sync experience | Prototype fallback |

## Repository Layout Proposal

Initial layout when implementation starts:

```text
backend/
  README.md
  pyproject.toml
  app/
    main.py
    config.py
    db.py
    models.py
    routes/
      health.py
      auth_strava.py
      sync.py
      proposals.py
    services/
      strava_oauth.py
      strava_client.py
      sync_service.py
      stream_service.py
      segment_dataset.py
      matching_service.py
  tests/
    test_health.py
    test_contract_proposals.py
    test_matching_service.py
```

Do not create this layout until implementation is explicitly started.

## Deployment Target Proposal

First milestone:

- local development server on the workstation;
- Android can point to a local LAN URL for testing.

First personal deployment candidate:

- small VPS, Render web service, Fly.io, or another simple Python-capable host.

Avoid Cloudflare Worker for first B2 because matching and dataset handling are
more backend-service shaped than edge-function shaped.

## Database Choice

Use SQLite for the first milestone:

- simple local development;
- good enough for single-user activity and proposal history;
- easy backup;
- low operational complexity.

Keep schema compatible with a later PostgreSQL migration if B2 becomes remote,
multi-device, or multi-user.

## Environment Variables

Expected variables:

- `B2_ENV`
- `B2_BASE_URL`
- `B2_DATABASE_URL`
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI`
- `B2_TOKEN_ENCRYPTION_KEY`
- `B2_SEGMENT_DATASET_PATH`
- `B2_SEGMENT_DATASET_VERSION`

No real values should be committed. Example files may use blank or obviously
fake values only.

## Secret Management

- Load secrets from environment variables or a local untracked `.env`.
- Keep `.env` ignored.
- Never log tokens or client secrets.
- Encrypt refresh tokens at rest if stored in SQLite.
- Document token deletion and reauthorization.

## Main Backend Modules

- `config`: environment and runtime configuration.
- `db`: database connection and migrations.
- `models`: persistence models.
- `auth_strava`: OAuth start, callback, refresh.
- `strava_client`: Strava API client wrapper.
- `sync_service`: activity sync orchestration.
- `stream_service`: stream download and normalization.
- `segment_dataset`: load versioned Paris logical segment dataset.
- `matching_service`: GPS trace to logical segment proposal matching.
- `proposals`: expose current proposals and dismissals.

## Data Model Draft

### Athlete or User

Single-user first.

Fields:

- `id`
- `strava_athlete_id`
- `display_name`
- `created_at`
- `updated_at`

### StravaToken

Fields:

- `id`
- `user_id`
- `access_token_encrypted`
- `refresh_token_encrypted`
- `expires_at`
- `scope`
- `created_at`
- `updated_at`

### StravaActivity

Fields:

- `id`
- `strava_activity_id`
- `activity_type`
- `name`
- `start_date`
- `distance_meters`
- `elapsed_time_seconds`
- `sync_status`
- `stream_status`
- `created_at`
- `updated_at`

### StravaStream

Fields:

- `id`
- `activity_id`
- `point_count`
- `summary_hash`
- `storage_policy`
- `created_at`

Open decision: store raw GPS stream, simplified stream, or only derived match
evidence.

### SegmentDatasetVersion

Fields:

- `id`
- `version`
- `source_path`
- `feature_count`
- `logical_segment_count`
- `checksum`
- `loaded_at`

### SegmentMatchProposal

Fields:

- `id`
- `logical_segment_id`
- `segment_dataset_version_id`
- `sync_run_id`
- `activity_ids`
- `coverage_ratio`
- `matched_distance_meters`
- `confidence`
- `status`
- `created_at`
- `updated_at`

Statuses:

- `proposed`
- `dismissed`
- `exported_to_android`
- `accepted_in_android`

Android remains responsible for final confirmation.

### SyncRun

Fields:

- `id`
- `started_at`
- `finished_at`
- `status`
- `activities_checked`
- `activities_imported`
- `streams_downloaded`
- `proposals_created`
- `rate_limit_state`

### SyncError

Fields:

- `id`
- `sync_run_id`
- `activity_id`
- `error_type`
- `message`
- `retryable`
- `created_at`

## API Endpoint Draft

### GET /health

Returns service status and version.

### GET /auth/strava/start

Starts OAuth by redirecting to Strava authorization.

### GET /auth/strava/callback

Receives OAuth callback and stores tokens.

### POST /auth/strava/refresh

Refreshes tokens if needed.

### POST /sync/strava

Starts a Strava sync run.

### GET /sync/status

Returns latest sync status and rate limit state.

### GET /proposals

Returns current segment proposals.

### POST /proposals/{proposal_id}/dismiss

Marks a proposal dismissed server-side.

### Optional POST /proposals/{proposal_id}/confirmed

Only if needed later. Android confirmation should remain the source of local
completion state.

## Strava Sync Flow

1. Ensure Strava token is present and valid.
2. Refresh token if needed.
3. Fetch activities after last sync cursor.
4. Keep runs and rides.
5. Store activity metadata.
6. Queue stream download for eligible activities.
7. Record sync run status and errors.

## GPS Stream Ingestion Flow

1. Download lat/lng streams for eligible activities.
2. Normalize points into a backend trace format.
3. Store stream metadata.
4. Apply retention policy for raw or simplified traces.
5. Send normalized trace to matching service.

## GPS-to-Segment Matching Flow

1. Load active segment dataset version.
2. For each normalized activity trace, find nearby logical segments.
3. Project GPS points onto candidate segment geometry.
4. Compute coverage ratio and matched distance.
5. Generate conservative proposals with confidence metadata.
6. Deduplicate proposals already dismissed or already proposed.

## Sync History Model

Every sync should create a `SyncRun` row. Activity and stream errors should
create `SyncError` rows with retry flags. Proposal generation should be
traceable to a sync run and activity ids.

## Error Handling

- OAuth denied: actionable auth state.
- Token refresh failed: require reconnect.
- Rate limit reached: pause sync and expose retry time.
- Stream missing: mark activity stream unavailable.
- Dataset mismatch: block proposal generation.
- Backend error: keep prior proposals and report failure.

## Rate Limit Handling

- Track Strava rate limit headers where available.
- Avoid repeated stream download.
- Use incremental sync cursors.
- Return rate limit status in `/sync/status`.
- Avoid automatic retry loops.

## Privacy Constraints

- Treat tokens and GPS traces as sensitive.
- Do not log tokens.
- Avoid logging raw GPS traces.
- Define deletion of tokens, activities, streams, sync history, and proposals.
- Keep first implementation private and single-user.

## Local Development Setup

First implementation should document:

- Python version.
- Virtual environment setup.
- Environment variable setup.
- SQLite database path.
- Local segment dataset path.
- How Android points to the local backend for testing.

Do not add dependencies until implementation starts.

## First Implementation Milestone

Milestone objective: prove B2 can authenticate with Strava, sync a small number
of runs or rides, produce conservative proposal payloads against the current
segment dataset, and let Android review them later.

First milestone excludes:

- multi-user support;
- production deployment;
- automatic completion;
- Play Store release;
- offline map changes.

## Open Questions

- First deployment target.
- Token encryption mechanism for SQLite.
- Raw GPS stream retention policy.
- Exact dataset version string and checksum source.
- Confidence scoring thresholds.
- Android authentication to B2 during local testing.
