<#
.SYNOPSIS
    Runs the OtoWall live desktop daemon with local playback and Retro CRT TV style.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host "Starting OtoWall Retro CRT Daemon..." -ForegroundColor Cyan
& $Python -m otowall run --source local --style ascii_crt --poll-interval 1.0 @args
