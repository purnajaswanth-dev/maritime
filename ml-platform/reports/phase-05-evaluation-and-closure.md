# Phase 05 Final Evaluation and Closure Report

**Project:** Where Is My Ferry?  
**Phase:** 05 — Snapshots, Baselines, and Controlled ETA Model Evaluation  
**Author:** Antigravity Senior Maritime Applied ML & Evaluation Specialist  
**Evaluation Scope:** Track A (Brest / Iroise Sea Passenger Ferry Corridor)  
**Status:** COMPLETED — STOP CONDITION ENFORCED (Awaiting User Review)

---

## 1. Executive Summary & Quality Gate Certification

Phase 05 has successfully materialized causal prediction snapshots from the 889 accepted real-world voyages, evaluated physical and causal historical baselines, trained and tested a regularized tabular machine learning model under the approved chronological protocol, conducted an exploratory unseen-vessel case study, and analyzed sequential ETA stability.

### Quality Gate Audit Summary

| Check / Gate | Target Requirement | Verified Result | Status |
| :--- | :--- | :--- | :---: |
| **Source Preservation** | Source archives & Phase 02–04 artifacts untouched | Byte-for-byte verified | **PASS** |
| **Causal Integrity** | No telemetry timestamped after prediction timestamp | Latest observation age $\ge 0$ for 100% of rows | **PASS** |
| **Target Validity** | Remaining travel time strictly positive | $t_{\text{remaining}} > 0$ for all 9,313 snapshots | **PASS** |
| **Split Disjointness** | Whole voyages kept together; 0 cross-split overlap | Set intersection of Train & Test voyage IDs is $\emptyset$ | **PASS** |
| **Leakage Isolation** | Training period strictly precedes test period | Train: Oct 2015 – Jan 2016; Test: Feb – Mar 2016 | **PASS** |
| **Test Suite** | Unit tests passing across entire repo | 100% passing (including 5 new Phase 05 tests) | **PASS** |

---

## 2. Dataset Materialization & Chronological Partition

### 2.1 Causal Snapshot Dataset
- **Artifact:** [`ml-platform/data/processed/phase_05_prediction_snapshots.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/processed/phase_05_prediction_snapshots.parquet)
- **Total Records:** **9,313 prediction snapshots** sampled every 5.0 minutes across 889 verified voyages.
- **Size:** 841,114 bytes.
- **Rejections:** 0 snapshots rejected (all verified voyages contained at least 2 valid AIS observations within bounds).
- **Lineage Manifest:** [`ml-platform/data/manifests/phase-05-source-lineage.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-05-source-lineage.json).

### 2.2 Protocol 1 Chronological Split
The evaluation strictly followed Protocol 1, partitioning whole voyages by departure timestamp:
- **Training Period:** 2015-10-01T00:00:00Z to 2016-01-31T23:59:59Z
  - **Voyages:** 685 (77.1%)
  - **Snapshots:** 6,941 (74.5%)
  - **Vessels:** 4 (FROMVEUR II, ENEZ EUSSA 3, ENEZ SUN 3, ANDRE COLIN)
  - **Corridors:** 5
- **Test Period:** 2016-02-01T00:00:00Z to 2016-03-31T23:59:59Z
  - **Voyages:** 204 (22.9%)
  - **Snapshots:** 2,372 (25.5%)
  - **Vessels:** 4
  - **Corridors:** 5
  - **Cross-Split Voyage Overlap:** **0 voyages** (strictly disjoint).

---

## 3. Comprehensive Model & Baseline Evaluation Results

All models and baselines were evaluated on the exact same 2,372 unseen test snapshots.

### 3.1 Overall Benchmark Performance (Protocol 1 Test Set, $N = 2,372$)

