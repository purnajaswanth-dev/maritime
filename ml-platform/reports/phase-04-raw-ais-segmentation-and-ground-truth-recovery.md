# Phase 04 Report: Raw AIS Trajectory Segmentation, Real-World Ground-Truth Recovery, and Data Integrity

**Author:** Senior Maritime Data Engineer, AIS Specialist, Geospatial Engineer, & Applied ML Researcher  
**Date:** 2026-10-16  
**Status:** `COMPLETED — VERIFIED REAL-WORLD DATASET RECOVERED`  
**Phase Output:** 889 Verified Real-World Ferry Voyages Recovered from Raw AIS Data  

---

## 1. Executive Summary & Core Results

The primary objective of Phase 04 was to transition from prototype candidate audits to empirical ground-truth recovery: systematically segmenting genuine real-world passenger ferry voyages from raw AIS telemetry, establishing traceable departure and arrival boundaries, enforcing strict causal isolation, and resolving all historical candidate discrepancies without synthetic interpolation or data fabrication.

### Key Quantitative Findings:
- **Total Candidate Voyages Segmented & Audited:** **1,364 voyages** across 6 months of historical AIS telemetry (October 1, 2015 to March 31, 2016).
- **Verified Supervised Voyages:** **889 voyages** meeting all strict maritime and data-integrity acceptance criteria (traceable berth departure, berth arrival dwell, duration within physical corridor bounds, max telemetry gap $\le 45.0$ minutes, observation count $\ge 5$, confirmed passenger ferry identity).
- **Uncertain / Excluded Voyages:** **475 voyages** explicitly flagged and segregated in the candidate audit register with machine-readable rejection reasons (e.g., telemetry gaps $> 45$ min, transit durations violating corridor physical speed constraints, unverified harbor movements).
- **Vessel Distribution (Verified Voyages):**
  - *FROMVEUR II* (MMSI `228017700`): **603 voyages**
  - *ENEZ SUN 3* (MMSI `227002630`): **141 voyages**
  - *ENEZ EUSSA 3* (MMSI `227003050`): **138 voyages**
  - *ANDRE COLIN* (MMSI `227002330`): **7 voyages**
- **Corridor Coverage (Verified Voyages):**
  - `LE_CONQUET -> MOLENE`: 146 voyages
  - `MOLENE -> LE_CONQUET`: 135 voyages
  - `BREST -> LE_CONQUET`: 131 voyages
  - `AUDIERNE -> ILE_DE_SEIN`: 127 voyages
  - `OUESSANT_STIFF -> MOLENE`: 126 voyages
  - `LE_CONQUET -> BREST`: 113 voyages
  - `MOLENE -> OUESSANT_STIFF`: 76 voyages
  - `OUESSANT_STIFF -> BREST`: 17 voyages
  - `ILE_DE_SEIN -> AUDIERNE`: 14 voyages
  - `BREST -> OUESSANT_STIFF`: 4 voyages

---

## 2. Pre-Flight Reconciliation: Investigation of Discrepant Records

### 2.1 Reconciling Candidate Identity and Vessel Selections
Earlier project documents (Phase 01 profiling and Phase 02 narrative) referenced vessels such as *Fromveur II*, *Coastal Inspiration*, *Queen of Alberni*, and *WSF Chelan*, while the Phase 03 closure audit reviewed 7 specific records from `voyage_candidates.parquet`.

**Root Cause Determination:**
1. In Phase 01 profiling, *Queen of Alberni* (`316001245`), *WSF Chelan* (`366709770`), and *Coastal Inspiration* (`316011408`) were cataloged from MarineCadastre as prominent passenger ferries.
2. When `generate_phase02_artifacts.py` was implemented, the developer generated 5 hardcoded prototype mockups with *Fromveur II*, *Coastal Inspiration*, *Queen of Cowichan*, and *Salish Heron* using nominal timetable hours (e.g. 08:00–08:45, 10:15–12:15) to test the pipeline schema before real segmentation was built.
3. The Phase 03 audit inspected those exact 7 candidate records from `voyage_candidates.parquet`, correctly finding that their nominal timestamps did not match real vessel positions at those hours.

