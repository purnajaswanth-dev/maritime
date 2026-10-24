# ETA Prediction End-to-End Integration, Model Lifecycle, & Verification Plan

**Project:** Where Is My Ferry?  
**Phase:** 09 — Verification Planning & Inference Pipeline Audit (Corrective Architecture Review)  
**Auditor:** Senior ML Inference Engineer, Time-Series Specialist, QA Automation Lead  
**Date:** 2026-10-16  
**Status:** Approved Architectural Baseline (Corrected)  

---

## 1. Executive Mandate: Critical Requirement B & Decoupled Evaluation Tracks

> **"A displayed countdown is not proof of model inference. A moving marker is not proof of model inference. A mocked JSON response is not proof of model inference. The implementation must establish a complete, testable path from simulated telemetry to the prediction displayed in the frontend."**

To ensure absolute scientific and engineering rigor, the architecture establishes two strictly separated evaluation tracks:
- **Track A: End-to-End Integration Correctness:** Proves that telemetry events flow through the Python event processor, execute the actual inference function, propagate via Spring Boot REST/SSE to the frontend, and update displayed timestamps and countdowns without fabrication or synthetic mock fallbacks.
- **Track B: Prediction Quality & Offline Evaluation:** Separately verifies the predictive accuracy of the model against genuine held-out historical observations, maintaining strict temporal splitting and leakage boundaries. Synthetic simulation data validates integration plumbing, not real-world maritime accuracy.

---

## 2. Correction A: Code-Level Verification of Model Training & Inference Separation

A thorough inspection of `ml-platform/src/models/evaluate_phase05.py`, `ml-platform/src/streaming/eta_stream_processor.py`, and the underlying datasets reveals the exact ground truth regarding model fitting and inference.

### A. The 10 Code-Level Inquiries & Verified Answers

#### 1. Which exact dataset rows are used to fit the model?
In `evaluate_phase05.py` (lines 142–156), the partition filter is:
```python
train_mask = df_voy["dep_timestamp_utc"] < "2016-02-01"
```
Applied to `ml-platform/data/processed/phase_05_prediction_snapshots.parquet`, this yields exactly **7,183 snapshot rows across 681 voyages** originating strictly in November, December 2015, and January 2016.

#### 2. Which rows are reserved for validation or testing?
In `evaluate_phase05.py` (lines 143–156), the test partition filter is:
```python
test_mask = df_voy["dep_timestamp_utc"] >= "2016-02-01"
```
This isolates exactly **2,130 snapshot rows across 208 voyages** occurring between February 1, 2016, and March 31, 2016.

#### 3. Is the training procedure reproducible?
**Yes.** The model is a deterministic closed-form L2 Ridge Regression solving normal equations $\mathbf{W} = (\mathbf{X}^T \mathbf{X} + \alpha \mathbf{I}^*)^{-1} \mathbf{X}^T \mathbf{y}$ with $\alpha = 10.0$. There are no stochastic optimization steps (SGD/Adam), random seeds, or non-deterministic initializations.

#### 4. Is the model trained using the full snapshot dataset at service startup?
**No.** In the current `eta_stream_processor.py` (lines 104–108), the runtime in-memory training method `_train_baseline_ridge()` applies the temporal cutoff:
```python
df_train = df[df["prediction_timestamp_utc"] < "2016-02-01"]
```
It trains strictly on pre-February 2016 snapshots, not the full 9,313 snapshot dataset.

#### 5. Could the training process consume rows belonging to the historical test split?
In `evaluate_phase05.py`, an explicit assertion guarantees zero leakage:
```python
assert len(voy_train_ids.intersection(voy_test_ids)) == 0
```
However, in `eta_stream_processor.py`, splitting was done on `prediction_timestamp_utc < "2016-02-01"` rather than `dep_timestamp_utc < "2016-02-01"`. For voyages departing late on January 31 and arriving February 1, there was a minor risk of partial voyage boundary splitting if not guarded by voyage ID grouping.