| Metric | Physical Kinematic (Pure) | Physical Kinematic (Current-Augmented) | Historical Route Duration (Causal) | Tabular Ridge ML ($\alpha=10.0$) | Tabular Advantage vs Physical |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **MAE (minutes)** | 18.23 | 18.20 | 5.55 | **5.20** | **-71.5% (-13.03m)** |
| **Median Absolute Error (min)** | 8.44 | 8.55 | **2.90** | 3.56 | **-57.8% (-4.88m)** |
| **RMSE (minutes)** | 43.33 | 43.23 | 8.71 | **7.47** | **-82.8% (-35.86m)** |
| **Mean Error Bias (min)** | -0.94 | -1.01 | -1.26 | **+0.07** | **Near-zero bias** |
| **P50 Absolute Error (min)** | 8.44 | 8.55 | **2.90** | 3.56 | -4.88m |
| **P75 Absolute Error (min)** | 20.87 | 20.92 | **6.23** | 6.76 | -14.11m |
| **P90 Absolute Error (min)** | 31.01 | 30.94 | 14.98 | **12.14** | **-18.87m** |
| **P95 Absolute Error (min)** | 45.90 | 45.88 | 23.87 | **16.67** | **-29.23m** |
| **P99 Absolute Error (min)** | 208.37 | 208.37 | 27.64 | **25.83** | **-182.54m** |
| **Max Error (min)** | 373.59 | 373.59 | **31.68** | 34.14 | -339.45m |
| **Within 3 Minutes (%)** | 26.7% | 26.6% | **51.4%** | 44.4% | +17.7% |
| **Within 5 Minutes (%)** | 38.4% | 38.5% | **69.1%** | 62.9% | +24.5% |
| **Within 10 Minutes (%)** | 54.3% | 54.2% | 83.0% | **86.0%** | **+31.7%** |
| **Large Errors (>15m) (%)** | 34.7% | 34.9% | 9.9% | **6.4%** | **-81.5% reduction** |
| **Premature Arrival Rate (%)** | 76.9% | 77.3% | 58.5% | **47.6%** | **Balanced (47.6 / 52.4)** |

### 3.2 Copernicus Ocean Current Collocation Findings
- **Hypothesis:** Collocating Copernicus GLORYS12V1 ocean currents (`uo`, `vo`) along-track will significantly improve physical kinematic ETA accuracy.
- **Experimental Result:** MAE changed from **18.23 minutes** (pure kinematic) to **18.20 minutes** (current-augmented), a negligible difference of **0.03 minutes (1.8 seconds)**.
- **Root Cause Analysis:**
  1. **Temporal Mismatch:** The Copernicus GLORYS12V1 reanalysis provides daily-mean fields ($P1D$). The Iroise Sea and Fromveur Passage are dominated by semidiurnal tidal currents with a 12.4-hour period where current speeds reverse and peak at 4 to 8 knots. Daily averages smooth out these tidal extremes.
  2. **Spatial Resolution:** A 0.083° grid (~9 km) cannot resolve narrow harbor channels, Goulet de Brest bathymetric choking, or shallow shoals around Molène.
- **Scientific Conclusion:** Global daily reanalysis currents are unsuitable for short-range tidal ferry ETA modeling without high-resolution hydrodynamic tidal models (e.g., MARS2D/TELEMAC).

---

## 4. Granular Performance Slices (Tabular Ridge Model)

### 4.1 Slices by Prediction Horizon (Remaining Time)

