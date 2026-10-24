# Spring Boot & Python Maritime Engine Architecture (Zero Mock Data Mandate)

**Project:** Where Is My Ferry?  
**Phase:** 09 — System Architecture Blueprint (Corrective Architecture Review)  
**Auditor:** Senior Backend Architect & Distributed Systems Specialist  
**Date:** 2026-10-16  
**Status:** Approved Architectural Baseline (Corrected)  

---

## 1. System Architecture Overview

The system architecture partitions concerns cleanly between presentation (React), API gateway/broadcasting (Spring Boot), and mathematical simulation/inference (Python). It enforces a strict **Zero Mock Data Policy**: all operational data displayed on client views originates from the running Python simulation and ML engine, relayed honestly through Spring Boot.

```mermaid
graph TB
    subgraph Client ["Client Presentation Tier (Browser - Port 5173)"]
        UI["React 19 + Vite Frontend"]
        MapComp["FleetMap (Leaflet 1.9.4)<br/>No-Key Carto/OSM/Vector Fallback"]
        PanelComp["VesselDetailPanel<br/>(Live Ticking Countdown & Provenance)"]
    end

    subgraph BackendGateway ["Application Gateway Tier (Java 17 / Spring Boot 3.4 - Port 8080)"]
        BootApp["Spring Boot Application"]
        RestController["Vessel & Simulation REST Controllers"]
        SseService["SSE Emitter Service<br/>(/api/v1/stream/vessels)"]
        PyClient["Python Engine HTTP Client<br/>(RestClient / WebClient)"]
        LocalCache["In-Memory Vessel State Cache<br/>(ConcurrentHashMap)"]
        HealthProbe["Actuator Health & Python Liveness Probe"]
    end

    subgraph PythonEngine ["Maritime Simulation & ML Tier (Python 3.13 - Port 8000 Loopback)"]
        PyDaemon["Internal FastAPI / Uvicorn Daemon<br/>(127.0.0.1:8000)"]
        FleetRunner["VirtualFleetRunner<br/>(Clock & Scenario Controller)"]
        AISGen["VirtualAISGenerator<br/>(4 Vessels, Kinematics)"]
        StreamProc["ETAStreamProcessor<br/>(Causal Feature Derivation)"]
        RidgeModel["VectorizedRidgeETAModel<br/>(Loads Frozen Weights)"]
        StateMachine["ETAStateMachine<br/>(6-State Lifecycle Guard)"]
        FrozenWeights["Frozen Model Weights Artifact<br/>(vectorized_ridge_model.json)"]
    end

    UI -->|REST /api/v1/*| RestController
    MapComp -->|SSE Events /stream/vessels| SseService
    PanelComp -->|SSE Events /stream/vessels| SseService
    
    RestController --> LocalCache
    SseService --> LocalCache
    HealthProbe --> PyClient
    
    PyClient -->|Loopback HTTP /internal/v1/*| PyDaemon
    PyClient --> LocalCache
    
    PyDaemon --> FleetRunner
    FleetRunner --> AISGen
    AISGen -->|Raw AIS Pings| StreamProc
    StreamProc -->|Features| RidgeModel
    RidgeModel -->|Raw Predictions| StateMachine
    RidgeModel -.->|Loads on boot (<1ms)| FrozenWeights
```

---

## 2. Toolchain Verification & Compatibility Decision

A direct host toolchain inspection was executed and confirmed:
- **Java Runtime & SDK:** OpenJDK 64-Bit Server VM (Temurin 17.0.16+8), verified at `c:\Users\sunka\.antigravity\extensions\tools\java\17.0.16.8-hotspot\bin\java.exe`. Java 17 is fully compatible with Spring Boot 3.4.x.
- **Build Tool:** Apache Maven 3.9.15, verified at `c:\Users\sunka\.antigravity\extensions\tools\maven\3.9.15\bin\mvn.cmd`.
- **Spring Boot Target:** Spring Boot 3.4.x (Java 17 baseline, Spring Framework 6.2, embedded Tomcat 10.1).
- **Python Runtime:** Python 3.13.6, verified with NumPy, Pandas, and PyArrow.
- **Frontend Toolchain:** Node.js v20.18.0, React 19, Vite 8, running on local port `5173`.
- **Development Ports:**
  - Frontend: `http://localhost:5173`
  - Spring Boot Backend: `http://localhost:8080`
  - Python Internal Daemon: `http://127.0.0.1:8000` (loopback only)
- **Cross-Origin & Proxy Configuration:**
  - Vite dev proxy configured in `vite.config.ts`:
    ```typescript
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8080',
          changeOrigin: true
        }
      }
    }
    ```
  - Spring Boot `WebMvcConfigurer` allows CORS for `http://localhost:5173`.

