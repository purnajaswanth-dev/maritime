# Phase 12 Verification Report: Frontend Integration with Spring Boot

**Project:** Where Is My Ferry?  
**Phase:** Phase 12 — Frontend Integration with Spring Boot  
**Date:** 2026-10-16  
**Auditor / Integration Architect:** Senior Backend Architect, Geospatial Systems Engineer & QA Automation Lead  
**Status:** `COMPLETED AND VERIFIED (ALL CRITERIA PASSED; ZERO MOCK OPERATIONAL DATA ENFORCED)`

---

## 1. Executive Summary

Phase 12 integrates the React + TypeScript frontend with the primary Spring Boot backend (`http://localhost:8080`) and the upstream Python virtual maritime simulation service (`127.0.0.1:8000`).

In compliance with the Non-Negotiable Integration Mandates:
1. **Primary API Gateway:** Spring Boot serves as the frontend's single primary backend gateway. In development, the Vite server proxies `/api` requests directly to `http://localhost:8080`, configurable via `VITE_API_BASE_URL`.
2. **Zero Mock Operational Data:** All hardcoded operational vessel arrays, canned coordinates, fabricated speeds, and client-side coordinate jitter timers were audited and eliminated across `TrackingPage`, `HomePage`, `OperatorFleetPage`, `OperatorDashboardPage`, `JourneyDetailPage`, and Admin portals.
3. **Live Server-Sent Events (SSE):** Connected live tracking to `GET /api/v1/stream/vessels` with bounded exponential backoff (1.0s–15.0s with jitter), stale telemetry watchdog (>30s without update), and clean unmount lifecycle management.
4. **Authoritative Countdown & Arrival State Machine:** Client-side countdown arithmetic never overrides authoritative backend arrival timestamps; countdown reaching zero does NOT trigger arrival without backend lifecycle state confirmation (`ARRIVED`).
5. **3-Tier Map Fallback:** Retained the zero-user-API-key requirement across CartoDB Voyager (Tier 1), OpenStreetMap (Tier 2), and local GeoJSON vector polygon fallback (`iroiseCoastline.json`, Tier 3) with a 6-consecutive-tile-error degradation threshold.
6. **Simulation Controls:** Real Spring Boot endpoints (`/api/v1/simulation/controls` and `/api/v1/simulation/scenarios/{id}`) wired with actual returned state feedback. Optimistic success claims eliminated.

---

## 2. Architecture & Integration Topology

```
+-------------------------------------------------------------------------+
|                              BROWSER CLIENT                             |
|  - React 19 + TypeScript + Leaflet                                      |
|  - useVesselStream (SSE consumer: snapshot, telemetry_update, ping)    |
|  - FleetMap (3-tier tile fallback + GeoJSON vector canvas)              |
|  - VesselDetailPanel (Deep Ridge ETA provenance & weight SHA-256)        |
+-------------------------------------------------------------------------+
                                    │
                                    │ HTTP /api/* (Vite dev proxy / 5173)
                                    ▼
+-------------------------------------------------------------------------+
|                  PRIMARY BACKEND: SPRING BOOT (PORT 8080)               |
|  - VesselController: GET /api/v1/vessels, GET /api/v1/vessels/{id}/eta   |
|  - SimulationController: /status, /controls, /scenarios/{id}            |
|  - VesselStreamController: GET /api/v1/stream/vessels (SSE)             |
|  - GlobalExceptionHandler: RFC 7807 ProblemDetail (404, 422, 503)        |
+-------------------------------------------------------------------------+
                                    │
                                    │ Internal Loopback HTTP (127.0.0.1:8000)
                                    ▼
+-------------------------------------------------------------------------+
|                 ML PLATFORM: PYTHON FASTAPI DAEMON (PORT 8000)          |
|  - VectorizedRidgeETAModel (Frozen Ridge artifact v1.0, SHA-256 verified) |
|  - VirtualFleetRunner + ETAStreamProcessor (Track A synthetic kinematics)|
|  - Internal endpoints: /internal/v1/health, /status, /fleet/snapshot    |
+-------------------------------------------------------------------------+
```

---

## 3. Endpoints Integrated

