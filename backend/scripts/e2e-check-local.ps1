param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

function Invoke-Check {
    param(
        [string]$Label,
        [string]$Path
    )

    try {
        $response = Invoke-RestMethod -Method Get -Uri "$BaseUrl$Path" -TimeoutSec 10
        Write-Host "OK   $Label"
        return $response
    } catch {
        Write-Host "FAIL $Label - $($_.Exception.Message)"
        return $null
    }
}

Write-Host "Checking Mapping Paris Strava B2 backend at $BaseUrl"
Write-Host "This check does not require Strava to be connected and does not print secrets."
Write-Host ""

$health = Invoke-Check "health" "/health"
$segments = Invoke-Check "segments status" "/segments/status"
$auth = Invoke-Check "Strava auth status" "/auth/strava/status"
$sync = Invoke-Check "sync status" "/sync/status"
$proposals = Invoke-Check "proposals status" "/proposals/status"

Write-Host ""
Write-Host "Summary"
if ($health) {
    Write-Host "Service: $($health.service) $($health.version), status $($health.status)"
}
if ($segments) {
    Write-Host "Segments loaded: $($segments.loaded), count $($segments.segment_count), active dataset $($segments.active_dataset_version_id)"
}
if ($auth) {
    Write-Host "Strava configured: $($auth.configured), connected: $($auth.connected)"
}
if ($sync) {
    Write-Host "Stored activities: $($sync.stored_activities), streams: $($sync.stored_streams)"
}
if ($proposals) {
    Write-Host "Proposals: proposed $($proposals.proposed_count), accepted $($proposals.accepted_count), dismissed $($proposals.dismissed_count)"
}