### 2.2 MMSI Investigation: 227574020 and 227705180
The Phase 03 closure notes mentioned MMSIs `227574020` and `227705180` as potential ferry candidates. An empirical source audit resolved their identities:
- **MMSI `227574020` (*TIBIDY*):** French Navy passenger launch (~34m, Call Sign FGD5859) operating inside Brest naval base / arsenal. While it has 114,300 observations in the Brest synopses, its operations are military harbor transfers rather than commercial open-water passenger ferry transits. It has been classified as `HARBOR_PASSENGER_CRAFT` and excluded from the commercial ferry dataset.
- **MMSI `227705180` (*CORSAIRE DE DINARD*):** Passenger vessel operating in Saint-Malo / Dinard (northern Brittany coast). A streaming scan of the Brest archive confirmed exactly **0 observations** for this MMSI. It was referenced erroneously in earlier notes and does not exist in the Brest dataset.

### 2.3 Debunking the Stated "09:47:04 Departure" for Candidate VOY-BREST-0002
The Phase 03 ground-truth audit previously claimed that candidate `VOY-BREST-0002` had a nominal interval of 09:30–10:15 UTC, zero matching AIS pings, and a "stated true departure at 09:47:04 UTC". Direct query of raw kinematic pings in `ais_brest_positions_raw.csv` and `ais_brest_synopses.csv` proved this claim was incorrect:
- **Empirical Reality on 2015-10-01:**
  - *Fromveur II* departed Molène at 08:39 UTC and was underway at 14.8 knots approaching Ouessant at 08:58:56 UTC (`lon=-5.0172, lat=48.4650`).
  - Between 08:59 and 09:53 UTC, the vessel docked at Port du Stiff, Ouessant (`lon=-5.0545, lat=48.4691`).
  - By 09:53:22 UTC, the vessel was recorded as stationary (`sog=0.1 kts`, `annot=00000001` *stop_start*) at the Ouessant berth, remaining moored until 11:25 UTC.
  - **Resolution:** *Fromveur II* did **NOT** depart at 09:47:04 UTC. It was already securely moored at Ouessant dock. The "09:47:04 departure" was an unsubstantiated narrative claim that has now been empirically disproven and removed.

---

## 3. Raw AIS Source Investigation

### 3.1 datAcron Brest AIS Archive (`ais_brest_synopses_v0.8.zip`)
- **File Integrity:** Size `1,993,633,450 bytes` (~1.86 GB compressed; 24.24 GB uncompressed across 9 members). SHA-256: `d8b3180106828e2ef18d34977fd8e290bb50a1ef9200bfcd49b7b838b5728a2d`.
- **Temporal Span:** October 1, 2015 00:00:00 UTC to March 31, 2016 23:59:59 UTC (6 full months).
- **Member Comparison:**
  - `ais_brest_positions_raw.csv`: 18,495,676 kinematic point observations (deduplicated NARI raw stream). Contains UNIX epoch millisecond timestamps, MMSI, lon, lat, SOG, COG, heading.
  - `ais_brest_synopses.csv`: 4,637,651 trajectory critical points computed via Apache Flink streaming summarization. Each point contains exact millisecond timestamp, MMSI, lon, lat, SOG, heading, course, and an 8-bit mobility annotation bitmap (bit 0: `stop_start`, bit 1: `stop_end`, bit 4: `gap_end`, etc.).
- **Per-Vertex Timestamps:** Fully available on every individual observation.
- **Suitability for Live Intermediate ETA:** **EXCELLENT.** The point pings support generating discrete, non-interpolated intermediate prediction snapshots at any prediction timestamp $t_{\text{pred}}$.
- **License / Commercial Status:** Academic research benchmark (ANR-11-LABX-0031-01 / Labex CominLabs). Permitted for internal R&D; commercial distribution remains `UNRESOLVED` (requires institutional clearance).

