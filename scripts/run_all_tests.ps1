# CI Test Runner Script: Where Is My Ferry?
# Executes all test suites across Python ML Platform, Spring Boot Backend, and React Frontend.
# Exits with non-zero status code on any failure.

param(
    [switch]$FailOnMissingTiers = $false
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Failed = $false
$TotalPassed = 0

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    WHERE IS MY FERRY? - COMPREHENSIVE TEST SUITE RUNNER  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Python ML Platform Tests
Write-Host "`n[1/3] Running Python ML Platform Tests..." -ForegroundColor Yellow
$PythonDir = Join-Path $RepoRoot "ml-platform"
$PythonExe = Join-Path $PythonDir ".venv\Scripts\python.exe"

if (Test-Path $PythonExe) {
    Push-Location $PythonDir
    try {
        & $PythonExe -m pytest tests/ -q
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Python ML tests FAILED with exit code $LASTEXITCODE" -ForegroundColor Red
            $Failed = $true
        } else {
            Write-Host "Python ML tests PASSED." -ForegroundColor Green
        }
    } catch {
        Write-Host "Error running pytest: $_" -ForegroundColor Red
        $Failed = $true
    } finally {
        Pop-Location
    }
} else {
    Write-Host "Python virtual environment not found at $PythonExe" -ForegroundColor Red
    $Failed = $true
}

# 2. Spring Boot Backend Tests
Write-Host "`n[2/3] Checking Spring Boot Backend Tests..." -ForegroundColor Yellow
$BackendDir = Join-Path $RepoRoot "backend"
if (Test-Path (Join-Path $BackendDir "pom.xml")) {
    Push-Location $BackendDir
    try {
        mvn test
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Java backend tests FAILED with exit code $LASTEXITCODE" -ForegroundColor Red
            $Failed = $true
        } else {
            Write-Host "Java backend tests PASSED." -ForegroundColor Green
        }
    } catch {
        Write-Host "Error running mvn test: $_" -ForegroundColor Red
        $Failed = $true
    } finally {
        Pop-Location
    }
} else {
    Write-Host "Backend directory or pom.xml not yet scaffolded (scheduled for Phase 3)." -ForegroundColor DarkYellow
    if ($FailOnMissingTiers) {
        $Failed = $true
    }
}

# 3. React Frontend Tests
Write-Host "`n[3/3] Checking React Frontend Tests..." -ForegroundColor Yellow
$FrontendDir = Join-Path $RepoRoot "frontend"
if (Test-Path (Join-Path $FrontendDir "package.json")) {
    Push-Location $FrontendDir
    try {
        npm test -- --run
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Frontend Vitest tests FAILED with exit code $LASTEXITCODE" -ForegroundColor Red
            $Failed = $true
        } else {
            Write-Host "Frontend Vitest tests PASSED." -ForegroundColor Green
        }
    } catch {
        Write-Host "Error running npm test: $_" -ForegroundColor Red
        $Failed = $true
    } finally {
        Pop-Location
    }
} else {
    Write-Host "Frontend directory or package.json not yet scaffolded (scheduled for Phase 6)." -ForegroundColor DarkYellow
    if ($FailOnMissingTiers) {
        $Failed = $true
    }
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
if ($Failed) {
    Write-Host "TEST RUN FAILED. One or more suites exited with an error." -ForegroundColor Red
    exit 1
} else {
    Write-Host "TEST RUN SUCCEEDED. All active suites passed." -ForegroundColor Green
    exit 0
}
