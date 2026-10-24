# Phase 01 Verification Report: Timetable and Voyage Library

**Project:** Where Is My Ferry?  
**Phase:** Phase 01 — Timetable and Voyage Library (ML Platform)  
**Date:** 2026-10-24  
**Status:** **PASSED (GATE MET)**  

---

## 1. Summary of Completed Tasks

1. **GTFS Loader & Normalization (`src/timetable/gtfs_loader.py`):**
   - Implemented `GTFSLoader` to parse and normalize GTFS feeds directly from archive (`penn_ar_bed_gtfs.zip`) or directories.
   - Normalized 20 trips across 12 routes into `ServiceDefinition` records and exported `data/timetable/services.json` and `services.parquet`.
   - Handled services crossing midnight with positive duration calculations and time formatting.
   - Handled `calendar.txt` weekly schedules and `calendar_dates.txt` holiday exceptions.
   - **Enforced Rule 6:** Mapped modelled corridors to engine virtual vessels (`V-FROMVEUR-SIM`, `V-AZENOR-SIM`, `V-OUESSANT-SIM`, `V-SEIN-SIM`) with `tracking_supported=true`. Unmodelled services (e.g. summer Camaret or secondary island connectors) are strictly flagged `tracking_supported=false` with `vessel_id=None`.

2. **Historical Voyage Library (`src/replay/voyage_library.py`):**
   - Extracted 889 historical voyages from `verified_voyages.parquet` and causal snapshots.
   - Segmented into **685 train voyages** and **204 test voyages** with **0 voyage ID overlap**.
   - Built monotonic trajectories:
     - Point 0 starts at origin terminal berth coordinates (`time_offset_s = 0.0`, distance to dock $\le$ terminal radius).
     - Intermediate points advance with strictly increasing timestamps.
     - Final point docks at destination terminal berth coordinates (distance to dock $\le$ terminal radius).
   - Embedded along-track mean ocean currents ($u_o, v_o$) from Copernicus physics.
   - Computed actual departure delays versus scheduled timetable services using `schedule_matcher` alignment principles.

3. **Delay Distributions & Persistence (`ml-platform/data/replay/`):**
   - Built empirical `delay_distribution` per corridor, bounded strictly in $[-10.0, +120.0]$ minutes.
   - Persisted `voyages.json` (889 voyages), `delay_distributions.json` (10 corridors), and `manifest.json`.
   - Manifest includes counts and SHA-256 checksums; tamper detection verifies file integrity.

---

## 2. Test Results

| Test Suite | Tests Run | Passed | Failed | Status |
|:---|:---:|:---:|:---:|:---:|
| `test_phase01_gtfs_loader.py` | 6 | 6 | 0 | **PASSED** |
| `test_phase01_voyage_library.py` | 5 | 5 | 0 | **PASSED** |
| `test_phase00_baseline.py` (Regression) | 3 | 3 | 0 | **PASSED** |
| Prior ML Tests (Regression) | 95 | 95 | 0 | **PASSED** |
| **Total Active ML Tests** | **109** | **109** | **0** | **PASSED** |

### Detailed Test Coverage:
- `test_time_conversion_and_midnight_crossing`: Seconds conversion, midnight rollover, and malformed time string rejection.
- `test_load_valid_penn_ar_bed_gtfs`: Clean extraction of 20 services and Rule 6 tracking flags.
- `test_every_service_maps_to_corridor_or_unsupported`: Strict unmodelled/summer route handling.
- `test_calendar_exceptions_handling`: Holiday addition/removal parsing.
- `test_malformed_gtfs_missing_columns`: ValueError on missing mandatory columns.
- `test_service_crossing_midnight`: Accurate positive duration calculation on midnight rollover.
- `test_voyage_library_counts_and_splits`: 889 total, 685 train, 204 test, 0 overlap.
- `test_modelled_corridors_coverage`: All 4 modelled corridors have historical voyages.
- `test_berth_anchors_and_monotonicity`: All voyages start/end inside berth radius with monotonic timestamps.
- `test_delay_distributions`: Non-empty distributions in $[-10, 120]$ min range with sampling.
- `test_manifest_tampering_detection`: Checksum verification rejects corrupted assets.

---

## 3. Deviations & Notes

- None. All tasks completed strictly according to specification.

---

## 4. Gate Determination

**Phase 01 Gate:** **PASSED**.
- Library covers all 4 modelled corridors (`BREST_LE_CONQUET`, `LE_CONQUET_BREST`, `BREST_OUESSANT_STIFF`, `AUDIERNE_ILE_DE_SEIN`) with hundreds of verified voyages.
- Test split contains exactly 204 voyages with 0 overlap.
- Delay distributions non-empty and bounded.
- 109/109 tests passing.
- Ready to proceed to **Phase 2: Replay engine (Python simulation)**.
