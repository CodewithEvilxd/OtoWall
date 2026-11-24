<#
.SYNOPSIS
    Runs the full pytest test suite with proper Python path.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

$Pytest = Join-Path $ProjectRoot ".venv\Scripts\pytest.exe"
if (-not (Test-Path $Pytest)) {
    $Pytest = "pytest"
}

Write-Host "Running OtoWall Test Suite..." -ForegroundColor Cyan
& $Pytest -q @args
