# Mapping Paris Strava B2 Backend

This folder contains the initial FastAPI skeleton for the Strava B2 backend.

B2 will eventually handle Strava OAuth, token storage, activity synchronization,
GPS stream ingestion, segment matching, and proposal APIs for the Android app.
This first skeleton only exposes a health endpoint. Strava OAuth, database
storage, activity sync, stream download, and matching are not implemented yet.

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
- `STRAVA_SYNC_DOWNLOAD_STREAMS`, default `true`
- `STRAVA_SYNC_SPORT_TYPES`, default `Run,Ride`
- `STRAVA_TOKEN_REFRESH_MARGIN_SECONDS`, default `300`

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

These routes prepare the Strava connection and encrypted token storage only.
Real segment matching, proposal generation, and Android integration are not
implemented yet.

## Strava sync routes

Implemented routes:

- `POST /sync/strava`
- `GET /sync/status`
- `GET /sync/runs`

`POST /sync/strava` runs one synchronous sync pass. There is no background
worker, scheduler, Celery, Redis, or cron in this milestone.

Current sync behavior:

- loads the encrypted stored Strava token;
- refreshes the token when expired or close to expiry;
- fetches recent activities from Strava;
- keeps `Run` and `Ride` by default;
- ignores unsupported sport types such as `Walk`;
- downloads `latlng`, `distance`, and `time` streams for eligible activities;
- stores sync runs and sync errors;
- never returns raw tokens, refresh tokens, client secrets, or encryption keys.

Activity sync and stream download are implemented as a backend foundation only.
Segment dataset ingestion, GPS-to-segment matching, proposal storage, proposal
APIs, and Android review are still future tasks.

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
