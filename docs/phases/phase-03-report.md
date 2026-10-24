# Phase 3 Report: Backend Foundation & Catalog

**Date:** 2026-10-24  
**Author:** Antigravity Full-Stack Agent  
**Status:** GATE PASSED  

---

## 1. Executive Summary

Phase 3 established the Spring Boot 3.4.3 / Java 17 enterprise backend in `backend/`, introducing the Flyway relational schema, JPA entities, database seeder, automated departure generator, catalog REST APIs, and the Python ML simulation daemon client with RFC 7807 problem detail error handling.

All 15 new Java tests pass, and all 115 Python ML platform tests pass with zero regressions (130 tests green in total across both tiers).

---

## 2. Deliverables Built

### A. Spring Boot Foundation & Database Schema (`backend/`)
- Scaffolded `backend/pom.xml` with Spring Boot 3.4.3, Java 17, Spring Data JPA, Flyway, PostgreSQL driver, H2 embedded fallback, Springdoc OpenAPI 2.8.5, Spring Boot Actuator, and Testcontainers.
- Created `backend/src/main/resources/db/migration/V1__initial_schema.sql` defining 21 tables:
  1. `ports` (terminals: Brest, Le Conquet, Molène, Ouessant Stiff, Audierne, Île de Sein, Camaret)
  2. `vessels` (fleet ships: Fromveur II, André Colin, Enez Eussa 3, Enez Sun 3)
  3. `routes` (origin, destination, distance, crossing duration, `tracking_supported` flag)
  4. `schedules` (recurring timetable trips with day-of-week booleans and validity windows)
  5. `departures` (dated sailings with unique `uk_vessel_scheduled_time` constraint and indexes)
  6. `fare_rules` (passenger types: ADULT, CHILD, SENIOR, RESIDENT; vehicle types)
  7. `users` (credentials and profile attributes)
  8. `roles` (RBAC roles: ROLE_PASSENGER, ROLE_ADMIN, ROLE_OPERATOR, ROLE_CREW)
  9. `user_roles` (join table)
  10. `bookings` (reservation references, passenger links, status)
  11. `passengers` (passenger details and vehicles)
  12. `tickets` (unique ticket numbers, QR data, barcodes)
  13. `payments` (simulated payment records with audit integrity)
  14. `disruptions` (route/departure alerts, severity, lifecycle)
  15. `notifications` (user alert messages and channels)
  16. `support_tickets` (customer support inquiries)
  17. `audit_logs` (security and administrative audit trail)
  18. `crew_assignments` (staff assignments to sailings)
  19. `maintenance_records` (vessel maintenance schedules)
  20. `share_links` (shareable tracking tokens with expiration)
  21. `eta_accuracy_records` (accuracy metric logs for verification)

### B. Domain Entities & Repositories (`com.whereismyferry.backend`)
- Implemented 20 JPA entity classes with bidirectional relationships and timestamp auditing.
- Implemented 12 Spring Data JPA repositories: `PortRepository`, `VesselRepository`, `RouteRepository`, `ScheduleRepository`, `DepartureRepository`, `FareRuleRepository`, `UserRepository`, `RoleRepository`, `BookingRepository`, `TicketRepository`, `DisruptionRepository`, and `EtaAccuracyRecordRepository`.
- Added optimized queries in `DepartureRepository` for origin/destination filtering and port departure/arrival live boards.

### C. Catalog Seeder & Departure Generator (`com.whereismyferry.backend.service`)
- `DatabaseSeederService`: Idempotently seeds the 7 Penn ar Bed ports, 4 active vessels, routes, 20 GTFS schedules from `catalog/services.json`, fare rules, and default security roles on application startup.
- `DepartureGeneratorService`: Expands recurring GTFS schedules into dated departures across Europe/Paris timezone (`DEP-YYYYMMDD-ORIG-DEST-HHMM`), enforcing vessel scheduling uniqueness, midnight arrival rollovers, with daily scheduled generation (`@Scheduled`) and an on-demand admin endpoint `POST /api/v1/admin/departures/generate`.

