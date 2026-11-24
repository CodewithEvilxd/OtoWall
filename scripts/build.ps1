<#
.SYNOPSIS
    Builds the standalone Windows executable using PyInstaller.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Set-Location $ProjectRoot

$PyInstaller = Join-Path $ProjectRoot ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $PyInstaller)) {
    $PyInstaller = "pyinstaller"
}

Write-Host "Building Windows Executable via PyInstaller..." -ForegroundColor Cyan
& $PyInstaller --noconfirm "$ProjectRoot\scripts\packaging\otowall-windows.spec" @args

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild succeeded! Executable located at: dist\OtoWall-windows.exe" -ForegroundColor Green
}
