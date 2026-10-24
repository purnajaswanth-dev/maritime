# PowerShell launcher for Where Is My Ferry? Python Simulation & Inference Daemon
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$MlDir = Join-Path $ScriptDir "ml-platform"

if (-not (Test-Path $MlDir)) {
    Write-Error "ml-platform directory not found at $MlDir"
    exit 1
}

Set-Location $MlDir

$PythonExe = Join-Path $MlDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " Starting Where Is My Ferry? Virtual Maritime Simulation Daemon  " -ForegroundColor Cyan
Write-Host " Address: http://127.0.0.1:8000 (Internal Loopback Only)          " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

& $PythonExe -m src.simulation.daemon
