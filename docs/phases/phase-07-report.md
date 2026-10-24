# Phase 7 Report: Interactive Map & Live Telemetry UI

**Date:** 2026-10-24  
**Author:** Antigravity Full-Stack Agent  
**Status:** GATE PASSED  

---

## 1. Executive Summary

Phase 7 delivered the real-time interactive maritime mapping and live telemetry streaming user interface. Centered on the Iroise Sea and Brittany coast, the interface displays Penn ar Bed vessels (*Fromveur II*, *Enez Sun 3*, *Enez Eussa 3*) with dynamic SVG markers that rotate smoothly according to compass heading, pulsed underway halos, voyage route polylines, and port terminal pins.

The accompanying live telemetry panel renders real-time speed in knots (SOG), heading (COG), GPS coordinates, ETA predictions, Ridge model estimated delays with confidence intervals (P10-P90), honest data provenance (`HISTORICAL_REPLAY` and weights SHA-256), and public voyage sharing links (`/track/:token`). Offline replay daemon states (503 ProblemDetails) are honestly handled with clear status messages and reconnection controls.

All 16 Vitest frontend test suites (50 tests total) pass cleanly, `npm run build` compiles with zero errors, and all existing Python (115 tests) and Java (34 tests) suites remain 100% green (199 total tests passing across all three tiers).

---

## 2. Deliverables Built

### A. Domain Models (`frontend/src/types/tracking.ts`)
- **`LiveTelemetry`**: Captures vessel telemetry including speed in knots, heading in degrees, GPS coordinates, Ridge delay predictions, confidence interval bounds (`ciLowerMinutes`, `ciUpperMinutes`), ETA timestamp, data source, and frozen model weights SHA-256.
- **`DepartureSummary`** & **`PublicTrackData`**: Structured schemas for sailing routes, scheduled times, and shared public tracking payloads.

### B. Interactive Map (`frontend/src/components/map/FerryMap.tsx`)
- Integrated Leaflet maritime view centered on the Iroise Sea (`[48.35, -4.75]`, zoom 10).
- OpenStreetMap / CartoDB maritime tiles.
- Custom SVG pins with code tags and popup metadata for all 7 Brittany terminals:
  - Brest Port de Commerce (BES)
  - Le Conquet Gare Maritime (LCQ)
  - Île-Molène Quai Nord (MOL)
  - Ouessant Port du Stiff (OUE)
  - Audierne Sainte-Évette (AUD)
  - Île de Sein (SEI)
  - Camaret-sur-Mer (CAM)
- Rotating vessel pin oriented to true heading (`headingDegrees`) with speed tooltip and animated pulse halo when underway.
- Dash-array polyline displaying the voyage track path.
- Persistent honesty badge overlay: *"Historical replay mode (simulated live)"*.
- Protected headless / test fallback ensuring tests run reliably in jsdom.

### C. Live Telemetry Panel (`frontend/src/components/tracking/LiveTelemetryPanel.tsx`)
- Primary vessel header with MMSI badge, route indicator, and sailing status chip.
- 4-column metric grid:
  1. Speed over Ground: Formatted in knots (`kts`).
  2. Course over Ground: Heading degrees with compass indicator.
  3. Predicted Delay: Estimated minutes delay with Ridge model confidence intervals (`CI [P10, P90] min`).
  4. Estimated Arrival: Calculated ETA time (`HH:MM`).
- Real-time GPS coordinate bar (`48.XXXX° N, X.XXXX° W`).
- Honest disclosure footer displaying data source (`HISTORICAL_REPLAY`) and Ridge model weights SHA-256.
- Reconnection action and offline warning when simulation daemon is offline (503 RFC 7807 ProblemDetail).

### D. Public Voyage Sharing (`frontend/src/components/tracking/ShareModal.tsx`, `frontend/src/pages/PublicTrackPage.tsx`)
- **`ShareModal.tsx`**: Requests expiring URL-safe tracking tokens via `POST /api/v1/departures/{id}/share` and copies link to clipboard with visual feedback.
- **`PublicTrackPage.tsx`**: Dedicated unauthenticated tracking route (`/track/:token`) allowing passengers, friends, and families to follow sailings live without logging in.

### E. Fleet Tracking View (`frontend/src/pages/TrackingPage.tsx`)
- Complete integration connecting the initial snapshot `GET /api/v1/departures/{id}/live`, route path `GET /api/v1/departures/{id}/track`, and real-time Server-Sent Events (SSE) `GET /api/v1/departures/{id}/stream`.
- Quick-switch departure tabs for active Brittany corridors (Brest $\leftrightarrow$ Le Conquet, Le Conquet $\leftrightarrow$ Ouessant, Audierne $\leftrightarrow$ Sein, Le Conquet $\leftrightarrow$ Molène).

---

## 3. Test Suites & Verification

### Test Counts
| Suite | Passed | Failed | Skipped | Time |
| :--- | :---: | :---: | :---: | :---: |
| **Python ML Platform (`pytest`)** | 115 | 0 | 0 | ~140s |
| **Java Spring Boot Backend (`mvn test`)** | 34 | 0 | 0 | ~24s |
| **React Vitest Frontend (`vitest run`)** | 50 | 0 | 0 | ~3.2s |
| **Total Test Count** | **199** | **0** | **0** | **~167s** |

### Verified Frontend Test Cases (16 Suites / 50 Tests)
- `LiveTelemetryPanel.test.tsx` (4 tests): Speed, heading, GPS coordinates, delay predictions with CI, 503 error state with reconnect action, share button callback.
- `ShareModal.test.tsx` (2 tests): Modal presentation, URL generation, clipboard copying.
- `FerryMap.test.tsx` (1 test): Container mounting, accessible labels, honesty badge overlay.
- `TrackingPage.test.tsx` (2 tests): Page header, honesty disclosure, departure selector tabs, tab switching.
- `PublicTrackPage.test.tsx` (1 test): Shared voyage view for valid public token.
- Plus all 40 tests from Phase 6 (`Button`, `Card`, `Badge`, `StatusChip`, `Input`, `Select`, `Modal`, `Alert`, `Navbar`, `Footer`, `App`).

### Production Build Verification
- `npm run build` executed with TypeScript type-checking (`tsc -b`) and Vite production bundler:
  - 1,630 modules transformed.
  - Production bundles generated cleanly in `dist/` without errors.

---

## 4. Deviations & Observations

- No design system or behavioral deviations.
- Map and telemetry views strictly observe WCAG 2.1 AA contrast standards and clear honesty badges disclosing historical replay mode.

---

## 5. Gate Checklist

- [x] Leaflet map centered on Iroise Sea with 7 Penn ar Bed port markers
- [x] Rotating vessel SVG marker indicating true heading and speed
- [x] Track polyline rendering historical and current sailing path
- [x] Live telemetry panel displaying knots, heading, GPS, ETA, delay minutes, and confidence intervals
- [x] Honest data labeling (`HISTORICAL_REPLAY`, Ridge model SHA-256) preserved
- [x] 1 Hz SSE stream integrated with offline 503 handling and reconnect action
- [x] ShareModal and public tracking page (`/track/:token`) implemented
- [x] 50 Vitest frontend tests passing (10 new Phase 7 tests + 40 earlier tests)
- [x] Production build (`npm run build`) compiles cleanly
- [x] Full regression passed across Python (115), Java (34), and Frontend (50) = 199 tests
- [x] `docs/phases/phase-07-report.md` written
