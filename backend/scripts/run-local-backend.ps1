param(
    [string]$HostName = "0.0.0.0",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$BackendRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $BackendRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Push-Location $BackendRoot
try {
    if (-not (Test-Path ".env")) {
        Write-Host "backend/.env not found. Create it from .env.example before real Strava OAuth:"
        Write-Host "Copy-Item .env.example .env"
        Write-Host "Then set TOKEN_ENCRYPTION_KEY, STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET and STRAVA_REDIRECT_URI."
        Write-Host ""
    }

    Write-Host "Starting Mapping Paris Strava B2 backend on http://$HostName`:$Port"
    Write-Host "For Android emulator, use http://10.0.2.2:$Port in the app."
    Write-Host "For a physical phone, use the PC LAN IP and the same Wi-Fi."
    & $Python -m uvicorn app.main:app --host $HostName --port $Port --reload
} finally {
    Pop-Location
}
