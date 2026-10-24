# Where Is My Ferry? — Capstone Final Report

**Project Title:** Where Is My Ferry? (Où est mon ferry ?)  
**Network:** Iroise Sea Maritime Transit Network (Finistère, Brittany, France)  
**Date:** 2026-10-24  
**Author:** Antigravity Full-Stack & ML Engineering Agent  
**Build Scope:** 13 Gated Phases (Phase 00 to Phase 12)  
**Overall Status:** ALL 13 PHASE GATES PASSED (100% COMPLETE)  

---

## 1. Executive Summary

"Where Is My Ferry?" is an end-to-end maritime transit platform serving passengers, dispatchers, captains, auditors, and administrators across the Iroise Sea (Penn ar Bed network: Brest, Le Conquet, Molène, Ouessant Le Stiff, Audierne, Île de Sein, Camaret-sur-Mer). 

The platform integrates three production tiers:
1. **Python 3.11 ML & Simulation Daemon (`ml-platform/`, Port 8000)**:
   - High-fidelity physical simulation engine modeling currents, tidal streams in the Passage du Fromveur, sea state, and vessel kinematics.
   - 22 deterministic scenarios including adversarial weather and AIS blackout faults.
   - Vectorized Ridge & LightGBM ETA regressors trained on historical AIS observations.
   - Calibrated Monte Carlo uncertainty intervals [p10, p90] and SHA-256 weight integrity verification.
2. **Spring Boot 3.4.3 Backend (`backend/`, Port 8080)**:
   - Java 17 enterprise service layer with Spring Data JPA and PostgreSQL 16 persistence.
   - Real-time Server-Sent Events (SSE) telemetry stream (`/api/v1/departures/{id}/stream`).
   - Booking engine with VAT breakdown, QR barcode generation, and a strict $\ge 24\text{h}$ passenger cancellation policy.
   - Append-only immutable audit trail and administrative maintenance mode lockdown.
   - OWASP security headers, JWT role-based access control, and MDC correlation tracing.
3. **React 19 + TypeScript + Vite 6 Frontend (`frontend/`, Port 5173 / Port 80)**:
   - WCAG 2.1 AA accessible design system with high-contrast tokens and dark mode.
   - Interactive Leaflet maritime map with vessel rotation, wake trails, and port geofences.
   - Three-step passenger booking wizard with seat selection and QR boarding pass download.
   - 5-tab Admin Control Portal (Overview, Simulation Controls, ML Diagnostics, Users, Audit Trail).
   - Progressive Web App (PWA) with offline fallback service worker.

---

## 2. 13-Phase Build Audit Summary

| Phase | Title | Key Milestones & Capabilities Delivered | Gate Status |
| :---: | :--- | :--- | :---: |
| **00** | **Environment Audit** | Repository hygiene, toolchain verification, baseline test discovery | **PASSED** |
| **01** | **Dataset & Schedule** | GTFS static schedules, Iroise Sea terminals, tidal currents, vessel specs | **PASSED** |
| **02** | **Backend Foundation** | Flyway migrations, JPA entities, JWT authentication, demo seeders | **PASSED** |
| **03** | **Simulation Engine** | 22 maritime scenarios, playback speed (1x-50x), AIS telemetry generator | **PASSED** |
| **04** | **ML Inference Platform** | LightGBM & Ridge ETA models, Monte Carlo envelope, SHA-256 integrity check | **PASSED** |
| **05** | **Real-Time Integration** | SSE departure streams, public share tokens, fallback to STALE_DATA | **PASSED** |
| **06** | **Frontend Foundation** | WCAG 2.1 AA tokens, responsive layout, reusable UI component suite | **PASSED** |
| **07** | **Interactive Live Map** | Leaflet Iroise map, rotating vessel SVGs, polyline wake, honesty badges | **PASSED** |
| **08** | **Timetable & Catalog** | Multi-corridor timetable explorer, port guide, interactive tariff estimator | **PASSED** |
| **09** | **Booking Engine** | 3-step checkout wizard, seat assignments, QR boarding passes, cancellations | **PASSED** |
| **10** | **Admin Governance** | 5-tab portal, scenario injector, ML diagnostics, audit trail, maintenance lock | **PASSED** |
| **11** | **Resilience & Hardening**| OWASP security headers, MDC correlation IDs, chaos script, PWA worker, runbook | **PASSED** |
| **12** | **Acceptance Capstone** | 7-step full-stack maritime passenger & ops verification script | **PASSED** |

---

## 3. Comprehensive Test Verification Metrics

Every phase was gated by regression testing. Across the 13 phases, the automated test suite expanded from 156 initial tests to **244 total tests**, with zero test deletions or artificial passes.

```
======================================================================
         FINAL MULTI-TIER TEST EXECUTION AUDIT (PHASE 12)
======================================================================
  [1] Python ML Platform (pytest)       : 115 Passed | 0 Failed (100%)
  [2] Java Spring Boot (mvn test)       :  50 Passed | 0 Failed (100%)
  [3] React 19 Frontend (vitest run)     :  79 Passed | 0 Failed (100%)
----------------------------------------------------------------------
  GRAND TOTAL TEST SUITE                : 244 Passed | 0 Regressions
======================================================================
```

---

## 4. Architectural Highlights & Key Design Decisions

1. **Deterministic Scenario Engine:**
   - The simulation engine allows deterministic fault injection across 22 operational scenarios (e.g. #21 *AIS Blackout*, #14 *Engine Failure*, #08 *Gale Force 8*).
   - Calls to `/api/v1/admin/simulation/control` allow dynamic runtime speed scaling from 1x to 50x without memory leaks.
2. **Strict Append-Only Security Logging:**
   - `AuditService` explicitly rejects updates and deletions with `UnsupportedOperationException`, preventing audit trail tampering.
3. **Emergency Maintenance Mode:**
   - A global toggle in the Admin Portal immediately blocks passenger transactions with RFC 7807 `ProblemDetail` (HTTP 503) while maintaining privileged administrator and auditor access.
4. **Honesty Badges:**
   - All passenger-facing views display clear transparency badges (*"Historical replay mode (simulated live)"* or *"Live AIS Feed"*), adhering to ethical AI presentation standards.
5. **Zero-Mock Production Parity:**
   - Live telemetry flows from the physical simulation engine through Spring Boot RestClient adapters to client-side SSE connections.

---

## 5. Deployment & Operational Runbook Reference

- **Native Orchestration:** Run `powershell .\run_all.ps1` from the project root to start all three tiers with automated health-check probing and graceful shutdown on `Ctrl+C`.
- **Container Deployment:** Run `docker compose up -d --build` to deploy the four-container stack (`postgres`, `ml-platform`, `backend`, `frontend`).
- **Operational Runbook:** See [docs/RUNBOOK.md](file:///docs/RUNBOOK.md) for detailed incident response playbooks, disaster recovery procedures, and k6 load testing configurations.
- **Root Documentation:** See [README.md](file:///README.md) for quick start, credentials, and API references.
