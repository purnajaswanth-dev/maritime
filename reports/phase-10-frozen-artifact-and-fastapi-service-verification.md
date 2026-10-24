# Phase 10 Verification Report — Frozen Ridge Artifact & Python FastAPI Service

**Date:** 2026-10-16  
**Auditor / Engineer:** Senior Backend Architect, ML Inference Engineer & Systems QA  
**Status:** COMPLETE — STAGES A & B VERIFIED (87/87 Platform Tests Passing; Strict Stop Condition Enforced Before Spring Boot)

---

## 1. Executive Summary

In accordance with Phase 10 authorization and the strict scope boundary:
1. **Stage A:** Exported and froze the existing Ridge regression ETA model into a versioned, self-contained JSON artifact with SHA-256 weight integrity verification. Numerical equivalence against the original in-memory model achieved a maximum absolute error of **0.0 minutes** ($\le 10^{-6}$ target surpassed). Historical held-out test evaluation demonstrated **MAE = 5.20 minutes** with zero voyage-ID leakage between splits.
2. **Stage B:** Implemented the internal Python FastAPI daemon (`ml-platform/src/simulation/daemon.py`) bound strictly to loopback (`127.0.0.1:8000`). Directly integrated the existing `VirtualAISGenerator`, `ETAStreamProcessor`, `VirtualFleetRunner`, and loaded frozen Ridge artifact. Implemented all 6 documented internal endpoints, returning truthful responses and HTTP 503 errors under failure conditions rather than fabricated mock data.
3. **Strict Stop Condition:** Halted prior to creating any Spring Boot code in `backend/` or modifying the React frontend.

---

## 2. Stage A — Frozen Model Artifact Specification & Equivalence

### 2.1 Artifact Details
- **Path:** `ml-platform/models/vectorized_ridge_model.json`
- **Schema Version:** `1.0.0`
- **Model Type:** `L2_RIDGE_LINEAR` ($\alpha = 10.0$, fit_intercept = True)
- **Artifact SHA-256:** `43c4781ac02ffb599f75e0b5d12cd226a3f236e49b2e559308f37b12fb0e3126`
- **Weights SHA-256:** `e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9`
- **Source Dataset:** `data/processed/phase_05_prediction_snapshots.parquet` (SHA-256: `785d71cbfb9d0e2e5e1e44fecba59b15b497fead8fb0127e4db95a9b7ffab580`)

### 2.2 Feature Ordering and Dimensionality
The model defines a 21-dimensional parameter vector:
- **Bias / Intercept:** 1 weight (`intercept = 34.621213032731885`)
- **Continuous Features (6):** `distance_to_dest_m`, `mean_sog_knots`, `bearing_error_deg`, `speed_ratio`, `corridor_progress_ratio`, `telemetry_age_seconds` (standardized with exact stored means and standard deviations)
- **One-Hot Corridors (10):** `AUDIERNE_ILE_DE_SEIN`, `BREST_LE_CONQUET`, `CAMARET_BREST`, `CONQUET_MOLENE`, `ILE_DE_SEIN_AUDIERNE`, `LE_CONQUET_BREST`, `MOLENE_LE_CONQUET`, `MOLENE_OUESSANT`, `OUESSANT_LE_CONQUET`, `OUESSANT_MOLENE`
- **One-Hot Vessels (4):** `SIM_AZENOR_VOYAGER`, `SIM_FROMVEUR_EXPRESS`, `SIM_IROISE_STAR`, `SIM_SEIN_SHUTTLE`

### 2.3 Dataset Split and Zero-Leakage Verification
- **Chronological Cutoff:** `2016-02-01T00:00:00Z` applied to voyage departure time.
- **Training Partition:** 6,941 causal snapshots across 685 voyages.
- **Test Partition:** 2,372 causal snapshots across 204 voyages.
- **Cross-Split Voyage Overlap:** **0 voyages** (strictly verified via set intersection).

### 2.4 Numerical Equivalence & Benchmark Evaluation
- **Target Equivalence Tolerance:** Absolute prediction error $\le 10^{-6}$ minutes.
- **Measured Discrepancy:**
  - Maximum absolute difference across all 2,372 test predictions: **0.0 minutes**.
  - Mean absolute difference: **0.0 minutes**.
- **Historical Accuracy Reproduction:**
  - In-memory model test MAE: **5.20 minutes**.
  - Frozen artifact test MAE: **5.20 minutes**.

