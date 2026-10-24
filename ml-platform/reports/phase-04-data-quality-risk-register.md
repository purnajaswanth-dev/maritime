# Phase 04 Data-Quality Risk Register

**Project:** Where Is My Ferry?  
**Reviewer:** Senior Maritime Data Engineer, AIS Data Scientist & Data-Quality Auditor  
**Date:** 2026-10-16  
**Status:** `ACTIVE RISK REGISTER — PHASE 04 AUDITED`  

---

## 1. Overview and Scope

This register documents all identified failure modes, empirical risks, observed evidence, implemented mitigations, and remaining unresolved risks across the raw AIS data ingestion, trajectory segmentation, identity verification, and ETA feature snapshot engineering pipeline.

---

## 2. Risk Matrix & Detailed Mitigations

| Risk ID | Risk Description | Severity | Evidence in Repository | Implemented Mitigation | Residual Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`RISK-001`** | **UTC / Local-Time Confusion** | CRITICAL | Brest data uses UNIX epoch milliseconds (UTC); US MarineCadastre uses ISO 8601 strings; GTFS schedules use local agency service days. | Preserved source time representations; strictly normalized all internal and output timestamps to UTC ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`); automated timestamp parsing unit tests enforce UTC formatting. | `RESOLVED` |
| **`RISK-002`** | **Wrong MMSI or Vessel Identity** | CRITICAL | MMSI `227574020` (*TIBIDY*) is a military harbor launch; MMSI `227705180` (*CORSAIRE DE DINARD*) operates in Saint-Malo with 0 records in Brest. Prior notes misidentified them. | Mandatory external identity verification (ITU MARS, IMO records, Regional Council of Brittany fleet rosters). Segregated commercial island ferries (*Fromveur II*, *Enez Sun 3*, *Enez Eussa 3*, *Andre Colin*) from military harbor craft (*Tibidy*). | `RESOLVED` |
| **`RISK-003`** | **Duplicate AIS Records** | MEDIUM | Deduplication performed in datAcron preprocessing (19.03M down to 18.49M raw messages). | `TrajectorySegmenter` enforces strictly monotonic timestamp ordering and discards zero-delta duplicate messages during streaming state transitions. | `RESOLVED` |
| **`RISK-004`** | **Missing AIS Messages & Telemetry Gaps** | HIGH | VHF line-of-sight shadowing behind cliffs (e.g. Ouessant island shadow between 08:58 and 09:53 UTC). | Hard threshold: Any voyage with an internal gap exceeding **45.0 minutes** is marked `UNCERTAIN` and excluded from supervised training. Gap lengths are explicitly recorded in `max_gap_seconds`. | `RESOLVED` |
| **`RISK-005`** | **Aggregated Tracklines Without Vertex Timestamps** | CRITICAL | MarineCadastre 2026-03 GeoPackage contains 2D MultiLineStrings with only scalar start/end times and zero per-vertex timestamps ($(M)$ or $(Z)$). | MarineCadastre 2026-03 tracks are explicitly disqualified from intermediate timestamp-sensitive ETA snapshots. Synthetic interpolation along 2D lines is strictly prohibited. | `RESOLVED` |
| **`RISK-006`** | **Incorrect Voyage Segmentation** | HIGH | Vessels calling at intermediate island ports (e.g. Brest -> Le Conquet -> Molène -> Ouessant) could be collapsed into a single inaccurate mega-voyage. | Implemented berth dwell and terminal exit state machine in `TrajectorySegmenter`. Segmented transits into discrete leg voyages with documented physical corridor duration bounds. | `RESOLVED` |
| **`RISK-007`** | **False Arrival from Terminal Proximity** | HIGH | Vessels sailing past a headland terminal at 15 knots (e.g., sailing past Le Conquet towards Ouessant) could falsely trigger arrival. | Proximity alone never triggers arrival. Arrival requires geofence penetration AND confirmed berth deceleration ($\text{SOG} < 3.0\text{ kts}$) or an explicit `stop_start` AIS annotation. | `RESOLVED` |
| **`RISK-008`** | **Schedule Mistaken for Actual Arrival** | CRITICAL | Phase 02 prototype candidate parquet hardcoded nominal schedule times (e.g. 08:00–08:45) which differed from physical AIS movements. | Complete architectural separation of scheduled timetable events from observed physical arrivals (`OBSERVED_ARRIVAL` vs `SCHEDULED_ARRIVAL`). All 889 verified voyages use actual AIS berth touchdown timestamps. | `RESOLVED` |
| **`RISK-009`** | **Label Leakage into Input Features** | CRITICAL | Prior `HistoricalRouteDurationBaseline` queried history with `departure_ts < pred_ts`, leaking durations of ongoing voyages. | Patched `baselines.py` to enforce `arrival_ts <= pred_ts`. Enforced strict cutoff in `extract_prediction_snapshots()`: only observations with $t_{\text{obs}} \le t_{\text{pred}}$ are accessible. Target remaining time is stored in a separate column. | `RESOLVED` |
| **`RISK-010`** | **Repeated Snapshots Treated as Independent Trips** | HIGH | Sampling 10 snapshots per voyage produces 8,890 snapshots that are autocorrelated. Splitting at the snapshot level causes severe data leakage. | Mandatory `voyage_id` grouping key in [`phase_04_snapshot_contract.yaml`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/configs/phase_04_snapshot_contract.yaml). All snapshots from the same voyage must be assigned to the exact same partition. | `RESOLVED` |
| **`RISK-011`** | **Source or Archive Silently Changed** | HIGH | Large downloads could be corrupted or mutated in place. | SHA-256 cryptographic hashes and exact byte sizes verified and recorded in [`phase-04-source-lineage.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-04-source-lineage.json). Original archives remain read-only. | `RESOLVED` |
| **`RISK-012`** | **Mixed Synthetic and Real Data** | CRITICAL | Prototype Phase 02 candidates contained 5 synthetic records labeled `SUPERVISED_USABLE`. | Segregated historical candidate files. Created clean `data/processed/verified_voyages.parquet` containing 100% physically observed real-world transits with zero synthetic records. | `RESOLVED` |
| **`RISK-013`** | **Incorrect Units or Coordinate Systems** | MEDIUM | Speed Over Ground in tenths of knots or knots; coordinates in WGS-84 decimal degrees. | Explicit schema validation in `TrajectorySegmenter`: speed normalized to knots, coordinates validated within $[-180, 180]$ and $[-90, 90]$, distances computed via haversine WGS-84 in meters. | `RESOLVED` |
| **`RISK-014`** | **Unverified Registry or Dataset License** | HIGH | datAcron Brest AIS is an academic benchmark; commercial reuse permissions require institutional clearance. | Manifests and reports explicitly label datAcron commercial redistribution as `UNRESOLVED`. Models trained on this dataset are restricted to internal research & development benchmarks. | `MONITORED` |
| **`RISK-015`** | **Route or Terminal Mismatch** | MEDIUM | Round-trip harbor maintenance or vessel repositioning returning to origin terminal. | Detected round-trip movements within $2,000\text{m}$ of departure terminal and excluded them from scheduled commercial ferry transit candidates. | `RESOLVED` |
| **`RISK-016`** | **Delayed or Out-of-Order Observations** | MEDIUM | Terrestrial AIS base stations can buffer and emit packets out of chronological order. | Trajectory segmenter sorts all vessel points chronologically before state machine evaluation and measures data freshness lag ($t_{\text{pred}} - t_{\text{obs}}$). | `RESOLVED` |
| **`RISK-017`** | **Overconfident Labels & Heuristic Scores** | HIGH | Assigning subjective numerical probabilities (e.g. 0.95, 0.80) creates false precision. | Categorical evidence grades (`HIGH_AIS_BERTH_OBSERVED`, `UNCERTAIN_TELEMETRY_GAP`, `EXCLUDED_DURATION_BOUNDS`) replace uncalibrated numerical probabilities. | `RESOLVED` |
| **`RISK-018`** | **Ocean Current Temporal Mismatch** | HIGH | Historical Copernicus ocean reanalysis spans 2015–2016; US MarineCadastre spans March 2026. | Strict temporal boundary enforcement: 2015 ocean currents are collocated ONLY with 2015–2016 Brest voyages and never with 2026 data. | `RESOLVED` |

---

## 3. Summary of Unresolved & Monitored Risks

1. **Commercial Licensing for datAcron Brest Data (`UNRESOLVED`):** Internal research and baseline benchmarking are fully permitted under the ANR/Labex CominLabs academic research framework. However, commercial redistribution or external SaaS deployment requires formal institutional clearance.
2. **MarineCadastre Raw NMEA Pings (`UNRESOLVED` for Track B):** Live intermediate ETA predictions for the Salish Sea corridor remain constrained until raw, non-aggregated point pings are acquired to supplement the pre-aggregated tracklines.
