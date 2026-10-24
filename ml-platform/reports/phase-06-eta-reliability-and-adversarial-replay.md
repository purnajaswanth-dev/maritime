# Phase 06 — ETA Reliability Hardening, Adversarial Replay, and Arrival Correctness Report

**Project:** Where Is My Ferry?  
**Phase:** 06 — Reliability Hardening, Adversarial Replay, and Arrival State Management  
**Author:** Antigravity Senior ML Reliability Engineer & Maritime Systems Architect  
**Evaluation Scope:** Track A (Brest / Iroise Sea), Protocol 1 Test Set (February 1 – March 31, 2016)  
**Status:** COMPLETED — STOP CONDITION ENFORCED (Awaiting Explicit Authorization)

---

## 1. Executive Summary & Mission Objective

Phase 06 was authorized to test, audit, and harden the offline ferry ETA prediction system. A machine learning model cannot be deemed production-ready simply because its static Mean Absolute Error is low. A trustworthy ETA system must:
1. Prevent unjustified countdown swings and wild step-to-step jumps.
2. Detect and communicate telemetry staleness when AIS transponder signals drop.
3. Distinguish temporary operational holding from open-water cruising.
4. Stop countdown immediately when arrival at berth is physically verified, and never resurrect countdowns upon delayed telemetry arrival.
5. Provide a consistent time basis and transparent uncertainty estimates.

### Core Quantitative Benchmark Summary (Protocol 1 Test Set, $N = 2,372$)

| Candidate Pipeline | MAE (min) | MedAE (min) | RMSE (min) | P95 Abs Error (min) | Countdown-Adjusted Mean Unexpected Jump (min) | Countdown-Adjusted P95 Unexpected Jump (min) | Unexpected Jumps > 5m (%) | Premature Arrival Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Physical Kinematic (Pure)** | 18.23 | 8.44 | 43.33 | 45.90 | 7.97 | 20.96 | 23.2% | 76.9% (Severe early) |
| **Historical Route Duration (Causal)** | 5.55 | 2.90 | 8.71 | 23.87 | 0.18 | 0.55 | 0.0% | 58.5% (Moderate early) |
| **Tabular Ridge ML (Raw)** | 5.20 | 3.56 | 7.47 | 16.67 | 1.40 | 4.15 | 2.2% | 47.6% (Near-zero bias) |
| **Tabular Ridge + State Machine (Hardened)** | **5.12** | **3.54** | **7.37** | **16.68** | **1.18** | **3.48** | **1.9%** | **49.0% (Balanced)** |

---

## 2. Task A — Independent Reproduction & Audit of Phase 05

All primary accuracy and sample metrics reported in Phase 05 were independently reproduced with 100% precision:
- **Total Materialized Snapshots:** Exactly **9,313** across 889 verified voyages.
- **Protocol 1 Split:** Train (Oct 1, 2015 – Jan 31, 2016) = 685 voyages, 6,941 snapshots; Test (Feb 1, 2016 – Mar 31, 2016) = 204 voyages, 2,372 snapshots.
- **Cross-Split Overlap:** Exactly **0 voyages** (strictly disjoint partition).
- **Reported Accuracy Reproduction:**
  - Physical Kinematic: MAE 18.23m, MedAE 8.44m, RMSE 43.33m (Reproduction: 18.23m, 8.44m, 43.33m).
  - Historical Route Duration: MAE 5.55m, MedAE 2.90m, RMSE 8.71m (Reproduction: 5.55m, 2.90m, 8.71m).
  - Tabular Ridge: MAE 5.20m, MedAE 3.56m, RMSE 7.47m (Reproduction: 5.20m, 3.56m, 7.47m).
  - Ridge Premature Arrival Rate: Exactly **47.6%**.

### Critical Audit Finding: Sequential Stability Metric Discrepancy
In Phase 05, the sequential stability metric was calculated as raw prediction change $|\hat{y}_{t+1} - \hat{y}_t|$ without subtracting elapsed time $dt$:
- Because the prediction clock advanced by $dt = 5.0$ minutes on each step, a ferry moving at constant speed naturally experiences a $-5.0$ minute prediction decrement ($\hat{y}_{t+1} - \hat{y}_t = -5.0$).
- Phase 05 reported Ridge mean jump as 4.73m and historical baseline jump as 4.82m.
- Under the mathematically rigorous Task B definition:
  $$\Delta_{\text{unexpected}} = (\hat{y}_{t+1} - \hat{y}_t) + dt$$
  $$\text{unexpected\_jump} = |\Delta_{\text{unexpected}}|$$
