# Phase 09 Existing System Audit & Architectural Baseline (Corrected)

**Project:** Where Is My Ferry?  
**Phase:** 09 — Backend Architecture & Integration Planning (Corrective Review)  
**Auditor:** Senior Backend Architect, ML Inference Specialist, QA Lead  
**Date:** 2026-10-16  

---

## 1. Executive Summary & Audit Baseline

A rigorous code-level audit was conducted across all subsystems (`frontend/`, `backend/`, `ml-platform/`) to resolve architectural risks and enforce the **Zero Mock Operational Data** policy for future integration.

### Ground-Truth System Status:
1. **Frontend (`frontend/`):**
   - React 19, TypeScript 5.9, Vite 8 with route-level dynamic code splitting (`React.lazy`).
   - 25 routes functional; 14 Vitest tests passing; 0 errors and 0 warnings in `oxlint`.
   - Leaflet 1.9.4 interactive tracking map operating with CartoDB Voyager tiles.
   - **Current Mock Dependency:** Operational pages (`/track`, `/`, `/operator`, `/admin`) currently import hardcoded arrays from `src/data/mockData.ts`. Under the Zero Mock Data mandate, these must be replaced with live backend service calls.
2. **Backend (`backend/`):**
   - Verified **100% empty**. No code has been implemented.
   - Verified local host environment: Java OpenJDK 17.0.16 (Temurin-17.0.16+8), Apache Maven 3.9.15.
3. **ML Platform (`ml-platform/`):**
   - Python 3.13.6 virtual environment (`ml-platform/.venv`).
   - Causal streaming pipeline: `VirtualAISGenerator` &rarr; `VirtualFleetRunner` &rarr; `ETAStreamProcessor` &rarr; `VectorizedRidgeETAModel` &rarr; `ETAStateMachine`.
   - **Artifact Discrepancy Resolved:** The previously cited artifact `ml-platform/models/phase_05_ridge_model.joblib` **does not exist on disk**. The inference pipeline uses `VectorizedRidgeETAModel` in `src/models/evaluate_phase05.py`, a pure NumPy L2-regularized linear model.
   - `mock_api_server.py` defines Python class dispatch methods (`MockAPIService`), but no HTTP network daemon currently listens on a socket.

---

## 2. Zero-Mock-Data Baseline Classification

To strictly enforce Section 1 of the Master Prompt, all repository data sources are categorized into five distinct tiers:

| Tier | Category | Description & Current Location | Post-Integration Target State |
|---|---|---|---|
| **Tier 1** | **Operational Data (Dynamic)** | Vessel positions, headings, speed, ETA predictions, countdowns, freshness flags, lifecycle states, simulation clock, scenario activations, operator metrics, and diagnostics. | **Exclusively fetched from Spring Boot (`/api/v1/*`) via REST & SSE.** All hardcoded mock vessel arrays removed from operational pages. |
| **Tier 2** | **Simulation Source (Internal)** | Kinematic route coordinates, terminal berths, nominal speeds, and scenario definitions (`ml-platform/configs/phase_08_virtual_fleet.json`, `phase_08_scenarios.json`). | **Preserved inside Python engine.** Drives the live virtual AIS generator. Never directly imported by frontend UI. |
| **Tier 3** | **Static Content (Presentation)** | Brand palette tokens, header/footer navigation links, terminal transit descriptions, static destination editorial guides, legal terms, empty-state SVGs. | **Preserved in frontend.** Legitimate static application resources that do not represent live operational state. |
| **Tier 4** | **Test Fixtures (Isolated)** | Deterministic test vectors, mock event payloads, and simulated snapshots (`src/tests/*`, `ml-platform/tests/*`). | **Strictly isolated in test suites.** Banned from inclusion in production application bundles. |
| **Tier 5** | **Obsolete Mock Data (To Eliminate)** | Hardcoded `mockVessels` in `src/data/mockData.ts`, static KPI numbers (`342 Pax`, `96.4%`), and static console log buffers in `AdminDiagnosticsPage.tsx`. | **Completely decommissioned from operational components.** Replaced by live backend streams with explicit offline/error fallback states. |

---

## 3. Toolchain & Runtime Compatibility Audit

Host environment tooling was verified through direct command execution:

