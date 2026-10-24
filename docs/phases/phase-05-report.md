# Phase 5 Report: Live Integration & Tracking APIs

**Date:** 2026-10-24  
**Author:** Antigravity Full-Stack Agent  
**Status:** GATE PASSED  

---

## 1. Executive Summary

Phase 5 delivered the real-time tracking, live telemetry integration, Server-Sent Events (SSE) streaming, and public shareable link infrastructure. The Spring Boot backend connects directly to the Python FastAPI simulation daemon at `http://127.0.0.1:8000/internal/v1/*`, streaming live vessel coordinates, speeds, headings, and Ridge model ETA predictions while preserving honest labeling (`HISTORICAL_REPLAY` and frozen weights SHA-256). When the daemon is offline, all tracking endpoints honestly report a 503 RFC 7807 ProblemDetail without degrading catalog functionality.

All 5 new Java tracking tests pass, and all 29 previous Java tests + 115 Python tests pass with zero regressions (149 total tests passing across both tiers).

---

## 2. Deliverables Built

### A. Live Tracking Endpoints (`com.whereismyferry.backend.controller.TrackingController`)
- **`GET /api/v1/departures/{id}/live`**:
  - Accepts numeric departure ID or standard code (`DEP-YYYYMMDD-ORIG-DEST-HHMM`).
  - Retrieves live vessel position, speed, heading, target berth radius, lifecycle state (`UNDERWAY`, `APPROACHING`, `ARRIVED`, etc.), and Ridge regression ETA predictions (point estimate, P10, P90).
  - Returns honest data provenance (`data_source: "HISTORICAL_REPLAY"`, frozen weights SHA-256: `e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9`).
  - Disconnected engine cleanly maps to 503 RFC 7807 ProblemDetail (`https://whereismyferry.bzh/problems/simulation-unavailable`).
- **`GET /api/v1/departures/{id}/track`**:
  - Retrieves the full voyage polyline coordinates and waypoints for map rendering.
- **`GET /api/v1/departures/{id}/stream`**:
  - Implements Server-Sent Events (SSE) `text/event-stream`.
  - Dispatches `event: live-update` at 1 Hz intervals to connected browser clients using an asynchronous `ScheduledExecutorService`.
  - Handles client disconnects, timeouts (120s with automatic browser re-connection), and stream cancellation.

### B. Public Shareable Tracking Links
- **`ShareLinkRepository.java` & Entity Persistence**:
  - Persists tracking tokens in the `share_links` table with cryptographic URL-safe tokens (`UUID` hex) and configurable expiration (default 24 hours).
- **`POST /api/v1/departures/{id}/share`**:
  - Generates shareable token and returns `ShareLinkResponseDto` (`token`, `shareUrl`, `departureCode`, `expiresAt`).
- **`GET /api/v1/track/{token}`**:
  - Public unauthenticated endpoint allowing external parties to track a sailing without requiring user registration or login.
  - Validates token validity and expiration. Returns 404 ProblemDetail (`https://whereismyferry.bzh/problems/resource-not-found`) for expired or unknown tokens.
  - Returns `PublicTrackResponseDto` combining departure metadata, route details, vessel capacity, live snapshot, and track coordinates.

### C. Security Filter Alignment (`SecurityConfig.java`)
- Explicitly permitted public access for `/api/v1/track/**` alongside existing `/api/v1/departures/**` routes.

---

## 3. Test Suites & Verification

### Test Counts
| Suite | Passed | Failed | Skipped | Time |
| :--- | :---: | :---: | :---: | :---: |
| **Python ML Platform (`pytest`)** | 115 | 0 | 0 | ~140s |
| **Java Spring Boot Backend (`mvn test`)** | 34 | 0 | 0 | ~29s |
| **Total Test Count** | **149** | **0** | **0** | **~169s** |

### Verified Test Cases
- `TrackingControllerTests`:
  - `testGetLiveTrackingSuccess`: 200 OK returning live position, speed, and ETA prediction.
  - `testGetLiveTrackingDaemonOffline`: 503 ProblemDetail with URI `https://whereismyferry.bzh/problems/simulation-unavailable`.
  - `testGetVoyageTrack`: 200 OK returning voyage polyline coordinates.
  - `testShareableLinkLifecycle`: POST generates URL-safe token, and public GET resolves it without authentication.
  - `testInvalidShareToken`: 404 ProblemDetail for invalid/expired tokens.

---

## 4. Deviations & Observations

- None. Implementation adhered strictly to the master build prompt specifications.

---

## 5. Gate Checklist

- [x] Live departure tracking proxy endpoint (`/api/v1/departures/{id}/live`) implemented
- [x] Voyage track endpoint (`/api/v1/departures/{id}/track`) implemented
- [x] 1 Hz Server-Sent Events stream (`/api/v1/departures/{id}/stream`) implemented
- [x] Honest data labeling (`HISTORICAL_REPLAY` and weights SHA-256) preserved
- [x] 503 RFC 7807 ProblemDetail returned on engine disconnect
- [x] Public shareable links (`/api/v1/departures/{id}/share` and `/api/v1/track/{token}`) implemented
- [x] 34 Java tests passing (5 new Phase 5 tests + 29 earlier tests)
- [x] 115 Python tests passing with zero regressions
- [x] `docs/phases/phase-05-report.md` written