---

## 3. Division of Component Responsibilities

### A. Spring Boot Backend Responsibilities
1. **Public API Gateway:** Exposes uniform, versioned `/api/v1/*` endpoints to the frontend, decoupling web clients from Python internal details.
2. **Server-Sent Events (SSE) Broadcasting:** Manages client connections, fan-out event distribution, client heartbeats (`ping`), and reconnect tokens without taxing the Python engine.
3. **In-Memory Fleet Cache:** Maintains latest known snapshot of all 4 vessels in a thread-safe `ConcurrentHashMap`. Public REST queries hit cache immediately with sub-millisecond response latency.
4. **Resilience & Honest Error Reporting (Zero Mock Guarantee):**
   - If the Python daemon crashes or becomes unreachable, Spring Boot **does not** return canned mock success payloads.
   - Returns structured RFC 7807 **HTTP 503 Service Unavailable** for REST calls.
   - Emits an `event: system_status` over SSE alerting clients that the simulation is offline.
   - Retains the last valid vessel coordinates with an explicit `is_stale: true` flag and exact `telemetry_age_seconds`.
5. **Actuator Health Integration:** Implements a custom `HealthIndicator` (`PythonSimulationHealthIndicator`) that continuously verifies loopback communication with Python port 8000.

### B. Python Maritime Platform Responsibilities
1. **Kinematic Telemetry Simulation:** Advances vessels along geo-waypoint corridors with realistic speed variance, course calculation, and terminal berth detection.
2. **Scenario Fault Injection:** Injects adverse tidal currents, AIS transponder blackouts, speed drops, and harbor holding patterns.
3. **Causal Feature Derivation:** Formulates exact 16-dimensional feature vectors strictly using information available at simulation time.
4. **Machine Learning Inference:** Evaluates `VectorizedRidgeETAModel` using frozen weights loaded at startup.
5. **ETA Lifecycle State Transitions:** Enforces state rules (`SCHEDULED` &rarr; `IN_TRANSIT` &rarr; `APPROACHING` &rarr; `ARRIVED` / `STALE`).

### C. Client Presentation Responsibilities
1. **No-Key Map Visualization:** Renders vessel markers, course heading angles, speed badges, and route corridors over Carto/OSM base tiles or local offline vector polygons.
2. **Authoritative Countdown Ticking:** Ticks seconds downward between SSE prediction events based on authoritative `predicted_arrival_utc`.
3. **Stale Data Disclosure:** Displays clear amber warning banners and update timestamps when telemetry is older than 60 seconds.
4. **Honest Outage State:** Displays clear `Service Offline / Reconnecting` states when Spring Boot or Python is down; never substitutes hardcoded mock data.

---

## 4. Model Lifecycle & Weight Loading Architecture

Following the resolution of Correction A:
1. **Offline Frozen Weights:** Model weights $\mathbf{W}$, standardization parameters $(\boldsymbol{\mu}, \boldsymbol{\sigma})$, and corridor/vessel one-hot indices are stored in a frozen artifact: `ml-platform/models/vectorized_ridge_model.json`.
2. **Instantaneous Startup (<1ms):** `ETAStreamProcessor` reads the JSON weights file on startup via standard JSON parsing. This eliminates the historical 1.5–3.0 second startup overhead of reading and re-training on 9,313 snapshot rows from disk.
3. **Zero Parquet Dependency in Daemon:** The runtime daemon does not require `phase_05_prediction_snapshots.parquet` to be present, preventing accidental runtime data leakage or training corruption.

---

## 5. Security & Deployment Topology

- **Network Binding:**
  - Python Maritime Engine: Binds strictly to `127.0.0.1:8000` (loopback only). Never bound to `0.0.0.0` or exposed externally.
  - Spring Boot: Binds to `0.0.0.0:8080` with CORS restricted to `http://localhost:5173`.
- **Actuator & Diagnostics Protection:**
  - Spring Boot Actuator endpoints (`/actuator/health`, `/actuator/metrics`) enabled locally for integration verification.
  - Simulation control endpoints (`/api/v1/simulation/*`) validated and restricted to localhost development.

---

## 6. Objective 2 Finalization: Python HTTP Framework Selection (ADR-BACKEND-01)

### A. Architectural Decision Record: ADR-BACKEND-01
- **Title:** Selection of Internal Python HTTP Framework for Virtual Maritime Engine
- **Status:** **APPROVED (RECOMMENDED)**
- **Scope:** Defines the networking framework used to expose internal simulation state and ML inference to Spring Boot.

