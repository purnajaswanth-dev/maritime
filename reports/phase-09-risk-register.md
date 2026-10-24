# Phase 09 Risk Register & Mitigation Strategy (Zero Mock Data Mandate)

**Project:** Where Is My Ferry?  
**Phase:** 09 — Architecture & Integration Risk Assessment (Corrective Architecture Review)  
**Auditor:** Senior Security Architect, ML Reliability Engineer, QA Lead  
**Date:** 2026-10-16  
**Status:** Approved Architectural Baseline (Corrected)  

---

## 1. Risk Matrix Overview

| Risk ID | Category | Risk Description | Likelihood | Impact | Severity | Primary Mitigation Strategy |
|---|---|---|---|---|---|---|
| **RSK-01** | ML Model | Historical reports reference `phase_05_ridge_model.joblib`, but the file does not exist on disk. Runtime fitting incurs startup latency and dataset dependency. | **High** | **Medium** | **MEDIUM** | Export pre-trained model weights $\mathbf{W}$ to frozen artifact `ml-platform/models/vectorized_ridge_weights.npz`. Daemon loads frozen weights at startup ($<1\text{ms}$), eliminating dataset dependency. |
| **RSK-02** | Geospatial | Public tile servers (Carto/OSM) may throttle requests or experience network dropouts under sustained use. | **Medium** | **High** | **HIGH** | Implement the 3-tier fallback state machine: Carto Voyager &rarr; OSM Standard &rarr; Local GeoJSON vector coastline polygon. Guarantees zero user API key requirement and 100% offline resilience. |
| **RSK-03** | Systems | Windows port contention or orphan background daemon processes on port 8000 or 8080. | **Medium** | **Medium** | **MEDIUM** | Provide unified `start-dev.ps1` and `stop-dev.ps1` scripts with explicit PID tracking, process killing, and port conflict validation. |
| **RSK-04** | Streaming / UX | Stale telemetry or countdown desynchronization during network pause or transponder dropout. | **Low** | **Medium** | **LOW** | Enforce authoritative stale-ETA policy: countdown ticks against target arrival UTC; if telemetry $>60\text{s}$, UI prominently displays amber `STALE TELEMETRY` banner and last update timestamp; arrival latched only by berth proximity. |
| **RSK-05** | ML Evaluation | Expectation that live virtual simulation will achieve identical MAE (5.12m) to historical retrospective evaluation. | **Medium** | **Low** | **LOW** | Strictly separate Track A (integration plumbing correctness) from Track B (historical offline accuracy benchmarking). Transparently document that synthetic data tests integration, not real maritime accuracy. |
| **RSK-06** | Data Integrity | Accidental retention of hardcoded mock vessel arrays or silent fallbacks in operational frontend components concealing backend failures. | **Medium** | **High** | **HIGH** | Enforce Zero Mock Operational Data acceptance gate (Gate Z). Isolate test fixtures to test-only paths; operational components display explicit HTTP 503 error states rather than mock data. |
| **RSK-07** | Performance | Leaflet marker DOM updates during continuous 1 Hz simulation stream causing memory creep or UI stutter. | **Low** | **Medium** | **LOW** | Update marker coordinates directly via `marker.setLatLng()` without re-mounting or un-mounting Leaflet map instances. |

---

## 2. Detailed Risk Analysis & Mitigation Actions

### RSK-01: Model Artifact Discrepancy, Lifecycle & Voyage Leakage Resolution
- **Analysis:** `ml-platform/src/streaming/eta_stream_processor.py` previously fit `VectorizedRidgeETAModel` in memory on startup by reading `phase_05_prediction_snapshots.parquet`. This required bundling the 5.2 MB training dataset, created a 1.5s cold start delay, and used `prediction_timestamp_utc` instead of `dep_timestamp_utc`, introducing potential voyage-boundary leakage.
- **Mitigation Decision:** Transition to **Option 2: Offline Frozen JSON Model Artifact**. Weights $\mathbf{W} \in \mathbb{R}^{16}$, mean/std scaling vectors, and categorical indices are stored in `ml-platform/models/vectorized_ridge_model.json`. Fitted strictly on the 681 voyages departing prior to `2016-02-01T00:00:00Z` (zero voyage-level overlap with test set). Loaded in $<1\text{ms}$ on daemon boot with SHA-256 integrity validation.

### RSK-02: Map Tile Reliability Without User API Keys
- **Analysis:** Commercial providers (Mapbox, Google) require private tokens and payment methods. Requiring an end-user to configure a key violates Critical Requirement A.
- **Mitigation Decision:**
  1. Primary: Carto Voyager raster tiles (no key, high contrast).
  2. Secondary: OSM Standard (automatic failover upon 6 consecutive tile errors within 5.0s).
  3. Tertiary: Local bundled GeoJSON vector coastline polygon (`frontend/src/data/iroiseCoastline.json`). Renders landmass and vessel markers with zero internet connectivity.

### RSK-04: Authoritative Stale-ETA & Arrival Semantics
- **Analysis:** Unclear whether countdown ticks or freezes when telemetry pauses, and whether a countdown reaching zero marks arrival.
- **Mitigation Decision:**
  1. The ticking countdown is a presentation calculation measuring time remaining to `predicted_arrival_utc`. It continues ticking.
  2. If telemetry age $>60\text{s}$, the UI displays an amber `STALE TELEMETRY (>60s)` warning and the exact last received timestamp.
  3. Reaching $00\text{m }00\text{s}$ does NOT mark arrival. Arrival is exclusively latched when the state machine detects the vessel inside the destination berth radius ($<250\text{m}$) with speed $<1.0\text{ kts}$.

### RSK-06: Zero Mock Operational Data Enforcement
- **Analysis:** If Spring Boot or Python goes offline, frontend developers might be tempted to leave mock fallback arrays in `TrackingPage` or `HomePage` to prevent UI errors. This conceals outages and presents fabricated data as live.
- **Mitigation Decision:**
  1. All operational mock arrays are removed from production components and relocated to `frontend/src/__tests__/fixtures/`.
  2. Spring Boot returns RFC 7807 HTTP 503 upon dependency outage; operational frontend pages display explicit `Service Unavailable / Reconnecting` banners.
  3. Acceptance Gate Z establishes 12 automated checks enforcing zero mock data.

---

## 3. Status of Key Architectural Decisions

1. **Python HTTP Framework Choice: RESOLVED (ADR-BACKEND-01)**
   - *Selected:* **FastAPI with Uvicorn** on loopback `127.0.0.1:8000`.
   - *Rationale:* Eliminates manual HTTP/JSON boilerplate, provides automated Pydantic schema validation matching Spring Boot DTOs, returns RFC 7807/HTTP 422 error details, and exposes OpenAPI `/docs` for local integration testing.
2. **Frozen Model Artifact Format: RESOLVED (ADR-ETA-02)**
   - *Selected:* `ml-platform/models/vectorized_ridge_model.json`.
   - *Rationale:* Versioned, human-readable, schema-validatable JSON avoiding pickle/joblib vulnerabilities; loads in $<1\text{ms}$; verified mathematically equivalent to in-memory model within $\epsilon \le 10^{-6}\text{ min}$.
3. **Spring Boot Java Baseline: CONFIRMED**
   - Host has Java OpenJDK 17.0.16 installed. Spring Boot 3.4.x targets Java 17 baseline, fully supported by Apache Maven 3.9.15. No JDK upgrade required.
