# Frontend Audit Baseline Report — Where Is My Ferry?

**Date:** 2026-10-16  
**Project:** Where Is My Ferry?  
**Audit Scope:** Frontend design and local prototype implementation validation only  
**Auditor:** Senior Frontend Architect, QA Automation Specialist, Maritime Product Designer  

---

## 1. Executive Summary & Inventory Baseline

An independent, rigorous audit was conducted on the existing frontend codebase in `frontend/`. Direct verification of the repository files, build pipelines, package configurations, lint rules, and test suites was performed without relying on unverified claims from previous phase reports.

### Environment & Tooling Baseline
- **Node / Runtime:** Node.js v20.x on Windows
- **Frontend Framework:** React 19 (`react@^19.2.0`, `react-dom@^19.2.0`, `react-router-dom@^7.13.0`)
- **Build System:** Vite 8 (`vite@^8.3.4`, `@vitejs/plugin-react@^6.1.1`)
- **Language / Typing:** TypeScript 5.9 (`typescript@~5.9.3`) with `strict: true` and DOM/ES2022 lib
- **Styling:** Tailwind CSS v4 (`@tailwindcss/vite@^4.2.1`, `tailwindcss@^4.2.1`) + Vanilla CSS custom variables (`src/index.css`)
- **Map & Geospatial:** Leaflet 1.9 (`leaflet@^1.9.4`, `@types/leaflet@^1.9.16`)
- **Iconography:** Lucide React (`lucide-react@^1.16.0`)
- **Unit / Component Test Runner:** Vitest 5 (`vitest@^5.0.5`)
- **Linter:** Oxlint (`oxlint@^1.57.0`)

---

## 2. Baseline Status Before Remediation

| Metric / Check | Initial Audit Finding | Status |
|---|---|---|
| **Git Working Tree** | Clean working tree; `backend/` verified empty; Python ML platform untouched | PASS |
| **Route Inventory** | 25 distinct routes declared in `src/App.tsx` | PASS |
| **Initial Production Build** | `tsc -b && vite build` built 1 monolithic bundle: JS 628.95 kB, CSS 66.79 kB | WARNING (Chunk size >500 kB) |
| **Initial Linter (`oxlint`)** | 0 errors, 64 warnings (mostly unused imports, 1 setState in effect, 3 impure Date.now() calls) | ATTENTION NEEDED |
| **Initial Vitest Tests** | 3 test files, 7 tests passed (100% pass) in 160ms | SHALLOW (mostly testing array lengths) |
| **Dev Server Status** | Running at `http://localhost:5173/` | PASS |
| **AIS API / Real Payment Gateways** | Zero external dependencies found; completely mock-isolated | PASS |

---

## 3. Directory Structure of Frontend
```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── index.css
│   ├── components/
│   │   ├── navigation/ (Header.tsx, Footer.tsx, OperatorSidebar.tsx, AdminHeader.tsx)
│   │   ├── search/ (FerrySearchBox.tsx)
│   │   ├── tracking/ (FleetMap.tsx, VesselDetailPanel.tsx)
│   │   └── ui/ (Button.tsx, Card.tsx, Badge.tsx, Input.tsx, Select.tsx, Tabs.tsx, SimulationBanner.tsx)
│   ├── data/ (mockData.ts)
│   ├── pages/
│   │   ├── public/ (HomePage, SearchResultsPage, JourneyDetailPage, DestinationsPage, DestinationDetailPage, PortsPage, PortDetailPage)
│   │   ├── tracking/ (TrackingPage)
│   │   ├── booking/ (BookingFlowPage)
│   │   ├── account/ (LoginPage, RegisterPage, AccountOverviewPage, TripsHistoryPage, TripDetailPage)
│   │   ├── operator/ (OperatorDashboardPage, OperatorFleetPage, OperatorSchedulesPage, OperatorManifestPage, OperatorDisruptionsPage)
│   │   ├── admin/ (AdminDashboardPage, AdminSimulationControlsPage, AdminRoutesPage, AdminDiagnosticsPage)
│   │   └── support/ (HelpPage, TermsPage, PrivacyPage, NotFoundPage, UnauthorizedPage)
│   ├── tests/ (dataContract.test.ts, designTokens.test.ts, sitemapRoutes.test.ts)
│   └── types/ (ferry.ts)
```

---

## 4. Initial Defect Observations
1. **Uncalibrated Confidence Claims (P1):** In `VesselDetailPanel.tsx`, `±2.4 min (95% CI)` was hardcoded based on synthetic demo fixtures without a validated calibration study.
2. **Boarding Pass Non-Operational Disclaimers (P1):** While simulation badges were rendered, the digital boarding pass lacked an unmistakable `DEMO — NOT VALID FOR TRAVEL` notice, and print stylesheets did not suppress screen navigation or footers.
3. **Operational Performance & Regulatory Claims (P2):**
   - In `OperatorDashboardPage.tsx`, "96.4% on-time" was presented as an operational metric without a demonstration qualifier.
   - In `OperatorManifestPage.tsx`, the export button was labeled "Export SOLAS Manifest" without statutory qualification.
4. **Monolithic Bundle Warning (P3):** Single JS bundle was 629 kB, triggering Vite chunk size warnings.
5. **Impure Render Functions (P3):** `Date.now()` and `new Date().getFullYear()` called during component render in `HomePage.tsx`, `OperatorDashboardPage.tsx`, and `Footer.tsx`.