### 3.2 US MarineCadastre Archive (`AISVesselTracks2026-03.zip`)
- **File Integrity:** Size `1,220,146,725 bytes`. Intact.
- **Granularity Assessment:** Layer `AIS_Tracks_2026_03` provides 2D `MultiLineString` geometries with scalar `start_time` and `end_time`. It contains **zero per-vertex timestamps** (no $(M)$ or $(Z)$ dimensions).
- **Prohibition on Interpolation:** Reconstructing intermediate vessel positions along a 2D line requires synthetic geometric interpolation. In accordance with Non-Negotiable Requirement 2, synthetic interpolation must never be presented as observed AIS data.
- **Suitability for Intermediate ETA Snapshots:** **UNSUITABLE** for timestamped intermediate prediction without raw NMEA receiver logs. MarineCadastre tracklines remain valid for retrospective total duration baselines, but cannot provide live intermediate in-progress features.

---

## 4. Trajectory Segmentation & Ground-Truth Recovery Methodology

The segmentation engine was implemented in [`ml-platform/src/ingestion/trajectory_segmenter.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/ingestion/trajectory_segmenter.py).

### 4.1 Terminal Geofencing & Berth Identification
Circular geofences were established around verified commercial ferry terminals (derived from NGA World Port Index Pub 150 and confirmed AIS docking coordinates):
- `BREST`: Gare Maritime / Port de Commerce (`lon=-4.4857, lat=48.3811, r=800m`)
- `LE_CONQUET`: Quai du Drellac'h (`lon=-4.7818, lat=48.3596, r=600m`)
- `MOLENE`: Port de Molène (`lon=-4.9565, lat=48.4022, r=500m`)
- `OUESSANT_STIFF`: Port du Stiff (`lon=-5.0545, lat=48.4691, r=800m`)
- `AUDIERNE`: Port de Sainte-Évette (`lon=-4.5524, lat=48.0061, r=600m`)
- `ILE_DE_SEIN`: Port de l'Île de Sein (`lon=-4.8486, lat=48.0390, r=500m`)
- `CAMARET`: Port de Camaret (`lon=-4.5940, lat=48.2780, r=600m`)

### 4.2 State-Machine Boundary Detection
1. **Departure Transition:** Vessel berthed at terminal geofence with low speed ($\text{SOG} < 2.0\text{ kts}$) accelerates to underway speed ($\text{SOG} \ge 3.0\text{ kts}$) and exits terminal radius. The departure boundary timestamp $t_{\text{dep}}$ is recorded as the last stationary / initial underway observation.
2. **Transit Monitoring:** Underway points are ingested chronologically. Telemetry gaps are continuously measured: $\Delta t_{\text{gap}} = t_i - t_{i-1}$.
3. **Arrival Transition:** Vessel penetrates destination terminal geofence ($d \le R_{\text{term}}$) and decelerates to berth speed ($\text{SOG} < 3.0\text{ kts}$) or registers an explicit `stop_start` annotation. The arrival boundary timestamp $t_{\text{arr}}$ is recorded at initial berth touchdown.
4. **Harbor Turnaround / Maneuver Filtering:** Movements departing and returning to the same terminal within $2,000\text{ meters}$ without open-water transit are classified as harbor repositioning and discarded.

### 4.3 Multi-Criteria Quality Gates
Every segmented candidate voyage is evaluated against 4 deterministic rules:
1. **Corridor Duration Bounds:** Transit duration $T$ must fall within realistic physical bounds (e.g., 45–120 min for Brest–Le Conquet; 35–150 min for Audierne–Sein; 20–60 min for Le Conquet–Molène).
2. **Maximum Telemetry Gap:** No internal telemetry gap during transit may exceed **45.0 minutes**. Trips exceeding this threshold are marked `UNCERTAIN` to prevent unobserved route anomalies.
3. **Observation Density:** Must contain at least **5 distinct physical observations** during transit.
4. **Vessel Identity:** MMSI must belong to an independently verified passenger ferry in ITU MARS / regional registry.

---

## 5. Design for Future ETA Task & Causal Snapshot Contract

To support Phase 05 model training without future-information leakage, a formal causal snapshot contract was established in [`ml-platform/configs/phase_04_snapshot_contract.yaml`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/configs/phase_04_snapshot_contract.yaml):

```text
Prediction Instant: t_pred  (where t_dep <= t_pred < t_arr)
Input Feature Cutoff: observations where t_obs <= t_pred
Data Freshness Lag: t_pred - t_obs_latest
Supervision Target: remaining_travel_time_minutes = (t_arr - t_pred) / 60.0
Grouping Key: voyage_id (enforcing non-overlapping voyage holdout splits)
```

The function `extract_prediction_snapshots()` was implemented and verified with automated unit tests to prove that:
- Input features contain only past observations.
- Remaining travel time is strictly positive.
- The target is computed from true arrival without post-prediction data exposure.

---

## 6. Generated Artifacts & Automated Test Evidence

### 6.1 Artifacts Produced
1. [`ml-platform/data/processed/verified_voyages.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/processed/verified_voyages.parquet)
   - **889 verified real-world passenger ferry voyages**
   - 100% `status == 'VERIFIED'`, 100% `evidence_grade == 'HIGH_AIS_BERTH_OBSERVED'`
   - File size: 90,208 bytes
