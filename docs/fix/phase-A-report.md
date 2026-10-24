# Phase A Completion Report: Map, ETA & Visualisations

**Date:** 2026-10-24  
**Author:** Senior Full-Stack Engineer  
**Gate Status:** PASSED (All tests passing, E2E verified)

---

## 1. Root-Cause Diagnosis Summary
1. **Engine:** Simulation daemon booted into idle berth dwells without turnaround cycling, causing vessel positions to remain at docks.
   - *Fix:* Added berth dwell turnaround cycling in `virtual_ais_generator.py` (12 steps / 60 seconds dwell before reversing route waypoints).
2. **Backend:** Missing multi-vessel fleet SSE stream `GET /api/v1/stream/vessels`.
   - *Fix:* Implemented `subscribeFleetVesselsStream()` in `TrackingService.java` and `TrackingController.java` emitting `snapshot`, `telemetry_update`, `eta_transition`, `ping`, and `stale` events. Added `VesselLiveDto.java` mapping.
3. **Frontend:** Ad-hoc SSE connection and missing fallback tile architecture caused "API key required" errors on provider failure.
   - *Fix:* Implemented `tileProviders.ts` with 3-tier fallback (CartoDB Voyager -> OpenStreetMap after 6 errors in 5s -> Local `iroiseCoastline.json` offline vector GeoJSON). Built `useVesselStream.ts` hook with exponential backoff and 30s stale watchdog.
4. **Visualisations:** `LiveTelemetryPanel.tsx` updated with tabular numerals (`tabular-nums`), distance in km and NM, speed sparkline, ETA residual convergence chart, plain-language lifecycle explanations, and collapsed "How is this calculated?" Ridge regressor transparency panel (α=10.0, MAE 5.20 min, SHA-256).

---

## 2. Files Modified & Added
- `ml-platform/src/simulation/virtual_ais_generator.py` (turnaround cycling)
- `ml-platform/src/simulation/daemon.py` (health and simulation autoloop)
- `backend/src/main/java/com/whereismyferry/backend/dto/VesselLiveDto.java` (new DTO)
- `backend/src/main/java/com/whereismyferry/backend/client/SimulationClient.java` (getFleetVessels)
- `backend/src/main/java/com/whereismyferry/backend/client/RestClientSimulationClient.java` (implementation)
- `backend/src/main/java/com/whereismyferry/backend/service/TrackingService.java` (stream implementation)
- `backend/src/main/java/com/whereismyferry/backend/controller/TrackingController.java` (/stream/vessels)
- `backend/src/main/java/com/whereismyferry/backend/security/SecurityConfig.java` (permit /api/v1/stream/**)
- `backend/src/test/java/com/whereismyferry/backend/VesselContractTests.java` (contract & 503 test)
- `frontend/src/map/tileProviders.ts` (3-tier fallback with zero API key guarantee)
- `frontend/src/map/iroiseCoastline.json` (offline vector GeoJSON)
- `frontend/src/hooks/useVesselStream.ts` (fleet SSE hook)
- `frontend/src/components/map/FerryMap.tsx` (Leaflet CSS, rotated markers, berth circles, connection chip, honest label)
- `frontend/src/components/tracking/LiveTelemetryPanel.tsx` (sparkline, ETA chart, tabular numerals, SHA checksum)
- `frontend/src/pages/TrackingPage.tsx` (route tabs, useVesselStream integration, honest badge)
- `frontend/vite.config.ts` (SSE keep-alive proxy)
- `frontend/src/__tests__/TileProviders.test.ts` (unit tests for zero API keys and fallback)
- `frontend/playwright.config.ts` & `frontend/e2e/phaseA.spec.ts` (Playwright E2E verification)

---

## 3. Test Results & Counts
| Suite | Baseline Required | Current Passing | Status |
| :--- | :--- | :--- | :--- |
| **Python (`ml-platform`)** | 87 | **115** | PASS |
| **Java (`backend`)** | 42 | **53** | PASS |
| **Vitest (`frontend`)** | 27 | **85** | PASS |
| **Playwright (`frontend`)** | 1 | **1** (`phaseA.spec.ts`) | PASS |
| **Total Tests** | 157 | **254** | **100% PASS** |

### Playwright E2E Verification (`phaseA.spec.ts`)
- Navigated to `/track`.
- Asserted raster tiles load with HTTP 200 from CartoDB Voyager.
- Asserted zero instances of the string `"API key"` in DOM.
- Asserted vessel telemetry panel displays live SOG, COG, predicted ETA, and model SHA.
- Asserted vessel moves across 10-second sampling window.

---

## 4. Open Issues
- None. Phase A Gate criteria completely fulfilled.
