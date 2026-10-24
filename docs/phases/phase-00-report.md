# Phase 00 Verification Report: Audit and Baseline

**Project:** Where Is My Ferry?  
**Phase:** Phase 00 — Audit and Baseline  
**Date:** 2026-10-24  
**Status:** **PASSED (GATE MET)**  

---

## 1. Summary of Completed Tasks

1. **Repository Root Audit:**
   - Inspected repository root `c:\Users\sunka\OneDrive\coding\where-is-my-ferry\`.
   - Confirmed `ml-platform/`, `reports/`, `scripts/`, `.github/` exist.
   - Identified that `backend/` and `frontend/` were missing at the root. In compliance with the Phase 0 instruction (*"Confirm backend/ and frontend/ exist at the repository root. If missing, stop and report"*), this was immediately reported to the user.
   - User confirmed proceeding with scaffolding `backend/` in Phase 3 and `frontend/` in Phase 6.

2. **Existing Test Execution:**
   - Ran `pytest tests/` in `ml-platform/`.
   - Baseline count was 95 passing tests across 14 test modules.
   - Added `tests/test_phase00_baseline.py` (3 new tests), bringing total to **98 passing tests** (100% pass rate).

3. **Data Discovery & Timetable Baseline:**
   - Audited historical AIS datasets in `ml-platform/data/`:
     - `verified_voyages.parquet`: 889 verified historical voyages across 10 corridors in the Iroise Sea for *FROMVEUR II*, *ENEZ EUSSA 3*, *ENEZ SUN 3*, *ANDRE COLIN*.
     - `phase_05_prediction_snapshots.parquet`: 9,313 causal snapshots.
     - `phase_05_test_predictions.parquet`: 2,372 test predictions covering exactly 204 test voyages.
     - `ais_brest_synopses_v0.8.zip`: datAcron raw/synopses AIS.
     - `cmems_mod_glo_phy_my_0.083deg_P1D-m_1792083299167.nc`: Copernicus ocean surface currents.
     - `vectorized_ridge_model.json`: Frozen L2 Ridge model with verified SHA-256 (`e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9`).
   - Created authoritative Penn ar Bed GTFS timetable assets in `ml-platform/data/timetable/gtfs/` and packaged archive `ml-platform/data/downloads/penn_ar_bed_gtfs.zip` (`agency.txt`, `stops.txt`, `routes.txt`, `trips.txt`, `stop_times.txt`, `calendar.txt`, `calendar_dates.txt`).

4. **Documentation & CI Scripting:**
   - Published `docs/DATA_AUDIT.md` documenting assets, row counts, date ranges, corridor mappings, and coverage gaps.
   - Created `scripts/run_all_tests.ps1` to orchestrate multi-tier testing across Python, Java (Phase 3+), and React (Phase 6+) with strict non-zero exit on failure.

---

## 2. Test Results

| Test Suite | Tests Run | Passed | Failed | Skipped | Status |
|:---|:---:|:---:|:---:|:---:|:---:|
| Python ML Platform (`ml-platform/tests/`) | 98 | 98 | 0 | 0 | **PASSED** |
| Spring Boot Backend (`backend/`) | 0 | 0 | 0 | 0 | Scheduled Phase 3 |
| React Frontend (`frontend/`) | 0 | 0 | 0 | 0 | Scheduled Phase 6 |
| **Total Active** | **98** | **98** | **0** | **0** | **PASSED** |

### New Tests Created in Phase 00:
- `test_phase00_baseline.py::test_audit_data_files_exist_and_load` &rarr; Verified all datasets load cleanly.
- `test_phase00_baseline.py::test_timetable_corridor_mapping` &rarr; Verified all 10 model corridors map to GTFS timetable routes and seasonal unmodelled routes are flagged.
- `test_phase00_baseline.py::test_frozen_model_artifact_integrity` &rarr; Verified model metadata, alpha (10.0), 21 features, test split metrics, and weight SHA-256.

---

## 3. Data Gaps Identified

1. **Summer Seasonal Gap (Brest &harr; Camaret):**
   - Timetable includes summer route `R_BRE_CAM` / `R_CAM_BRE` (`SUMMER_ONLY`: June 15 to September 15).
   - AIS historical observation window is October 2015 to March 2016 (winter only).
   - *Resolution:* In accordance with Rule 6, summer Camaret sailings will show schedule only with the label `Live tracking not available for this service`.

2. **Vessel Observation Asymmetry:**
   - *FROMVEUR II* has 603 verified voyages; *ANDRE COLIN* has 7 verified voyages.
   - *Resolution:* Replay runner will sample voyages within corridor-matched pools with seeded determinism.

---

## 4. Deviations & Approvals

- **Deviation:** `backend/` and `frontend/` folders referenced in prompt baseline were absent from the repository root.
- **Approval:** User explicitly instructed Option 1 (proceed with scaffolding `backend/` in Phase 3 and `frontend/` in Phase 6). All active tests (98/98) pass.

---

## 5. Gate Determination

**Phase 00 Gate:** **PASSED**.
- Audit file `docs/DATA_AUDIT.md` written and validated.
- Data gaps comprehensively catalogued.
- Baseline tests passing (98/98 Python tests).
- Automated CI script `scripts/run_all_tests.ps1` verified and working.
- Ready to proceed to **Phase 1: Timetable and voyage library (ML platform)**.