### B. Comparative Evaluation Matrix

| Evaluation Dimension | Candidate 1: FastAPI with Uvicorn | Candidate 2: Standard Library `http.server` | Analysis & Decision Impact |
|---|---|---|---|
| **Dependency Footprint** | Moderate: Adds `fastapi`, `uvicorn`, `starlette`, `pydantic` (~8 transitive packages) to `pyproject.toml`. | **Zero:** Included in standard Python 3.13 library. No dependencies added. | While `http.server` has zero dependencies, FastAPI's dependencies are industry-standard, lightweight wheels totaling $<12\text{ MB}$. |
| **Implementation Complexity** | **Very Low:** Declarative routing (`@app.get`, `@app.post`), automatic Pydantic model serialization, typed query/path params. | High: Manual URI parsing, regex routing, manual `Content-Length` stream reading (`self.rfile.read`). | Hand-rolling routing and JSON handling in `http.server` creates hundreds of lines of fragile boilerplate. |
| **Request Validation** | **Automatic & Strict:** Pydantic models reject invalid inputs with structured HTTP 422 errors detailing field and reason. | Manual & Fragile: Every endpoint must manually assert types, keys, and boundary conditions. | Hand-rolled validation introduces defects when Spring Boot passes simulation parameters (speed multiplier, scenario IDs). |
| **Error Handling & Standards** | **Robust:** Native support for RFC 7807 problem details, standardized status codes, exception handlers. | Manual: Uncaught exceptions produce plain-text stack traces or broken socket connections. | Spring Boot's `RestClient` requires consistent JSON error structures to trigger appropriate fallback states. |
| **Concurrency & Performance** | **High Throughput:** Native asynchronous event loop (ASGI) handles concurrent status polling and SSE dispatch in $<2\text{ ms}$. | Low / Threaded: Requires `ThreadingHTTPServer`; synchronous thread-per-request model risks socket contention on Windows. | Uvicorn's event loop handles 1000+ req/sec on localhost with negligible CPU overhead. |
| **Maintainability & Tooling** | **Superior:** Auto-generated interactive OpenAPI docs (`/docs` Swagger UI) enables direct curl/browser testing during backend development. | Poor: No schema documentation; API contracts must be manually verified. | OpenAPI documentation dramatically accelerates Spring Boot DTO generation and debugging. |

### C. Selected Decision: FastAPI with Uvicorn
We select **FastAPI with Uvicorn** for the following project-specific reasons:
1. **Pydantic Type Symmetry with Spring Boot DTOs:** FastAPI uses Pydantic schemas that map 1:1 with Spring Boot's Java records/DTOs (`FleetSnapshotResponse`, `SimulationControlRequest`). This ensures strict contract verification at compile and run time.
2. **Automated Error Boundaries:** Malformed control actions or out-of-range simulation speeds (e.g. `speed_multiplier: -5.0`) are rejected immediately with HTTP 422, preventing invalid state from corrupting the virtual fleet kinematics.
3. **OpenAPI Interactive Documentation:** Uvicorn automatically provides Swagger UI at `http://127.0.0.1:8000/docs`, allowing engineers to inspect live simulation status, test scenario triggers, and verify responses independently of Spring Boot.

### D. Rejected Alternative: Standard Library `http.server`
Python's `http.server` was rejected because the maintenance overhead of hand-crafting JSON body readers, query-parameter parsers, route dispatchers, and thread-pool wrappers introduces unacceptable defect risk at the inter-service boundary. Avoiding an external package does not justify maintaining custom HTTP server boilerplate.

### E. Proposed Internal Loopback Endpoints (`http://127.0.0.1:8000/internal/v1/*`)
- **Health & Diagnostics:**
  - `GET /internal/v1/health` &rarr; Checks process uptime, model load status, and frozen weight checksum.
  - `GET /internal/v1/status` &rarr; Returns simulation clock, step rate, active scenario ID, and total event count.
- **Fleet & Inference:**
  - `GET /internal/v1/fleet/snapshot` &rarr; Returns current telemetry, coordinates, and ETA states for all 4 vessels.
  - `GET /internal/v1/vessels/{vessel_id}/eta` &rarr; Returns deep prediction provenance and state-machine transitions.
- **Simulation Management:**
  - `POST /internal/v1/simulation/control` &rarr; Accepts `{"action": "pause" | "resume" | "speed" | "reset", "speed_multiplier": float}`.
  - `POST /internal/v1/simulation/scenarios/{scenario_id}` &rarr; Activates scenarios 1 through 4.