| Frontend Method | Backend Endpoint | Request Type | Purpose & Mapping |
| :--- | :--- | :--- | :--- |
| `apiClient.getFleetSnapshot()` | `GET /api/v1/vessels` | REST JSON | Initial fleet population; returns `VesselDto[]` with real coordinates, SOG, COG, and ETA lifecycle states. |
| `apiClient.getVesselEta(vesselId)` | `GET /api/v1/vessels/{id}/eta` | REST JSON | Deep ETA provenance; returns model type, alpha, weight SHA-256, uncertainty bounds, and reason codes. |
| `apiClient.getSimulationStatus()` | `GET /api/v1/simulation/status` | REST JSON | Live simulation clock, speed multiplier, active scenario, and processed event counters. |
| `apiClient.postSimulationControl(req)` | `POST /api/v1/simulation/controls` | REST JSON | Lifecycle controls: `pause`, `resume`, `speed`, `reset`. |
| `apiClient.postSimulationScenario(id)` | `POST /api/v1/simulation/scenarios/{id}` | REST JSON | Activates scenario injection (e.g. `scenario-1`, `scenario-2` tidal current delay). |
| `useVesselStream()` | `GET /api/v1/stream/vessels` | SSE Stream | Real-time continuous stream of `snapshot`, `telemetry_update`, `system_status`, and `ping` events. |

---

## 4. Zero Mock Operational Data Audit & Remediation

| Screen / Component | Previous State (Defect) | Remediation Applied |
| :--- | :--- | :--- |
| `TrackingPage.tsx` | Used `mockVessels` with client-side coordinate jitter loop (`setInterval` modifying lat/lon/speed). | Removed `setInterval` and `mockVessels`. Subscribed to `useVesselStream()`. Shows real live vessel positions, honest offline/reconnecting banners, and stale indicators. |
| `HomePage.tsx` | Rendered static `mockVessels` in "Live Virtual Fleet Radar" section. | Replaced with `apiClient.getFleetSnapshot()`. Shows skeleton loading cards; displays honest "Operational Telemetry Offline" banner on 503 rather than fake vessels. |
| `OperatorFleetPage.tsx` | Rendered static `mockVessels` registry cards. | Replaced with `apiClient.getFleetSnapshot()`. Sourced live from Spring Boot; 503 or network failure displays honest offline state. |
| `OperatorDashboardPage.tsx` | Hardcoded active vessel count (`mockVessels.length`) and static vessel rows. | Replaced with `apiClient.getFleetSnapshot()`. Displays live vessel count, live speed, COG, and arrival predictions. |
| `JourneyDetailPage.tsx` | Displayed hardcoded vessel speed (`vessel.speedKnots`). | Added live fetch from `apiClient.getVesselEta(vesselId)`. Displays real live speed, ETA lifecycle state, and Ridge model provenance. |
| `AdminSimulationControlsPage.tsx` | Used mock local state variables (`isPaused`, `simSpeed`) and canned timeouts. | Connected to `useSimulationControls()` calling real Spring Boot endpoints. Optimistic claims eliminated. |
| `AdminDiagnosticsPage.tsx` | Displayed canned static log array. | Connected to live Spring Boot SSE stream (`/api/v1/stream/vessels`). Telemetry updates and heartbeats append in real-time. |
| `FleetMap.tsx` | Accepted only legacy mock vessel interface. | Upgraded to accept both `VesselDto` and `VirtualVessel`. Renders real coordinates with 3-tier fallback. |
| `VesselDetailPanel.tsx` | Displayed hardcoded ETA estimates. | Upgraded to fetch live ETA provenance (`/api/v1/vessels/{id}/eta`), displaying real Ridge weight SHA-256 and uncertainty bounds. |

### Remaining Mock Data Justification (Static Editorial Content)
- `mockDestinations`: Static editorial travel destination guides (Ouessant, Molène, Île de Sein). Approved static editorial content.
- `mockJourneys`: Schedule timetables and catalog fares for route search demonstration.
- `mockTerminals`: GeoJSON terminal harbor dock locations and berth facilities.
- Isolated test fixtures in `src/tests/*`: Allowed test fixtures verifying schema contracts.

---

## 5. Live SSE Stream Implementation & Error Handling

The `useVesselStream` hook (`frontend/src/hooks/useVesselStream.ts`) manages the streaming lifecycle:
- **Initial REST Snapshot:** Calls `apiClient.getFleetSnapshot()` immediately upon mount so vessels appear without waiting for the first SSE tick.
- **Event Listeners:**
  - `snapshot`: Updates full vessel array and sets authoritative last-update timestamp.
  - `telemetry_update`: Updates individual vessel kinematics and ETA predictions in-place.
  - `system_status`: Synchronizes simulation clock and run state.
  - `ping`: Resets stale-data watchdog timer.
- **Exponential Backoff with Jitter:**
  $$\text{Delay}_{n} = \min(15000, 1000 \times 1.5^{n}) \pm \text{jitter} \; (\pm 20\%)$$
