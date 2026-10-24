# Phase 08: Preflight Audit & Architectural Feasibility Report

**Project:** Where Is My Ferry?  
**Phase:** 08 — Virtual Live Maritime Simulation & End-to-End System Readiness  
**Date:** 2026-10-16  
**Auditor:** Senior Backend Architect, Real-Time Systems & Reliability Specialist  
**Status:** **AUDIT PASSED — READY FOR IMPLEMENTATION**  

---

## 1. Objective of Audit

In strict compliance with the Phase 08 Master Execution Prompt, this preflight audit establishes baseline workspace integrity, inventories frozen assets and cryptographic signatures, audits existing streaming and inference interfaces, determines baseline test suite results, and documents planned additions and architectural boundaries before any new code is written.

---

## 2. Baseline Test Execution Results

Prior to making any modifications, the entire repository test suite was executed against the active virtual environment (`ml-platform/.venv`, Python 3.13.6 on Windows):

- **Command:** `pytest -q`
- **Result:** **60 passed, 3 warnings in 80.25s** (100% pass rate)
- **Suite Breakdown:**
  - `tests/test_phase07_mock_streaming.py`: 11 passed (Schema, deduplication, watermark, staleness, arrival latching, API endpoints, 20 scenarios)
  - `tests/test_eta_state_machine.py`: 6 passed
  - `tests/test_vectorized_baselines.py`: 6 passed
  - `tests/test_ocean_collocation.py`: 6 passed
  - `tests/test_historical_ground_truth.py`: 5 passed
  - `tests/test_trajectory_segmenter.py`: 5 passed
  - `tests/test_corridor_matcher.py`: 4 passed
  - `tests/test_candidate_registry.py`: 4 passed
  - `tests/test_terminal_proximity.py`: 3 passed
  - `tests/test_us_ais_investigator.py`: 3 passed
  - `tests/test_data_profiler.py`: 3 passed
  - `tests/test_source_audit.py`: 4 passed

---

## 3. Frozen Artifacts & Cryptographic Signatures

The following model, snapshot, and contract artifacts from Phases 04–07 are strictly frozen and verified against their cryptographic SHA-256 hashes:

| Artifact Path | SHA-256 Hash | Status |
|---|---|:---:|
| `data/processed/phase_05_prediction_snapshots.parquet` | `39f9f1ae9cbff17c9061460f156f0341c24dd2aab4a5ef7bff8350d48122579d` | **FROZEN** |
| `data/processed/verified_voyages.parquet` | `43f5e018368580bc22f14656bc3c606eed1c80516d2ed09816cde4aac2d99997` | **FROZEN** |
| `configs/phase_07_streaming_event_contract.yaml` | `28a421341a62b558a8f6289cfba7098603dea3b105daf93f5c0b4378c20fee88` | **FROZEN** |
| `src/models/baselines.py` | `f589c1c6fef9b57cff6464ff42f9c8d00a88e94b74db1e8d73b143d110ee114b` | **FROZEN** |
| `src/models/eta_state_machine.py` | `6231bca103740691c6e5479dcd7f6423f622f36a5eed6c77e5ee08c6e856b1b2` | **FROZEN** |
| `src/streaming/eta_stream_processor.py` | `694d46337d108262e2bf2b4d2eadbd2c5f141e0a18c9ff8e8b9ef47ded3eb204` | **FROZEN** |

---

## 4. Existing Components Reused in Phase 08

1. **`ETAStreamProcessor` (`src/streaming/eta_stream_processor.py`):**
   - Core stateful ingestion interface connecting event validation, deduplication, out-of-order detection, causal feature derivation, and ETA prediction.
   - Will be directly connected to the virtual fleet runner as the authoritative processor.
2. **`IncomingAISEvent` & `validate_ais_event` (`src/streaming/event_schema.py`):**
   - Schema v1.0.0 validation, ISO UTC timestamp parsing, coordinate/speed bounds checking.
   - Extended with virtual simulation provenance fields (`is_synthetic_fixture: True`, `source_id: "virtual_maritime_sim"`).