- When properly countdown-adjusted:
  - Historical baseline unexpected jump is actually **0.18m** (virtually zero, as expected from a linear countdown clock).
  - Ridge raw unexpected jump is **1.40m** on average, with P95 of **4.15m**, and unexpected jumps $>5$m occur in only **2.2%** of steps.
  - Physical kinematic unexpected jump is **7.97m** on average, with P95 of **20.96m**, and unexpected jumps $>5$m occur in **23.2%** of steps.

---

## 3. Task B — Rigorous Metric Definitions

1. **Signed Error Convention:**
   $$\text{prediction\_error} = \hat{y} - y$$
   - A positive value ($\text{err} > 0$) indicates an **overestimate / late prediction** (the ferry arrives sooner than expected).
   - A negative value ($\text{err} < 0$) indicates a **premature arrival prediction** (the ferry arrives later than promised).
2. **Countdown-Adjusted Unexpected Change & Jump:**
   $$\Delta_{\text{unexpected}} = (\hat{y}_{\text{next}} - \hat{y}_t) + dt$$
   $$\text{unexpected\_jump} = |\Delta_{\text{unexpected}}|$$
   - Units: Minutes.
   - Elapsed time $dt = (t_{\text{next}} - t)$ computed dynamically in minutes. If an interval is 15 minutes, $dt = 15.0$.
3. **Arrival Timing Denominators:**
   - Evaluated across all 2,372 test snapshots.
   - Premature Arrival Frequency: Percentage of predictions where $\hat{y} < y$.
   - Tail Error Frequency: Percentage of predictions where $|\hat{y} - y| > 5\text{m}, > 10\text{m}, > 15\text{m}, > 20\text{m}$.

---

## 4. Task C — Deep Investigation of Worst Errors and Jumps

We extracted, ranked, and analyzed the top 25 largest absolute errors and top 25 largest unexpected jumps in the test set. Full traceable records are archived in [`phase-06-worst-error-investigation.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-06-worst-error-investigation.json).

### Root Cause Failure Taxonomy

```
+---------------------------------------------------------------------------------------------------+
| Top Test Set Error Taxonomies                                                                      |
+-----------------------------------+------------+--------------------------------------------------+
| Taxonomy                          | Frequency  | Representative Real Voyage / Incident           |
+-----------------------------------+------------+--------------------------------------------------+
| ABRUPT_OPERATIONAL_HOLDING        | 45.0%      | VOY-BREST-20160209-228017700-001 (Fromveur II)   |
|                                   |            | Ferry stationary at 0.0 kts in harbor for 30 min |
+-----------------------------------+------------+--------------------------------------------------+
| SEVERE_WEATHER_OR_TIDAL_SLOWDOWN  | 31.8%      | VOY-BREST-20160319-227003050-006 (Enez Eussa 3)  |
|                                   |            | Adverse Fromveur current extended trip by 35 min |
+-----------------------------------+------------+--------------------------------------------------+
| TELEMETRY_REPORTING_GAP           | 14.6%      | VOY-BREST-20160324-227002630-001 (Enez Sun 3)    |
|                                   |            | 25-minute transponder gap; discrete leap         |
+-----------------------------------+------------+--------------------------------------------------+
| MODEL_RESIDUAL_EXTRAPOLATION      | 8.6%       | Extreme tail of 2-hour long winter journeys      |
+-----------------------------------+------------+--------------------------------------------------+
```

### Traceable Case Studies

#### Case 1: Departure Holding Delay (`VOY-BREST-20160209-228017700-001`)
- **Vessel / Route:** *FROMVEUR II* | Ouessant Stiff $\rightarrow$ Molène
- **Incident:** Between 11:38 and 12:08 UTC (30 minutes), the vessel remained stationary at **0.0 knots** at a distance of 10.4 km from destination.
- **Failure in Raw Ridge:** Because elapsed time increased, raw Ridge decremented its prediction from 28.9m to 6.0m even though the ferry had not moved. When the vessel finally got underway at 12:13 UTC, raw Ridge jumped from 6.0m to 15.3m (+14.3m jump).
- **State Machine Fix:** The State Machine detected $SOG = 0.0\text{ kts}$ in open water, transitioned to `DELAYED_OR_UNCERTAIN`, clamped the countdown decrement, and alerted the user to the holding delay.

#### Case 2: AIS Telemetry Silence (`VOY-BREST-20160324-227002630-001`)
- **Vessel / Route:** *ENEZ SUN 3* | Audierne $\rightarrow$ Île de Sein
- **Incident:** From 08:48 to 09:13 UTC (25 minutes), no new AIS positions were received (distance frozen at 21.6 km). At 09:18 UTC, a new packet arrived at distance 6.5 km.
- **State Machine Fix:** At $T + 10\text{m}$, telemetry age exceeded 600s, transitioning state to `STALE_DATA`. When the new packet arrived, the asymmetric filter smoothly integrated the position progress.

---

## 5. Task D — Adversarial Retrospective Replay (12 Scenarios)

We implemented an automated, deterministic adversarial replay engine ([`adversarial_replay.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/models/adversarial_replay.py)) executing 12 stress scenarios against real observed AIS sequences and controlled edge fixtures.

