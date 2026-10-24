# Where Is My Ferry? — Phase 03 Final Judgment & Technical Closure Audit

**Date:** 2026-10-16  
**Auditor / Reviewer:** Senior ML Engineer, Maritime AIS Data Scientist, Data Quality Auditor & ML Evaluation Specialist  
**Evaluation Status:** `ACCEPTED WITH LIMITATIONS`  
**Operational Status:** `PROJECT PAUSED — PHASE 04 & MODEL TRAINING UNAUTHORIZED`

---

## 1. Executive Verdict & Core Determinations

Following an evidence-driven audit of Phase 03 deliverables, intermediate Parquet artifacts, YAML contracts, Python implementations, test suites, and raw source archives, the Phase 03 technical closure is formally marked:

### **VERDICT: ACCEPTED WITH LIMITATIONS**

### Primary Determinations
1. **Candidate Dataset Audit (VERIFIED):**
   - The interim artifact `voyage_candidates.parquet` contains **zero (0) confirmed real-world supervised voyages**.
   - All five records marked `SUPERVISED_USABLE` in Phase 02 were demonstration mockups created to validate schema parsing and arrival detector heuristics; their nominal timestamps failed independent reconstruction when cross-referenced against physical AIS pings.
   - Prior artifacts are preserved unmodified; audited dispositions are versioned in `phase_03_voyage_audit_result.parquet`.
2. **Raw Archive Recovery Potential (VERIFIED):**
   - The raw archives contain **hundreds of potentially recoverable real-world voyages**.
   - For Brest (`ais_brest_synopses_v0.8.zip`), raw AIS records demonstrate that verified passenger ferry *FROMVEUR II* (MMSI `228017700`) completed multiple physically observed transits on 2015-10-01 (e.g. Brest $\rightarrow$ Le Conquet departing 06:20:27 UTC, arriving 07:48:37 UTC).
   - For Salish Sea (`AISVesselTracks2026-03.gpkg`), verified BC Ferries vessels have extensive trackline coverage (777 tracks for *Coastal Inspiration*, 553 for *Queen of Alberni*).
   - **Crucial Distinction:** Zero verified voyages in the *current candidate Parquet* must not be equated with zero recoverable voyages in the *raw archives*. The number of independently verified voyages *actually extracted* to date is **0**.
3. **Record Count Discrepancy (RESOLVED):**
   - Empirical streaming line counts of `ais_brest_synopses_v0.8.zip` resolved the reported discrepancy between ~18.5M and 24M records:
     - `ais_brest_positions_raw.csv`: **18,495,677 lines** (18,495,676 deduplicated raw kinematic point observations from NARI).
     - `ais_brest_synopses.csv`: **4,637,652 lines** (4,637,651 critical point trajectory synopses).
     - **24.24 GB**: The **uncompressed file size** of the complete 9-member ZIP archive (`24,236,795,478 bytes`).
     - *Cause:* Prior narrative reports inadvertently conflated the 24.24 GB uncompressed archive volume with observation counts.
4. **AIS Granularity & Live Inference (VERIFIED):**
   - **Brest AIS:** High-frequency timestamped point observations with instantaneous SOG, COG, and millisecond timestamps; supports genuine in-progress ETA prediction snapshots at arbitrary cutoffs $t_{\text{pred}}$.
   - **MarineCadastre 2026-03:** 2D `MultiLineString` tracklines with single scalar `start_time`, `end_time`, `duration_minutes`, and **zero per-vertex timestamps**. Intermediate positions at $t_{\text{pred}}$ cannot be known without synthetic interpolation (strictly prohibited). Supports retrospective full-trip duration analysis, but **cannot support genuine live ETA prediction without raw NMEA pings**.