| Horizon Bucket | Snapshot Count | Physical MAE | Historical MAE | Tabular Ridge MAE | Within 5m (%) | Within 10m (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **< 15 minutes** | 647 | 11.23 min | **2.62 min** | 2.73 min | **89.5%** | **98.5%** |
| **15 – 30 minutes** | 599 | 12.35 min | 4.31 min | **3.73 min** | 78.6% | **94.8%** |
| **30 – 60 minutes** | 868 | 21.05 min | 6.78 min | **6.00 min** | 46.2% | **83.1%** |
| **> 60 minutes** | 258 | 39.95 min | 11.66 min | **10.97 min** | 16.3% | **44.2%** |

*Insight:* In the critical arrival window (<30 minutes), the Tabular Ridge model achieves **94.8% to 98.5% accuracy within 10 minutes**, eliminating the wild deceleration errors of the physical baseline.

### 4.2 Slices by Corridor

| Corridor | Test Snapshots | Physical MAE | Historical MAE | Tabular Ridge MAE | Tabular RMSE |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **AUDIERNE_ILE_DE_SEIN** | 511 | 17.75 min | 4.80 min | **4.72 min** | 6.13 min |
| **ILE_DE_SEIN_AUDIERNE** | 35 | 23.02 min | **3.24 min** | 5.91 min | 6.44 min |
| **BREST_LE_CONQUET** | 604 | 19.41 min | **4.85 min** | 6.26 min | 8.87 min |
| **LE_CONQUET_BREST** | 1,195 | 17.15 min | 6.00 min | **4.64 min** | 7.03 min |
| **BREST_OUESSANT_STIFF** | 27 | 27.81 min | 13.54 min | **10.81 min** | 12.38 min |

### 4.3 Slices by Vessel

| Vessel Name | MMSI | Test Snapshots | Physical MAE | Historical MAE | Tabular Ridge MAE |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **FROMVEUR II** | 228017700 | 1,073 | 16.89 min | 5.75 min | **5.79 min** |
| **ENEZ EUSSA 3** | 227002630 | 726 | 19.34 min | 5.56 min | **5.37 min** |
| **ENEZ SUN 3** | 227002330 | 546 | 18.08 min | **4.70 min** | 4.88 min |
| **ANDRE COLIN** | 227005550 | 27 | 27.81 min | 13.54 min | **10.81 min** |

### 4.4 Slices by Ground-Truth Evidence Grade

| Evidence Grade | Test Snapshots | Physical MAE | Historical MAE | Tabular Ridge MAE | Large Error (>15m) % |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **HIGH_AIS_BERTH_OBSERVED** | 1,844 (77.7%) | 17.91 min | 5.61 min | **5.16 min** | 5.9% |
| **MEDIUM_ALGORITHMIC_STOP** | 528 (22.3%) | 19.33 min | 5.34 min | **6.22 min** | 8.1% |

*Insight:* Both evidence grades exhibit consistent model performance. High-grade berth-observed arrivals have slightly lower MAE (5.16m vs 6.22m) and lower catastrophic error rates (5.9% vs 8.1%), validating the Phase 04 labeling hierarchy.

---

## 5. Protocol 2: Exploratory Unseen-Vessel Fleet Generalization

To test whether the model can generalize zero-shot to a completely unseen vessel, we executed Protocol 2 as an exploratory case study:

### Case Study A: Shared Corridor Leave-One-Out
- **Held-Out Vessel:** *ENEZ EUSSA 3* (MMSI 227002630)
- **Routes Served:** Brest – Le Conquet (shared with *FROMVEUR II*)
- **Training Vessels:** *FROMVEUR II*, *ENEZ SUN 3*, *ANDRE COLIN* (7,078 snapshots)
- **Zero-Shot Test Performance ($N = 2,235$ snapshots):**
  - MAE: **6.40 min** | MedAE: **4.17 min** | RMSE: **9.01 min**
  - Within 10 min: **79.3%** | Large Errors (>15m): **9.3%**
  - *Result:* Because *FROMVEUR II* sailed the identical corridor, the model transferred corridor geometry effectively despite never seeing *ENEZ EUSSA 3*.

### Case Study B: Exclusive Corridor Leave-One-Out
- **Held-Out Vessel:** *ENEZ SUN 3* (MMSI 227002330)
- **Routes Served:** Audierne – Île de Sein (exclusive route; no other vessel sailed here)
- **Training Vessels:** *FROMVEUR II*, *ENEZ EUSSA 3*, *ANDRE COLIN* (7,103 snapshots)
- **Zero-Shot Test Performance ($N = 2,210$ snapshots):**
  - MAE: **9.48 min** | MedAE: **5.52 min** | RMSE: **13.88 min**
  - Within 10 min: **62.8%** | Large Errors (>15m): **19.8%**
  - *Result:* When a vessel is the sole operator on a route, holding it out eliminates corridor-specific geometric calibration, degrading zero-shot performance substantially.

### Protocol 2 Methodological Conclusion
> [!IMPORTANT]
> With $N = 4$ total vessels in the entire fleet dataset, **zero-shot fleet generalization is mathematically confounded with route coverage**. Protocol 2 cannot be claimed as a statistically conclusive test of generalized vessel physics. Zero-shot claims across arbitrary unseen fleets must be explicitly rejected.

---

## 6. Leakage, Data Integrity, and Lineage Audit

1. **Chronological Splitting:** The split was enforced on voyage departure time (`2016-02-01T00:00:00Z`). All 685 training voyages finished or started strictly before February 1. All 204 test voyages departed strictly on or after February 1.
2. **Feature Scaler & Category Isolation:** In `VectorizedRidgeETAModel`, continuous feature means and standard deviations were computed exclusively on `df_train`. Categorical one-hot matrices were defined by training categories. Test instances with unseen categories receive zero dummy weights and fallback safely to the global intercept and continuous kinematics.
3. **Historical Baseline Isolation:** At each snapshot timestamp $T_{\text{pred}}$, the causal historical baseline only queries voyages whose `arr_timestamp_utc` $< T_{\text{pred}}$. Current and future voyages are strictly excluded.
4. **Source Archive Immutability:** All source archives (`ais_brest_synopses_v0.8.zip`, `AISVesselTracks2026-03.zip`, NetCDF) and Phase 02–04 artifacts were verified unaltered with identical MD5 checksums.

---

## 7. Deliverables & Artifact Inventory

| Category | Artifact Path | Size / Count | Purpose |
| :--- | :--- | :---: | :--- |
| **Snapshots** | [`ml-platform/data/processed/phase_05_prediction_snapshots.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/processed/phase_05_prediction_snapshots.parquet) | 9,313 rows (841 KB) | Causal prediction snapshots |
| **Predictions** | [`ml-platform/data/processed/phase_05_test_predictions.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/processed/phase_05_test_predictions.parquet) | 2,372 rows (261 KB) | Test set model & baseline outputs |
| **Lineage** | [`ml-platform/data/manifests/phase-05-source-lineage.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-05-source-lineage.json) | 8.8 KB | Complete upstream & downstream lineage |
| **Metrics** | [`ml-platform/data/manifests/phase-05-evaluation-metrics.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-05-evaluation-metrics.json) | 5.5 KB | Benchmark metrics & slices |
| **Case Study** | [`ml-platform/data/manifests/phase-05-protocol2-case-study.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-05-protocol2-case-study.json) | 2.1 KB | Exploratory Protocol 2 metrics |
| **Pipeline Code** | [`ml-platform/src/ingestion/materialize_snapshots.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/ingestion/materialize_snapshots.py) | 165 lines | Snapshot generator pipeline |
| **Evaluation Code**| [`ml-platform/src/models/evaluate_phase05.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/models/evaluate_phase05.py) | 374 lines | Baselines & Ridge model evaluation |
| **Case Study Code**| [`ml-platform/src/models/evaluate_protocol2_case_study.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/models/evaluate_protocol2_case_study.py) | 170 lines | Protocol 2 leave-one-vessel-out runner |
| **Unit Tests** | [`ml-platform/tests/test_phase05_evaluation.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/tests/test_phase05_evaluation.py) | 170 lines | 5 automated integrity tests |
| **Stability Report**| [`ml-platform/reports/phase-05-eta-stability-and-overshoot.md`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/reports/phase-05-eta-stability-and-overshoot.md) | Markdown | 2,168-step replay & overshoot analysis |

---

## 8. Go / No-Go Decision & Next Step Recommendations

### Go / No-Go Recommendation

> [!IMPORTANT]
> **GO / NO-GO RECOMMENDATION: CONDITIONAL "GO" FOR TRACK A OFFLINE ML BASELINE; "NO-GO" FOR UNVALIDATED LIVE SERVICE DEPLOYMENT.**
> 
> 1. **GO (Approved):** The Tabular Ridge model (`VectorizedRidgeETAModel`) is approved as the primary offline benchmark model for Track A. It decisively beats the physical kinematic baseline (5.20m vs 18.23m MAE), reduces large errors by 81.5%, and achieves 86.0% accuracy within 10 minutes.
> 2. **NO-GO (Halted):** Do NOT deploy this model to live production APIs or passenger-facing clients. Retrospective offline logs cannot validate real-time cellular telemetry latency, WebSocket streaming stability, or out-of-order message handling.
> 3. **NO-GO (Halted):** Do NOT use daily Copernicus ocean reanalysis for real-time ETA correction. It provides no statistically significant accuracy improvement in tidal corridors.
> 4. **NO-GO (Halted):** Do NOT claim zero-shot generalization across unobserved ferry fleets.

### Scope Boundaries for Next Phases
- **Phase 06 (Application Architecture & Mock Live Streaming):** When authorized, Phase 06 should design the backend service contract, API boundaries, and streaming replay harness without declaring production live readiness until live end-to-end testing passes.
- **Strict Stop Condition:** Work is paused immediately. Antigravity will make no further modifications or transitions until explicit user authorization.
