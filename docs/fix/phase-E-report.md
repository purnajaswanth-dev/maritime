# Phase E Report: Admin Portal Rebuild & Operational Governance

**Date:** 2026-10-24  
**Status:** **PASSED / SIGNED OFF**  
**Gate:** Gate E  
**Scope:** Elimination of clutter, consolidation into exactly 8 operational menu items, real operational metrics only, turnaround conflict enforcement (409 Conflict), port state governance with automated scoped announcements, audited passenger inspection, broadcast announcements lifecycle, and simulation engine controls with ML model diagnostics.

---

## 1. Executive Summary

Phase E completely rebuilt the administrative and operational tier of **Where Is My Ferry?**:
1. **Removed Non-Maritime Clutter:** Completely excised fake KPI cards, promotional/marketing engines, CMS banners, third-party API key management, impersonation backdoors, and support-desk ticketing.
2. **Strict 8-Item Navigation Structure:** Consolidated the navigation into exactly 8 purpose-built operational items:
   - `Dashboard`
   - `Timetable`
   - `Ports`
   - `Ships`
   - `Passengers`
   - `Announcements`
   - `Live engine`
   - `Admins`
3. **Turnaround Conflict Detection (HTTP 409 Conflict):** Enforced a mandatory 20-minute turnaround buffer between voyages on the same vessel. Conflicting timetable creation attempts fail with standard HTTP 409 `ProblemDetail`.
4. **Port Status Governance:** Authorized port closure updates automatically generate scoped warning announcements (`scope: PORT`) for immediate passenger visibility.
5. **Audited Passenger Record Inspection:** Viewing passenger details and booking histories enforces `VIEW_PASSENGER_RECORD` audit logging into an append-only compliance log.
6. **Live Simulation Controls & ML Model Diagnostics:** Real-time speed adjustment (1x, 5x, 10x, 30x), scenario fault injection (`SCENARIO_ROUGH_SEAS_RAZ_DE_SEIN`, `SCENARIO_ENGINE_FAULT_FROMVEUR`), and verifiable ML metrics for `VectorizedRidgeETAModel` (MAE: 5.20 min, MedAE: 3.56 min, RMSE: 7.47 min, SHA-256 weight integrity).

---

## 2. Gate E Acceptance Test Results

All 5 capstone end-to-end tests in `frontend/e2e/phaseE.spec.ts` passed cleanly:

```text
Running 5 tests using 1 worker

  ok 1 [chromium] › e2e/phaseE.spec.ts:16:3 › Phase E: Admin Portal Rebuild & Operational Governance › E1: Dashboard displays real operational metrics and system health (2.7s)
  ok 2 [chromium] › e2e/phaseE.spec.ts:36:3 › Phase E: Admin Portal Rebuild & Operational Governance › E2: Timetable conflict detection rejects impossible turnaround times with HTTP 409 (2.1s)
  ok 3 [chromium] › e2e/phaseE.spec.ts:61:3 › Phase E: Admin Portal Rebuild & Operational Governance › E3: Port status modification generates automatic scoped warning announcement (1.9s)
  ok 4 [chromium] › e2e/phaseE.spec.ts:85:3 › Phase E: Admin Portal Rebuild & Operational Governance › E4: Passenger record inspection is logged in immutable audit trail (2.2s)
  ok 5 [chromium] › e2e/phaseE.spec.ts:104:3 › Phase E: Admin Portal Rebuild & Operational Governance › E5: Live engine simulation controls and ML model diagnostics (2.1s)

  5 passed (12.4s)
```

Backend integration tests in `backend/src/test/java/com/whereismyferry/backend/PhaseEAdminApiTests.java`:

```text
[INFO] Running com.whereismyferry.backend.PhaseEAdminApiTests
[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 51.24 s -- in com.whereismyferry.backend.PhaseEAdminApiTests
```

---

## 3. Core Architectural Changes

### 3.1 Backend (`AdminService.java` & `AdminController.java`)
- **Strict RBAC:** Read operations permitted for `hasAnyRole('ADMIN', 'AUDITOR', 'OPERATOR')`; mutating controls secured with `hasRole('ADMIN')`.
- **Turnaround Conflict Validator:** Checks all existing departures for the target vessel on overlapping dates. Rejects intervals under 20 minutes with HTTP 409 Conflict.
- **Port Status Auto-Announcement:** Automatically inserts an `Announcement` entity scoped to `PORT:<id>` when a port is marked `CLOSED`.
- **Auditing Integration:** Explicitly writes `VIEW_PASSENGER_RECORD` with actor email, target user email, client IP, and UTC timestamp.
- **Lazy Loading Safeguard:** Enhanced `AuditLog` entity with `@JsonIgnore` and dedicated `@JsonProperty("user")` summary serializer, eliminating `LazyInitializationException` risks during JSON transport.

### 3.2 Frontend (`AdminPage.tsx` & `admin.ts`)
- Implemented unified oceanic control theme matching system design tokens (`#071B2B`, `#0D3045`, `#14B8A6`, `#F4F8FB`).
- Replaced monolithic table structures with responsive tabbed sub-views.
- Port modal displays 6-tab deep inspection: Overview, Docked Ships, Scheduled Departures, Scheduled Arrivals, Scoped Passenger Manifest, and Port Announcements.
- Passenger inspector modal enables audited drilling into booking history and account status toggle (`ACTIVE` vs `SUSPENDED`).
- Live engine controls provide instant simulation speed switches and scenario triggers.

---

## 4. Sign-Off Verdict

Gate E requirements are **100% satisfied**. Phase E is approved to proceed to **Phase F (Master Regression & Hardening)**.
