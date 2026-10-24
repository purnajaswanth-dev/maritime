# Where Is My Ferry? — Phase 03: ETA Modeling Specification & Baseline Architecture

**Date:** 2026-10-16  
**Auditor / Engineer:** Senior ML Engineer & Data Scientist  
**Scope:** Phase 03 ETA Target Formulation, Feature Contracts, Baseline Models, Evaluation Design, and Model Selection  
**Status:** `MODELING SPECIFICATION FORMALIZED — GENERALIZATION EVALUATION BLOCKED PENDING DATA SEGMENTATION`

---

## 1. ETA Target Formulation & Mathematical Semantics

The modeling task is defined as: given an in-progress passenger ferry voyage observed up to simulation cutoff timestamp $t_{\text{pred}}$, predict the remaining duration until verified arrival at the destination berth.

### Formal Formulation

For a voyage $v$ with verified departure timestamp $t_{\text{dep}}$ and verified arrival timestamp $t_{\text{arr}}$:
$$\text{remaining\_travel\_time\_minutes} = \frac{t_{\text{arr}} - t_{\text{pred}}}{60.0}$$

### Mandatory Boundary Constraints
1. **In-Progress Precondition:**
   $$t_{\text{dep}} \le t_{\text{pred}} < t_{\text{arr}}$$
2. **Positivity Constraint:**
   $$y > 0.0 \quad \forall t_{\text{pred}} < t_{\text{arr}}$$
3. **Unit & Normalization:**
   Target is denominated in fractional decimal minutes (e.g., $15.50\text{ min} = 15\text{ min } 30\text{ s}$).
4. **Time Zone Normalization:**
   All timestamps ($t_{\text{dep}}, t_{\text{pred}}, t_{\text{arr}}$) must be strictly normalized to **UTC (ISO-8601)** prior to computing differences. Local time daylight saving shifts must never pollute elapsed duration math.

### Arrival Event Ground-Truth Definition
- **Direct Touchdown / Berth Event (`OBSERVED_ARRIVAL`):** Speed over ground drops below $0.5\text{ kn}$ inside the defined terminal berth polygon ($r \le 800\text{ m}$) with stationary dwell $\ge 3\text{ minutes}$.
- **Proximity Event (`INFERRED_PORT_ARRIVAL`):** Final observation ping terminates within $800\text{ m}$ of terminal coordinates. Scored with confidence penalty ($0.80$ vs $0.95$).

---

## 2. Feature Availability and Leakage Prevention

### The Golden Rule of Causal Inference
**A feature $x$ is legitimate if and only if its value was known and unalterable at $t \le t_{\text{pred}}$.**

### Prohibited Leakage Attributes (Strictly Blocked at Ingestion)
| Prohibited Attribute | Leakage Mechanism | Enforcement Guardrail |
| :--- | :--- | :--- |
| `actual_arrival_timestamp_utc` | Direct label leakage ($y = t_{\text{arr}} - t_{\text{pred}}$) | Excluded from training feature matrix; restricted to label evaluation |
| `total_voyage_duration_minutes` | Label leakage ($y = T_{\text{total}} - t_{\text{elapsed}}$) | Stripped from feature store |
| `future_track_coordinates` | Geometric lookahead | Pings with $t > t_{\text{pred}}$ dropped by causal filter |
| `future_speeds_or_headings` | Kinematic lookahead | Kinematics computed strictly from window $[t_{\text{pred}} - 15\text{m}, t_{\text{pred}}]$ |
| `future_ocean_physics` | Spatiotemporal reanalysis leakage | Daily Copernicus reanalysis mapped strictly to observation date |
| `retrospective_gtfs_updates` | Post-hoc schedule modification | Schedules must have release date $\le t_{\text{dep}}$ |

### Corridor-Specific Feature Availability Matrix