- **Stale Data Watchdog:** If no heartbeat or telemetry update is received for $>30$ seconds, `isStale` transitions to `true` and reconnect is scheduled.
- **Arrival Latching:** Countdown reaching 0 computes remaining minutes as 0, but the vessel's lifecycle state remains strictly bound to backend authoritative state (`IN_TRANSIT` -> `APPROACHING` -> `ARRIVED`). A countdown reaching 0 never marks a vessel as arrived.
- **Cleanup:** `es.close()` and `clearTimeout(reconnectTimeout)` run on component unmount, preventing memory leaks or orphaned connections.

---

## 6. Map Reliability & 3-Tier Provider Fallback

1. **Tier 1 (CartoDB Voyager):**
   - High-contrast, clean maritime tiles: `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png`.
   - Requires zero user API keys. Proper CartoDB & OpenStreetMap attribution preserved.
2. **Tier 2 (OpenStreetMap Standard):**
   - Fallback tile provider: `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`.
   - Triggered when Tier 1 encounters 6 consecutive tile load errors within a 5.0-second sliding window.
3. **Tier 3 (Local GeoJSON Vector Basemap):**
   - Offline, network-independent vector fallback using `frontend/src/assets/iroiseCoastline.json`.
   - Renders coastline polygons directly into Leaflet `L.geoJSON` layer against a deep maritime navy background (`#071B2B`) with slate landmasses (`#E2E8F0`).
   - Real backend coordinates (`lat`, `lon`) are preserved and plotted without fabrication.

---

## 7. Test and Build Verification

### 1. Frontend Test Suite (`vitest run`)
- **Command:** `npm test -- --run` in `frontend/`
- **Result:** **7 test files passed, 27 tests passed, 0 failures in 213ms**.
  - `src/tests/apiClientAndStream.test.ts`: 8 passed
  - `src/tests/operationalUiAndMapFallback.test.ts`: 5 passed
  - `src/tests/bookingWorkflow.test.ts`: 3 passed
  - `src/tests/dataContract.test.ts`: 4 passed
  - `src/tests/designTokens.test.ts`: 2 passed
  - `src/tests/etaUncertaintyAndSimulation.test.ts`: 4 passed
  - `src/tests/sitemapRoutes.test.ts`: 1 passed

### 2. Frontend Production Build (`tsc -b && vite build`)
- **Command:** `npm run build` in `frontend/`
- **Result:** **Built in 486ms with 0 errors**. All 59 production chunks and CSS assets compiled cleanly.

### 3. Backend Java Test Suite (`mvn test`)
- **Command:** `mvn test` in `backend/`
- **Result:** **42 tests passed, 0 failures, 0 errors, 3 skipped** (LivePython integration tests skipped as expected in standalone unit test profile).

### 4. Python ML Platform Test Suite (`pytest tests -v`)
- **Command:** `.venv\Scripts\python -m pytest tests -v` in `ml-platform/`
- **Result:** **87 passed, 0 warnings in 85.57s (100% clean)**.

---

## 8. Live End-to-End Verification Evidence

During verification, the real Python simulation daemon and Spring Boot backend were executed concurrently:

1. **Python Simulation Daemon:**
   - Started at `http://127.0.0.1:8000`.
   - Loaded frozen model artifact: `VectorizedRidgeETAModel` (weight SHA-256: `e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9`).
2. **Spring Boot Backend Gateway:**
   - Started on port 8080 (`WhereIsMyFerryApplication`).
   - Connected to Python simulation daemon.
3. **Live Endpoint Responses (Real Executions):**
   - `GET /api/v1/simulation/status`: Returned HTTP 200 with `simulation_available: true`, `active_vessels_count: 4`, `speed_multiplier: 1.0`.
   - `GET /api/v1/vessels`: Returned HTTP 200 with 4 live simulated vessels (`V-FROMVEUR-SIM`, `V-AZENOR-SIM`, `V-OUESSANT-SIM`, `V-SEIN-SIM`), each with real coordinates, SOG, COG, and ETA lifecycle states (`ESTIMATING`).
   - `GET /api/v1/vessels/V-FROMVEUR-SIM/eta`: Returned HTTP 200 with Ridge model provenance, weight checksum `e4da4af...`, and uncertainty bounds [75.17m, 108.07m].
   - `POST /api/v1/simulation/controls`: Body `{"action":"pause"}` returned HTTP 200 (`{"status":"SUCCESS","is_paused":true}`); body `{"action":"resume"}` returned HTTP 200 (`{"status":"SUCCESS","is_paused":false}`).
   - `POST /api/v1/simulation/scenarios/scenario-1`: Returned HTTP 200 (`{"status":"APPLIED","scenario_id":"SCENARIO_01_NORMAL_VOYAGE"}`).
