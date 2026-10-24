# Phase 04A Independent Ground-Truth Acceptance Audit

**Role:** Independent Senior AIS Data Auditor & ML Evaluation Specialist  
**Date:** 2026-10-16  
**Audit Target:** `ml-platform/data/processed/verified_voyages.parquet` (889 voyages) & `ml-platform/data/interim/phase_04_candidate_voyage_audit.parquet` (1,364 candidates)  
**Status:** `AUDIT COMPLETE`  
**Verdict:** **`ACCEPTED WITH LIMITATIONS FOR HISTORICAL BENCHMARKING (TRACK A ONLY)`**  

---

## 1. Executive Verdict & Critical Summary

As an independent senior auditor who did not author the Phase 04 segmentation pipeline, I have conducted an adversarial, evidence-grounded audit of the Phase 04 deliverables against the raw AIS archive, interim candidate artifacts, source lineage manifests, physical navigation constraints, and automated unit test suites.

### Audit Verdict: ACCEPTED WITH LIMITATIONS
The 889 verified voyages in [`ml-platform/data/processed/verified_voyages.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/processed/verified_voyages.parquet) are **ACCEPTED WITH LIMITATIONS** as a defensible ground-truth dataset for **offline retrospective ETA evaluation and hydrodynamic current benchmark modeling (Track A — Brest / Iroise Sea)**.

The previous state of the project ($N=0$ verified real voyages in Phase 02/03 prototype candidate files) has been successfully overcome with genuine physical AIS voyages. However, critical limitations prevent treating this dataset as an unrestricted production training set:

1. **Extreme Vessel Concentration:** A single vessel (*FROMVEUR II*) accounts for **603 of 889 voyages (67.8%)**. Only 4 independent passenger vessels exist in total.
2. **Protocol 2 (Zero-Shot Generalization) Underpowered:** The Phase 04 report's claim that zero-shot vessel holdout evaluation (Protocol 2) has "high statistical power" is **REJECTED AS AN OVERSTATEMENT**. With only $N=4$ vessels, a leave-one-vessel-out test set has an effective sample size of $N_{\text{vessels}} = 1$ (or 2), which is dominated by vessel- and route-specific idiosyncrasies rather than generalizable vessel dynamics.
3. **Snapshot Materialization Status:** An active causal snapshot schema contract exists in [`phase_04_snapshot_contract.yaml`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/configs/phase_04_snapshot_contract.yaml), but an actual materialized `snapshots.parquet` dataset has **NOT** yet been generated.
4. **Offline Retrospective vs Live Streaming:** The dataset tests offline retrospective prediction accuracy, but **cannot** test real-time WebSocket push stability, live countdown flicker, or cellular telemetry drop recovery.
5. **Route Asymmetry (Sein -> Audierne):** Return trips from Île de Sein to Audierne are severely underrepresented (14 verified vs 127 outbound trips) because the vessel regularly powers down its AIS transponder upon reaching the harbour entrance in the evening.

---

## 2. Audit A — Artifact & Provenance Verification

### 2.1 File Inventory and Schema Conformance
All reported artifacts were verified on disk, successfully parsed, and audited:
- [`data/processed/verified_voyages.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/processed/verified_voyages.parquet):
  - Exactly **889 rows**, 21 columns, **0 null values** across all fields.
  - Zero duplicate `voyage_id` strings (889 unique IDs).
  - Continuous chronological coverage: `2015-10-01T06:24:01Z` to `2016-03-31T17:36:05Z`.
  - Coordinates strictly conform to WGS-84 (Lat: $[48.006, 48.469]$, Lon: $[-5.055, -4.485]$).
  - All verified records have `status == 'VERIFIED'` and `evidence_grade == 'HIGH_AIS_BERTH_OBSERVED'`.
- [`data/interim/phase_04_candidate_voyage_audit.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/phase_04_candidate_voyage_audit.parquet):
  - Exactly **1,364 rows** (889 `VERIFIED`, 475 `UNCERTAIN`).
  - 100% of `UNCERTAIN` records have explicit, non-null rejection reasons citing specific quality criteria.
- **Historical Prototype Candidate Dataset:**
  - [`data/interim/voyage_candidates.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/voyage_candidates.parquet) remains byte-for-byte intact (7 rows, 25 columns, untouched).

### 2.2 Cryptographic Checksum & Archive Lineage
- **Source Archive:** `ml-platform/data/downloads/ais_brest_synopses_v0.8.zip`
- **Recomputed SHA-256:** `d8b3180106828e2ef18d34977fd8e290bb50a1ef9200bfcd49b7b838b5728a2d`
- **Manifest Conformance:** The recomputed hash matches [`data/manifests/phase-04-source-lineage.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-04-source-lineage.json) identically.
- **Archive Size Clarification:** The actual archive size on disk is **1,993,633,450 bytes** (matching the Phase 00 inventory in `archive_inventory.json`). An earlier reference to 1,249,045,958 bytes in the Phase 03 closure narrative was a typographical transcription error; the physical archive was never altered or re-downloaded.

---

## 3. Audit B — Independent Voyage-Level Evidence

### 3.1 Sampling Methodology
To rigorously audit label correctness, a stratified sample of **50 candidate voyages** was drawn:
- **37 Verified Voyages:** Sampled across all 10 corridors and all 4 vessels, including shortest duration, median duration, longest duration, minimum observations ($N=5$), maximum observations ($N=905$), and maximum telemetry gaps.
- **13 Rejected Candidates:** Sampled across failure modes (telemetry gaps $>45\text{ min}$, duration bounds violations, non-standard routes).

All 50 sampled trajectories were re-extracted from raw synopsis records in `ais_brest_synopses.csv` and audited ping-by-ping. The results are permanently recorded in [`ml-platform/data/interim/phase_04a_sampled_voyage_audit.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/phase_04a_sampled_voyage_audit.parquet).

