# Where Is My Ferry? (Où est mon ferry ?)

[![CI / Tests](https://img.shields.io/badge/Tests-236%20Passed-brightgreen.svg)](#test-suite)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%20FastAPI-blue.svg)](file:///ml-platform)
[![Backend](https://img.shields.io/badge/Spring%20Boot-3.4.3%20%7C%20Java%2017-forestgreen.svg)](file:///backend)
[![Frontend](https://img.shields.io/badge/React-19%20%7C%20TypeScript-61dafb.svg)](file:///frontend)
[![A11y](https://img.shields.io/badge/WCAG-2.1%20AA%20Compliant-purple.svg)](#accessibility)
[![License](https://img.shields.io/badge/License-Proprietary-gray.svg)](#)

Real-time maritime transit tracking, passenger booking engine, and machine-learning powered ETA estimation platform serving the **Iroise Sea Ferry Network** in Finistère, Brittany, France.

Connecting mainland Brittany with the Ponant Islands:
- **Mainland Ports:** Brest, Le Conquet, Audierne, Camaret-sur-Mer
- **Islands:** Île de Molène, Île d'Ouessant (Port du Stiff), Île de Sein

---

## Architecture Overview

```
                                      +---------------------------------------------+
                                      |            Browser Client (PWA)             |
                                      | React 19 + TypeScript + Leaflet + Tailwind  |
                                      | Port: 5173 (Dev) / Port: 80 (Docker)        |
                                      +---------------------------------------------+
                                                             |
                                           REST API & Server-Sent Events (SSE)
                                           Bearer JWT Auth + X-Correlation-Id
                                                             v
+-------------------------------------------------------------------------------------------------------------------+
|                                            Spring Boot 3.4.3 Backend (Java 17)                                    |
|                                                      Port: 8080                                                   |
|-------------------------------------------------------------------------------------------------------------------|
|  * Security & RBAC: PASSENGER, DISPATCHER, CAPTAIN, AUDITOR, ADMIN                                                |
|  * OWASP Hardening: X-Frame-Options DENY, nosniff, HSTS, Referrer-Policy                                           |
|  * Booking Engine: Dynamic fare catalog, VAT breakdown, QR boarding pass generation, >=24h cancellation rule      |
|  * Audit Trail: Append-only immutable log (updates/deletions forbidden)                                           |
|  * System Configuration: Maintenance mode emergency lockdown & dynamic feature flags                              |
|  * Spring Actuator: /actuator/health (Custom SimulationDaemonHealthIndicator)                                    |
+-------------------------------------------------------------------------------------------------------------------+
                  |                                                                 |
   JDBC / Flyway  |                                           Internal HTTP         |
                  v                                           (127.0.0.1:8000)      v
+----------------------------------+                        +---------------------------------------------------+
|         PostgreSQL 16 DB         |                        |         Python 3.11 ML & Simulation Daemon        |
|            Port: 5432            |                        |                     Port: 8000                    |
|----------------------------------|                        |---------------------------------------------------|
| * Users & RBAC credentials       |                        | * Maritime Simulation Engine (22 scenarios)       |
| * Departures & Sailings catalog  |                        | * LightGBM Gradient Boosted ETA Regressor         |
| * Passenger Bookings & Tickets   |                        | * Monte Carlo Uncertainty Envelope [p10, p90]     |
| * Immutable Audit Records        |                        | * SHA-256 Model Integrity Verification Checksum   |
+----------------------------------+                        +---------------------------------------------------+
```

---

## Quick Start

### Option 1: Single-Command Native Orchestration (Windows / PowerShell)
Clone the repository and launch all tiers with health-checked auto-start:
```powershell
.\run_all.ps1
```
*Press `Ctrl+C` in the terminal to cleanly terminate all processes.*

### Option 2: Production Docker Deployment (Cloud / VPS)
```bash
# 1. Clone repository
git clone https://github.com/purnajaswanth-dev/maritime.git where-is-my-ferry
cd where-is-my-ferry

# 2. Configure environment (customize secrets if desired)
cp .env.example .env

# 3. Launch with automated deployment script (or docker compose up -d --build)
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```
*For detailed cloud provider instructions (AWS, DigitalOcean, Hetzner, GCP, Azure, SSL/HTTPS), see the [Production Deployment Guide](file:///docs/DEPLOYMENT_GUIDE.md).*

---

## Service URLs & Endpoints

| Service | Address | Description |
| :--- | :--- | :--- |
| **Passenger Web App** | `http://localhost:5173` | Interactive map, live departures, booking wizard, QR boarding pass |
| **Backend REST API** | `http://localhost:8080` | REST API, SSE endpoints, OpenAPI / Swagger |
| **Backend Health** | `http://localhost:8080/actuator/health` | Spring Boot Actuator health & component indicators |
| **ML Daemon Health** | `http://127.0.0.1:8000/health` | Loopback-only ML simulation daemon health |
| **Admin Portal** | `http://localhost:5173/admin` | Scenario triggers, speed multiplier, ML diagnostics, audit trail |

---

## Demo Credentials

All accounts use password: `123`

| Role | Username | Permissions |
| :--- | :--- | :--- |
| **Passenger** | `passenger` | Book tickets, view reservations, download QR boarding pass, cancel (≥24h) |
| **Dispatcher** | `dispatcher` | Post delay advisories, update sailing statuses, broadcast alerts |
| **Captain** | `captain` | Confirm departures, report vessel arrival, manage vessel state |
| **Auditor** | `auditor` | Read-only governance, security audit logs, compliance reports |
| **Admin** | `admin` | Full system control, 22 simulation scenarios, speed slider, maintenance lock |

---

## Verification & Test Suite

The system includes comprehensive automated testing across all architectural tiers:

```powershell
# Run the complete multi-tier test suite:
powershell -ExecutionPolicy Bypass -File scripts/run_all_tests.ps1
```

- **Python ML Tests:** 115 passing tests (`pytest`) covering physics, navigation, scenarios, Monte Carlo ETA, and integrity checksums.
- **Java Backend Tests:** 50 passing integration tests (`mvn test`) covering booking workflows, RBAC barriers, audit immutability, SSE streaming, and security hardening.
- **Frontend Vitest Tests:** 74 passing tests (`npm run test:run`) covering WCAG accessibility, booking wizard, admin governance, and PWA service worker registration.
- **Total:** **239 tests passing** with zero regressions.

---

## Resilience & Quality Hardening

- **Chaos Engineering:** `scripts/chaos_engine_kill.ps1` verifies instant detection of daemon death (`STALE_DATA` status / degraded health) and automatic recovery upon restart without state reversal.
- **Load Testing:** `scripts/load_test.js` (k6) targets 200 concurrent VUs with p95 latency under 200ms.
- **Accessibility:** Tested against WCAG 2.1 AA with high-contrast color palettes (≥4.5:1 ratio), screen-reader semantics, and reduced-motion compliance.
- **Offline / PWA:** Configured with `manifest.json`, theme color `#0F172A`, and a cache-first service worker providing offline navigation fallback.

---

## Documentation

- [Operational Runbook](file:///docs/RUNBOOK.md) — Incident response, disaster recovery playbooks, performance tuning.
- [Phase Reports](file:///docs/phases/) — Comprehensive documentation for each of the 13 build phases.
- [Data Audit](file:///docs/DATA_AUDIT.md) — GTFS schedule generation, geography, and AIS calibration details.