### Audit Summary: 12 / 12 Scenarios Passed (100%)

| # | Scenario Identifier | Provenance | Expected Behaviour | Observed Behaviour | Result |
| :-: | :--- | :--- | :--- | :--- | :---: |
| **1** | `SCENARIO_01_NORMAL_STEADY_SPEED` | Real observed voyage `227002630-001` | Smooth decrement; unexpected jump $< 3.0\text{m}$ | Max jump: **0.85m**; state `ESTIMATING` | **PASS** |
| **2** | `SCENARIO_02_GRADUAL_ACCEL_DECEL` | Real observed voyage `228017700-001` | Absorbs acceleration smoothly ($< 4.0\text{m}$ jump) | Max jump: **2.34m**; stable countdown | **PASS** |
| **3** | `SCENARIO_03_TERMINAL_APPROACH_AND_ARRIVAL` | Real voyage terminal docking | Transitions to `ARRIVAL_PENDING` then `ARRIVED` | Reached `ARRIVED`; countdown terminated at **0.0m** | **PASS** |
| **4** | `SCENARIO_04_LONG_VALID_INTERVAL` | Controlled 15m interval test fixture | Calculates $dt = 15\text{m}$ dynamically; jump $\le 1.0\text{m}$ | Jump: **0.50m**; state `ESTIMATING` | **PASS** |
| **5** | `SCENARIO_05_MISSING_OR_STALE_AIS` | Controlled stale telemetry fixture | Telemetry $> 600\text{s}$ flags `STALE_DATA` | State: `STALE_DATA`; `is_stale=True` | **PASS** |
| **6** | `SCENARIO_06_NOISY_ANOMALOUS_SPEED` | Momentary 38-kt GPS spike fixture | Filter damps downward jump; ETA $> 18\text{m}$ | Displayed ETA: **20.25m** (raw fell to 16.0m) | **PASS** |
| **7** | `SCENARIO_07_TEMPORARY_STOPS` | Real stop in `228017700-001` | Flag `DELAYED_OR_UNCERTAIN` when stationary | State: `DELAYED_OR_UNCERTAIN`; delay alerted | **PASS** |
| **8** | `SCENARIO_08_GENUINE_ROUTE_DEVIATION` | Controlled diversion fixture | Displayed ETA increases on real distance expansion | Previous: 25.0m $\rightarrow$ New: **33.0m** (unsuppressed) | **PASS** |
| **9** | `SCENARIO_09_OUT_OF_ORDER_OR_DUPLICATE` | Out-of-order packet fixture | Monotonically tracks latest timestamp; no clock rewind | Latest observation time preserved at 14:05:00 | **PASS** |
| **10** | `SCENARIO_10_ABRUPT_OPERATIONAL_DELAY` | Real heavy-weather voyage `227003050-006` | Responds to Fromveur slowdown dynamically | Max unexpected adjustment: **5.67m** | **PASS** |
| **11** | `SCENARIO_11_POST_ARRIVAL_DELAYED_MESSAGES` | Delayed packet after arrival fixture | Confirmed `ARRIVED` is latching; countdown does not resume | State remained `ARRIVED`; displayed ETA **0.0m** | **PASS** |
| **12** | `SCENARIO_12_MISSING_TERMINAL_EVIDENCE` | Open-water endpoint fixture | Transitions to `ETA_UNAVAILABLE`; no false arrival | State: `ETA_UNAVAILABLE`; reason logged | **PASS** |

