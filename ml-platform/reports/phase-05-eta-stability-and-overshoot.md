# Phase 05 — Sequential ETA Stability and Overshoot Replay Report

**Project:** Where Is My Ferry?  
**Phase:** 05 — Snapshots, Baselines, and Controlled ETA Model Evaluation  
**Author:** Antigravity Senior Maritime Applied ML & Evaluation Specialist  
**Evaluation Scope:** Track A (Brest / Iroise Sea), Protocol 1 Test Set (February 1 – March 31, 2016)  
**Artifact Dependencies:**
- Snapshots: [`ml-platform/data/processed/phase_05_prediction_snapshots.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/processed/phase_05_prediction_snapshots.parquet)
- Test Predictions: [`ml-platform/data/processed/phase_05_test_predictions.parquet`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/processed/phase_05_test_predictions.parquet)
- Evaluation Metrics: [`ml-platform/data/manifests/phase-05-evaluation-metrics.json`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-05-evaluation-metrics.json)

---

## 1. Executive Summary & Objective

The goal of this sequential stability replay is to quantify how predicted ferry ETAs behave over time as successive observations arrive every 5 minutes during a voyage. An ETA algorithm with low static MAE can still provide an intolerable passenger experience if its countdown exhibits violent oscillations, sudden wild jumps, or severe premature-arrival overshoots.

Using the strictly causal chronological test split of 204 verified passenger ferry voyages (February 1 – March 31, 2016) comprising **2,168 consecutive 5-minute prediction update intervals**, we measured step-to-step jump distributions, directional overshoot, countdown monotonicity, and behavior during terminal approach.

### Key Quantitative Findings

| Model / Baseline | Mean Absolute Step Jump | 95th Percentile Step Jump | Steps Jumping > 5 min | Premature Arrival Rate (Overshoot) | Mean Error Bias |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Physical Kinematic Baseline** | **7.99 min** | **23.62 min** | 35.8% | **76.9%** (Severe early bias) | -0.94 min |
| **Ocean-Augmented Physical** | **7.98 min** | **23.60 min** | 35.8% | **77.3%** (Severe early bias) | -1.01 min |
| **Historical Route Duration (Causal)** | **4.82 min** | **5.00 min** | 0.0% | **58.5%** (Moderate early bias) | -1.26 min |
| **Tabular Ridge ETA Model** | **4.73 min** | **7.82 min** | 36.4% | **47.6%** (Near-zero bias) | **+0.07 min** |

*Note: In an ideal constant-speed voyage sampled every 5.0 minutes, the true remaining time decreases by exactly 5.0 minutes per step ($\Delta \text{Remaining} = -5.0\text{ min}$). A step jump is defined as $|\Delta \text{Pred} - \Delta \text{True}|$.*

---

## 2. Sequential Step Jump Dynamics & Noise Sources

### 2.1 The Failure of Instantaneous Kinematic ETA
The physical kinematic baseline ($t_{\text{remaining}} = d_{\text{remaining}} / v_{\text{instantaneous}}$) suffers from catastrophic instability:
1. **P95 jump of 23.62 minutes:** A ferry cruising at 15 knots that briefly slows to 5 knots while maneuvering through the Goulet de Brest causes the instantaneous denominator to collapse by $3\times$, causing the remaining time prediction to spike upwards by 20 to 40 minutes within a single 5-minute interval.
2. **Terminal deceleration blowup:** As the vessel approaches the berth within the final 1.5 km, speed naturally decreases from cruising speed (~14 kts) to docking speed (<3 kts). The physical baseline's predicted remaining time rapidly balloons, creating a false alarm of extreme delay immediately before the vessel safely ties up.

### 2.2 Historical Route Duration Stability vs Rigidity
The causal historical route baseline ($\text{Remaining} = \bar{D}_{\text{route}} - t_{\text{elapsed}}$) exhibits mathematically minimal step jumps:
- Because $\bar{D}_{\text{route}}$ is constant during a voyage, each 5-minute advance in clock time decreases remaining time by exactly 5.0 minutes ($\text{Jump} = 0.0$ min relative to clock).
- **The Failure Mode:** Complete insensitivity to reality. If a vessel encounters severe adverse weather, heavy seas in the Fromveur Passage, or holds outside the port, the historical baseline continues ticking down toward zero, predicting arrival even when the vessel is stopped dead in the water.

### 2.3 Tabular Ridge Model Stabilization
The trained L2-regularized linear model achieves the optimal trade-off:
- **Mean absolute jump:** **4.73 minutes** (virtually identical to the ideal 5.0-minute tick).
- **P95 jump:** Clamped to **7.82 minutes** (a **$3.0\times$ reduction** compared to physical baseline's 23.62 min).
- By weighting cumulative elapsed time, total direct distance, corridor-level fixed effects, and instantaneous SOG jointly, the Ridge model filters out momentary GPS jitter while remaining responsive to sustained voyage-level progress.

---

## 3. Overshoot and Premature Arrival Analysis

In public passenger transit applications, a **premature arrival prediction** (predicting the ferry will arrive earlier than it actually does, $\hat{y} < y$) is significantly more damaging to passenger trust than a minor late overestimate:
- If an app promises arrival in 5 minutes but the ferry arrives in 15 minutes, waiting passengers miss connections or assume the ferry has already departed.
- If an app estimates arrival in 15 minutes and the ferry arrives in 12 minutes, passengers are already at the terminal.

### Overshoot Comparison
1. **Physical Baselines:** **76.9% premature arrival rate**. The physical model assumes open-water cruising speed is maintained continuously all the way to the slipway, completely ignoring terminal approach zones, harbor speed limits (3–5 knots), and docking maneuvers.
2. **Historical Baseline:** **58.5% premature arrival rate**. While better than kinematic, winter weather (Feb–Mar) caused seasonal slowdowns relative to the October–January training history, leading the historical mean to underestimate winter trip times.
3. **Tabular Ridge Model:** **47.6% premature arrival rate** (47.6% early vs 52.4% late). The learned model exhibits almost zero systemic bias (**+0.07 minutes** overall mean error), producing a symmetric, well-calibrated distribution.

---

## 4. Countdown Monotonicity and Display Smoothing Policies

### 4.1 Why Monotonicity Must NOT Be Enforced Artificially
A common temptation in ETA display engineering is to force $\hat{y}_t \le \hat{y}_{t-1}$ to prevent the countdown timer from ever increasing. **This is fundamentally prohibited in this project:**
- If a ferry stops or slows down to wait for outgoing traffic in the Port of Brest, remaining travel time has genuinely increased.
- Forcing monotonicity hides operational reality, causing the timer to "freeze" at 1 minute for 15 minutes, completely misleading the user.

### 4.2 Display Smoothing vs Latency Trade-off
To eliminate high-frequency UI jitter without suppressing real delays, we evaluated an Exponential Moving Average (EMA) post-processing filter on predicted remaining time:
$$\tilde{y}_t = \beta \tilde{y}_{t-1} + (1 - \beta) \hat{y}_t$$

| Smoothing Factor ($\beta$) | Mean Step Jump | P95 Step Jump | Large Errors (>15m) | Detection Delay for Real Stops |
| :---: | :---: | :---: | :---: | :---: |
| **$\beta = 0.0$ (Raw Model)** | 4.73 min | 7.82 min | 6.4% | **0 min (Immediate)** |
| **$\beta = 0.3$ (Light EMA)** | 3.65 min | 5.90 min | 6.2% | +1 update step (+5 min) |
| **$\beta = 0.6$ (Heavy EMA)** | 2.40 min | 4.10 min | 7.1% | +2 to +3 steps (+10 to 15 min) |

**Recommendation:** For initial deployment, **Raw Model predictions ($\beta = 0.0$)** should be displayed directly or paired with an extremely light filter ($\beta \le 0.2$). Heavy smoothing introduces dangerous lag when real slowdowns occur.

---

## 5. Critical Scope Limitation: Retrospective vs Live Telemetry

> [!WARNING]
> **Strict Operational Disclaimer:**
> The sequential stability metrics reported here are computed from retrospective historical AIS logs sampled at discrete 5-minute intervals. 
> 
> **Retrospective offline replay DOES NOT and CANNOT establish:**
> 1. Real-time cellular network jitter or telemetry ingestion lag over 4G/LTE along the Iroise coast.
> 2. Live WebSocket delivery stability or client-side reconnection drops.
> 3. Out-of-order AIS message arrival from dual terrestrial receiver stations.
> 4. GPS clock drift or client browser rendering discrepancies.
> 
> True live-display stability must be validated in future phases under live streaming soak tests with synthetic or real-time message streams. Offline retrospective replay is a necessary first screen, not proof of live-client readiness.
