# Checks whether the TriPlan backend is working correctly.
#
#   .\check.ps1                 check the server on http://127.0.0.1:8000
#   .\check.ps1 -Url http://127.0.0.1:8061
#   .\check.ps1 -Offline       skip the live server checks
#
# Exit code 0 means healthy, 1 means something is wrong.

param(
    [string]$Url = "http://127.0.0.1:8000",
    [switch]$Offline
)

$ErrorActionPreference = "Stop"
$backendRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $backendRoot

$python = Join-Path $backendRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "The virtual environment is missing." -ForegroundColor Red
    Write-Host "Create it with:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Yellow
    Write-Host "  .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

if ($Offline) {
    & $python "scripts\check_backend.py" --no-server
} else {
    & $python "scripts\check_backend.py" $Url
}

exit $LASTEXITCODE