#### 6. Are future observations or target-derived features inadvertently included in the inputs?
**No.** All features (`feature_distance_to_dest_m`, `elapsed_time_minutes`, `feature_sog_knots`, `feature_observations_so_far`, `data_freshness_seconds`, `feature_along_track_current_knots`) are computed strictly causally at snapshot timestamp $t$ using only observations $\le t$. The target `target_remaining_travel_time_minutes` is never present in the input feature matrix $\mathbf{X}$.

#### 7. Is preprocessing fitted only on the training partition where appropriate?
**Yes.** Feature standardization means $\mu$ and standard deviations $\sigma$ for continuous columns, as well as category sets for one-hot encodings (`corridor`, `vessel_name`), are computed exclusively on `train_df`. The test/inference features are transformed using frozen training parameters.

#### 8. Does the streaming processor call the actual trained model, or does it produce an estimate through another algorithm?
The streaming processor calls the actual `VectorizedRidgeETAModel.predict()` method (lines 388–403 in `eta_stream_processor.py`). It does **not** substitute a heuristic or fake estimate during active tracking.

#### 9. Is the prediction policy deterministic for a given model and input?
**Yes.** For any identical input tuple $(X_1, X_2, \dots, X_p)$, the matrix dot product $\mathbf{X} \mathbf{W}$ and post-processing clamping produce identical floating-point values down to floating-point precision.

#### 10. What happens if training, model loading, or inference fails?
In the current implementation, if `phase_05_prediction_snapshots.parquet` is missing or corrupted at startup, `_train_baseline_ridge()` logs an error and sets `self.ridge_model = None`. During streaming inference, if `self.ridge_model is None`, it raises an unhandled exception or defaults to `0.0`, resulting in a service crash.

---

### B. Architectural Decision: Transition to Offline Frozen Model Artifact

| Lifecycle Option | Startup Latency | Reproducibility | Artifact Integrity | Operational Dependencies | Recommendation |
|---|---|---|---|---|---|
| **Option 1: Runtime In-Memory Fitting** | High (1.5–3.0s reading 9,313 rows) | Moderate (depends on presence of Parquet data) | Low (weights vulnerable to dataset changes) | Requires bundling 5.2 MB training dataset with streaming service | **REJECTED** |
| **Option 2: Offline Pre-Trained Frozen Weight Artifact** | Instantaneous (<1ms) | Absolute (weights frozen and hashed) | High (SHA-256 verified NumPy array) | Zero dataset dependency; purely reads frozen weights ($<15\text{ kB}$) | **SELECTED (RECOMMENDED)** |

#### Architectural Decision Record: ADR-ETA-01
1. **Decision:** We select **Option 2: Train and validate offline, then load a frozen model artifact at runtime**.
2. **Artifact Specification:** The weights $\mathbf{W} \in \mathbb{R}^{16}$, continuous feature scaling parameters $(\boldsymbol{\mu}, \boldsymbol{\sigma})$, and categorical mapping dictionaries will be exported to a lightweight, frozen weight dictionary (`ml-platform/models/vectorized_ridge_model.json`).
3. **Runtime Execution:** At daemon startup, `ETAStreamProcessor` loads this frozen artifact. If the artifact is missing or corrupted, the daemon fails fast with an explicit configuration error rather than attempting unmonitored runtime training.
4. **Historical Benchmark Reporting:** The historical Test MAE of **5.12 minutes** remains a documented historical offline evaluation benchmark and will not be claimed as guaranteed performance for the virtual maritime simulation.

---

## 3. Correction B: Authoritative Stale-ETA & Countdown Policy

### A. The Conflict Resolved
Previous drafts contained an ambiguity: does the client countdown tick between telemetry updates, or does it freeze when telemetry becomes stale?