### 3.2 Audit Findings on Sampled Voyages
```text
Sample Classification (37 Verified Voyages Audited):
- VERIFIED_FROM_SOURCE_EVIDENCE:  18 voyages (48.6%)
- PLAUSIBLE_ALGORITHMIC_ONLY:     19 voyages (51.4%)
- REJECTED_DISPUTED:               0 voyages (0.0%)

Sample Classification (13 Rejected Candidates Audited):
- REJECTION_CONFIRMED_JUSTIFIED:  13 candidates (100.0%)
```

#### Detailed Findings:
1. **Departure & Arrival Dwell Verification:**
   - In 18 of 37 samples, pre-departure dock dwell ($\text{SOG} < 2.0\text{ kts}$) AND post-arrival berth dwell were directly observed within 15 minutes of the trip.
   - In 19 of 37 samples, pre-departure dwell or post-arrival dwell was not recorded because ferry crews powered down their AIS transponder while moored at night or during layovers, powering it on only 1–3 minutes before casting off (or powering off immediately upon docking).
   - The trajectory segmenter correctly captured the vessel at the terminal berth, but the arrival/departure timestamps represent **observed transponder transitions** bounded by the reporting interval rather than extended stationary monitoring.
2. **Rejection Reason Verification:**
   - 100% of sampled rejected candidates (13/13) were legitimately rejected.
   - Trips spanning 12 to 17 hours ($755-1049\text{ min}$) with 15-hour overnight transponder gaps were rightfully excluded.
3. **Independent Timetable Corroboration:**
   - Comparing empirical durations against published Penn Ar Bed public timetables (Gare Maritime de Brest):
     - Brest to Le Conquet: Empirical median **81.1 min** vs Timetable scheduled **75–90 min**.
     - Le Conquet to Molène: Empirical median **39.0 min** vs Timetable scheduled **35–45 min**.
     - Molène to Ouessant: Empirical median **27.7 min** vs Timetable scheduled **30 min**.
     - Audierne to Île de Sein: Empirical median **60.2 min** vs Timetable scheduled **60 min**.
   - This provides external validation that the segmented voyages reflect real scheduled ferry runs.

---

## 4. Audit C — Count Concentration & Generalization Claims

### 4.1 Concentration Metrics
The 889 verified voyages exhibit heavy operational concentration:

| Dimension | Category | Verified Count | Proportion | Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Vessel** | *FROMVEUR II* (`228017700`) | 603 | **67.8%** | Dominates dataset |
| **Vessel** | *ENEZ SUN 3* (`227002630`) | 141 | 15.9% | Route isolated (Audierne–Sein) |
| **Vessel** | *ENEZ EUSSA 3* (`227003050`) | 138 | 15.5% | Shared Brest–Ouessant corridor |
| **Vessel** | *ANDRE COLIN* (`227002330`) | 7 | 0.8% | High-speed craft (sparse data) |
| **Corridor** | `LE_CONQUET <-> MOLENE` | 281 | **31.6%** | Core island shuttle |
| **Corridor** | `BREST <-> LE_CONQUET` | 244 | **27.4%** | Mainland coastal approach |
| **Corridor** | `OUESSANT_STIFF <-> MOLENE`| 202 | **22.7%** | Inter-island shuttle |
| **Corridor** | `AUDIERNE <-> ILE_DE_SEIN` | 141 | **15.9%** | Southern Finistère crossing |
| **Corridor** | `BREST <-> OUESSANT` (Direct) | 21 | **2.4%** | Express / direct transits |

### 4.2 Statistical Significance Assessment of Generalization Protocols

```text
Protocol 1 (Temporal Split on Known Vessels):
- Setup: Train on Oct 2015 – Jan 2016 (N ~ 600 voyages); Test on Feb – Mar 2016 (N ~ 289 voyages).
- Status: VALID WITH STATISTICAL POWER.
- Rationale: Tests non-stationary weather, seasonal currents, and temporal drift across known vessels and routes.

Protocol 2 (Zero-Shot Unseen Vessel Holdout):
- Setup: Train on 3 vessels; Test on 1 held-out vessel (e.g. hold out ENEZ SUN 3).
- Status: STATISTICALLY UNDERPOWERED (BLOCKED AS A PRIMARY BENCHMARK).
- Rationale: The test set has N_vessels = 1. If ENEZ SUN 3 is held out, the model is tested on an unseen vessel operating on a completely unseen route (Audierne-Sein). Success or failure reflects route and vessel confounding, not statistical generalization.
```

