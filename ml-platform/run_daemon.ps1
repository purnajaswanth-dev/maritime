# PowerShell script to start the Python Virtual Maritime Simulation & Inference Daemon
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

if (Test-Path ".\.venv\Scripts\python.exe") {
    $PythonExe = ".\.venv\Scripts\python.exe"
} else {
    $PythonExe = "python"
}

Write-Host "Starting Where Is My Ferry? Python Simulation & Inference Daemon on http://127.0.0.1:8000..." -ForegroundColor Cyan
& $PythonExe -m src.simulation.daemon