2. [`ml-platform/data/interim/phase_04_candidate_voyage_audit.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/phase_04_candidate_voyage_audit.parquet)
   - **1,364 total segmented candidates** (889 verified, 475 uncertain/rejected with explicit failure reasons)
   - File size: 137,428 bytes
3. [`ml-platform/data/manifests/phase-04-source-lineage.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-04-source-lineage.json)
   - Complete cryptographic provenance, archive SHA-256, parameter definitions, and data-preservation attestations.
4. [`ml-platform/configs/phase_04_snapshot_contract.yaml`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/configs/phase_04_snapshot_contract.yaml)
   - Formal feature/label separation and grouped partitioning specification.

### 6.2 Automated Test Execution
Executed `pytest tests -v` inside `ml-platform/.venv`:
```text
33 passed, 3 warnings in 79.68s (100% passing)
- tests/test_trajectory_segmenter.py: 8 passed (new Phase 04 test suite)
- tests/test_phase03_baselines.py: 10 passed
- tests/test_phase02_feasibility.py: 6 passed
- tests/test_us_ais_investigator.py: 5 passed
- tests/test_profiling.py: 4 passed
```

### 6.3 Data Preservation Confirmation
- Original archives (`AISVesselTracks2026-03.zip`, `ais_brest_synopses_v0.8.zip`, Copernicus NetCDF) were **untouched**.
- Historical candidate dataset (`data/interim/voyage_candidates.parquet`) was **preserved byte-for-byte**.
- Zero synthetic observations or interpolated positions entered the verified dataset.

---

## 7. Limitations and Recommendations for Phase 05

1. **Ocean Physics Collocation:** Copernicus NetCDF daily current fields (`uo`, `vo`) are available for October 2015 – March 2016 in the Iroise Sea. The 889 verified Brest voyages can now be collocated with ocean current velocities for hydrodynamic ETA modeling.
2. **Generalization Feasibility Reached:** With 889 verified voyages across 4 distinct passenger vessels and 10 corridors, the previous `GENERALIZATION_EVALUATION_BLOCKED` status is officially lifted for Track A (Brest / Iroise Sea). Both Protocol 1 (Temporal split on known vessels) and Protocol 2 (Zero-shot vessel holdout) can now be evaluated with statistical power.
3. **Next Recommended Action:** Phase 05 authorization to collocate ocean currents, generate grouped prediction snapshots under the causal contract, and evaluate ETA baselines against the 889 verified real-world voyages.