4. **Live Browser Verification (`http://localhost:5173/track`):**
   - Verified active connection badge: `LIVE SSE STREAM (1.0 Hz)`.
   - Verified live fleet loaded from Spring Boot: `SIM_FROMVEUR_EXPRESS` (15.6 kts), `SIM_AZENOR_VOYAGER` (14.6 kts), `SIM_IROISE_STAR` (17.0 kts), `SIM_SEIN_SHUTTLE` (14.1 kts).
   - Verified interactive Leaflet map rendered vessels with Track A routing.
   - Verified deep ETA provenance panel displayed: `VectorizedRidgeETAModel + Kinematics`, SHA-256 weight checksum, authoritative countdown, and uncertainty bounds.
   - Verified simulation disclosure banner: `SIMULATION ONLY — Physics-informed arrival predictions across Track A`.

---

## 9. Changed Files Inventory

| File Path | Action | Description |
| :--- | :--- | :--- |
| `frontend/vite.config.ts` | Modified | Configured development proxy forwarding `/api` to `http://localhost:8080`. |
| `frontend/src/assets/iroiseCoastline.json` | Created | Local GeoJSON vector coastline asset for Tier 3 offline map fallback. |
| `frontend/src/services/apiClient.ts` | Created | Strongly-typed API client matching Spring Boot DTOs with RFC 7807 `ProblemDetail` parsing. |
| `frontend/src/hooks/useVesselStream.ts` | Created | SSE hook managing stream subscription, exponential backoff with jitter, and stale watchdog. |
| `frontend/src/hooks/useSimulationControls.ts` | Created | Simulation lifecycle and scenario activation hook. |
| `frontend/src/components/tracking/FleetMap.tsx` | Modified | Upgraded to 3-tier basemap fallback with 6-error threshold and multi-vessel rendering. |
| `frontend/src/components/tracking/VesselDetailPanel.tsx` | Modified | Upgraded to fetch deep ETA provenance, model SHA-256 checksum, and authoritative countdown. |
| `frontend/src/pages/tracking/TrackingPage.tsx` | Modified | Connected `useVesselStream()`; eliminated client-side coordinate jitter loop; added live connection status banner. |
| `frontend/src/pages/public/HomePage.tsx` | Modified | Sourced live fleet from Spring Boot; added honest offline state handling; removed `mockVessels`. |
| `frontend/src/pages/operator/OperatorFleetPage.tsx` | Modified | Sourced live fleet registry from Spring Boot; removed `mockVessels`. |
| `frontend/src/pages/operator/OperatorDashboardPage.tsx` | Modified | Sourced live fleet overview from Spring Boot; removed `mockVessels`. |
| `frontend/src/pages/public/JourneyDetailPage.tsx` | Modified | Sourced live vessel speed and Ridge model provenance from Spring Boot API. |
| `frontend/src/pages/admin/AdminSimulationControlsPage.tsx` | Modified | Wired controls and scenarios directly to Spring Boot endpoints. |
| `frontend/src/pages/admin/AdminDiagnosticsPage.tsx` | Modified | Connected to live SSE event broker stream. |
| `frontend/src/tests/apiClientAndStream.test.ts` | Created | Comprehensive tests for API client, ProblemDetail parsing, 503/404 handling, and simulation controls. |
| `frontend/src/tests/operationalUiAndMapFallback.test.ts` | Created | Tests for Tier 3 GeoJSON, 6-error map threshold, countdown non-arrival latching, and zero-mock policy. |
| `MEMORY.md` | Modified | Updated project status header and appended complete Section 13 audit log. |
| `reports/phase-12-frontend-integration-verification.md` | Created | This verification report. |

---

## 10. Unresolved Risks & Constraints

1. **No External AIS Integration:** All vessel tracking remains strictly virtual/simulated. Real-world AIS feeds must not be connected without explicit authorization.
2. **No Real Payment Processing:** Booking and boarding-pass flows remain in simulated/demonstration mode. Real payment gateways must not be added.
3. **No External Infrastructure:** No Redis, Kafka, or paid tile providers have been introduced.
4. **Phase Stop Condition:** Phase 12 is complete. Work has halted. No subsequent phase or deployment will be initiated without explicit user approval.
