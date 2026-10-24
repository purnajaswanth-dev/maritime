# Phase 09 Implementation Roadmap & Acceptance Gates (Zero Mock Data Mandate)

**Project:** Where Is My Ferry?  
**Phase:** 09 — Staged Implementation Blueprint (Corrective Architecture Review)  
**Auditor:** Senior Program Architect, Backend Lead, QA Automation Specialist  
**Date:** 2026-10-16  
**Status:** Approved Architectural Baseline (Corrected)  

---

## 1. Staged Implementation Architecture

The planned implementation is organized into **9 discrete, sequential stages** with rigorous acceptance gates. No subsequent stage may commence until the preceding gate has been verified with reproducible evidence.

```
Stage A ──► Stage B ──► Stage C ──► Stage D ──► Stage E ──► Stage F ──► Stage G ──► Stage H ──► Stage Z
Contracts   Python      Spring      Frontend    SSE         Map         Decoupled   System      ZERO MOCK
& Schemas   HTTP Daemon Boot App    REST        Streaming   No-Key      Verification Hardening  OPERATIONAL
                        Gateway     Client      Updates     Reliability Tests       & Memory    DATA GATE
```

---

## 2. Detailed Stage Specifications

### Stage A — Contracts, Frozen Weights & Schema Formalization
- **Objective:** Finalize shared data transfer schemas between Python, Spring Boot, and React TypeScript interfaces. Export offline frozen weights artifact for `VectorizedRidgeETAModel` using strictly voyage-grouped historical split.
- **Prerequisites:** Approval of Corrected Phase 09 Architecture Plan.
- **Files Impacted:**
  - `ml-platform/models/vectorized_ridge_model.json` (New offline pre-trained frozen model JSON artifact with SHA-256 checksum)
  - `ml-platform/src/models/export_ridge_artifact.py` (Export utility script)
  - `ml-platform/src/streaming/event_schema.py`
  - `frontend/src/types/ferry.ts`
  - `ml-platform/configs/phase_07_streaming_event_contract.yaml`
- **Scope Exclusions:** No backend coding; no runtime retraining.
- **Verification Tests:** TypeScript schema compilation, Python artifact loading unit test, numerical equivalence test ($|y_{\text{frozen}} - y_{\text{in-memory}}| \le 10^{-6}$), dimension and SHA-256 checksum validation.
- **Acceptance Gate A:** Schema compatibility verified across all 3 tiers with zero type mismatches; frozen JSON artifact validates with test MAE $\approx 5.12\text{ min}$ on Protocol 1 test partition with zero voyage-level leakage.

---

### Stage B — Python Maritime HTTP Daemon (FastAPI & Uvicorn on Loopback)
- **Objective:** Equip the Python maritime engine with an internal loopback HTTP interface powered by FastAPI and Uvicorn, exposing endpoints for fleet snapshots, simulation controls, and scenario triggers. Loads frozen weights at startup.
- **Prerequisites:** Gate A passed.
- **Files Impacted:**
  - `ml-platform/pyproject.toml` (Add `fastapi` and `uvicorn`)
  - `ml-platform/requirements-lock.txt` (Locked dependencies)
  - `ml-platform/src/simulation/daemon.py` (FastAPI app running on loopback `127.0.0.1:8000`)
- **Scope Exclusions:** No external AIS feeds; loopback only; no runtime fitting on startup.
- **Verification Tests:** `pytest ml-platform/tests/test_api_server.py`, HTTP status 200 on `/internal/v1/health`, `/internal/v1/status` and `/internal/v1/fleet/snapshot`, automated OpenAPI `/docs` inspection.
- **Acceptance Gate B:** Python FastAPI daemon responds to loopback queries in $<5\text{ ms}$ and executes `VectorizedRidgeETAModel.predict()` from frozen weights in $<1\text{ ms}$.

---

### Stage C — Spring Boot Foundation & Application Gateway
- **Objective:** Bootstrap the Spring Boot 3.4.x backend in `backend/` using Java 17 and Maven, configuring `RestClient`, fleet in-memory cache, Actuator health probes, and RFC 7807 problem details.
- **Prerequisites:** Gate B passed.
- **Files Impacted:**
  - `backend/pom.xml`
  - `backend/src/main/java/com/whereismyferry/...` (Application, Controllers, Services, DTOs)
  - `backend/src/main/resources/application.yml`
- **Scope Exclusions:** No canned mock data generation; no SQL database setup (in-memory prototype cache only); no real payment gateways.
- **Verification Tests:** `mvn clean test`, Spring Boot actuator `/actuator/health` returns `UP` when Python daemon is running, and returns `DOWN` (503) when Python daemon is stopped.
- **Acceptance Gate C:** Spring Boot compiles cleanly, starts on port `8080`, and proxies Python fleet status without generating any fabricated mock records.

---

### Stage D — Frontend REST Integration & Mock Data Decommissioning
- **Objective:** Connect the React frontend to Spring Boot REST endpoints (`/api/v1/vessels`, `/api/v1/simulation/status`). Remove hardcoded operational mock arrays from production components (`TrackingPage`, `HomePage`, `OperatorDashboardPage`, `AdminDiagnosticsPage`).
- **Prerequisites:** Gate C passed.
- **Files Impacted:**
  - `frontend/src/services/vesselApi.ts` (Typed API client)
  - `frontend/src/pages/tracking/TrackingPage.tsx`
  - `frontend/src/pages/public/HomePage.tsx`
  - `frontend/src/pages/operator/OperatorDashboardPage.tsx`
  - `frontend/src/pages/admin/AdminDiagnosticsPage.tsx`
  - `frontend/src/data/mockVessels.ts` (Isolated strictly to test fixtures directory: `frontend/src/__tests__/fixtures/`)