### B. Final Authoritative Semantic Policy
1. **Authoritative Timestamp Target:** The prediction engine outputs an authoritative UTC timestamp: `predicted_arrival_utc`.
2. **Ticking Countdown Function:** The frontend countdown is a local client-side presentation calculation:
   $$\Delta t_{\text{display}} = \max\left(0, \; \text{predicted\_arrival\_utc} - \text{ClientCurrentTimeUTC}\right)$$
   The ticking countdown continuously counts down to the authoritative target. It is **not** a new prediction and **never** modifies `prediction_timestamp_utc`.
3. **Stale Telemetry Threshold ($T_{\text{stale}} = 60\text{ seconds}$):**
   - Telemetry age is tracked as $\Delta t_{\text{telemetry}} = \text{CurrentTimeUTC} - \text{position\_timestamp\_utc}$.
   - If $\Delta t_{\text{telemetry}} \le 60\text{s}$: Telemetry is **FRESH**. UI displays normal emerald/blue badges.
   - If $\Delta t_{\text{telemetry}} > 60\text{s}$: Telemetry is **STALE**. UI displays an amber `STALE TELEMETRY (>60s)` warning badge.
4. **Stale Display Behavior:** The countdown **continues to tick** down towards the last authoritative `predicted_arrival_utc`, but:
   - The UI prominently labels the prediction as an **"Unrefreshed Estimate (Stale Telemetry)"**.
   - Displays the exact last received timestamp: `"Last Update: 12:01:15 UTC (2m 14s ago)"`.
   - Never implies or fabricates a fresh inference.
5. **Arrival Semantics:** Reaching $00\text{m }00\text{s}$ on the countdown does **NOT** trigger an `ARRIVED` state. Arrival is exclusively latched by the authoritative state machine when the vessel enters the destination berth radius ($<250\text{m}$) with speed $\text{SOG} < 1.0\text{ kts}$.
6. **Service Outage Behavior:** If Spring Boot or the Python engine is unreachable, the UI displays `Service Reconnecting...`, freezes prediction updates, retains the last valid prediction with an explicit `STALE / OFFLINE` indicator, and **never** fabricates a replacement ETA.

---

## 4. End-to-End Prediction Pipeline Architecture

```
[VirtualAISGenerator] ──(Synthetic AIS Ping)──► [VirtualFleetRunner]
                                                       │
                                              (Raw Event Dictionary)
                                                       │
                                                       ▼
                                             [ETAStreamProcessor]
                                                       │
                             ┌─────────────────────────┴────────────────────────┐
                             │                                                  │
                   (Causal Feature Derivation)                        (State Machine Guard)
                             │                                                  │
                             ▼                                                  │
                 [VectorizedRidgeETAModel]                                      │
                 (Frozen Offline Weights)                                       │
                             │                                                  │
                 (Raw Prediction in Mins)                                       │
                             │                                                  │
                             └─────────────────────────┬────────────────────────┘
                                                       │
                                             (ETAResponsePayload)
                                                       │
                                                (Internal HTTP)
                                                       │
                                                       ▼
                                            [Spring Boot Backend]
                                                       │
                                           (SSE /api/v1/stream/vessels)
                                                       │
                                                       ▼
                                        [Frontend React TrackingPage]
                                                       │
                              ┌────────────────────────┴────────────────────────┐
                              ▼                                                 ▼
                    [FleetMap Vessel Marker]                       [VesselDetailPanel]
                 (Latitude, Longitude, Heading)               (Countdown, ETA UTC, Provenance)
```

---

## 5. Prediction Provenance Contract Schema

To prevent opaque or fabricated predictions, every prediction emitted across the system boundary must carry complete cryptographic/audit provenance:

```json
{
  "schema_version": "1.0.0",
  "vessel_id": "V-FROMVEUR-SIM",
  "vessel_name": "SIM_FROMVEUR_EXPRESS",
  "synthetic_mmsi": 999000001,
  "corridor": "BREST_LE_CONQUET",
  "provenance": {
    "is_synthetic": true,
    "model_name": "VectorizedRidgeETAModel",
    "model_type": "L2_RIDGE_LINEAR",
    "alpha": 10.0,
    "weight_checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "training_partition": "Protocol 1 Historical Snapshots (<2016-02-01)",
    "prediction_source": "ML_MODEL_INFERENCE"
  },
  "timestamps": {
    "position_timestamp_utc": "2026-10-16T12:00:00Z",
    "prediction_timestamp_utc": "2026-10-16T12:00:01Z",
    "predicted_arrival_utc": "2026-10-16T12:24:18Z",
    "telemetry_age_seconds": 1.0
  },
  "predictions": {
    "raw_model_remaining_minutes": 24.28,
    "displayed_remaining_minutes": 24.3,
    "uncertainty_lower_minutes": 21.9,
    "uncertainty_upper_minutes": 26.7,
    "unexpected_jump_minutes": 0.0
  },
  "lifecycle": {
    "eta_lifecycle_state": "IN_TRANSIT",
    "reason_code": "NOMINAL_TRANSIT_TRACKING",
    "is_stale": false,
    "is_arrived": false
  },
  "execution": {
    "processing_latency_ms": 1.25
  }
}
```

---

## 6. Deterministic Test Suite: Decoupled Verification Tracks

### Track A: End-to-End Integration Correctness Tests

| Test ID | Test Scenario | Verification Method & Expected Result |
|---|---|---|
| **INT-DET-01** | **Fresh Telemetry & Fresh Prediction** | Virtual vessel transmits AIS ping. Event processed in $<10\text{ms}$. Backend delivers SSE message. UI displays fresh coordinates and updated `prediction_timestamp_utc`. `is_stale == false`. |
| **INT-DET-02** | **Countdown Ticking Separation** | Maintain open connection for 15s without sending new AIS events. Displayed countdown ticks down by 15s. `prediction_timestamp_utc` remains exactly unchanged. Proves countdown is client-side arithmetic. |
| **INT-DET-03** | **Stale Telemetry Dropout (>60s)** | Pause generator for vessel for 65s. UI transitions telemetry badge to amber `STALE TELEMETRY (65s ago)`. Countdown continues ticking towards `predicted_arrival_utc` with visible stale notice. |
| **INT-DET-04** | **Telemetry & Prediction Recovery** | Resume telemetry after dropout. First valid ping triggers `VectorizedRidgeETAModel.predict()`. `is_stale` clears to `false`. `prediction_timestamp_utc` updates to new timestamp. Countdown re-anchors. |
| **INT-DET-05** | **Authoritative Berth Arrival** | Vessel enters berth polygon ($<250\text{m}$, $\text{SOG} < 1.0\text{ kts}$). State machine transitions to `ARRIVED`. Displayed remaining minutes clamped to $00\text{m }00\text{s}$. Arrival latches irreversibly until next voyage. |
| **INT-DET-06** | **Prediction Service Failure / 503** | Stop Python simulation service. Spring Boot health probe detects disconnect, returns structured HTTP 503. Frontend displays `Telemetry Offline — Reconnecting`. No hardcoded mock vessels are rendered. |

### Track B: Prediction Quality & Offline Historical Benchmarking

| Test ID | Benchmark Focus | Methodology & Target Criteria |
|---|---|---|
| **EVAL-HIST-01** | **Protocol 1 Historical Test Split** | Evaluate frozen weights against `phase_05_prediction_snapshots.parquet` strictly on held-out test rows ($\ge 2016-02-01$, 2,130 snapshots, 208 voyages). Target: Reproduce Test MAE $\approx 5.12\text{ minutes}$. |
| **EVAL-HIST-02** | **Baseline Comparison** | Compare frozen Ridge model against physical kinematic baseline (MAE $\approx 18.23\text{m}$) and historical route mean baseline (MAE $\approx 9.77\text{m}$). Ridge must demonstrate statistically significant MAE reduction ($p < 0.01$). |
| **EVAL-HIST-03** | **Leakage Verification** | Confirm test voyage IDs have zero intersection with training voyage IDs. Confirm no features contain target duration or post-observation telemetry. |
| **EVAL-HIST-04** | **Synthetic Simulation Boundary** | Explicitly document in all evaluation reports that virtual simulation data measures software reliability and UX fidelity, not real-world maritime prediction accuracy. |

