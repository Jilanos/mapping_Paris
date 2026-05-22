# Mapping Paris Strava B2 Backend

This folder contains the FastAPI prototype for the Strava B2 backend.

B2 handles Strava OAuth foundations, encrypted token storage, activity
synchronization, GPS stream ingestion, segment dataset ingestion, segment
matching, and proposal APIs for the Android app.

The Android app remains responsible for reviewing and confirming proposed
segments. The backend must not automatically mark segments as completed.

## Local setup on Windows PowerShell

From the `backend/` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks script execution for the current session, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Configuration

Configuration is centralized in `app/core/config.py` and loaded from
environment variables. Local `.env` files are also supported for development,
but they must never be committed.

Available variables:

- `APP_NAME`, default `mapping-paris-strava-b2`
- `APP_VERSION`, default `0.1.0`
- `ENV`, default `local`
- `LOG_LEVEL`, default `INFO`
- `API_BASE_URL`, optional
- `STRAVA_CLIENT_ID`, optional and empty by default
- `STRAVA_CLIENT_SECRET`, optional and empty by default
- `STRAVA_REDIRECT_URI`, optional and empty by default
- `STRAVA_SCOPES`, default `read,activity:read_all`
- `STRAVA_AUTHORIZE_URL`, default `https://www.strava.com/oauth/authorize`
- `STRAVA_TOKEN_URL`, default `https://www.strava.com/oauth/token`
- `AUTH_STATE_TTL_SECONDS`, default `600`
- `TOKEN_ENCRYPTION_KEY`, optional and empty by default
- `DATABASE_URL`, default `sqlite:///./mapping_paris_strava_b2.db`
- `STRAVA_SYNC_PER_PAGE`, default `30`
- `STRAVA_SYNC_MAX_PAGES`, default `1`
- `STRAVA_SYNC_LOAD_MORE_MAX_PAGES`, default `5`
- `STRAVA_SYNC_ABSOLUTE_MAX_PAGES`, default `10`
- `STRAVA_SYNC_DOWNLOAD_STREAMS`, default `true`
- `STRAVA_SYNC_SPORT_TYPES`, default `Run,Ride`
- `STRAVA_TOKEN_REFRESH_MARGIN_SECONDS`, default `300`
- `SEGMENT_DATASET_PATH`, default `../app/src/main/assets/paris_segments.geojson`
- `SEGMENT_DATASET_VERSION`, optional
- `MATCH_MAX_DISTANCE_METERS`, default `30`
- `MATCH_MIN_COVERAGE_RATIO`, default `0.35`
- `MATCH_MIN_MATCHED_POINTS`, default `2`
- `MATCH_MAX_ACTIVITIES_PER_RUN`, default `20`
- `MATCH_CANDIDATE_BBOX_BUFFER_METERS`, default `50`

To prepare local configuration later:

```powershell
Copy-Item .env.example .env
```

Do not commit a real `.env` file, real Strava credentials, access tokens, or
refresh tokens.

The backend does not require Strava configuration to start or serve `/health`.
OAuth routes fail with explicit configuration errors until the required Strava
variables are present.

## Database

The first persistence layer uses SQLite through SQLAlchemy. Tables are created
automatically on local application startup. The default database URL is:

```text
sqlite:///./mapping_paris_strava_b2.db
```

Set `DATABASE_URL` in `.env` to use another local SQLite path.

Alembic migrations and PostgreSQL support are intentionally not part of this
milestone.

## Token encryption

Strava access and refresh tokens are encrypted before database storage with a
Fernet key loaded from `TOKEN_ENCRYPTION_KEY`.

Generate a local development key with:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Then place it in your untracked `.env`:

```text
TOKEN_ENCRYPTION_KEY=
```

If the key is missing, `/health` still works, but OAuth callback and refresh
token storage fail safely. The backend never stores raw tokens as a fallback.

## Strava OAuth routes

Implemented routes:

- `GET /auth/strava/start`
- `GET /auth/strava/callback`
- `POST /auth/strava/refresh`
- `GET /auth/strava/status`

These routes prepare the Strava connection and encrypted token storage.

## Strava sync routes

Implemented routes:

- `POST /sync/strava`
- `GET /sync/status`
- `GET /sync/runs`

`POST /sync/strava` runs one synchronous sync pass. There is no background
worker, scheduler, Celery, Redis, or cron in this milestone.

The default request body is empty and keeps the normal refresh behavior. For a
larger page scan, the route also accepts optional JSON:

```json
{
  "max_pages": 5,
  "per_page": 30
}
```

`max_pages` is clamped by `STRAVA_SYNC_ABSOLUTE_MAX_PAGES` and `per_page` is
clamped to `100`. The sync pass scans Strava pages from `1` to the requested
depth, skips eligible activities already stored with streams, downloads streams
for new eligible `Run`/`Ride` activities, and reports
`skipped_existing_activities` plus `pages_requested` in the response.

Current sync behavior:

- loads the encrypted stored Strava token;
- refreshes the token when expired or close to expiry;
- fetches recent activities from Strava;
- keeps `Run` and `Ride` by default;
- ignores unsupported sport types such as `Walk`;
- downloads `latlng`, `distance`, and `time` streams for eligible activities;
- stores sync runs and sync errors;
- never returns raw tokens, refresh tokens, client secrets, or encryption keys.