- **Strict Requirement:** No silent mock fallbacks. If the backend is unreachable, operational pages must render clear error/reconnecting banners (`"Service Unavailable — Telemetry Engine Offline"`), never fallback mock arrays.
- **Verification Tests:** Vitest integration tests, browser validation verifying live vessel list loaded from backend; fault test verifying explicit error display when backend is stopped.
- **Acceptance Gate D:** Frontend renders live fleet data fetched from `http://localhost:8080/api/v1/vessels`; zero obsolete mock data imported in production components.

---

### Stage E — Server-Sent Events (SSE) Live Telemetry Streaming
- **Objective:** Implement real-time pushing of synthetic AIS updates and ETA predictions from Spring Boot to the browser over SSE.
- **Prerequisites:** Gate D passed.
- **Files Impacted:**
  - `backend/src/main/java/com/whereismyferry/service/SseBroadcastService.java`
  - `frontend/src/services/sseClient.ts`
  - `frontend/src/pages/tracking/TrackingPage.tsx`
- **Scope Exclusions:** No external WebSockets or third-party cloud push services.
- **Verification Tests:** Browser subagent monitoring SSE event reception, automatic reconnect upon disconnect, heartbeat reception every 15s.
- **Acceptance Gate E:** Map markers and ETA countdowns update dynamically in the browser as virtual vessels advance, with zero full-page re-renders.

---

### Stage F — Map Reliability & No-Key Fallback Validation
- **Objective:** Implement the 3-tier tile fallback in `FleetMap.tsx` (Carto Voyager &rarr; OSM Standard &rarr; Local GeoJSON Vector Coastline).
- **Prerequisites:** Gate E passed.
- **Files Impacted:**
  - `frontend/src/components/tracking/FleetMap.tsx`
  - `frontend/src/data/iroiseCoastline.json` (Local offline vector polygon)
- **Scope Exclusions:** No paid map APIs (Mapbox/Stadia); zero user API key prompts.
- **Verification Tests:** Vitest tile error threshold simulation, browser validation with network throttling and blocked CDN domains, offline test in airplane mode.
- **Acceptance Gate F:** Map functions cleanly on fresh clone with zero API keys; renders local coastline vector fallback when external tiles are blocked; markers and polylines remain interactive.

---

### Stage G — Decoupled Prediction Verification Execution (Track A & Track B)
- **Objective:** Execute all 10 verification tests from the ETA Verification Plan, rigorously separating Track A (integration plumbing correctness) from Track B (historical predictive accuracy).
- **Prerequisites:** Gate F passed.
- **Verification Tests:** All 10 tests documented in `phase-09-eta-integration-verification-plan.md` (INT-DET-01 through INT-DET-06, and EVAL-HIST-01 through EVAL-HIST-04).
- **Acceptance Gate G:** Verified audit evidence that predicted arrival timestamps originate from `VectorizedRidgeETAModel` inference; ticking countdown does not modify inference timestamp; stale telemetry triggers clear amber warning.

---

### Stage H — Final System Hardening & Memory Synchronization
- **Objective:** Final regression test run, bundle size verification, memory leak audit, and update of project memory.
- **Prerequisites:** Gate G passed.
- **Verification Commands:** `npm test`, `npm run lint`, `npm run build`, `mvn test`, `pytest ml-platform/tests`.
- **Acceptance Gate H:** Full test suite passes across all tiers; documentation finalized; all lint and build checks clean.

---

## 3. Mandatory Acceptance Gate Z: Zero Mock Operational Data

The integrated application cannot be accepted into Phase 10 or declared complete until the following **12 binary conditions** are verified:

- [ ] **Z-01:** All operational vessel records (coordinates, SOG, COG, status) originate exclusively from the running Python simulation engine through Spring Boot.
- [ ] **Z-02:** All operational ETA values and arrival estimates originate from `VectorizedRidgeETAModel` inference or the state-machine clamp.
- [ ] **Z-03:** No production frontend component imports hardcoded mock vessel arrays or static operational JSON fixtures.
- [ ] **Z-04:** No backend endpoint fabricates canned successful operational responses when Python or an internal dependency is unavailable.
- [ ] **Z-05:** If Spring Boot or Python is offline, the UI renders an honest service-unavailable or reconnecting state; no silent substitution occurs.
- [ ] **Z-06:** Dashboard operational figures (active vessels, transits in progress, on-time rate) derive dynamically from integrated state or are explicitly labeled as static editorial content.
- [ ] **Z-07:** Simulation controls (speed, pause, scenarios) measurably affect the running simulation state and live vessel telemetry.
- [ ] **Z-08:** The tracking map displays the correct integrated vessel positions matching backend payloads.
- [ ] **Z-09:** Prediction timestamps, model name, and weight checksums are observable in the UI provenance drawer.
- [ ] **Z-10:** Stale telemetry ($>60\text{s}$) displays an amber stale badge and last valid timestamp without claiming fresh inference.
- [ ] **Z-11:** Test fixtures remain strictly isolated in test directories and do not leak into the production bundle.
- [ ] **Z-12:** The map requires zero user API keys and successfully falls back to local vector polygons when offline.
