param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$backendRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$dbBase = Join-Path $backendRoot "mapping_paris_strava_b2.db"
$targets = @(
    $dbBase,
    "$dbBase-shm",
    "$dbBase-wal"
)

Write-Host "This deletes only the local Strava B2 SQLite database files:"
$targets | ForEach-Object { Write-Host " - $_" }
Write-Host "It does not touch backend/.env, source code, Android app data, or segment datasets."
Write-Host "Deleting this DB removes local Strava tokens, synced activities, streams, proposals, and job history."

if (-not $Force) {
    Write-Host ""
    Write-Host "Re-run with -Force to confirm:"
    Write-Host ".\scripts\reset-local-db.ps1 -Force"
    exit 1
}

foreach ($target in $targets) {
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Force
        Write-Host "Deleted $target"
    }
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Run .\scripts\init-local-db.ps1"
Write-Host "2. Restart the backend"
Write-Host "3. Reconnect Strava if OAuth tokens were deleted"