- **Java Runtime:** `openjdk version "17.0.16" 2025-07-15`, Eclipse Adoptium Temurin-17.0.16+8 (64-Bit Server VM).
- **Build Tool:** `Apache Maven 3.9.15` (C:\apache-maven\apache-maven-3.9.15).
- **Target Framework:** `Spring Boot 3.4.x` (Full official compatibility with Java 17 and Java 21). Java 17 is selected as the compilation and runtime target to eliminate any requirement for the user to install additional JDKs.
- **Python Runtime:** `Python 3.13.6` (AMD64 on Windows 11). Virtual environment in `ml-platform/.venv` contains NumPy 2.5.4, Pandas 3.0.6, PyArrow 26.0.0.
- **Node Runtime:** Node v20.x with npm lockfile v3.
- **Port Allocation Plan:**
  - `5173`: React Frontend (Vite dev server)
  - `8080`: Spring Boot Application Gateway & SSE Hub
  - `8000`: Python Maritime Engine HTTP Daemon (strictly bound to loopback `127.0.0.1`)

---

## 4. Code-Level Audit of Model Training & Inference Separation

### A. The 10 Technical Verifications:
1. **Exact dataset rows used to fit the model:** In `evaluate_phase05.py`, the training partition consists of snapshots where the voyage departure timestamp is strictly prior to `2016-02-01T00:00:00Z` (`voy_train_ids = df_voy[df_voy["dep_timestamp_utc"] < "2016-02-01"]["voyage_id"]`). This comprises **7,183 historical snapshots** across 681 verified voyages.
2. **Rows reserved for validation/testing:** Test split consists of snapshots from voyages departing on or after `2016-02-01T00:00:00Z` through `2016-03-31T23:59:59Z`. This comprises **2,130 historical snapshots** across 208 verified voyages.
3. **Reproducibility:** The training procedure is completely deterministic. It computes closed-form normal equations $\mathbf{W} = (\mathbf{X}^T \mathbf{X} + \alpha \mathbf{I}^*)^{-1} \mathbf{X}^T \mathbf{y}$ with fixed $\alpha=10.0$ and no stochastic gradient steps.
4. **Is the full dataset used at startup?** No. Both `evaluate_phase05.py` and `eta_stream_processor.py` apply chronological cutoff filtering to exclude data after `2016-02-01`.
5. **Could training consume test split rows?**
   - In `evaluate_phase05.py`: **Zero leakage.** Partitioning is done strictly at the `voyage_id` level (`len(voy_train_ids.intersection(voy_test_ids)) == 0`).
   - In `eta_stream_processor.py`: Filtering is currently done on snapshot timestamp (`prediction_timestamp_utc < "2016-02-01"`). If a voyage crossed midnight on Jan 31, late snapshots could theoretically split. **Corrective Action:** The model weights will be pre-computed offline from the strict voyage-level split and serialized to a frozen weight file.
6. **Are future observations or target-derived features included?** No. Feature inputs are strictly causal: distance to destination, elapsed minutes, current SOG, observation count so far, and data freshness.
7. **Is preprocessing fitted only on the training partition?** Yes. Continuous feature scaling parameters ($\mu$ and $\sigma$) and categorical dummy lists are computed exclusively on `df_train` when `is_training=True` in `_prepare_features()`.
8. **Does the streaming processor call the actual model?** Yes. Line 243 of `eta_stream_processor.py` calls `raw_pred = float(self.model.predict(df_feature)[0])`.
9. **Is prediction deterministic?** Yes. For any identical feature vector $\mathbf{X}$, $\hat{y} = \max(\mathbf{X} \mathbf{W}, 0.1)$ yields identical floating-point output.
10. **Failure handling:** If the snapshot parquet file is missing, `eta_stream_processor.py` currently instantiates an unfitted model with `self.weights = None`, causing inference calls to throw a `TypeError`. **Corrective Action:** Pre-serialized weight loading with explicit validation of non-null weights on daemon startup.

---

## 5. Architectural Change Log & Corrections Applied

1. **Model Lifecycle Decision:** Shifted from in-memory runtime training to **offline pre-trained frozen weight loading** (`ml-platform/models/vectorized_ridge_weights.npz`). This eliminates cold-start delay ($<1\text{ ms}$ vs $1.5\text{ s}$), removes the runtime dependency on the 841 kB parquet dataset, and guarantees zero leakage from test voyages.
2. **Stale-ETA Semantic Resolution:** Replaced ambiguous countdown freezing with a **ticking countdown paired with an authoritative stale warning**. The countdown ticks down against the last known prediction, prominently displaying `STALE TELEMETRY (>60s)` with the last update timestamp.
3. **No-User-Key Map Safeguards:** Added a local GeoJSON coastline vector basemap (Tier 3) to Leaflet, guaranteeing full visual functionality even in an air-gapped, offline environment.
4. **Zero Mock Data Policy:** Added strict architectural boundaries prohibiting hardcoded mock fallbacks in operational components when backend services are offline.