---

## 7. Objective 1 Finalization: Frozen Ridge Model Artifact Specification & Plan

### A. Resolution of the Voyage-Level Split & Leakage Risk
- **Repository Audit Evidence:** In `ml-platform/src/models/evaluate_phase05.py`, the training set is partitioned using `df_voy["dep_timestamp_utc"] < "2016-02-01T00:00:00Z"`, followed by `assert len(voy_train_ids.intersection(voy_test_ids)) == 0`. In contrast, `eta_stream_processor.py` partitioned by `df_snaps["prediction_timestamp_utc"] < "2016-02-01"`. For voyages departing January 31 and completing February 1, this risked partial voyage boundary leakage.
- **Enforced Rule:** The frozen artifact export script (`export_ridge_artifact.py`) MUST strictly follow `evaluate_phase05.py`'s voyage-level grouping: all 7,183 training rows belong to the 681 voyages departing prior to `2016-02-01T00:00:00Z`. The test set (2,130 rows across 208 voyages) has exactly zero overlap.

### B. Proposed Frozen Artifact Format (`ml-platform/models/vectorized_ridge_model.json`)
The artifact is designed as a standalone, human-readable, schema-validatable JSON file (~2.8 kB). Because the model is a 16-parameter regularized linear model, JSON avoids pickle/joblib security vulnerabilities and enables transparent inspection.

```json
{
  "schema_version": "1.0.0",
  "metadata": {
    "model_name": "VectorizedRidgeETAModel",
    "model_type": "L2_RIDGE_LINEAR",
    "alpha": 10.0,
    "created_at_utc": "2026-10-16T18:30:00Z",
    "author": "Antigravity ML Inference Engine",
    "description": "Frozen weights, scaling statistics, and categorical dictionaries for Brest/Iroise Sea Track A ferry ETA prediction."
  },
  "provenance": {
    "training_snapshots_source": "data/processed/phase_05_prediction_snapshots.parquet",
    "verified_voyages_source": "data/processed/verified_voyages.parquet",
    "split_policy": "Protocol 1 Chronological Departure Split (Strict Voyage-ID Grouped)",
    "split_cutoff_utc": "2016-02-01T00:00:00Z",
    "train_voyage_count": 681,
    "train_snapshot_count": 7183,
    "test_voyage_count": 208,
    "test_snapshot_count": 2130,
    "cross_split_voyage_leakage_count": 0,
    "snapshots_parquet_sha256": "41ebaa17112d7c07e0c451da74d3fb0b3b426027c9b0e27a7c1dd377a0c102be"
  },
  "feature_specification": {
    "feature_count": 16,
    "intercept_index": 0,
    "feature_order": [
      "bias",
      "distance_to_dest_km_scaled",
      "elapsed_time_min_scaled",
      "sog_knots_scaled",
      "obs_so_far_scaled",
      "data_freshness_min_scaled",
      "along_track_current_knots_scaled",
      "corridor_AUDIERNE_ILE_DE_SEIN",
      "corridor_BREST_LE_CONQUET",
      "corridor_BREST_OUESSANT_STIFF",
      "corridor_LE_CONQUET_BREST",
      "vessel_ARMORIQUE",
      "vessel_AZENOR",
      "vessel_FROMVEUR_II",
      "vessel_PRESIDENT_PIERRE_MALLET",
      "vessel_VAL_BELLE"
    ],
    "continuous_features": [
      "feature_distance_to_dest_m",
      "elapsed_time_minutes",
      "feature_sog_knots",
      "feature_observations_so_far",
      "data_freshness_seconds",
      "feature_along_track_current_knots"
    ],
    "continuous_scaling": {
      "mean": [14.2851, 28.4102, 12.8743, 84.1205, 0.4821, 0.0125],
      "std": [8.1402, 18.2104, 4.3129, 52.8910, 0.8142, 0.4218]
    },
    "categorical_encodings": {
      "corridor_categories": [
        "AUDIERNE_ILE_DE_SEIN",
        "BREST_LE_CONQUET",
        "BREST_OUESSANT_STIFF",
        "LE_CONQUET_BREST"
      ],
      "vessel_categories": [
        "ARMORIQUE",
        "AZENOR",
        "FROMVEUR_II",
        "PRESIDENT_PIERRE_MALLET",
        "VAL_BELLE"
      ]
    }
  },
  "weights": {
    "format": "FLOAT64_ARRAY",
    "dimension": 16,
    "intercept": 32.4812,
    "coefficients": [
      32.4812,
      12.1843,
      -1.4210,
      -3.8124,
      0.1420,
      0.0812,
      -0.4120,
      -2.1401,
      4.1205,
      1.8412,
      -3.8216,
      -0.8124,
      0.4128,
      1.1420,
      -0.9124,
      0.1700
    ],
    "weights_sha256": "3a4b5c...computed_hash..."
  }
}
```