Activity sync and stream download are implemented as a backend foundation.

## Segment dataset ingestion

The backend can ingest the same Paris segment GeoJSON used by the Android app:

```text
../app/src/main/assets/paris_segments.geojson
```

Run ingestion from the `backend/` folder:

```powershell
.\.venv\Scripts\python.exe -m app.tools.ingest_segments --source ..\app\src\main\assets\paris_segments.geojson
```

The command:

- parses the GeoJSON FeatureCollection;
- preserves `id` and `logical_segment_id`;
- falls back to `id` when `logical_segment_id` is missing;
- stores geometry as JSON text;
- computes per-segment bounding boxes;
- computes a SHA-256 dataset hash;
- creates one active dataset version;
- does not duplicate an already-ingested dataset hash.

Read-only segment routes:

- `GET /segments/status`
- `GET /segments/datasets`
- `GET /segments/search`

Search examples:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/segments/status"
Invoke-RestMethod "http://127.0.0.1:8000/segments/search?arrondissement=18&limit=20"
Invoke-RestMethod "http://127.0.0.1:8000/segments/search?street_name=Lepic"
```

`/segments/search` returns metadata and bounding boxes by default. It does not
return user progress, Strava tokens, or raw secrets. Full geometry is returned
only with `include_geometry=true`.

## Matching and proposal routes

Implemented routes:

- `POST /proposals/generate`
- `GET /proposals`
- `GET /proposals/status`
- `POST /proposals/{proposal_id}/dismiss`
- `POST /proposals/{proposal_id}/accept`

`POST /proposals/generate` runs synchronously against stored Strava streams and
the active segment dataset. It does not call Strava directly and it does not
write Android completion state.

The default request body is empty. After importing older activities, Android
uses an unprocessed-stream mode so proposal generation does not keep retrying
the same recent activities:

```json
{
  "only_unprocessed": true,
  "max_activities": 100
}
```

In this mode, streams whose activity already has proposals for the active
dataset are skipped. The response reports how many activities had streams, how
many already had proposals, how many were processed, and how many proposals were
created, updated, or skipped.

Matching assumptions:

- GPS stream points are compared with segment polylines using a lightweight
  local meter approximation.
- Candidate segments are reduced by bounding box intersection plus
  `MATCH_CANDIDATE_BBOX_BUFFER_METERS`.
- A proposal is created only when distance, coverage, and matched-point
  thresholds pass.
- Coverage is estimated from projected matched GPS points along the segment
  polyline.
- Confidence is deterministic:
  - 55% coverage component;
  - 35% distance component;
  - 10% matched-points component.

Proposal statuses are backend review states only:

- `proposed`
- `dismissed`
- `accepted`

`accepted` does not mean completed in Android. Android integration and final
manual confirmation remain future work.

## Run the server

```powershell
uvicorn app.main:app --reload
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "mapping-paris-strava-b2",
  "version": "0.1.0"
}
```

Auth status:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/auth/strava/status
```

## Run tests

From the repository root:

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests
```

Or from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

Tests mock Strava API calls. They do not call the real Strava API.

## Local E2E validation checklist

Use this checklist when validating the full local backend-to-Android flow. Real
Strava credentials must stay in the untracked `backend/.env` file.

Backend setup:

```powershell
cd backend
Copy-Item .env.example .env
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Then edit `.env` locally and set:

- `TOKEN_ENCRYPTION_KEY`
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REDIRECT_URI=http://127.0.0.1:8000/auth/strava/callback`

Initialize the local segment dataset:

```powershell
.\scripts\init-local-db.ps1
```

Start the backend:

```powershell
.\scripts\run-local-backend.ps1
```

In another PowerShell window, run non-secret status checks:

```powershell
.\scripts\e2e-check-local.ps1
```

Complete Strava OAuth manually:

```text
http://127.0.0.1:8000/auth/strava/start
```

Android setup:

- build and install the debug APK;
- open `Propositions Strava B2`;
- emulator backend URL: `http://10.0.2.2:8000`;
- physical phone backend URL: `http://PC_LAN_IP:8000`;
- physical phone and PC must be on the same Wi-Fi;
- Windows firewall may need to allow inbound access to port `8000`.

Manual E2E flow:

1. Start the backend.
2. Ingest the Paris segment dataset.
3. Complete Strava OAuth in the browser.
4. Trigger Strava sync from Android.
5. Generate proposals from Android.
6. Load proposals from Android.
7. Verify proposed segments appear in orange.
8. Accept or ignore a proposal.
9. Verify local Android completion statistics do not change.

Troubleshooting:

- Backend unreachable: check URL, Wi-Fi, firewall, and whether uvicorn is
  listening on `0.0.0.0` for physical-phone tests.
- Wrong redirect URI: make the Strava app callback match
  `STRAVA_REDIRECT_URI`.
- Missing encryption key: generate `TOKEN_ENCRYPTION_KEY` before OAuth callback.
- Missing scopes: keep `STRAVA_SCOPES=read,activity:read_all`.
- No activities: first sync only keeps `Run` and `Ride`.
- No streams: the Strava activity may not expose GPS streams.
- No proposals: ingest segments first, then sync streams, then generate
  proposals.
- Physical phone cannot reach `localhost`: use the PC LAN IP, not `localhost`.