### 2.5 Stage A Automated Test Outcomes (`test_model_artifact.py`)
| Test Case | Description | Result |
| :--- | :--- | :--- |
| `test_frozen_vs_in_memory_numerical_equivalence` | Verifies bit-exact prediction match ($\le 10^{-6}$ min) across test set | **PASSED** |
| `test_deterministic_inference` | Verifies 100 iterations of identical feature inputs yield identical predictions | **PASSED** |
| `test_feature_ordering_and_column_shuffling` | Verifies predictions are invariant to column reordering in input DataFrame | **PASSED** |
| `test_missing_artifact_raises_file_not_found` | Verifies clear `FileNotFoundError` when artifact file is absent | **PASSED** |
| `test_tampered_weights_fail_sha256_validation` | Verifies `ModelArtifactTamperedError` when any coefficient is altered | **PASSED** |
| `test_unsupported_schema_version_rejection` | Verifies `UnsupportedModelSchemaVersionError` on version mismatch | **PASSED** |
| `test_voyage_level_split_has_zero_overlap` | Verifies zero voyage ID overlap between train and test splits | **PASSED** |
| `test_historical_test_partition_evaluation` | Asserts exact reproduction of 5.20 min MAE on held-out test data | **PASSED** |

---

## 3. Stage B — Python FastAPI Service Implementation

### 3.1 Network Binding & Security
- **Bound Host:** `127.0.0.1` (Strict Loopback).
- **Bound Port:** `8000`.
- **Enforcement:** Programmatic assertion in `run_daemon()` raises `ValueError("SECURITY VIOLATION: Daemon must only bind to loopback (127.0.0.1)...")` if binding to `0.0.0.0` or external addresses is attempted.

### 3.2 Implemented Endpoints
1. `GET /internal/v1/health`
   - Returns service health, model load status, model alpha, artifact path, and weight SHA-256.
   - Returns HTTP 503 if the model artifact failed to load.
2. `GET /internal/v1/status`
   - Returns simulation clock (`sim_time_utc`), execution state (`is_running`, `is_paused`), speed multiplier, and event processing counters.
3. `GET /internal/v1/fleet/snapshot`
   - Returns dynamic coordinates, speeds, headings, and state-machine ETA predictions for all 4 virtual fleet vessels (`SIM_FROMVEUR_EXPRESS`, `SIM_AZENOR_VOYAGER`, `SIM_IROISE_STAR`, `SIM_SEIN_SHUTTLE`).
4. `GET /internal/v1/vessels/{vessel_id}/eta`
   - Resolves by vessel ID, vessel name, or synthetic MMSI.
   - Returns authoritative timestamps, raw vs displayed remaining minutes, uncertainty bounds, lifecycle reason codes, and model weight checksum.
   - Returns HTTP 404 for unknown vessel identifiers.
5. `POST /internal/v1/simulation/control`
   - Validates control actions (`pause`, `resume`, `speed`, `reset`).
   - Validates speed multiplier bounds ($>0.0, \le 100.0$).
6. `POST /internal/v1/simulation/scenarios/{scenario_id}`
   - Resolves scenario aliases (e.g. `scenario-1` &rarr; `SCENARIO_01_NORMAL_VOYAGE`).
   - Applies fault injection and returns applied scenario status. Returns HTTP 404 for unknown scenarios.

### 3.3 Zero Mock Operational Data Policy Enforcement
- Endpoints never fabricate canned successful operational telemetry or mock coordinates.
- In degraded or model-missing states (tested via fault injection), endpoints return explicit HTTP 503 errors (`Service Unavailable`) with diagnostic descriptions.

### 3.4 Stage B Automated Test Outcomes (`test_fastapi_daemon.py`)
| Test Case | Description | Result |
| :--- | :--- | :--- |
| `test_health_endpoint_healthy` | Checks health status, model metadata, and weight checksum | **PASSED** |
| `test_status_endpoint_returns_simulation_state` | Validates simulation run ID, clock, and event counters | **PASSED** |
| `test_fleet_snapshot_endpoint_integrity` | Verifies coordinates, speeds, and state machine states for all 4 vessels | **PASSED** |
| `test_single_vessel_eta_provenance` | Validates model provenance, timestamps, and prediction bounds | **PASSED** |
| `test_vessel_not_found_returns_404` | Verifies HTTP 404 for invalid vessel queries | **PASSED** |
| `test_simulation_controls_lifecycle` | Tests pause, resume, speed changes, and reset operations | **PASSED** |
| `test_simulation_controls_validation_errors` | Verifies HTTP 422 on negative/excessive speed multipliers and invalid actions | **PASSED** |
| `test_scenario_activation` | Verifies scenario triggering and alias resolution | **PASSED** |
| `test_invalid_scenario_returns_404` | Verifies HTTP 404 on unrecognized scenario IDs | **PASSED** |
| `test_loopback_security_enforcement` | Verifies exception raised when binding beyond loopback | **PASSED** |
| `test_unavailable_model_returns_honest_503` | Verifies HTTP 503 is returned when model fails to load (no fake data) | **PASSED** |

---

## 4. Full Platform Test Execution & Warning Resolution (Phase 10.1)

