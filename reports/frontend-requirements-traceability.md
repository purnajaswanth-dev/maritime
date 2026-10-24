# Requirements Traceability Matrix — Where Is My Ferry?

**Date:** 2026-10-16  
**Auditor:** Senior Frontend Architect & Maritime Product Auditor  
**Scope:** Frontend Design & Local Prototype Verification  

---

## Traceability Matrix

| Req ID | Description | Expected Behavior | Implementation Location | Verification Method | Status | Severity / User Impact |
|---|---|---|---|---|---|---|
| **REQ-A01** | Global Navigation Shell | Header with logo, public nav items, auth links, active states | `src/components/navigation/Header.tsx` | Browser subagent inspection & route clicks | **PASS** | None |
| **REQ-A02** | Simulation Labeling | Persistent demo/simulation warning banner visible across all pages | `src/components/ui/SimulationBanner.tsx` | Component inspection on 10+ routes | **PASS** | None |
| **REQ-A03** | 404 Fallback | Non-existent URLs resolve to custom Not Found screen | `src/pages/support/NotFoundPage.tsx` | Route verification in `sitemapRoutes.test.ts` & direct URL | **PASS** | None |
| **REQ-A04** | Client-side Auth presentation | Login/Register demonstration pages | `src/pages/account/LoginPage.tsx` | Direct browser navigation and submission | **PASS** | Demo-only (real auth requires future backend) |
| **REQ-B01** | Maritime Hero Section | Clear value proposition, visual sea background | `src/pages/public/HomePage.tsx` | Desktop & mobile browser rendering | **PASS** | None |
| **REQ-B02** | Ferry Search Interface | Origin, destination, date, passenger selectors | `src/components/search/FerrySearchBox.tsx` | Form submission to `/search` query params | **PASS** | None |
| **REQ-B03** | Live Fleet Preview | Preview cards showing virtual vessels and predicted arrival | `src/pages/public/HomePage.tsx` | Render check on homepage | **PASS** | None |
| **REQ-C01** | Search Results & Filtering | Filter by operator, departure time, sorting by price/duration | `src/pages/public/SearchResultsPage.tsx` | Filter buttons, search param reactivity | **PASS** | None |
| **REQ-C02** | Fare Display Consistency | EUR currency symbols, transparent fare tiers (Standard/Flexi) | `src/pages/public/SearchResultsPage.tsx` | `bookingWorkflow.test.ts` & browser test | **PASS** | None |
| **REQ-D01** | Journey Detail Timeline | Departure, arrival, terminal, sailing duration breakdown | `src/pages/public/JourneyDetailPage.tsx` | Browser inspection at `/journeys/J-BRE-OUE-01` | **PASS** | None |
| **REQ-D02** | Ticket Category Selection | Standard vs Flexi fare options with luggage and refund rules | `src/pages/public/JourneyDetailPage.tsx` | Clickable tier selection updating CTA link | **PASS** | None |
| **REQ-E01** | Destination & Port Discovery | Guides for Ouessant, Molène, Brest, Le Conquet | `src/pages/public/DestinationsPage.tsx`, `PortsPage.tsx` | Browser inspection of cards, descriptions, transit tags | **PASS** | None |
| **REQ-T01** | Leaflet Fleet Map | Interactive map with vessel icons, headings, and corridors | `src/components/tracking/FleetMap.tsx` | Interactive browser click, marker selection | **PASS** | None |
| **REQ-T02** | Authoritative ETA Countdown | Real-time countdown to predicted UTC timestamp | `src/components/tracking/VesselDetailPanel.tsx` | Browser countdown verification & Vitest test | **PASS** | None |
| **REQ-T03** | Uncertainty Range Qualification | Display ± minutes without unsubstantiated "95% CI" claim | `src/components/tracking/VesselDetailPanel.tsx` | Code audit & browser panel check | **PASS** (Remediated) | Corrected from uncalibrated 95% CI |
| **REQ-T04** | Arrival & Stale State Transitions | Clean visual badges for ARRIVED, IN_TRANSIT, STALE | `src/components/tracking/VesselDetailPanel.tsx` | `etaUncertaintyAndSimulation.test.ts` | **PASS** | None |
| **REQ-BK01** | Multi-step Booking Flow | 3-step checkout: Passenger info, Addons, Demo Payment | `src/pages/booking/BookingFlowPage.tsx` | Browser subagent end-to-end execution | **PASS** | None |
| **REQ-BK02** | Deterministic Fare Arithmetic | Addons (bicycles, pets) and flex guarantee calculated accurately | `src/pages/booking/BookingFlowPage.tsx` | `bookingWorkflow.test.ts` (14 assertions) | **PASS** | None |
| **REQ-BK03** | Demo Payment Guard | No real payment gateway or cards accepted; zero charge warning | `src/pages/booking/BookingFlowPage.tsx` | Step 3 form inspection and submit behavior | **PASS** | None |
| **REQ-BK04** | Digital Boarding Pass | Printable boarding pass with simulated barcode/turnstile code | `src/pages/booking/BookingFlowPage.tsx`, `TripDetailPage.tsx` | Browser inspection, print media CSS check | **PASS** (Remediated) | Added `DEMO — NOT VALID FOR TRAVEL` |
| **REQ-OP01** | Operator Dashboard Metrics | KPI summary cards, active fleet status table | `src/pages/operator/OperatorDashboardPage.tsx` | Browser audit at `/operator` | **PASS** (Remediated) | Qualified on-time metric as simulated |
| **REQ-OP02** | Passenger Manifest | Check-in status table and export feature | `src/pages/operator/OperatorManifestPage.tsx` | Browser audit at `/operator/manifest` | **PASS** (Remediated) | Qualified SOLAS claim as demonstration draft |
| **REQ-OP03** | Disruption Posting | Weather and tidal advisory dispatch tool | `src/pages/operator/OperatorDisruptionsPage.tsx` | Browser audit at `/operator/disruptions` | **PASS** | None |
| **REQ-AD01** | Simulation Controls | Speed multipliers (1x, 2x, 5x, 10x), scenario selector | `src/pages/admin/AdminSimulationControlsPage.tsx` | Interactive button clicks in browser subagent | **PASS** | None |
| **REQ-AD02** | Streaming Event Diagnostics | Event log window adhering to Phase 07 streaming schema | `src/pages/admin/AdminDiagnosticsPage.tsx` | Interactive level filter toolbar | **PASS** | None |
| **REQ-DS01** | Design System Tokens | Deep Ocean (`#071B2B`), Electric Teal (`#14B8A6`), Arctic White | `src/index.css`, `frontend-design-system.md` | `designTokens.test.ts` & visual inspection | **PASS** | None |
| **REQ-AC01** | Responsive Viewports | Seamless layout from Mobile (375px) to Desktop (1440px) | All component CSS and container grids | Browser subagent multi-viewport testing | **PASS** | None |
| **REQ-BE01** | Real Backend Integration | Spring Boot server, database persistence, external AIS feed | Future phases | Scope check | **NOT YET IMPLEMENTED — BACKEND DEPENDENCY** | Expected |

---

## Summary of Matrix Results
- **PASS:** 27 requirements
- **PARTIAL / REMEDIATED TO PASS:** 4 requirements (Uncertainty CI qualification, Boarding pass disclaimers, Operator on-time qualifier, Manifest draft qualification)
- **NOT YET IMPLEMENTED (BACKEND DEPENDENCY):** 1 requirement (Spring Boot backend & real AIS telemetry)
- **FAIL:** 0
- **BLOCKED:** 0