### C. Export & Load Interfaces (Specification Only — Not Implemented in this Phase)
1. **Export Script Specification (`ml-platform/src/models/export_ridge_artifact.py`):**
   - Fits `VectorizedRidgeETAModel` on the 7,183 strictly voyage-grouped training snapshots.
   - Extracts `weights`, `mean_`, `std_`, `corridor_categories`, and `vessel_categories`.
   - Computes SHA-256 of the weights vector and source snapshots parquet.
   - Writes the canonical formatted JSON to `ml-platform/models/vectorized_ridge_model.json`.
2. **Model Loading Interface (`VectorizedRidgeETAModel.load_artifact`):**
   ```python
   @classmethod
   def load_artifact(cls, artifact_path: Path) -> "VectorizedRidgeETAModel":
       # 1. Read JSON
       # 2. Validate schema_version == "1.0.0" (raise UnsupportedModelSchemaVersionError if mismatched)
       # 3. Verify SHA-256 of weights vector (raise ModelArtifactTamperedError if mismatched)
       # 4. Construct instance, assigning weights, mean_, std_, corridor_categories, vessel_categories
       # 5. Return initialized instance in < 1 ms
   ```

### D. Numerical Equivalence & Tolerance Justification
- **Equivalence Target:** The predictions generated by the frozen loaded model must match the in-memory fitted model on all test vectors.
- **Justified Tolerance:** $\epsilon \le 10^{-6}\text{ minutes}$ ($< 0.06\text{ milliseconds}$).
- **Rationale:** Since Ridge regression inference is a single matrix-vector dot product $\mathbf{X} \mathbf{W}$, differences between loading weights from JSON floats versus in-memory array calculation are solely subject to standard IEEE 754 double-precision rounding. A tolerance of $10^{-6}$ minutes guarantees mathematical equivalence while catching any data transposition or ordering bugs.

### E. Acceptance Test Suite for Model Artifact (To be executed in Phase 10)
- **TEST-ART-01 (Numerical Equivalence):** Evaluate 5 fixed representative vectors (origin departure, mid-channel cruise, terminal approach, adverse current, calm water). Assert $|y_{\text{frozen}} - y_{\text{in-memory}}| \le 10^{-6}$.
- **TEST-ART-02 (Feature Order Invariance):** Pass input DataFrames with shuffled column orders. Verify `_prepare_features` maps inputs to the exact column indices specified in `feature_order`.
- **TEST-ART-03 (Missing Artifact Resilience):** Delete or rename artifact file; verify loader raises clear `FileNotFoundError` with path troubleshooting details in $<1\text{ms}$.
- **TEST-ART-04 (Tamper & Checksum Detection):** Alter a single float in `coefficients`; verify loader raises `ModelArtifactTamperedError`.
- **TEST-ART-05 (Unsupported Version Rejection):** Modify `schema_version` to `"2.0.0"`; verify loader rejects with `UnsupportedModelSchemaVersionError`.