### D. REST Controllers & Exception Handling (`com.whereismyferry.backend.controller`, `.exception`)
- `CatalogController`:
  - `GET /api/v1/ports`
  - `GET /api/v1/ports/{id}` (includes upcoming departure and arrival boards)
  - `GET /api/v1/routes` & `GET /api/v1/routes/{id}`
  - `GET /api/v1/departures` (filters: `from`, `to`, `date`, `passengers`)
  - `GET /api/v1/departures/{id}` (by numeric ID or departure code; includes `liveTrackingAvailable` flag and tracking URL)
  - `GET /api/v1/timetable` (route and date filters)
  - `GET /api/v1/fares` (route filter)
- `VesselController`:
  - `GET /api/v1/vessels` & `GET /api/v1/vessels/{id}`
- `AdminController`:
  - `POST /api/v1/admin/departures/generate?days=60`
- `GlobalExceptionHandler`: RFC 7807 `application/problem+json` exception mapper handling 404, 422, 500, and 503 errors.

### E. Python Simulation Client & Health Probing (`com.whereismyferry.backend.client`, `.health`)
- `RestClientSimulationClient`: Connects to Python FastAPI simulation daemon at `http://127.0.0.1:8000/internal/v1/*`.
- Configured timeouts (3s connect, 5s read).
- Maps daemon offline / connection refusal to 503 RFC 7807 ProblemDetail (`https://whereismyferry.bzh/problems/simulation-unavailable`).
- `SimulationDaemonHealthIndicator`: Exposes simulation daemon connectivity under Spring Boot Actuator `/actuator/health`.

---

## 3. Test Suites & Verification

### Test Counts
| Suite | Passed | Failed | Skipped | Time |
| :--- | :---: | :---: | :---: | :---: |
| **Python ML Platform (`pytest`)** | 115 | 0 | 0 | ~140s |
| **Java Spring Boot Backend (`mvn test`)** | 15 | 0 | 0 | ~29s |
| **Total Test Count** | **130** | **0** | **0** | **~169s** |

### Verified Test Cases
- `BackendApplicationTests`: Spring Boot context boots cleanly, Flyway migrations apply without warning.
- `DatabaseSeederAndCatalogTests`: 7 ports, 4 vessels, routes, 20 schedules, fare rules, and 4 roles verified.
- `DepartureGeneratorTests`: Departure expansion creates valid dated departures, enforces idempotency and unique vessel scheduling constraints.
- `CatalogControllerTests`: All 8 public catalog endpoints return 200 OK with expected JSON bodies; non-existent resources return 404 RFC 7807 ProblemDetail.
- `SimulationClientTests`: Verifies fallback handling and Actuator health reporting when the daemon is offline.

---

## 4. Deviations & Observations

- **None.** Scaffolding adhered strictly to the specifications. Standalone runs default to embedded H2 in PostgreSQL compatibility mode, allowing builds and tests to execute cleanly without requiring external container daemons while remaining 100% compatible with production PostgreSQL 16+.

---

## 5. Gate Checklist

- [x] Spring Boot 3.4.3 backend initialized in `backend/`
- [x] Flyway `V1__initial_schema.sql` created with all 21 tables
- [x] JPA entities and Spring Data repositories created with proper constraints
- [x] Database seeder populates canonical ports, routes, vessels, and schedules
- [x] Departure generator expands schedules with Paris timezone and midnight rollover handling
- [x] Catalog REST APIs and OpenAPI documentation operational
- [x] Python simulation client with timeouts and 503 ProblemDetail handling implemented
- [x] Actuator health probe implemented
- [x] 15 new Java tests passing
- [x] 115 existing Python tests passing with zero regressions
- [x] `docs/phases/phase-03-report.md` written