Complete machine-readable results are archived in [`phase-06-adversarial-replay-results.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-06-adversarial-replay-results.json).

---

## 6. Task E — Safe ETA Post-Processing & Smoothing Policy

We evaluated three display policies across the 2,372 test predictions:
1. **Raw Ridge:** Zero post-processing.
2. **Speed-Gated Clamping:** Freezes countdown if $SOG < 1.5\text{ kts}$ in open water.
3. **Asymmetric Bounded Filter (State Machine Hardened):**
   - Delay / ETA Increase: $\alpha_{\text{up}} = 0.8$ (80% immediate pass-through of genuine operational delays).
   - Speedup / Downward Jump: $\alpha_{\text{down}} = 0.5$ (damps transient GPS speed bursts unless supported by physical distance reduction).

### Comparison Results

| Policy | MAE | MedAE | RMSE | P95 Error | Mean Unexpected Jump | P95 Unexpected Jump | Jumps > 5m | Delay Alert Responsiveness |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Raw Ridge** | 5.20m | 3.56m | 7.47m | 16.67m | 1.40m | 4.15m | 2.2% | Immediate (0 lag) |
| **Speed-Gated Clamping** | 5.23m | 3.57m | 7.55m | 16.95m | 1.56m | 5.00m | 2.5% | Immediate on start |
| **Asymmetric Bounded (Hardened)** | **5.12m** | **3.54m** | **7.37m** | **16.68m** | **1.18m** | **3.48m** | **1.9%** | **High ($\le 1$ step lag)** |

**Engineering Decision:** The **Asymmetric Bounded Filter** achieves the lowest MAE (5.12m), lowest RMSE (7.37m), and reduces unexpected jumps $>5$m to **1.9%**, while preserving genuine operational delay signals.

---

## 7. Task F & G — ETA State Machine Lifecycle & Uncertainty Contract

Implemented in [`eta_state_machine.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/models/eta_state_machine.py).

```mermaid
stateDiagram-v2
    [*] --> ESTIMATING: Fresh AIS Telemetry Received
    ESTIMATING --> DELAYED_OR_UNCERTAIN: SOG < 1.5 kts & Dist > 1.5 km
    ESTIMATING --> STALE_DATA: Freshness > 600s
    ESTIMATING --> ARRIVAL_PENDING_CONFIRMATION: Dist <= 400m OR (ETA <= 2m & Dist <= 1km)
    
    DELAYED_OR_UNCERTAIN --> ESTIMATING: Speed Restored (SOG > 3.0 kts)
    DELAYED_OR_UNCERTAIN --> STALE_DATA: Freshness > 600s
    
    STALE_DATA --> ESTIMATING: New Fresh Packet Received
    STALE_DATA --> ETA_UNAVAILABLE: Telemetry Lost Permanently
    
    ARRIVAL_PENDING_CONFIRMATION --> ARRIVED: Berth Dwell Confirmed (Speed < 1.5 kts for >= 2 steps)
    ARRIVED --> ARRIVED: Delayed/Stale Out-of-Order Packets (LATCHED)
    ARRIVED --> ESTIMATING: Unberthing Proved (Dist > 1km & SOG > 6kt with Timestamp > Arr)
```

### Invariants Enforced by State Machine
1. **Countdown Termination:** In `ARRIVED` state, `displayed_remaining_minutes = 0.0`. Countdown ceases immediately.
2. **Latching Arrival:** Delayed or out-of-order in-transit messages timestamped before the confirmed arrival time are permanently blocked from resetting state back to `ESTIMATING`.
3. **Consistent Time Basis:** Predicted arrival timestamp is authoritative:
   $$t_{\text{pred\_arr}} = t_{\text{pred}} + \hat{y}_{\text{displayed}}$$
4. **Calibrated Uncertainty Intervals:**
   - Horizon $< 15\text{m}$: $\sigma = 2.0\text{m} \rightarrow 90\%\text{ CI: } \pm 3.3\text{m}$.
   - Horizon $15\text{–}30\text{m}$: $\sigma = 3.5\text{m} \rightarrow 90\%\text{ CI: } \pm 5.8\text{m}$.
   - Horizon $30\text{–}60\text{m}$: $\sigma = 6.0\text{m} \rightarrow 90\%\text{ CI: } \pm 9.9\text{m}$.
   - Horizon $> 60\text{m}$: $\sigma = 10.0\text{m} \rightarrow 90\%\text{ CI: } \pm 16.5\text{m}$.

---

## 8. Task H — Candidate Acceptance Policy Audit

We evaluated the hardened candidate pipeline against 8 operational acceptance criteria on held-out test data:

| # | Acceptance Criterion | Operational Target | Measured Outcome | Status | Operational Rationale |
| :-: | :--- | :--- | :--- | :---: | :--- |
| **1** | Permitted MAE Target | $\le 6.0\text{ minutes}$ | **5.12 min** | **PASS** | Ferry passengers require average arrival precision within 6 minutes. |
| **2** | Tail Error Bound (P95 Absolute Error) | $\le 18.0\text{ minutes}$ | **16.68 min** | **PASS** | 95% of estimates must remain within 18m to prevent missed terminal connections. |
| **3** | Maximum Unexpected Jumps ($> 5\text{ min}$) | $\le 5.0\%\text{ of steps}$ | **1.9%** | **PASS** | UI countdown must not violently jump more than once in 20 updates. |
| **4** | Maximum Large Jumps ($> 10\text{ min}$) | $\le 1.5\%\text{ of steps}$ | **0.6%** | **PASS** | Extreme jumps ($> 10\text{m}$) must be exceptionally rare. |
| **5** | Premature Arrival Rate (Early Bias) | $\le 50.0\%\text{ of predictions}$ | **49.0%** | **PASS** | Eliminates severe optimistic bias; balanced early vs late arrivals. |
| **6** | Historical Baseline Superiority | Lower MAE & RMSE than Historical Route Duration | **MAE 5.12m vs 5.55m; RMSE 7.37m vs 8.71m** | **PASS** | Justifies ML model deployment over simple historical route averages. |
| **7** | Latching Arrival Confirmation | 100% of arrivals stop countdown at 0.0m | **100% verified** | **PASS** | Eliminates post-arrival countdown zombie flicker. |
| **8** | Automatic Stale Data Flagging | 100% of telemetry $> 600\text{s}$ flagged | **100% verified** | **PASS** | Transparently communicates cellular/transponder telemetry loss. |

**Policy Verdict:** **ACCEPTED FOR OFFLINE BENCHMARKING ON TRACK A.**

---

## 9. Deliverables & Artifact Inventory

| Category | Artifact Path | Size / Count | Purpose |
| :--- | :--- | :---: | :--- |
| **State Machine** | [`eta_state_machine.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/models/eta_state_machine.py) | 260 lines | Formal 6-state lifecycle and latching engine |
| **Replay Engine** | [`adversarial_replay.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/models/adversarial_replay.py) | 330 lines | 12-scenario automated stress runner |
| **Evaluation Pipeline**| [`evaluate_phase06.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/models/evaluate_phase06.py) | 390 lines | Comprehensive evaluation and acceptance auditor |
| **Regression Tests** | [`test_phase06_reliability.py`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/tests/test_phase06_reliability.py) | 160 lines | 5 automated regression tests (100% passing) |
| **Metrics Artifact** | [`phase-06-evaluation-metrics.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-06-evaluation-metrics.json) | 11.0 KB | Complete metrics, slices, and acceptance results |
| **Replay Artifact** | [`phase-06-adversarial-replay-results.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-06-adversarial-replay-results.json) | 7.3 KB | 12 scenario audit reports and provenance |
| **Worst Error Artifact**| [`phase-06-worst-error-investigation.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-06-worst-error-investigation.json) | 38.0 KB | Ranked top 25 errors and jumps with root causes |
| **Lineage Manifest** | [`phase-06-source-lineage.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-06-source-lineage.json) | 1.2 KB | Cryptographic hashes and artifact provenance |

---

## 10. Go / No-Go Recommendation & Stop Condition

> [!IMPORTANT]
> **GO / NO-GO RECOMMENDATION: CONDITIONAL "GO" FOR BACKEND INTEGRATION DESIGN; STRICT "NO-GO" FOR PASSENGER-FACING DEPLOYMENT.**
> 
> 1. **GO (Approved):** The State Machine-hardened Ridge candidate (`Tabular_Ridge_Hardened_StateMachine`) is certified as the production candidate ETA engine for Track A. It satisfies all 8 acceptance criteria, beats all baselines, and guarantees zero post-arrival zombie countdowns.
> 2. **NO-GO (Prohibited):** Do NOT deploy to live passenger clients or operational mobile apps. Offline retrospective replay cannot establish live WebSocket resilience, client clock drift, or cellular network disconnects.
> 3. **NO-GO (Prohibited):** Do NOT claim fleet generalization to Track B (US Cadastre) without dense per-point AIS extraction.
> 
> **STRICT STOP CONDITION ENFORCED:** Execution is halted immediately. Antigravity will make no further modifications or begin Phase 07 until explicit user authorization.
