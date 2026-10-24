# Frontend Design Preflight & Workspace Audit Report

**Project:** Where Is My Ferry?  
**Phase:** Complete Professional Frontend Design & Local Implementation  
**Date:** 2026-10-16  
**Auditor:** Senior Product Designer, UI/UX Architect, and Senior React Frontend Developer  
**Status:** **AUDIT PASSED — READY FOR INITIALIZATION**  

---

## 1. Objective of Audit

In strict compliance with Section 3 of the Master Execution Prompt, this preflight audit inspects the workspace, records the state of existing frontend and backend directories, verifies existing ML and streaming assets, and establishes the technical blueprint for the design system and application implementation.

---

## 2. Directory & Baseline Inspection

### Root Directory State
- `c:\Users\sunka\OneDrive\coding\where-is-my-ferry\`:
  - `backend/`: **Empty directory confirmed.**
  - `frontend/`: **Empty directory confirmed.** (No existing React, Vite, or package files).
  - `ml-platform/`: Contains completed Phases 00–08 artifacts, models, streaming engines, and test suites.
  - `MEMORY.md`: Root architectural memory and decision log.
  - `.gitignore`: Configured for python, node, and IDE artifacts.

### Development Environment
- **Node.js:** `v24.18.1` (Verified via `node -v`)
- **npm:** `11.16.0` (Verified via `npm -v`)
- **OS:** Windows (PowerShell environment)

---

## 3. Review of Existing ML & Streaming Contracts

From Phase 07 and Phase 08 reports and code artifacts:
- **Corridors & Terminals:** Calibrated for Brittany / Iroise Sea maritime network:
  - *Brest* (Gare Maritime): `48.3811° N, -4.4857° W`
  - *Le Conquet* (Port du Conquet): `48.3596° N, -4.7818° W`
  - *Ouessant Stiff* (Port du Stiff): `48.4691° N, -5.0545° W`
  - *Molène* (Port de Molène): `48.4022° N, -4.9565° W`
  - *Audierne* (Sainte-Evette): `48.0061° N, -4.5524° W`
  - *Île de Sein* (Port de l'Île de Sein): `48.0390° N, -4.8486° W`
  - *Camaret* (Port de Camaret-sur-Mer): `48.2780° N, -4.5940° W`
- **Virtual Fleet:**
  - `V-FROMVEUR-SIM` (MMSI `999000001`): *SIM_FROMVEUR_EXPRESS* (Brest - Le Conquet)
  - `V-AZENOR-SIM` (MMSI `999000002`): *SIM_AZENOR_VOYAGER* (Le Conquet - Brest)
  - `V-OUESSANT-SIM` (MMSI `999000003`): *SIM_IROISE_STAR* (Brest - Ouessant Stiff)
  - `V-SEIN-SIM` (MMSI `999000004`): *SIM_SEIN_SHUTTLE* (Audierne - Île de Sein)
- **Lifecycle ETA States:**
  1. `ESTIMATING`: Normal transit countdown.
  2. `DELAYED_OR_UNCERTAIN`: Vessel holding, reduced speed in open water, or unexpected route deviation.
  3. `STALE_DATA`: Telemetry gap exceeding 600s.
  4. `ARRIVAL_PENDING_CONFIRMATION`: Vessel within 1,000m of destination terminal.
  5. `ARRIVED`: Vessel docked within berth (<250m, <1.0 kt); countdown locks to 0.0m.
  6. `ETA_UNAVAILABLE`: Telemetry dropped before terminal approach.
- **Authoritative Time & Countdown Anchoring:**
  - Countdown presentation is strictly derived from `predicted_arrival_timestamp_utc` and reference clock:
    $$\text{remaining\_minutes} = \max\left(0.0, \frac{T_{\text{predicted\_arrival}} - T_{\text{current}}}{60}\right)$$
  - Never repeatedly subtracts from a cached number.
  - Latched `ARRIVED` state cannot be undone by late packets.

---

## 4. Planned Frontend Architecture & Tech Stack

Since `frontend/` is currently an empty directory, we will initialize a clean, modern, robust web application:
- **Framework & Build:** React 18 / 19 + TypeScript + Vite.
- **Routing:** `react-router-dom` (v6) for declarative, full sitemap routing (Public, Booking, Account, Operator, Admin).
- **Styling & Design Tokens:**
  - Tailwind CSS + Custom CSS Variables for the mandatory palette (`Deep Ocean`, `Ocean Blue`, `Electric Teal`, `Arctic White`, `Sea Mist`, `Bright Sky Blue`, `Coral Orange`, `Success Green`, `Warning Amber`, `Error Red`).
  - Typography: Inter with clean tabular numbers (`font-mono` / tabular-nums for ETAs, prices, times).
- **Icons:** `lucide-react` for consistent, maritime and UI icons.
- **Interactive Mapping:** `leaflet` & `react-leaflet` with CartoDB Positron / OSM tiles for token-free, reliable, high-performance maritime vessel tracking.
- **Date & Time:** Native date utilities with ISO UTC parsing.
- **Testing:** Vitest / React Testing Library.

---

## 5. Planned File Changes & Delivery Strategy

1. Initialize Vite React TypeScript project in `frontend/`.
2. Configure Tailwind CSS with the mandatory design tokens.
3. Build the core design system and reusable UI components (`Button`, `Card`, `Badge`, `Input`, `Select`, `Dialog`, `Table`, `Tabs`, `Toast`, etc.).
4. Implement centralized, typed mock maritime data (`ports`, `routes`, `schedules`, `vessels`, `fares`, `demoBookings`).
5. Build the complete application sitemap across 4 major workspaces:
   - **Public Passenger Web:** Home, Search Results, Journey Details, Destinations, Destination Detail, Ports, Port Detail.
   - **Virtual Vessel Tracking:** Interactive Fleet Map, Vessel Detail with real-time countdown, state badges, and simulation disclosure.
   - **E-Commerce & Passenger Account:** Multi-step booking checkout (Journey -> Fare -> Passenger info -> Addons -> Review -> Simulated Checkout -> Confirmation), Booking History, Ticket View, Profile, Saved Routes.
   - **Operator & Admin Portals:**
     - Operator Dashboard (`/operator`): Fleet Overview, Vessel Profiles, Route/Schedule Management, Passenger Manifest, Service Disruptions.
     - Platform Admin (`/admin`): System Overview, Operator Verification, Port & Route Registry, Simulation Controls, System Diagnostics, Audit Logs.
   - **Shared Support:** Help Centre, FAQs, Boarding Instructions, Terms, Privacy Policy, 404 Not Found, Unauthorized.
6. Verify responsive layouts (Desktop, Tablet, Mobile).
7. Execute automated tests, type checks, and production build checks.
8. Deliver detailed documentation and update `MEMORY.md`.