| Feature Name | Description | Corridor A (Brest) | Corridor B (Salish Sea) | Technical Notes |
| :--- | :--- | :---: | :---: | :--- |
| `latitude`, `longitude` | Current position | **AVAILABLE** | **NOT_AVAILABLE** | US AIS lacks per-vertex timestamps on tracklines |
| `sog_knots` | Instantaneous speed | **AVAILABLE** | **NOT_AVAILABLE** | Present in Brest pings; missing in US tracklines |
| `cog_degrees` | Course over ground | **AVAILABLE** | **NOT_AVAILABLE** | Present in Brest pings; missing in US tracklines |
| `elapsed_time_minutes` | $t_{\text{pred}} - t_{\text{dep}}$ | **AVAILABLE** | **AVAILABLE_WITH_LIMITATIONS** | Retrospectively computable only if track = voyage |
| `remaining_nav_distance_nm` | Fairway route distance | **AVAILABLE_WITH_LIMITATIONS** | **AVAILABLE_WITH_LIMITATIONS** | Requires fairway routing graph; straight-line is naive |
| `vessel_length_m`, `draft_m` | Static vessel metrics | **AVAILABLE** | **AVAILABLE** | ITU MARS (Brest) / Cadastre (US) |
| `daily_uo_vo_currents` | Copernicus ocean vector | **AVAILABLE_WITH_LIMITATIONS** | **NOT_AVAILABLE** | 2015 data available for Brest; no 2026 data for US |
| `scheduled_departure_time` | Timetable published time | **NOT_AVAILABLE** | **NOT_AVAILABLE** | No contemporaneous 2015 Brest or March 2026 BC GTFS |

---

## 3. Implemented Deterministic Baselines

Three small, deterministic baseline classes were implemented and validated under [ml-platform/src/models/baselines.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/models/baselines.py) with 8 unit tests in [test_phase03_baselines.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/tests/test_phase03_baselines.py):

### Baseline 1 — Physical ETA Baseline (`PhysicalETABaseline`)
- **Mathematical Logic:**
  $$\hat{y}_{\text{physical}} = \left(\frac{d_{\text{navigable}}}{v_{\text{current}}}\right) \times 60.0$$
- **Safety Rules & Guardrails:**
  - Speed $v_{\text{current}} < 0.5\text{ kn}$ or missing returns `status="UNAVAILABLE_SPEED"`.
  - Speed $v_{\text{current}} > 50.0\text{ kn}$ returns `status="IMPLAUSIBLE_SPEED"`.
  - Distance $d \le 0$ or missing returns `status="UNAVAILABLE_DISTANCE"`.
  - When straight-line distance is used, explicit limitation is logged: `"Straight-line Euclidean/Haversine distance underestimates actual navigable fairway distance."`

### Baseline 2 — Historical Route-Duration Baseline (`HistoricalRouteDurationBaseline`)
- **Mathematical Logic:**
  $$\hat{y}_{\text{historical}} = \max\left(0.0, \text{median}\left(\{T_i : \text{route}(i) = r, t_{\text{dep}, i} < t_{\text{pred}}, i \neq v\}\right) - t_{\text{elapsed}}\right)$$
- **Safety Rules & Guardrails:**
  - **Causal Masking:** Only past voyages strictly preceding $t_{\text{pred}}$ are included.
  - **Identity Masking:** Current voyage $v$ is explicitly excluded from historical median.
  - **Sample Threshold:** Requires $N_{\text{history}} \ge 3$ prior voyages. Returns `status="INSUFFICIENT_HISTORY"` if threshold is unmet.

### Baseline 3 — Descriptive Corridor Reference (`DescriptiveCorridorBaseline`)
- **Mathematical Logic:**
  $$\hat{y}_{\text{descriptive}} = \max\left(0.0, \text{median}\left(T_{\text{corridor}}\right) - t_{\text{elapsed}}\right)$$
- **Role:** Global dataset benchmark for variance decomposition. Explicitly marked as non-operational.

---

## 4. Leakage-Safe Evaluation Design

### Splitting Architecture
1. **Voyage-Grouped Isolation:**
   All prediction snapshots for voyage $v$ must belong exclusively to one split (Train, Validation, or Test). Shuffling snapshots across splits creates severe temporal leakage and is strictly prohibited.
2. **Chronological Holdout:**
   Splits are partitioned temporally:
   - Train: Weeks 1–3
   - Validation: Week 3.5
   - Test: Week 4
3. **Vessel-Held-Out Evaluation:**
   Cross-vessel transferability protocol: train on Vessel $A$ (*Fromveur II*), evaluate on Vessel $B$ (*Enez Sun 3*).

