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

Configuration is loaded from environment variables.

Available variables:

- `APP_NAME`, default `mapping-paris-strava-b2`
- `APP_VERSION`, default `0.1.0`
- `ENV`, default `local`
- `STRAVA_CLIENT_ID`, optional and empty by default
- `STRAVA_CLIENT_SECRET`, optional and empty by default

Copy `.env.example` only for local reference if needed. Do not commit a real
`.env` file or real Strava credentials.

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

## Run tests

From the repository root:

```powershell
pytest backend/tests
```

Or from `backend/`:

```powershell
pytest tests
```
