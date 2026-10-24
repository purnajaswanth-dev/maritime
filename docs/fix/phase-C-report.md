# Phase C Report: Ports, Ships, and Timetable Data Model

**Date:** 2026-10-24  
**Status:** GATE PASSED  

---

## 1. Summary of Changes

Phase C implements the complete PostgreSQL-driven data model for ports, vessels, routes, services, departures, and announcements, fully synchronized with the Python ML simulation engine.

1. **Database Schema & Migrations (`V3__ports_ships_timetable.sql`):**
   - **`ports`:** Added `berth_radius_m`, `status` (`OPEN`/`CLOSED`), `address`, `phone`, `email`, `facilities`, `notes`. Canonical coordinates and berth radii seeded for:
     - `BREST`: lat 48.3811, lon -4.4857, radius 800m
     - `LE_CONQUET`: lat 48.3596, lon -4.7818, radius 600m
     - `OUESSANT_STIFF`: lat 48.4691, lon -5.0545, radius 800m
     - `MOLENE`: lat 48.4022, lon -4.9565, radius 500m
     - `AUDIERNE`: lat 48.0061, lon -4.5524, radius 600m
     - `ILE_DE_SEIN`: lat 48.0390, lon -4.8486, radius 500m
     - `CAMARET`: lat 48.2780, lon -4.5940, radius 600m
   - **`vessels`:** Added `engine_vessel_id`, `home_port_id`, `capacity`. Seeded the 4 modelled fleet vessels: `V-FROMVEUR-SIM`, `V-AZENOR-SIM`, `V-OUESSANT-SIM`, and `V-SEIN-SIM`.
   - **`routes`:** Added `distance_km`, `typical_duration_min`, and `engine_corridor_id`.
   - **`services`:** Created timetable recurring service patterns table with `route_id`, `vessel_id`, `departure_time`, `duration_min`, `days_of_week`, `valid_from`, `valid_to`, `base_fare`, `capacity`, and `active`.
   - **`departures`:** Added `cancel_reason`, `seats_available`, and `service_id`, with unique constraint on `(vessel_id, scheduled_departure_time)`.
   - **`announcements`:** Created announcements table with `title`, `body`, `severity` (`INFO`, `WARNING`, `CRITICAL`), `scope` (`ALL`, `PORT`, `ROUTE`, `DEPARTURE`), `target_id`, `starts_at`, `ends_at`, and `created_by`.

2. **Backend JPA Entities & Services (`backend/`):**
   - Updated `Port.java`, `Vessel.java`, `Route.java`, and `Departure.java` entities.
   - Created `ServiceEntity.java`, `ServiceEntityRepository.java`, `Announcement.java`, and `AnnouncementRepository.java`.
   - Updated `DatabaseSeederService.java` with `@Order(1)` to seed `ServiceEntity` and route corridors.
   - Upgraded `DepartureGeneratorService.java` with 60 days ahead generation, idempotent duplicate checking, protection of booked departures, and automated synchronization with Python simulation engine on startup and daily schedule.
   - Implemented `syncTimetable` on `SimulationClient` and `RestClientSimulationClient` connecting to `POST /internal/v1/timetable/sync`.
   - Permitted `/api/v1/tracking/**` and `/api/v1/announcements/**` in `SecurityConfig.java`.

3. **Python ML Simulation Daemon (`ml-platform/`):**
   - Implemented `sync_timetable(departures)` in `replay_runner.py` accepting dynamic departure payloads, matching corridors, and running real historical voyages.
   - Added `POST /internal/v1/timetable/sync` and `GET /internal/v1/departures/{id}/live` in `daemon.py`.
   - Implemented `GET /internal/v1/accuracy` for predicted vs actual arrival ground truth.

---

## 2. Files Touched

- `backend/src/main/resources/db/migration/V3__ports_ships_timetable.sql`
- `backend/src/main/java/com/whereismyferry/backend/entity/Port.java`
- `backend/src/main/java/com/whereismyferry/backend/entity/Vessel.java`
- `backend/src/main/java/com/whereismyferry/backend/entity/Route.java`
- `backend/src/main/java/com/whereismyferry/backend/entity/Departure.java`
- `backend/src/main/java/com/whereismyferry/backend/entity/ServiceEntity.java`
- `backend/src/main/java/com/whereismyferry/backend/entity/Announcement.java`
- `backend/src/main/java/com/whereismyferry/backend/repository/ServiceEntityRepository.java`
- `backend/src/main/java/com/whereismyferry/backend/repository/AnnouncementRepository.java`
- `backend/src/main/java/com/whereismyferry/backend/repository/BookingRepository.java`
- `backend/src/main/java/com/whereismyferry/backend/client/SimulationClient.java`
- `backend/src/main/java/com/whereismyferry/backend/client/RestClientSimulationClient.java`
- `backend/src/main/java/com/whereismyferry/backend/service/DatabaseSeederService.java`
- `backend/src/main/java/com/whereismyferry/backend/service/DepartureGeneratorService.java`
- `backend/src/main/java/com/whereismyferry/backend/security/SecurityConfig.java`
- `backend/src/test/java/com/whereismyferry/backend/PhaseCTimetableAndSyncTests.java`
- `ml-platform/src/replay/replay_runner.py`
- `ml-platform/src/simulation/daemon.py`
- `ml-platform/tests/test_phase02_replay_engine.py`

---

## 3. Test Counts & Verification

| Test Suite | Total Tests | Passed | Failures / Errors |
| :--- | :--- | :--- | :--- |
| **Python Pytest Suite** (`ml-platform`) | 116 | 116 | 0 |
| **Java Maven Suite** (`backend`) | 61 | 61 | 0 |
| **Vitest Unit Suite** (`frontend`) | 91 | 91 | 0 |
| **Playwright E2E Suite** (`frontend`) | 2 | 2 | 0 |

---

## 4. Gate Verification

- **PostgreSQL Departures:** 16 departures generated and returned for today (`2026-10-24`) via `GET /api/v1/departures`; 976 departures generated for the 60-day horizon.
- **Engine Synchronization:** `POST /internal/v1/timetable/sync` returns `{ "status": "SYNCED", "synced_count": 16, "supported_count": 10, "sim_date": "2026-10-24" }`.
- **Live Replay:** Replays active for supported vessels (`V-FROMVEUR-SIM`, `V-AZENOR-SIM`, `V-OUESSANT-SIM`, `V-SEIN-SIM`).

**Phase C Gate is officially PASSED.**