### 4.1 Initial Test Suite Warning Audit
Initial run produced `87 passed, 4 warnings in 83.58s`. Investigation revealed:
1. **Warning 1 (`StarletteDeprecationWarning`):**
   - *Message:* `Using 'httpx' with 'starlette.testclient' is deprecated; install 'httpx2' instead.`
   - *Source:* `fastapi/testclient.py:1`
   - *Classification:* Informational / Upstream Third-Party Deprecation.
   - *Root Cause:* Starlette 1.8.0 introduced an upstream migration check prompting for `httpx2`. Because installing dependencies without authorization was prohibited, installing `httpx2` was not permitted.
   - *Targeted Fix:* Wrapped `from fastapi.testclient import TestClient` in `ml-platform/tests/test_fastapi_daemon.py` with a targeted `warnings.catch_warnings()` filter for `StarletteDeprecationWarning`.
2. **Warnings 2–4 (`RuntimeWarning` on 3 records):**
   - *Message:* `RuntimeWarning: Non-conformant content for record [1200, 1031, 3667] in column start_time, 2026-03-01T00:00:0X.0Z, successfully parsed`
   - *Source:* `pyogrio/raw.py:200`
   - *Classification:* Informational / Harmless Third-Party Data Formatting Notice.
   - *Root Cause:* NOAA MarineCadastre's raw external GeoPackage (`AIS_Tracks_2026_03`) contains records where timestamps have 1 millisecond decimal place (`.0Z`) rather than 0 or 3 digits. GDAL parses them with 100% accuracy, but logs CPL warnings.
   - *Targeted Fix:* Wrapped `pyogrio.read_dataframe(...)` in `ml-platform/src/ingestion/us_ais_investigator.py::query_by_mmsi()` with a targeted `warnings.catch_warnings()` filter for `RuntimeWarning: Non-conformant content for record.*`.

### 4.2 Final Verification Run
Command executed:
```bash
.venv\Scripts\python -m pytest tests -v
```
**Outcome:** **87 passed in 83.28s (0 warnings, 0 failures)** across all 12 test suites:
- `tests/test_fastapi_daemon.py`: 11 passed (0 warnings)
- `tests/test_model_artifact.py`: 8 passed (0 warnings)
- `tests/test_phase02_feasibility.py`: 6 passed (0 warnings)
- `tests/test_phase03_baselines.py`: 10 passed (0 warnings)
- `tests/test_phase04a_audit.py`: 6 passed (0 warnings)
- `tests/test_phase05_evaluation.py`: 5 passed (0 warnings)
- `tests/test_phase06_reliability.py`: 5 passed (0 warnings)
- `tests/test_phase07_mock_streaming.py`: 11 passed (0 warnings)
- `tests/test_phase08_virtual_simulation.py`: 8 passed (0 warnings)
- `tests/test_profiling.py`: 4 passed (0 warnings)
- `tests/test_trajectory_segmenter.py`: 8 passed (0 warnings)
- `tests/test_us_ais_investigator.py`: 5 passed (0 warnings)

---

## 5. Artifact and File Inventory of Changes

| File | Change Type | Purpose |
| :--- | :--- | :--- |
| `ml-platform/src/models/export_ridge_artifact.py` | New | Reproducible model export utility |
| `ml-platform/models/vectorized_ridge_model.json` | New | Versioned frozen Ridge model artifact with SHA-256 metadata |
| `ml-platform/src/models/evaluate_phase05.py` | Modified | Added strict `load_artifact()` and integrity exceptions to `VectorizedRidgeETAModel` |
| `ml-platform/src/simulation/daemon.py` | New | Internal FastAPI/Uvicorn daemon bound strictly to `127.0.0.1:8000` |
| `ml-platform/src/ingestion/us_ais_investigator.py` | Modified | Targeted warning suppression for benign NOAA timestamp formatting |
| `ml-platform/tests/test_model_artifact.py` | New | Stage A verification and numerical equivalence test suite (8 tests) |
| `ml-platform/tests/test_fastapi_daemon.py` | New | Stage B FastAPI service test suite (11 tests) with targeted Starlette warning handling |
| `ml-platform/pyproject.toml` | Modified | Added `fastapi`, `uvicorn`, `httpx` to dependencies |
| `MEMORY.md` | Modified | Recorded Phase 10 & 10.1 implementation, hashes, and verification results |

---

## 6. Scope Boundary and Stop Condition

- **Spring Boot Backend:** `backend/` directory remains unmodified and empty. No Spring Boot classes, POM files, or configurations have been created.
- **Frontend Code:** `frontend/src/` remains untouched.
- **Stop Condition:** Phase 10 Stages A & B and Phase 10.1 warning investigations are complete and verified. Work is paused awaiting explicit authorization before beginning Spring Boot backend integration.
