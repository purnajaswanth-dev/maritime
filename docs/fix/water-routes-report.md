# Water Routes & Land-Avoidance Corridor Navigation Report

## 1. Executive Summary & Root Cause Analysis

### Problem Statement
On `/track` on the live application, vessel tracking showed vessels navigating directly over dry land, and corridor track guidelines were rendered as straight lines crossing peninsulas and headlands (specifically across the Plouzane peninsula between Brest and Le Conquet).

### Root Cause
1. **Geometric Oversimplification:** Both the synthetic AIS simulation generator (`VirtualAISGenerator`) and the frontend map (`FerryMap.tsx`) utilized 2-point or straight Euclidean lines directly connecting ferry terminals. In maritime geography, straight paths between ports frequently intersect peninsulas, headlands, and islands.
2. **Missing Land Mask / Sea Fairways:** Neither the FastAPI simulation daemon nor the frontend had awareness of coastal geography or fairway channels (such as the *Goulet de Brest*, the *Pointe Saint-Mathieu* bypass, or the *Chenal du Four*).
3. **Decoupled Geometries:** Frontend corridor tracks were hardcoded as 2-point straight segments, while the backend engine computed positions along different waypoints, causing visual dissociation between vessels and drawn routes.

### Resolution
A water-only routing subsystem was implemented with:
- High-resolution coastline land mask (`iroise_land.geojson`, 0.71 MB) derived from OpenStreetMap coastline data clipped to the Iroise Sea.
- Validated sea corridor waypoints and 500m geofence safety corridors (`routes.json`, 173.8 KB, SHA-256 verified) navigating strictly through water.
- Along-track kinematic advancement with smoothed lookahead COG tangent generation (eliminating heading discontinuities).
- Automatic runtime safety guard snapping vessels back to water if any position falls outside water corridors.
- Additive endpoint `/api/v1/routes/geometry` providing single-source-of-truth route geometries to the frontend map.

---

## 2. Corridor Route Metrics & Validation

All 4 operational corridors were generated and validated against the Iroise land mask:

| Corridor ID | Name | Great Circle (km) | Water Route (km) | Distance Ratio | Land Crossings | Min Clearance (m) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BREST_LE_CONQUET` | Brest $\rightarrow$ Le Conquet | 21.83 km | 29.65 km | 1.358 | **0** | 362.5 m |
| `LE_CONQUET_BREST` | Le Conquet $\rightarrow$ Brest | 21.83 km | 29.65 km | 1.358 | **0** | 362.5 m |
| `BREST_OUESSANT_STIFF` | Brest $\rightarrow$ Ouessant (Stiff) | 42.55 km | 51.58 km | 1.212 | **0** | 182.6 m |
| `AUDIERNE_ILE_DE_SEIN` | Audierne (Sainte-Évette) $\rightarrow$ Île de Sein | 23.29 km | 27.03 km | 1.161 | **0** | 323.0 m |

*All distance ratios are well within the required safety bound [1.0, 1.4]. Open-sea clearance strictly exceeds 100 meters across all fairway segments.*

### Visual Comparisons
Before/after comparison graphics have been generated and saved:
- `docs/fix/corridor_brest_le_conquet.png`
- `docs/fix/corridor_le_conquet_brest.png`
- `docs/fix/corridor_brest_ouessant.png`
- `docs/fix/corridor_audierne_sein.png`

---

## 3. Files Changed and Preserved

### Files Modified or Added:
- **`ml-platform/data/geo/iroise_land.geojson`**: Committed land polygon mask (0.71 MB < 5 MB limit).
- **`ml-platform/data/geo/routes.json`**: Committed corridor polylines and geofences (173.8 KB < 200 KB limit).
- **`ml-platform/data/geo/README.md`**: Attribution, licensing, and schema documentation.
- **`ml-platform/src/geo/land_mask.py`**: Spatial query engine (`is_on_land`, `segment_crosses_land`, berth exemptions).
- **`ml-platform/src/geo/sea_routes.py`**: Route generation, clearance validation, and manifest checksum computation.
- **`ml-platform/src/simulation/virtual_ais_generator.py`**: Polyline kinematics, lookahead COG tangent, runtime guard, `route_waypoints` separation.
- **`ml-platform/src/simulation/virtual_fleet_runner.py`**: Propagate `geofence_corrections` metric.
- **`ml-platform/src/simulation/daemon.py`**: Expose `GET /internal/v1/routes` corridor geometry endpoint.
- **`ml-platform/src/replay/replay_runner.py`**: Respect `GEOFENCE_ENABLED` and land boundary snapping.
- **`backend/src/main/java/com/whereismyferry/backend/dto/RouteGeometryDto.java`**: Additive DTO.
- **`backend/src/main/java/com/whereismyferry/backend/dto/VesselLiveDto.java`**: Added `position_valid` field with `@JsonIgnoreProperties`.
- **`backend/src/main/java/com/whereismyferry/backend/client/SimulationClient.java`**: Declared `getRouteGeometries()`.
- **`backend/src/main/java/com/whereismyferry/backend/client/RestClientSimulationClient.java`**: Implemented `getRouteGeometries()`.
- **`backend/src/main/java/com/whereismyferry/backend/service/TrackingService.java`**: Caching and retrieval of route geometries.
- **`backend/src/main/java/com/whereismyferry/backend/controller/TrackingController.java`**: `@GetMapping("/routes/geometry")`.
- **`backend/src/test/java/com/whereismyferry/backend/RouteGeometryContractTests.java`**: Contract and error resilience tests.
- **`frontend/src/components/map/FerryMap.tsx`**: Replaced straight-line tracks with dynamic water routes; enforced 300m jump suppression rule.
- **`frontend/src/pages/TrackingPage.tsx`**: Dynamic route selection from geometry API.
- **`frontend/src/__tests__/FerryMapRoutes.test.tsx`**: Vitest tests for geometry rendering, failure resilience, and 300m rule.
- **`frontend/e2e/waterRoutes.spec.ts`**: Playwright E2E spec for water corridors.
- **`ml-platform/tests/test_water_routes.py`**: Comprehensive 8-test Python suite.

### Strictly Preserved (NOT Changed):
- **Authentication & RBAC**: Untouched.
- **Database & Flyway Migrations**: Untouched.
- **Admin Portal & Timetables**: Untouched.
- **Booking & Fares**: Untouched.
- **ETA ML Model & Weights**: Model architecture, training pipeline, and frozen weights SHA-256 (`e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9`) completely unchanged.
- **Deployment & Infrastructure**: `render.yaml`, `Dockerfile`s, environment configurations unchanged.

---

## 4. Test Suite Execution & Verification

All existing and new test suites pass 100% without weakening or deleting any assertions:

| Test Suite | Tests Passed | Failures | Notes |
| :--- | :--- | :--- | :--- |
| **Python (`ml-platform`)** | **123 passed, 1 skipped** (124 total) | 0 | Includes 8 new water route & geofence tests across 20 seeds & 22 scenarios |
| **Java (`backend`)** | **86 passed** (86 total) | 0 | Includes new contract & error tests for `/api/v1/routes/geometry` |
| **Vitest (`frontend`)** | **101 passed** (28 test files) | 0 | Includes new `FerryMapRoutes.test.tsx` (3 tests) |
| **Frontend Production Build** | **Success** | 0 | `tsc -b && vite build` clean |
| **Backend Packaging** | **Success** | 0 | `mvn -B package -DskipTests` jar packaged |

### Geofence Corrections Observed
During nominal simulation of all 4 corridors across 20 distinct random seeds (totalling over 50,000 simulated positions), the aggregate runtime geofence correction count was:
$$\text{Total Geofence Corrections} = \mathbf{0}$$
Every single simulated position naturally stayed in water and within its 500m fairway corridor.

---

## 5. Feature Flags & Operational Guide

### Feature Flag: `GEOFENCE_ENABLED`
- **Default:** `true` (or unset). The engine loads `routes.json` and `iroise_land.geojson`, advances vessels along water fairways, and applies runtime geofence snapping.
- **Fallback / Disabling:** Set `GEOFENCE_ENABLED=false` in the environment. The engine immediately reverts to previous waypoint interpolation without crashing or interrupting simulation streaming.
- **Graceful Error Handling:** If `routes.json` or `iroise_land.geojson` is missing, corrupted, or unreadable, the engine logs an error, sets `position_valid=False`, and safely runs with fallback waypoints.

### Route Regeneration Guide
To regenerate or update water corridors (e.g., when adding a new port or updating fairway waypoints):
```bash
cd ml-platform
python -m src.geo.sea_routes
```
This script validates clearance against the land mask, verifies berth radii, recomputes length and great-circle metrics, and updates the manifest SHA-256.

---

## 6. Observations & Non-Interference Notes

### SSE "Reconnecting" Indicator
Per explicit instructions, the SSE "Reconnecting" status indicator was **NOT altered or disturbed**. Observations:
- In production, modern browsers and proxy layers (e.g. Render / Cloudflare) may close idle HTTP connections after 100-120 seconds.
- The backend SSE emitter sends heartbeats (`ping` events) every 15 seconds to keep connections alive.
- The frontend `EventSource` automatically reconnects upon stream termination according to standard SSE semantics, momentarily displaying the "Reconnecting" pill before resuming.
- Telemetry data and vessel markers continue streaming normally.

### Terminal Marker "CA"
- Confirmed that the "CA" marker on the map represents **Camaret-sur-Mer** (`CAM`), an authentic canonical Penn-ar-Bed terminal in Finistère present in the GTFS database and catalog seed. It is correctly placed at Port de Camaret ($48.2778^\circ\text{ N}, -4.5956^\circ\text{ W}$) in water.
