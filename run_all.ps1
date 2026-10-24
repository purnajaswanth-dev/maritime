# ==============================================================================
# run_all.ps1
# Master Single-Command Launcher for "Where Is My Ferry?"
# Launches Python ML Daemon (8000), Spring Boot Backend (8080), and Vite UI (5173)
# ==============================================================================
$ErrorActionPreference = "Stop"

$RootDir = $PSScriptRoot
$MlDir = Join-Path $RootDir "ml-platform"
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "        WHERE IS MY FERRY? - FULL-STACK PRODUCTION LAUNCHER       " -ForegroundColor Cyan
Write-Host "   Iroise Sea Maritime Network (Brest - Molene - Ouessant)        " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Resolve Python Interpreter
$PythonExe = Join-Path $MlDir ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

# 2. Health check helper
function Wait-For-Port {
    param([string]$Url, [int]$TimeoutSec = 40, [string]$ServiceName)
    Write-Host "Waiting for $ServiceName at $Url..." -NoNewline
    $start = Get-Date
    while (((Get-Date) - $start).TotalSeconds -lt $TimeoutSec) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400) {
                Write-Host " [ONLINE]" -ForegroundColor Green
                return $true
            }
        } catch {}
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
    Write-Host " [TIMEOUT]" -ForegroundColor Red
    return $false
}

$processes = @()

try {
    # --------------------------------------------------------------------------
    # Step 1: Launch Python Simulation & ML Daemon (Port 8000)
    # --------------------------------------------------------------------------
    Write-Host "`n[1/3] Starting Maritime Simulation Engine & ML Daemon on port 8000..." -ForegroundColor Yellow
    $mlProc = Start-Process -FilePath $PythonExe -ArgumentList "-m", "src.simulation.daemon" -WorkingDirectory $MlDir -PassThru
    $processes += $mlProc
    Write-Host "      ML Engine Process ID: $($mlProc.Id)"

    if (-not (Wait-For-Port -Url "http://127.0.0.1:8000/health" -TimeoutSec 20 -ServiceName "ML Daemon")) {
        throw "Failed to start ML Daemon on port 8000"
    }

    # --------------------------------------------------------------------------
    # Step 2: Launch Spring Boot Backend (Port 8080)
    # --------------------------------------------------------------------------
    Write-Host "`n[2/3] Starting Spring Boot 3 Java Backend on port 8080..." -ForegroundColor Yellow
    $mvnCmd = if ($IsWindows -or $env:OS -like "*Windows*") { "mvn.cmd" } else { "mvn" }
    $backendProc = Start-Process -FilePath $mvnCmd -ArgumentList "spring-boot:run" -WorkingDirectory $BackendDir -PassThru
    $processes += $backendProc
    Write-Host "      Backend Process ID: $($backendProc.Id)"

    if (-not (Wait-For-Port -Url "http://localhost:8080/actuator/health" -TimeoutSec 60 -ServiceName "Spring Boot Backend")) {
        throw "Failed to start Spring Boot Backend on port 8080"
    }

    # --------------------------------------------------------------------------
    # Step 3: Launch Vite React Frontend (Port 5173)
    # --------------------------------------------------------------------------
    Write-Host "`n[3/3] Starting Vite React Frontend on port 5173..." -ForegroundColor Yellow
    $npmCmd = if ($IsWindows -or $env:OS -like "*Windows*") { "npm.cmd" } else { "npm" }
    $frontendProc = Start-Process -FilePath $npmCmd -ArgumentList "run", "dev" -WorkingDirectory $FrontendDir -PassThru
    $processes += $frontendProc
    Write-Host "      Frontend Process ID: $($frontendProc.Id)"

    if (-not (Wait-For-Port -Url "http://localhost:5173" -TimeoutSec 25 -ServiceName "Frontend UI")) {
        throw "Failed to start Frontend on port 5173"
    }

    # --------------------------------------------------------------------------
    # Ready Banner
    # --------------------------------------------------------------------------
    Write-Host "`n==================================================================" -ForegroundColor Green
    Write-Host " ALL SYSTEMS OPERATIONAL - WHERE IS MY FERRY IS READY!           " -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Green
    Write-Host " - Passenger Portal & Live Map : http://localhost:5173"
    Write-Host " - Backend API & Actuator      : http://localhost:8080/actuator/health"
    Write-Host " - ML Simulation Engine        : http://127.0.0.1:8000/health"
    Write-Host "`n Demo Accounts:"
    Write-Host "   * Passenger   : passenger / 123"
    Write-Host "   * Dispatcher  : dispatcher / 123"
    Write-Host "   * Captain     : captain / 123"
    Write-Host "   * Admin       : admin / 123"
    Write-Host "   * Auditor     : auditor / 123"
    Write-Host "`nPress Ctrl+C to terminate all services gracefully." -ForegroundColor Yellow
    Write-Host "==================================================================" -ForegroundColor Green

    # Keep script alive until Ctrl+C
    while ($true) {
        Start-Sleep -Seconds 2
        # Check if any process terminated unexpectedly
        foreach ($proc in $processes) {
            if ($proc.HasExited) {
                Write-Warning "Process $($proc.Id) terminated unexpectedly with exit code $($proc.ExitCode)."
                exit 1
            }
        }
    }

} finally {
    Write-Host "`nShutting down Where Is My Ferry services..." -ForegroundColor Yellow
    foreach ($proc in $processes) {
        if ($proc -and -not $proc.HasExited) {
            Write-Host "Stopping process PID $($proc.Id)..."
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "All processes cleanly stopped." -ForegroundColor Green
}
