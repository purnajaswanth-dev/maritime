# Where Is My Ferry? — Operational Runbook

**System:** Where Is My Ferry? (Iroise Sea Maritime Transit & ML ETA Predictor)  
**Classification:** Tier-1 Maritime Operations & Passenger Service  
**Operating Environment:** Production / Hybrid Cloud / On-Premise Ports  

---

## 1. System Overview & Architecture Topology

```
+-------------------------------------------------------------------------------+
|                             CLIENT / BROWSER TIER                             |
|  - Progressive Web App (PWA, Service Worker offline fallback)                 |
|  - React 19 + TypeScript + Vite 6 (Port 5173 / Port 80)                       |
|  - Leaflet Map + SSE Real-time Streaming + WCAG 2.1 AA Design Tokens          |
+-------------------------------------------------------------------------------+
                                      |
                     REST / SSE (Bearer JWT, X-Correlation-Id)
                                      v
+-------------------------------------------------------------------------------+
|                            SPRING BOOT 3.4.3 BACKEND                          |
|  - Port 8080                                                                  |
|  - OWASP Security Headers (HSTS, CSP, X-Frame-Options DENY, nosniff)           |
|  - Role-Based Access Control (PASSENGER, CAPTAIN, DISPATCHER, ADMIN, AUDITOR) |
|  - Append-Only Audit Logging & System Configuration / Maintenance Mode        |
|  - PostgreSQL 16 Persistence / Flyway DB Migrations                           |
|  - Actuator Health & Metrics (/actuator/health, /actuator/metrics)           |
+-------------------------------------------------------------------------------+
                                      |
                Internal HTTP Loopback (127.0.0.1:8000, 3s Timeout)
                                      v
+-------------------------------------------------------------------------------+
|                       PYTHON FASTAPI ML & SIMULATION ENGINE                   |
|  - Port 8000 (Loopback only)                                                  |
|  - LightGBM Gradient Boosted Regressor (MAE 5.20 min, MedAE 3.56 min)         |
|  - Monte Carlo Uncertainty Envelope & Residual Error Calibrations             |
|  - 22 Deterministic Scenario Injectors & Historical Replay Engine             |
|  - SHA-256 Model Integrity Verification Checksum                              |
+-------------------------------------------------------------------------------+
```

---

## 2. Standard Startup & Shutdown Procedures

### 2.1 Single-Command Launch (Recommended for Local Dev & Testing)
Run the master PowerShell orchestrator from the workspace root:
```powershell
.\run_all.ps1
```
This script:
1. Validates and starts the Python ML daemon on `http://127.0.0.1:8000`.
2. Starts the Spring Boot backend on `http://localhost:8080` and waits for Actuator health check `UP`.
3. Starts Vite React frontend on `http://localhost:5173`.
4. Gracefully intercepts `Ctrl+C` to terminate all spawned child processes.

### 2.2 Docker Compose Deployment
To launch the complete containerized stack:
```bash
docker compose up -d --build
```
Verify container health:
```bash
docker compose ps
```

### 2.3 Graceful Shutdown
```powershell
# If using run_all.ps1, simply press Ctrl+C in the terminal.
# To cleanly terminate any orphaned background processes:
Get-Process -Name "java" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*src.simulation.daemon*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

---

## 3. Disaster Recovery & Incident Playbooks

### Playbook 3.1: Python Simulation Daemon Crash / Abrupt Termination
- **Symptoms:**
  - Actuator `/actuator/health` reports status `DOWN` with detail: `"status": "UNAVAILABLE"`.
  - Frontend displays `OFFLINE_FALLBACK` or `STALE_DATA` banner.
  - Live vessel movement halts on the passenger map.
- **Root Cause Identification:**
  - Check Python daemon logs or check if process was terminated (OOM, unhandled exception).
- **Remediation Steps:**
  1. Execute chaos test verification script to diagnose process status:
     ```powershell
     powershell -ExecutionPolicy Bypass -File scripts/chaos_engine_kill.ps1
     ```
  2. If running standalone, restart the daemon:
     ```powershell
     cd ml-platform
     .\.venv\Scripts\python.exe -m src.simulation.daemon
     ```
  3. Verify reconnection via `http://localhost:8080/actuator/health`. Spring Boot automatically polls and restores live telemetry within 1 cycle without data loss or reversal.

### Playbook 3.2: AIS Blackout / Stale Telemetry
- **Symptoms:**
  - Vessel tracking indicates `STALE_DATA` state.
  - Uncertainty cone widens to indicate unconfirmed vessel dead reckoning.
- **Remediation Steps:**
  1. Log in to the Admin Portal (`/admin`) using administrative credentials (`admin` / `123`).
  2. Navigate to **Simulation Controls** -> **Scenarios**.
  3. If Scenario #21 (*AIS Transponder Blackout*) was injected, trigger **Resume / Normal Speed (1x)**.
  4. Ensure dispatcher issues passenger broadcast notification via Dispatcher Console.

### Playbook 3.3: Database Outage & Recovery
- **Symptoms:**
  - Backend returns HTTP 500 on booking creation or user authentication.
- **Remediation Steps:**
  1. Check PostgreSQL container status:
     ```bash
     docker compose ps postgres
     ```
  2. Restart PostgreSQL:
     ```bash
     docker compose restart postgres
     ```
  3. Validate database connection:
     ```bash
     docker compose exec postgres pg_isready -U ferry_user -d where_is_my_ferry
     ```
  4. Spring Boot JPA connection pool will re-establish automatically.

---

## 4. Security Incident Response

### Playbook 4.1: Activating Emergency Maintenance Mode
When performing emergency patching or mitigating high-severity vulnerabilities:
1. Log in as an administrator.
2. In the Admin Portal, open the **Audit Trail & Security** tab.
3. Toggle **Maintenance Mode** to `ENABLED`.
4. **Behavior:**
   - All public booking creation endpoints immediately reject passenger transactions with `HTTP 503 Service Unavailable` (`ProblemDetail` standard RFC 7807).
   - Administrative and auditor access remains fully operational for investigation.
   - Public timetable and map viewing remain available in read-only mode.

### Playbook 4.2: Audit Trail Forensics
- Audit logs are **strictly append-only**. Mutations or deletes throw `UnsupportedOperationException`.
- To inspect audit entries:
  ```http
  GET /api/v1/admin/audit-logs?page=0&size=50
  Authorization: Bearer <ADMIN_OR_AUDITOR_JWT>
  ```
- All log lines include `correlationId` traceable across backend logs (`X-Correlation-Id`).

---

## 5. Performance & Load Verification

### Running k6 Load Tests
A pre-configured load test script is available in `scripts/load_test.js`:
```bash
k6 run scripts/load_test.js
```
- **SLA Requirements:**
  - 200 concurrent Virtual Users (VUs).
  - p95 latency under 200ms for timetable and catalog queries.
  - Less than 1% error rate during sustained traffic bursts.

---

## 6. Default Demo Credentials & Roles

| Role | Username | Password | Permitted Capabilities |
| :--- | :--- | :--- | :--- |
| **PASSENGER** | `passenger` | `123` | Bookings, Ticket QR passes, Cancellation (≥24h), Live tracking |
| **DISPATCHER** | `dispatcher` | `123` | Delay advisories, sailing status updates, timetable alerts |
| **CAPTAIN** | `captain` | `123` | Departure & arrival confirmation, vessel status |
| **AUDITOR** | `auditor` | `123` | Read-only governance, security audit logs, compliance reports |
| **ADMIN** | `admin` | `123` | Full access, simulation controls, user roles, maintenance lock |