5. **Causal Baseline Flaw (RESOLVED):**
   - An audit of `HistoricalRouteDurationBaseline` detected a causal leakage flaw: filtering past voyages on `departure_timestamp_utc < pred_ts` permitted under-way voyages (arriving *after* $t_{\text{pred}}$) to leak future duration outcomes into the historical median.
   - Corrected in `ml-platform/src/models/baselines.py` by requiring voyage completion before prediction cutoff (`arrival_timestamp_utc <= pred_ts`). Validated via new unit tests.
6. **Generalization Evaluation (BLOCKED):**
   - Both in-distribution temporal holdouts and cross-vessel generalization evaluation are marked **`BLOCKED`**. Computing error metrics on $N=0$ verified real voyages is statistically invalid.

---

## 2. Evidence-Based Issue Register

| Issue ID | Domain | Severity | Description | Status | Evidence / Action |
| :-: | :--- | :-: | :--- | :-: | :--- |
| **ISSUE-01** | Ground Truth | HIGH | 5 candidate voyages in `voyage_candidates.parquet` carried `SUPERVISED_USABLE` labels despite possessing synthetic nominal timestamps that failed raw AIS verification. | RESOLVED | Dispositions downgraded to `UNVERIFIED` in `phase_03_voyage_audit_result.parquet`. Documented 0 verified real voyages currently extracted. |
| **ISSUE-02** | Telemetry | MEDIUM | Reported observation counts for Brest AIS conflicted across documentation (18.5M vs 24M). | RESOLVED | Empirical streaming count: `ais_brest_positions_raw.csv` has 18,495,677 lines; `ais_brest_synopses.csv` has 4,637,652 lines; 24.24 GB is uncompressed byte volume. |
| **ISSUE-03** | Granularity | HIGH | MarineCadastre MultiLineString features lack per-vertex timestamps, preventing intermediate live ETA prediction without synthetic interpolation. | VERIFIED & CONSTRAINED | Formalized in feature contract: US aggregated tracklines restricted to retrospective duration analysis; live ETA prediction marked `NOT_AVAILABLE`. |
| **ISSUE-04** | Causal Baseline | MEDIUM | `HistoricalRouteDurationBaseline` checked departure time rather than arrival time, causing future duration leakage from voyages still at sea at $t_{\text{pred}}$. | RESOLVED | Code updated in `baselines.py` to enforce `arrival_timestamp_utc <= pred_ts`. Unit test added. |
| **ISSUE-05** | Arrival Rules | MEDIUM | Arrival heuristics (0.5 kn, 800m berth radius, 3m dwell) were represented as validated probabilities (0.95, 0.80). | RESOLVED | Clarified in contract as uncalibrated heuristic scores. Documented that repository contains terminal point coordinates only, not boundary polygons. |
| **ISSUE-06** | Evaluation | HIGH | Generalization evaluation cannot run legitimately with 0 verified real-world voyages. | BLOCKED | `evaluation_policy.yaml` explicitly marked `GENERALIZATION_EVALUATION_BLOCKED` until $N \ge 50$ real voyages are systematically segmented. |
| **ISSUE-07** | Licensing | MEDIUM | Commercial redistribution terms for datAcron and downloaded GTFS feeds were unverified. | FORMALIZED AS UNRESOLVED | Commercial status explicitly designated `UNRESOLVED`. Internal R&D usage permitted under research terms. |

---

## 3. Candidate-Voyage Audit Details (All 7 Candidates Rechecked)

### Candidate 1: `VOY-FR-BREST-001`
- **Vessel Identity:** MMSI `228017700` (*FROMVEUR II*), IMO 9613147. Confirmed passenger/ro-ro ferry via ITU MARS and Penn-ar-Bed fleet records.
- **Source File & Identifiers:** `ais_brest_synopses.csv`, records for `id == 228017700` on 2015-10-01. Epoch millisecond timestamps in UTC.
- **Reported Phase 02 Timestamps:** `2015-10-01 08:30:00` to `2015-10-01 09:45:00` (75.0 min).
- **Physical AIS Ground Truth:** Vessel departed Port de Brest at **06:20:27 UTC** (speed 0.1 $\rightarrow$ 2.6 kn), transit Goulet at 20.5 kn, and arrived Le Conquet at **07:48:37 UTC** (speed 0.4 kn at 48.3595°N, -4.7844°W). At 08:30:00 UTC, vessel was already past Le Conquet heading towards Molène.
- **Disposition:** **`UNVERIFIED`** (Nominal timestamps fail physical reconstruction).
- **Raw Archive Recovery Potential:** High (actual 06:20 $\rightarrow$ 07:48 UTC voyage is recoverable from raw pings).