**Auditor Judgment:** Claims of "high statistical significance for zero-shot vessel generalization" are rejected. Protocol 2 may only be reported as an exploratory, confounded case study.

---

## 5. Audit D — ETA Snapshot Readiness

1. **Snapshot Dataset Status:**
   - [`ml-platform/configs/phase_04_snapshot_contract.yaml`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/configs/phase_04_snapshot_contract.yaml) defines a strict causal contract.
   - The generator function `extract_prediction_snapshots()` in `trajectory_segmenter.py` correctly enforces $t_{\text{obs}} \le t_{\text{pred}}$ and prevents post-arrival data leakage.
   - **Critical Distinction:** The physical `snapshots.parquet` file has **NOT** yet been generated. Snapshot creation is an approved task for Phase 05.
2. **Offline vs Live Operational Scope:**
   - Historical static logs test **retrospective offline accuracy** (e.g. MAE in minutes under varying forecast horizons).
   - They **cannot** evaluate live streaming display stability (e.g., countdown bounce, WebSocket reconnect jitter, dropped packet interpolation).

---

## 6. Audit E — Physical Plausibility & The Sein-Audierne Asymmetry

### 6.1 Uncovering the 127 vs 14 Return Trip Discrepancy
An audit of `data/interim/phase_04_candidate_voyage_audit.parquet` explained why `AUDIERNE -> ILE_DE_SEIN` has 127 verified voyages, but `ILE_DE_SEIN -> AUDIERNE` has only 14:
- 137 return candidates were segmented, but **123 were marked `UNCERTAIN` and rejected**.
- **Root Cause:** *Enez Sun 3* departs Île de Sein in late afternoon, arrives at Audierne harbour around 18:00, and immediately powers down its AIS transponder for the night. The vessel did not register an AIS docking ping at $\text{SOG} < 3.0\text{ kts}$ before shutoff.
- The state machine remained in `UNDERWAY` state all night, only closing the voyage when AIS was turned back on at 07:00 the next morning.
- The duration filter ($35-150\text{ min}$) and telemetry gap filter ($\le 45\text{ min}$) correctly rejected these 12-to-17-hour overnight trips.
- **Auditor Verdict:** The rejection was **100% correct and evidence-justified**. The segmentation engine successfully protected the verified dataset from accepting corrupted overnight spans.

---

## 7. Automated Test Suite Verification

An independent automated test suite was authored in [`ml-platform/tests/test_phase04a_audit.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/tests/test_phase04a_audit.py) to permanently enforce these audit determinations:
1. Exact row count and null check on verified voyages.
2. Candidate audit exact status counts (889 vs 475).
3. Rejection of overnight shutdown trips ($> 300\text{ min}$).
4. Vessel concentration bounds quantification.
5. Physical corridor duration conformance across all 889 voyages.
6. Sampled audit artifact conformance.

**Full Test Suite Execution (`pytest tests -q`):**
```text
39 passed, 3 warnings in 78.53s (100% passing)
- tests/test_phase04a_audit.py: 6 passed (new audit regression tests)
- tests/test_trajectory_segmenter.py: 8 passed
- tests/test_phase03_baselines.py: 10 passed
- tests/test_phase02_feasibility.py: 6 passed
- tests/test_us_ais_investigator.py: 5 passed
- tests/test_profiling.py: 4 passed
```

---

## 8. Final Decision & Exact Permitted Scope for Phase 05

### Audit Decision: ACCEPTED WITH LIMITATIONS

The 889 verified voyages are approved for Phase 05 execution under the following strictly defined scope:

### Permitted Phase 05 Actions:
1. **Materialize Intermediate Prediction Snapshots:** Sample verified voyages at 5-minute intervals under [`phase_04_snapshot_contract.yaml`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/configs/phase_04_snapshot_contract.yaml) with mandatory `voyage_id` grouping.
2. **Collocate Ocean Current Data:** Collocate contemporaneous Copernicus NetCDF ocean current velocities (`uo`, `vo`) with verified Brest voyages.
3. **Benchmark Baselines Under Protocol 1:** Evaluate `PhysicalETABaseline` and causal `HistoricalRouteDurationBaseline` under chronological holdout (Train: Oct 2015 – Jan 2016; Test: Feb – Mar 2016).
4. **Report Concentration Limitations:** Explicitly document that model performance reflects the Brittany island ferry network (predominantly *Fromveur II* on the Brest–Ouessant corridor).

### Prohibited Actions:
1. **Do NOT claim zero-shot fleet generalizability (Protocol 2) with statistical significance.**
2. **Do NOT claim live countdown UI stability from historical batch logs.**
3. **Do NOT interpolate 2D tracklines in US MarineCadastre to force US intermediate snapshots.**
4. **Do NOT train complex deep neural networks (GRU/LSTM) prior to establishing deterministic tabular baseline accuracy.**

---

## 9. Strict Stop Condition

Execution is **STOPPED**. No models have been trained, no ML libraries installed, and Phase 05 has not been initiated. Awaiting explicit user authorization.
