# Phase 02 Verification Report: Replay Engine (Python Simulation)

**Project:** Where Is My Ferry?  
**Phase:** Phase 02 — Replay Engine (Python Simulation)  
**Date:** 2026-10-24  
**Status:** **PASSED (GATE MET)**  

---

## 1. Summary of Completed Tasks

1. **Departure Scheduler (`src/replay/departure_scheduler.py`):**
   - Implemented `DepartureScheduler` to expand normalized GTFS services into concrete daily departures with canonical identifiers (`DEP-YYYYMMDD-ORIG-DEST-HHMM`, e.g., `DEP-20261024-BRE-CNQ-0830`).
   - Handled weekday active days, season validity dates (e.g. Camaret summer-only service), and holiday calendar exceptions (`calendar_dates.txt`).
   - Anchored simulation timestamps to `Europe/Paris` timezone (`PARIS_TZ = zoneinfo.ZoneInfo("Europe/Paris")`), accurately managing daylight-saving transitions (CEST UTC+2 in summer to CET UTC+1 in winter).
   - Sorted daily departures chronologically by scheduled departure epoch.

2. **Replay Runner (`src/replay/replay_runner.py`):**
   - Implemented `ReplayRunner` to coordinate timetable-driven playback of real historical AIS voyages through the frozen Ridge ETA pipeline.
   - Deterministic assignment: Each scheduled departure is pre-assigned a historical voyage matching its corridor and an empirical departure delay (sampled once via seeded RNG).
   - Lifecycle state progression:
     - Prior to scheduled time: `SCHEDULED`.
     - At scheduled departure during delay: `BOARDING` or `DELAYED` (stationary at origin terminal dock).
     - At actual departure time: `IN_TRANSIT` (underway along historical trajectory coordinates).
     - Upon reaching destination dock: Enforces Rule 4 arrival latching (`ARRIVAL_PENDING_CONFIRMATION` &rarr; `ARRIVED` only after 2 consecutive berth dwell observations with SOG $\le$ 1.8 knots).
   - Ground truth recording: Records authoritative `actual_arrival_utc`, computes arrival delay, actual duration, and accuracy error ($|\text{predicted} - \text{actual}|$) across all prediction snapshots.
   - Reset support: Deterministically restarts the day with seed.

3. **VirtualFleetRunner Integration & Zero Scenario Regression:**
   - Plugged `ReplayRunner` into `VirtualFleetRunner` without modifying or degrading any of the 22 existing fault injection scenarios (`SCENARIO_01` to `SCENARIO_22`).
   - Validated that AIS blackout scenarios cleanly drive `STALE_DATA` / `ETA_UNAVAILABLE` after 600s gap and recover upon telemetry resumption.

4. **Internal Endpoints Implemented in `src/simulation/daemon.py`:**
   - `GET /internal/v1/timetable/today`: Returns today's scheduled departures from timetable.
   - `GET /internal/v1/departures`: Returns current departure list with status, delays, and ground truth if arrived.
   - `GET /internal/v1/departures/{id}/live`: Returns live vessel coordinates, SOG, COG, ETA, lifecycle, `data_source: "HISTORICAL_REPLAY"`, and model weight SHA-256 (`e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9`). Returns RFC 7807 404 for unknown IDs.
   - `GET /internal/v1/departures/{id}/track`: Returns coordinates path so far.
   - `GET /internal/v1/accuracy`: Returns predicted vs actual arrival ground truth records.

---

## 2. Test Results

| Test Suite | Tests Run | Passed | Failed | Status |
|:---|:---:|:---:|:---:|:---:|
| `test_phase02_replay_engine.py` | 6 | 6 | 0 | **PASSED** |
| `test_phase01_gtfs_loader.py` (Regression) | 6 | 6 | 0 | **PASSED** |
| `test_phase01_voyage_library.py` (Regression) | 5 | 5 | 0 | **PASSED** |
| `test_phase00_baseline.py` (Regression) | 3 | 3 | 0 | **PASSED** |
| Prior ML Tests (Regression) | 95 | 95 | 0 | **PASSED** |
| **Total Active ML Tests** | **115** | **115** | **0** | **PASSED** |

### Detailed Test Coverage:
- `test_departure_scheduler_weekday_season_and_dst`: Correct departures per weekday/season, daylight-saving boundary handling (CEST to CET), midnight rollover.
- `test_replay_seeded_determinism_and_bounds`: Seeded determinism, coordinates strictly within Iroise Sea bounds ($47.9 \le \text{lat} \le 48.6, -5.2 \le \text{lon} \le -4.3$).
- `test_pipeline_lifecycle_transitions_and_arrival_latch`: Progressive lifecycle states (`ESTIMATING` &rarr; `ARRIVED`), berth dwell confirmation, arrival latching.
- `test_scenario_overlay_ais_blackout_and_recovery`: AIS blackout drives `STALE_DATA` after 600s, recovery verified.
- `test_new_internal_endpoints`: All 5 new internal endpoints return valid schemas, 404 on unknown ID, weight checksum verified.
- `test_full_simulated_day_at_60x`: 12-hour simulated day completed at 60x speed, all supported departures reach `ARRIVED` with recorded ground truth.

---

## 3. Deviations & Notes

- None. All tasks completed strictly according to specification.

---

## 4. Gate Determination

**Phase 02 Gate:** **PASSED**.
- Full simulated day runs at 60x without errors.
- Every supported departure ends `ARRIVED` with recorded ground truth arrival time.
- All 115 ML Platform tests pass with 0 failures.
- Ready to proceed to **Phase 3: Backend foundation and catalog**.
