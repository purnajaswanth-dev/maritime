# Where Is My Ferry? — Phase 03 Technical Correction Log

**Date:** 2026-10-16  
**Auditor / Engineer:** Senior ML Engineer, Maritime AIS Data Scientist & Evaluation Specialist  
**Status:** All Corrections Completed & Verified  

---

## 1. Summary of Changes and Corrections

| # | File Affected | Category | Reason for Correction | Change Applied | Validation & Test Result |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **CORR-01** | `ml-platform/src/models/baselines.py` | Causal Bug Fix | `HistoricalRouteDurationBaseline` previously filtered past voyages on `departure_timestamp_utc < pred_ts`. If a historical voyage departed before $t_{\text{pred}}$ but arrived *after* $t_{\text{pred}}$, its full duration was not yet known at $t_{\text{pred}}$, causing temporal leakage. | Updated temporal filter to enforce completion before prediction cutoff: `arrival_timestamp_utc <= pred_ts` (using arrival timestamp or computed `departure + actual_duration`). | Added `test_historical_route_duration_uncompleted_trip_exclusion`; PASSED. |
| **CORR-02** | `ml-platform/tests/test_phase03_baselines.py` | Test Expansion | Verify that under-way voyages at $t_{\text{pred}}$ are strictly excluded from historical baseline pools, and ensure route/direction isolation. | Added `test_historical_route_duration_uncompleted_trip_exclusion` and `test_historical_route_duration_route_isolation`. | Suite expanded to 10 baseline tests; 10/10 PASSED. |
| **CORR-03** | `ml-platform/configs/evaluation_policy.yaml` | Policy Clarification | Previous policy lacked explicit boundary handling, data-dependent cutoffs, metric limitation disclaimers, and clear separation of evaluation protocols. | Added explicit `protocol_1_temporal_generalization` and `protocol_2_vessel_transferability`, boundary-spanning voyage rule (assignment by departure timestamp), mandatory independent counts reporting, and detailed metric limitation descriptions. | Verified schema conformance; status marked `BLOCKED`. |
| **CORR-04** | `ml-platform/configs/eta_feature_contract.yaml` | Contract Clarification | Terminal boundary representations in repo are point coordinates only (NGA Pub 150), not polygons. Arrival thresholds (0.5 kn, 800m, 3m dwell) are uncalibrated heuristics. Explicit edge case dispositions were needed. | Added `terminal_geofencing_and_arrival_heuristics` section documenting point-only coordinates, uncalibrated confidence scores, and explicit dispositions for `AMBIGUOUS_MULTI_BERTH`, `INCOMPLETE_TRACK`, `INTERMEDIATE_WAYPOINT_STOP`, and `CENSORED_SIGNAL_LOSS`. | Verified configuration consistency. |
| **CORR-05** | `ml-platform/reports/phase-03-ground-truth-audit.md` | Factual Audit Correction | Previous audit draft reported Brest AIS as "24M observations". Empirical line counting revealed `ais_brest_positions_raw.csv` has 18,495,677 lines and `ais_brest_synopses.csv` has 4,637,652 lines. The "24M" figure was an inadvertent conflation with the archive's 24.24 GB uncompressed size. | Corrected record count explanation and distinguished candidate parquet zero status from raw archive potential. | Empirically verified via raw streaming line counts. |
| **CORR-06** | `ml-platform/reports/phase-03-modeling-specification.md` | Specification Qualification | Preliminary sample threshold of 50 voyages was described without sufficient qualification; LightGBM inference and generalization claims required empirical framing. | Qualified 50 voyages as an initial feasibility milestone (not statistical sufficiency); noted snapshot correlation; framed ML performance claims as hypotheses to be benchmarked. | Consistent with evaluation policy. |
| **CORR-07** | `MEMORY.md` | Project Memory Alignment | Update root memory with final audit verdict (`ACCEPTED WITH LIMITATIONS`), resolved record count discrepancy, corrected baseline causality, and explicit project pause. | Synchronized root `MEMORY.md` with complete Phase 03 technical closure. | Clean markdown links and status. |

---

## 2. Preservation of Historical Artifacts and Raw Data

1. **Original Source Data Preservation:**
   - [AISVesselTracks2026-03.zip](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/downloads/AISVesselTracks2026-03.zip): Verified byte-for-byte unchanged at `1,220,146,725` bytes.
   - [ais_brest_synopses_v0.8.zip](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/downloads/ais_brest_synopses_v0.8.zip): Verified byte-for-byte unchanged at `1,993,633,450` bytes.
   - [cmems_mod_glo_phy_my_0.083deg_P1D-m_1792083299167.nc](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/downloads/cmems_mod_glo_phy_my_0.083deg_P1D-m_1792083299167.nc): Verified untouched.
   - All GTFS download archives: Verified untouched.
2. **Historical Phase 02 Artifacts Preservation:**
   - [voyage_candidates.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/voyage_candidates.parquet): Preserved untouched.
   - [vessel_registry_candidates.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/vessel_registry_candidates.parquet): Preserved untouched.
   - [voyage_match_audit.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/voyage_match_audit.parquet): Preserved untouched.
   - [phase-02-source-lineage.json](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-02-source-lineage.json): Preserved untouched.
3. **Versioned Audit Artifacts Created:**
   - [phase_03_voyage_audit_result.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/phase_03_voyage_audit_result.parquet): Documents audited dispositions without mutating Phase 02 artifacts.
