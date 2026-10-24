# Where Is My Ferry? — ML Platform & Simulation Engine

This directory contains the Python ML platform, feature pipelines, frozen Ridge ETA model inference engine, and the virtual maritime simulation daemon.

## Requirements & Environment

- Python >= 3.11
- Virtual environment at `.venv/` (already configured in `ml-platform/.venv`)

## Running the Simulation Daemon

The Python service must bind to `127.0.0.1:8000` (internal loopback only) and expose health, status, fleet snapshot, and ETA inference endpoints for the Spring Boot backend.

### Option A: From root directory
```powershell
.\run_simulation.ps1
```

### Option B: From ml-platform directory
```powershell
cd ml-platform
.\run_daemon.ps1
```

### Option C: Direct module invocation
```powershell
cd ml-platform
.\.venv\Scripts\python -m src.simulation.daemon
```

### Option D: Direct Uvicorn invocation
```powershell
cd ml-platform
.\.venv\Scripts\uvicorn src.simulation.daemon:app --host 127.0.0.1 --port 8000
```

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/internal/v1/health` | GET | Health check returning status `healthy` and model readiness |
| `/internal/v1/status` | GET | Simulation status (scenario, step, simulation time, tick rate) |
| `/internal/v1/fleet/snapshot` | GET | Current live positions, speeds, courses, and ETAs for all 4 vessels |
| `/internal/v1/predict/eta` | POST | Frozen Ridge ETA prediction from vessel telemetry features |
| `/internal/v1/control/reset` | POST | Reset the maritime simulation |

## Running ML Tests

From `ml-platform/`:
```powershell
.\.venv\Scripts\python -m pytest tests -v
```
