# Frontend Defect Register — Where Is My Ferry?

**Date:** 2026-10-16  
**Auditor:** Senior Frontend Architect & QA Automation Specialist  
**Status:** All in-scope identified defects successfully resolved and retested  

---

## Prioritization Key
- **P0 — Critical:** Misleading real-world operational claims, serious security/privacy issues, destructive behavior.
- **P1 — High:** Core search, tracking, ETA, or booking workflow broken; simulated data easily mistaken for real.
- **P2 — Medium:** Secondary functionality, responsive layout, accessibility, or regulatory claims unverified.
- **P3 — Low:** Bundle size, lint warnings, minor polish, dead code.

---

## Defect Inventory & Remediation Log

### DEF-01: Uncalibrated "95% CI" Claim in ETA Panel
- **Defect ID:** `DEF-01`
- **Severity:** **P1 (High)**
- **Description:** `VesselDetailPanel.tsx` displayed `±2.4 min (95% CI)` as an authoritative confidence interval. No statistical calibration study exists for this prototype mock dataset.
- **Reproduction:** Navigate to `/track`, select any vessel, view the Confidence metric in the ETA box.
- **Root Cause:** Hardcoded label `(95% CI)` was copied from previous theoretical reports without empirical calibration.
- **Affected File:** `frontend/src/components/tracking/VesselDetailPanel.tsx`
- **Fix Applied:** Replaced label with `Uncertainty` and formatted value as `±X min (Simulated Range)` with tooltip `Estimated uncertainty range — demonstration only`.
- **Regression Test:** `frontend/src/tests/etaUncertaintyAndSimulation.test.ts`
- **Retest Result:** **PASS** (Verified in Vitest and browser screenshot `tracking_panel_scrolled_1792153133361.png`).
- **Remaining Risk:** None for demonstration frontend. Future ML pipeline calibration study required before claiming calibrated statistical coverage.

---

### DEF-02: Missing Prominent "DEMO — NOT VALID FOR TRAVEL" Notice on Digital Boarding Pass
- **Defect ID:** `DEF-02`
- **Severity:** **P1 (High)**
- **Description:** The confirmation screen and trip detail pages displayed realistic-looking passenger boarding vouchers that could potentially be confused with operational boarding authorizations.
- **Reproduction:** Complete checkout at `/booking/checkout` or visit `/account/bookings/BK-DEMO-9821`.
- **Root Cause:** Disclaimer was confined to a small footnote; no bold warning watermark was present.
- **Affected Files:**
  - `frontend/src/pages/booking/BookingFlowPage.tsx`
  - `frontend/src/pages/account/TripDetailPage.tsx`
  - `frontend/src/index.css`
- **Fix Applied:**
  1. Added bold, amber-tinted banner: `DEMO • NOT VALID FOR TRAVEL • SIMULATION ONLY`.
  2. Added print stylesheet in `src/index.css` (`@media print`) suppressing headers, footers, and interactive action buttons during browser printing.
- **Regression Test:** `frontend/src/tests/bookingWorkflow.test.ts`
- **Retest Result:** **PASS** (Verified in Vitest and browser screenshot `booking_confirmed_1792153224182.png`).
- **Remaining Risk:** None.

---

### DEF-03: Unsubstantiated "SOLAS-Compliant" and "96.4% On-Time" Claims in Operator Portal
- **Defect ID:** `DEF-03`
- **Severity:** **P2 (Medium)**
- **Description:**
  - `OperatorDashboardPage.tsx` displayed "On-Time Arrival (Ridge): 96.4%" implying a verified production operational metric.
  - `OperatorManifestPage.tsx` displayed an "Export SOLAS Manifest" button without statutory certification.
- **Reproduction:** Navigate to `/operator` and `/operator/manifest`.
- **Root Cause:** Unverified regulatory compliance terminology used in mock UI copy.
- **Affected Files:**
  - `frontend/src/pages/operator/OperatorDashboardPage.tsx`
  - `frontend/src/pages/operator/OperatorManifestPage.tsx`