### Candidate 2: `VOY-FR-BREST-002`
- **Vessel Identity:** MMSI `228017700` (*FROMVEUR II*).
- **Source File & Identifiers:** `ais_brest_synopses.csv`.
- **Reported Phase 02 Timestamps:** `2015-10-01 10:15:00` to `2015-10-01 11:10:00` (55.0 min).
- **Physical AIS Ground Truth:** Vessel completed its morning transit from Le Conquet to Ouessant before 09:30 UTC. From 09:30 to 15:21 UTC, vessel remained stationary with speed 0.0 kn at Port du Stiff (Ouessant). The candidate interval occurred during stationary berth dwell.
- **Disposition:** **`UNVERIFIED`** (Fictitious interval during stationary dwell).
- **Raw Archive Recovery Potential:** High (actual morning run 07:49 $\rightarrow$ 09:30 UTC is recoverable).

### Candidate 3: `VOY-FR-BREST-003`
- **Vessel Identity:** MMSI `228064900` (*ABEILLE BOURBON*), IMO 9308352.
- **Vessel Type Evidence:** Emergency towing and salvage vessel operated for the French Navy (Marine Nationale), not a passenger ferry.
- **Reported Timestamps:** `2015-10-02 04:00:00` to `2015-10-02 08:30:00` (270.0 min).
- **Physical AIS Ground Truth:** Vessel operated an open-sea standby patrol in the Iroise Sea without terminal arrival.
- **Disposition:** **`REJECTED`** (Non-ferry service; open-water endpoint).

### Candidate 4: `VOY-US-SALISH-001`
- **Vessel Identity:** MMSI `316011408` (*COASTAL INSPIRATION*), IMO 9332767. Verified BC Ferries passenger/vehicle ferry.
- **Source File & Identifiers:** `AIS_Tracks_2026_03` layer in `AISVesselTracks2026-03.gpkg`.
- **Reported Phase 02 Timestamps:** `2026-03-01 14:15:00` to `2026-03-01 16:05:00` (110.0 min).
- **Physical AIS Ground Truth:** Database contains 29 tracklines for this vessel on 2026-03-01. Feature `1215` ended at `14:22:58Z`; feature `1216` began at `16:00:01Z`. No feature exists spanning 14:15:00 to 16:05:00. The candidate timestamps were artificially constructed from May 2026 GTFS schedules.
- **Disposition:** **`UNVERIFIED`** (Feature absent from source database).
- **Raw Archive Recovery Potential:** Moderate for retrospective duration (e.g. Feature `1203`, duration 93 min from Duke Point to Tsawwassen).

### Candidate 5: `VOY-US-SALISH-002`
- **Vessel Identity:** MMSI `316001245` (*QUEEN OF ALBERNI*), IMO 7414080. Verified BC Ferries vessel.
- **Source File & Identifiers:** `AIS_Tracks_2026_03`.
- **Reported Phase 02 Timestamps:** `2026-03-02 08:30:00` to `2026-03-02 10:20:00` (110.0 min).
- **Physical AIS Ground Truth:** Database contains 22 tracklines on 2026-03-02. Feature `54502` ended at `08:27:29Z`. No feature corresponds to 08:30:00 to 10:20:00.
- **Disposition:** **`UNVERIFIED`** (Feature absent from source database).

