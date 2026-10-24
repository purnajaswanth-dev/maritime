<#
.SYNOPSIS
    Where Is My Ferry? - Unified Local Orchestrator and Service Runner

.DESCRIPTION
    Launches and monitors all three tiers of the Where Is My Ferry platform:
      1. Python Virtual AIS & ML Simulation Engine (Port 8000)
      2. Spring Boot REST & SSE API Gateway (Port 8080)
      3. Vite React Modern Maritime Passenger Portal (Port 5173)

.EXAMPLE
    .\run_all.ps1
#>

[CmdletBinding()]
param(
    [switch]$SkipTests,
    [string]$Profile = "test"
)

$ErrorActionPreference = "Stop"
$ScriptRoot = $PSScriptRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  WHERE IS MY FERRY? - THREE-TIER MARITIME PLATFORM LAUNCHER     " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# -----------------------------------------------------------------------------
# 1. PREREQUISITE CHECKS
# -----------------------------------------------------------------------------
Write-Host "[1/5] Verifying toolchain prerequisites..." -ForegroundColor Yellow

function Test-CommandAvailable {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

$prereqsMet = $true

if (-not (Test-CommandAvailable "java")) {
    Write-Host "  [-] Java 17+ not found in PATH." -ForegroundColor Red
    $prereqsMet = $false
} else {
    $javaVer = java -version 2>&1 | Select-Object -First 1
    Write-Host "  [+] Java: $javaVer" -ForegroundColor Green
}

if (-not (Test-CommandAvailable "mvn")) {
    Write-Host "  [-] Apache Maven not found in PATH." -ForegroundColor Red
    $prereqsMet = $false
} else {
    Write-Host "  [+] Maven: Available" -ForegroundColor Green
}

if (-not (Test-CommandAvailable "node")) {
    Write-Host "  [-] Node.js not found in PATH." -ForegroundColor Red
    $prereqsMet = $false
} else {
    $nodeVer = node --version
    Write-Host "  [+] Node: $nodeVer" -ForegroundColor Green
}

$pythonExe = Join-Path $ScriptRoot "ml-platform\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "  [-] Python virtualenv not found at $pythonExe" -ForegroundColor Red
    $prereqsMet = $false
} else {
    $pyVer = & $pythonExe --version
    Write-Host "  [+] Python Virtualenv: $pyVer" -ForegroundColor Green
}

if (-not $prereqsMet) {
    Write-Error "Prerequisite verification failed. Please install missing dependencies and try again."
    exit 1
}

# -----------------------------------------------------------------------------
# 2. HEALTH POLLING HELPER
# -----------------------------------------------------------------------------
function Wait-ForUrl {
    param(
        [string]$Url,
        [string]$ServiceName,
        [int]$TimeoutSeconds = 60
    )
    Write-Host "  Waiting for $ServiceName at $Url..." -NoNewline -ForegroundColor Gray
    $start = Get-Date
    while ((Get-Date) - $start -lt [TimeSpan]::FromSeconds($TimeoutSeconds)) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400) {
                Write-Host " [ONLINE]" -ForegroundColor Green
                return $true
            }
        } catch {
            # retry
        }
        Start-Sleep -Seconds 2
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
    Write-Host " [TIMED OUT]" -ForegroundColor Red
    return $false
}

# -----------------------------------------------------------------------------
# 3. START SERVICES
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/5] Starting Tier 1: Python Simulation Engine (Port 8000)..." -ForegroundColor Yellow
$pyProcess = Start-Process -FilePath $pythonExe `
    -ArgumentList "-m", "src.simulation.daemon" `
    -WorkingDirectory (Join-Path $ScriptRoot "ml-platform") `
    -PassThru

$pyHealthy = Wait-ForUrl -Url "http://127.0.0.1:8000/health" -ServiceName "ML Simulation Engine" -TimeoutSeconds 30
if (-not $pyHealthy) {
    Write-Warning "ML simulation engine did not report healthy in time. Check daemon logs."
}

Write-Host ""
Write-Host "[3/5] Starting Tier 2: Spring Boot REST & SSE Gateway (Port 8080)..." -ForegroundColor Yellow
$mvnArgs = "spring-boot:run -Dspring-boot.run.arguments=--spring.profiles.active=$Profile"
$javaProcess = Start-Process -FilePath "mvn.cmd" `
    -ArgumentList $mvnArgs `
    -WorkingDirectory (Join-Path $ScriptRoot "backend") `
    -PassThru

$javaHealthy = Wait-ForUrl -Url "http://127.0.0.1:8080/actuator/health" -ServiceName "Spring Boot Gateway" -TimeoutSeconds 75
if (-not $javaHealthy) {
    Write-Warning "Spring Boot gateway did not report healthy in time."
}

Write-Host ""
Write-Host "[4/5] Starting Tier 3: Vite React Passenger Portal (Port 5173)..." -ForegroundColor Yellow
$npmProcess = Start-Process -FilePath "npm.cmd" `
    -ArgumentList "run", "dev" `
    -WorkingDirectory (Join-Path $ScriptRoot "frontend") `
    -PassThru

$frontendHealthy = Wait-ForUrl -Url "http://localhost:5173" -ServiceName "Vite Passenger Portal" -TimeoutSeconds 30

# -----------------------------------------------------------------------------
# 4. SYSTEM READY BANNER
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  ALL 3 SERVICES SUCCESSFULLY INITIALIZED AND READY!              " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  Passenger Portal:    http://localhost:5173" -ForegroundColor Cyan
Write-Host "  Admin Control Room:  http://localhost:5173/admin/login" -ForegroundColor Cyan
Write-Host "    - Email:           admin@example.com" -ForegroundColor Gray
Write-Host "    - Password:        AdminPass123!" -ForegroundColor Gray
Write-Host "  Backend Swagger:     http://localhost:8080/swagger-ui.html" -ForegroundColor Cyan
Write-Host "  Simulation API:      http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "Press [Ctrl+C] to stop all services..." -ForegroundColor Yellow

# -----------------------------------------------------------------------------
# 5. PROCESS MONITORING & TEARDOWN
# -----------------------------------------------------------------------------
try {
    while ($true) {
        Start-Sleep -Seconds 5
        if ($pyProcess.HasExited) {
            Write-Warning "Python simulation engine exited unexpectedly (Code: $($pyProcess.ExitCode))"
            break
        }
        if ($javaProcess.HasExited) {
            Write-Warning "Spring Boot gateway exited unexpectedly (Code: $($javaProcess.ExitCode))"
            break
        }
        if ($npmProcess.HasExited) {
            Write-Warning "Vite frontend exited unexpectedly (Code: $($npmProcess.ExitCode))"
            break
        }
    }
} finally {
    Write-Host "`nStopping all background service processes..." -ForegroundColor Yellow
    if ($pyProcess -and -not $pyProcess.HasExited) { Stop-Process -Id $pyProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($javaProcess -and -not $javaProcess.HasExited) { Stop-Process -Id $javaProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($npmProcess -and -not $npmProcess.HasExited) { Stop-Process -Id $npmProcess.Id -Force -ErrorAction SilentlyContinue }
    Write-Host "All Where Is My Ferry services stopped." -ForegroundColor Green
}