- **Fix Applied:**
  1. Renamed KPI card to `On-Time Performance (Simulated)` with subtext `Demonstration benchmark (historical replay simulation)`.
  2. Changed manifest export button to `Export Manifest (Demonstration Draft)`.
- **Regression Test:** Visual audit and route verification in browser subagent.
- **Retest Result:** **PASS** (Verified in browser screenshot `operator_portal_1792153255679.png`).
- **Remaining Risk:** None.

---

### DEF-04: Monolithic 629 kB JavaScript Bundle Size
- **Defect ID:** `DEF-04`
- **Severity:** **P3 (Low / Performance)**
- **Description:** All 25 routes, including the heavy Leaflet map, were imported synchronously in `src/App.tsx`, producing a single monolithic JS bundle of 628.95 kB (173.06 kB gzip) and triggering Vite build warnings.
- **Reproduction:** Run `npm run build`.
- **Root Cause:** Lack of route-level dynamic imports.
- **Affected File:** `frontend/src/App.tsx`
- **Fix Applied:** Converted all page imports in `src/App.tsx` to `React.lazy()` dynamic imports wrapped in `<Suspense fallback={<PageLoadingFallback />}>`.
- **Outcome:**
  - Main index bundle reduced from **628.95 kB to 286.02 kB** (90.08 kB gzip) — a **54.5% reduction**.
  - Tracking page and Leaflet isolated in separate chunk `TrackingPage-DGqg6HfR.js` (167.69 kB).
  - All page modules split into lightweight chunks (1–15 kB).
  - Vite chunk size warnings completely eliminated.
- **Regression Test:** `npm run build`
- **Retest Result:** **PASS** (Build finished in 546ms with zero warnings).
- **Remaining Risk:** None.

---

### DEF-05: React Impure Functions and Cascading SetState Warnings
- **Defect ID:** `DEF-05`
- **Severity:** **P3 (Code Quality / Linter)**
- **Description:** `oxlint` reported 64 warnings, including `react(purity)` (calling `Date.now()` and `new Date().getFullYear()` during render) and `react(set-state-in-effect)` in `VesselDetailPanel.tsx` and `TrackingPage.tsx`.
- **Reproduction:** Run `npm run lint`.
- **Root Cause:** Setting state synchronously inside `useEffect` on mount/param change, and calling impure date constructors in JSX.
- **Affected Files:**
  - `frontend/src/components/tracking/VesselDetailPanel.tsx`
  - `frontend/src/pages/tracking/TrackingPage.tsx`
  - `frontend/src/pages/public/HomePage.tsx`
  - `frontend/src/pages/operator/OperatorDashboardPage.tsx`
  - `frontend/src/components/navigation/Footer.tsx`
  - Unused imports cleaned across 10 files.
- **Fix Applied:**
  1. Derived `selectedVessel` directly from active vessel ID in `TrackingPage.tsx` without `useEffect` setState.
  2. Initialized countdown state directly from timestamp in `VesselDetailPanel.tsx`.
  3. Made year static in `Footer.tsx` and removed render-time `Date.now()` calls.
  4. Removed all unused lucide icon imports.
- **Regression Test:** `npm run lint`
- **Retest Result:** **PASS** (`Found 0 warnings and 0 errors` across all 53 files in 24ms).
- **Remaining Risk:** None.

---

## Defect Summary Table

| Defect ID | Description | Severity | Status | Verification |
|---|---|---|---|---|
| `DEF-01` | Uncalibrated 95% CI Claim in ETA Panel | P1 | **FIXED** | Vitest + Browser subagent |
| `DEF-02` | Missing DEMO - NOT VALID FOR TRAVEL Banner | P1 | **FIXED** | Vitest + Browser subagent |
| `DEF-03` | SOLAS & Operational Metric Disclaimers | P2 | **FIXED** | Browser subagent |
| `DEF-04` | Monolithic 629 kB Bundle Split | P3 | **FIXED** | `vite build` 546ms, 286 kB |
| `DEF-05` | Linter Impure Renders & Unused Imports | P3 | **FIXED** | `oxlint` 0 warnings / 0 errors |