### Evaluation Metrics
- **Mean Absolute Error (MAE):** $\frac{1}{N}\sum |y_i - \hat{y}_i|$ (Primary operational metric, in minutes).
- **Root Mean Squared Error (RMSE):** $\sqrt{\frac{1}{N}\sum (y_i - \hat{y}_i)^2}$ (Penalizes catastrophic outliers).
- **Median Absolute Error (MedAE):** Robust to heavy-tailed harbour dwell distributions.
- **Acc_5min:** Percentage of predictions within $\pm 5.0\text{ minutes}$ of actual arrival.
- **Acc_10min:** Percentage of predictions within $\pm 10.0\text{ minutes}$ of actual arrival.
- **MAPE Safeguard:** $\frac{|y_i - \hat{y}_i|}{\max(y_i, 1.0\text{ min})} \times 100\%$ (Guards against zero-division on final approach).

### Evaluation Status: BLOCKED
- **Current Status:** `GENERALIZATION_EVALUATION_BLOCKED`.
- **Reason:** As demonstrated in the Phase 03 Audit Report, there are currently **0 verified real-world ground-truth voyages** in the interim dataset ($N=0$). Generating train/test partitions on 0 samples would be fraudulent.
- **Unblocking Requirement:** Minimum 50 independently verified voyages from systematic trajectory extraction.

---

## 5. Model Selection Decision Matrix

| Model Architecture | Input Data Requirements | Temporal Resolution Needed | Interpretability | Leakage Risk | Computational Cost | Generalization Risk | Recommendation |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Physical ETA Baseline** | Navigable distance, current SOG | Single point ping | **HIGH** | **ZERO** | Negligible ($\mu\text{s}$) | High in variable currents/berthing | **BASELINE (ALWAYS ACTIVE)** |
| **Historical Route Median** | Route ID, departure time, past trips | Departure + current elapsed time | **HIGH** | **ZERO (when causally masked)** | Negligible ($\mu\text{s}$) | High during schedule disruptions | **BASELINE (ALWAYS ACTIVE)** |
| **Gradient Boosted Trees (LightGBM/XGBoost)** | Tabular feature vector (kinematics, distance, ocean current, elapsed time) | Snapshots sampled at 5-min intervals | **HIGH** (Tree SHAP) | **LOW (if feature contract enforced)** | Low (sub-ms inference) | Low on in-distribution routes | **RECOMMENDED PRIMARY ML MODEL** |
| **Recurrent Sequence Models (GRU / LSTM)** | Evenly spaced continuous ping sequences | Uniform high-frequency telemetry ($1\text{ Hz}$ to $0.1\text{ Hz}$) | **LOW** (Black box) | **HIGH (hidden state leakage)** | High (GPU training, recurrent inference) | High over irregular AIS ping gaps | **REJECTED AT CURRENT PHASE** |

### Strategic Recommendation & Empirical Qualifications
1. **Tier 1 (Fallback / Baseline):** Implement `PhysicalETABaseline` and `HistoricalRouteDurationBaseline` as active fallbacks in production. Both are fully deterministic and free from hidden state leakage.
2. **Tier 2 (Candidate Primary ML Model):** Select **LightGBM** as the primary learning candidate once systematic trajectory segmentation extracts $N \ge 50$ real voyages.
   - *Sample Size Qualification:* 50 independent voyages represents an engineering feasibility milestone to test pipeline convergence, not a statistically established sufficiency threshold for operational generalization.
   - *Snapshot Correlation:* Multiple prediction snapshots per voyage are autocorrelated and cannot be treated as independent degrees of freedom.
   - *Performance & Latency Claims:* Claims of sub-millisecond inference and generalization superiority are hypotheses that must be empirically measured against the baselines on held-out test splits.
   - *Interpretability Limits:* Tree SHAP provides feature attribution relative to the model's learned output, but does not prove physical causality or maritime navigational correctness.
3. **Sequence Models (GRU/LSTM):** Deprioritized. Marine AIS telemetry suffers from stochastic transmission gaps ($10\text{ s}$ to $15\text{ min}$), making fixed-interval recurrent architectures poorly suited without complex continuous-time differential approximations.

---

## 6. Acceptance Checklist

- [x] Target concept formally defined with positivity and time-zone rules.
- [x] Leakage prohibitions explicitly codified in configuration contracts.
- [x] Corridor-specific feature availability classified and verified.
- [x] Three deterministic baselines implemented in code with 10 passing unit tests.
- [x] Leakage-safe evaluation policy formalized (voyage grouping, chronological holdout).
- [x] Generalization evaluation status marked BLOCKED honestly due to $N=0$ real voyages.
- [x] Model comparison matrix complete with LightGBM qualified as candidate primary ML model.
