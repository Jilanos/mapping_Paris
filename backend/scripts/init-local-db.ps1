param(
    [string]$Source = "..\app\src\main\assets\paris_segments.geojson"
)

$ErrorActionPreference = "Stop"

$BackendRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $BackendRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Push-Location $BackendRoot
try {
    Write-Host "Ingesting segment dataset from $Source"
    & $Python -m app.tools.ingest_segments --source $Source
    Write-Host ""
    Write-Host "When the backend is running, verify dataset status with:"
    Write-Host "Invoke-RestMethod http://127.0.0.1:8000/segments/status"
} finally {
    Pop-Location
}