### Candidate 6: `VOY-FR-BREST-004`
- **Vessel Identity:** MMSI `259019000` (Unknown vessel; unlisted in ITU MARS).
- **Reported Timestamps:** `2015-10-01 02:00:00` to `2015-10-01 05:40:00` (220.0 min).
- **Physical AIS Ground Truth:** 45-minute telemetry gap; open-water termination.
- **Disposition:** **`REJECTED`** (Unverified identity; excessive telemetry gap; open-water endpoint).

### Candidate 7: `VOY-US-SALISH-003`
- **Vessel Identity:** MMSI `366709770` (*WSF CHELAN*), IMO 7808140. Verified Washington State Ferries vessel.
- **Source File & Identifiers:** `AIS_Tracks_2026_03`.
- **Reported Phase 02 Timestamps:** `2026-03-01 09:05:00` to `2026-03-01 09:55:00` (50.0 min).
- **Physical AIS Ground Truth:** Source GeoPackage contains exactly ONE single 24-hour trackline (`OBJECTID 3667`, duration 1439 min) aggregating the vessel's entire operating day into one MultiLineString.
- **Disposition:** **`UNVERIFIED`** (Discrete 50-minute voyage does not exist as an independent feature in source).

---

## 4. Record-Count Discrepancy Resolution

| Source File / Metric | Empirical Measurement | Documentation Reference | Resolution Finding |
| :--- | :---: | :--- | :--- |
| `ais_brest_positions_raw.csv` | **18,495,677 lines** | NARI ReadMe: 18,495,677 point locations | **VERIFIED:** Exact count of deduplicated raw kinematic AIS messages. |
| `ais_brest_synopses.csv` | **4,637,652 lines** | datAcron ReadMe: ~4.68M critical points | **VERIFIED:** Exact count of compressed trajectory synopses critical points. |
| `ais_brest_synopses_v0.8.zip` | **24,236,795,478 bytes** | Phase 00 Audit: 24.24 GB uncompressed | **VERIFIED:** Uncompressed byte size across all 9 members of the ZIP archive. |
| "24 Million Observations" Claim | **N/A (Disproven)** | Erroneously transcribed in early Phase 03 notes | **RESOLVED:** Narrative error confusing 24.24 GB uncompressed volume with row count. |

---

## 5. Baselines Audit & Bias Analysis

### A. Physical ETA Baseline (`PhysicalETABaseline`)
- **Unit Dimensionality:** Verified. Distance in nautical miles, speed in knots: $(\text{nm} / \text{kn}) \times 60.0 = \text{minutes}$.
- **Input Guardrails:** Zero, negative, missing, or $> 50\text{ kn}$ speeds return explicit status codes (`UNAVAILABLE_SPEED`, `IMPLAUSIBLE_SPEED`).
- **Limitation:** In the absence of a validated fairway routing graph, straight-line distance underestimates actual nautical distance and is flagged explicitly with a limitation warning.

### B. Historical Route-Duration Baseline (`HistoricalRouteDurationBaseline`)
- **Formula:** $\hat{y} = \max(0.0, \text{median}(T_{\text{hist}}) - t_{\text{elapsed}})$.
- **Bias Analysis:**
  - This formula assumes remaining travel time decreases linearly with elapsed time.
  - When a ferry is delayed ($t_{\text{elapsed}} > \text{median}(T_{\text{hist}})$), the prediction is clamped to $0.0\text{ minutes}$. This is physically biased: a delayed vessel has not arrived; in fact, its conditional remaining duration $E[T - t_{\text{elapsed}} \mid T > t_{\text{elapsed}}]$ is strictly positive.
- **Recommended Non-Leaking Alternative Baseline (Milestone / Progress Conditioned):**
  - Partition route into standardized progress milestones $s \in [0.1, 0.2, \dots, 0.9]$ based on normalized distance along fairway or passage across designated channel waypoints.
  - Predict remaining travel time as the historical median of actual remaining duration from milestone $s$ to destination among past completed voyages:
    $$\hat{y}(s) = \text{median}\left(\{t_{\text{arr}, i} - t_i(s) : i \in \text{PastCompletedVoyages}(t_{\text{pred}})\}\right)$$
  - This avoids elapsed-time clamping bias, accounts for terminal deceleration legs, and preserves strict causality without leakage.