3. **`ETAStateMachine` (`src/models/eta_state_machine.py`):**
   - 6-state lifecycle (`ESTIMATING`, `DELAYED_OR_UNCERTAIN`, `STALE_DATA`, `ARRIVAL_PENDING_CONFIRMATION`, `ARRIVED`, `ETA_UNAVAILABLE`), asymmetric display smoothing ($\alpha=0.35$), dynamic clamping, and arrival latching.
4. **`VectorizedRidgeETAModel` (`src/models/baselines.py`):**
   - Frozen Ridge regression model predicting remaining transit minutes.
   - Used for virtual vessels traversing the calibrated Brest / Iroise corridors.
5. **`MockAPIService` / `MockAPIClient` (`src/streaming/mock_api_server.py`):**
   - REST dispatch interface for telemetry ingestion (`POST /api/v1/telemetry`) and passenger ETA queries (`GET /api/v1/eta/{mmsi}`).
   - Reused and extended with simulation control (`/api/v1/simulation/*`) and vessel fleet listing (`/api/v1/vessels`).

---

## 5. Architectural Gaps & Planned Enhancements

| Gap Identified | Mitigation in Phase 08 |
|---|---|
| No continuous autonomous movement engine | Implement `VirtualAISGenerator` (`src/simulation/virtual_ais_generator.py`) providing great-circle segment interpolation along ordered waypoints with realistic acceleration, speed caps, and dwell. |
| No multi-vessel concurrent simulation manager | Implement `VirtualFleetRunner` (`src/simulation/virtual_fleet_runner.py`) supporting start, stop, pause, resume, accelerated playback, and multi-vessel tracking. |
| Scenarios were historical replays, not virtual simulations | Create configuration-driven scenario library (`configs/phase_08_scenarios.yaml`) covering all 22 required synthetic fault and movement scenarios. |
| Virtual fleet configuration was not externalized | Create `configs/phase_08_virtual_fleet.yaml` defining virtual vessels, synthetic MMSIs, route geometries, and departure schedules. |
| In-memory state loss on process restart | Assess restart behavior explicitly in tests; document that in-memory state is intentionally ephemeral and that recovery requires re-establishing telemetry. |

---

## 6. Planned File Changes

### New Files to Create
1. `ml-platform/configs/phase_08_virtual_fleet.yaml`: Configuration of 4+ virtual vessels, routes, waypoints, and nominal speeds.
2. `ml-platform/configs/phase_08_scenarios.yaml`: Definitions for all 22 test scenarios with injected faults, disturbances, and expected states.
3. `ml-platform/src/simulation/virtual_ais_generator.py`: Continuous kinematic movement and event synthesis engine.
4. `ml-platform/src/simulation/virtual_fleet_runner.py`: Continuous simulation runner with lifecycle management (start/stop/pause/resume/rate).
5. `ml-platform/src/simulation/evaluate_phase08.py`: Master runner executing the 22 scenarios, measuring latency/throughput, and checking acceptance criteria.
6. `ml-platform/tests/test_phase08_virtual_simulation.py`: Comprehensive automated test suite for Phase 08.
7. `ml-platform/reports/phase-08-virtual-live-simulation.md`: Comprehensive Phase 08 report.
8. `ml-platform/data/manifests/phase-08-acceptance-results.json`: Machine-readable acceptance results.
9. `ml-platform/data/manifests/phase-08-scenario-results.json`: Machine-readable results for all 22 scenarios.
10. `ml-platform/data/manifests/phase-08-performance-metrics.json`: Machine-readable latency and throughput metrics.

### Existing Files to Extend (Backward-Compatible)
- `ml-platform/src/streaming/mock_api_server.py`: Extend with simulation status, fleet listing, and scenario trigger endpoints.
- `MEMORY.md`: Update with Phase 08 execution records, architectural decisions, and strict stop condition.

---

## 7. Blockers & Verification Checklist

- [x] Preflight test suite verified (60/60 passing).
- [x] Frozen artifact hashes recorded and verified.
- [x] Confirmed NO external paid or live AIS feeds will be accessed.
- [x] Confirmed virtual telemetry will be explicitly tagged with synthetic provenance.
- [x] Confirmed model retraining is strictly prohibited.
- [x] Workspace ready for Phase 08 implementation.