---

## 6. Model Selection Audit & Claims Review

1. **50-Voyage Threshold:** Re-classified as a **preliminary engineering feasibility milestone**, not a statistically established sufficiency threshold. Statistical power calculations require corridor-specific variance estimates.
2. **Snapshot Correlation:** Re-iterated that multiple prediction snapshots sampled from the same voyage are autocorrelated. They provide temporal evaluation coverage but do not constitute independent degrees of freedom.
3. **Inference Latency & Superiority Claims:** Claims that LightGBM evaluates in sub-milliseconds and achieves low generalization error are categorized as **hypotheses to be empirically benchmarked** once real data is segmented.
4. **SHAP Interpretability:** Clarified that SHAP values quantify feature attribution within the learned model; they do **not prove causal correctness or maritime physical validity**.

---

## 7. Data-Source Licensing and Provenance Summary

| Data Source | Acquisition Provenance | Research / Dev Permission | Commercial Use Permission | Attribution Requirements | Status |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **Natural Earth** | NaturalEarthData.com | YES | YES | Public Domain / CC0 | **VERIFIED** |
| **NGA World Port Index** | US National Geospatial-Intelligence Agency | YES | YES | US Public Domain (17 U.S.C. § 105) | **VERIFIED** |
| **MarineCadastre AIS** | US BOEM & NOAA | YES | YES | US Public Domain with NOAA citation | **VERIFIED** |
| **Copernicus Marine** | EU Copernicus Marine Service | YES | YES | Open access with mandatory citation | **VERIFIED** |
| **datAcron Brest AIS** | Zenodo / NARI / UPRC (EU H2020) | YES | **UNRESOLVED** | Citation required; raw NARI redistribution restricted | **UNRESOLVED** |
| **BC Ferries GTFS** | Transitland / BC Ferries Open Data | YES | **UNRESOLVED** | Open transit terms require commercial clearance | **UNRESOLVED** |
| **Balearia / Los Reginas GTFS** | Transitland | YES | **UNRESOLVED** | Third-party commercial redistribution unverified | **UNRESOLVED** |
| **Bee-Line Bus GTFS** | Transitland (Westchester County Bus) | NO | NO | Quarantined / Excluded (non-ferry transit) | **EXCLUDED** |

---

## 8. Summary of Technical Corrections Applied

1. `ml-platform/src/models/baselines.py`: Enforced causal voyage completion check (`arrival_timestamp_utc <= pred_ts`) in `HistoricalRouteDurationBaseline`.
2. `ml-platform/tests/test_phase03_baselines.py`: Added 2 new tests verifying uncompleted voyage exclusion and route isolation. All 10 baseline tests pass.
3. `ml-platform/configs/evaluation_policy.yaml`: Added explicit protocol separation (temporal vs vessel transferability), boundary-spanning voyage rules, and metric limitation descriptions.
4. `ml-platform/configs/eta_feature_contract.yaml`: Clarified terminal point-only representations, uncalibrated heuristic scores, and edge-case dispositions (`AMBIGUOUS_MULTI_BERTH`, `INCOMPLETE_TRACK`, `INTERMEDIATE_WAYPOINT_STOP`, `CENSORED_SIGNAL_LOSS`).
5. `ml-platform/reports/phase-03-correction-log.md`: Published comprehensive correction log.
6. `MEMORY.md`: Root memory updated with final judgment and exact status.

---

## 9. Verification & Test Suite Execution

Full automated test suite executed:
- `tests/test_phase02_feasibility.py`: 6 passed
- `tests/test_phase03_baselines.py`: 10 passed
- `tests/test_profiling.py`: 4 passed
- `tests/test_us_ais_investigator.py`: 5 passed
- **Total Test Result:** **25 passed, 0 failed, 0 skipped** (111.30s).
