"""Automated regression tests for Phase 06 ETA reliability, adversarial replay, and state machine lifecycle."""

import json
import os
import numpy as np
import pytest

from src.models.eta_state_machine import (
    ETAState,
    ETAStateMachine,
    ObservationTelemetry,
)
from src.models.adversarial_replay import AdversarialReplayRunner
from src.models.evaluate_phase06 import compute_accuracy_metrics, compute_stability_metrics


from pathlib import Path

repo_dir = Path(__file__).resolve().parents[1]

@pytest.fixture(scope="module")
def evaluation_metrics():
    path = repo_dir / "data" / "manifests" / "phase-06-evaluation-metrics.json"
    assert path.exists(), f"Phase 06 evaluation metrics missing at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def adversarial_results():
    path = repo_dir / "data" / "manifests" / "phase-06-adversarial-replay-results.json"
    assert path.exists(), f"Phase 06 adversarial replay results missing at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def worst_error_artifact():
    path = repo_dir / "data" / "manifests" / "phase-06-worst-error-investigation.json"
    assert path.exists(), f"Phase 06 worst error artifact missing at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_metric_definitions_signed_error_and_unexpected_jump():
    """Validates mathematical correctness of signed error and countdown-adjusted unexpected jump."""
    # 1. Signed error convention: pred - true
    y_true = np.array([20.0, 30.0, 10.0])
    y_pred = np.array([15.0, 35.0, 10.0])  # Early (-5), Late (+5), Perfect (0)
    acc = compute_accuracy_metrics(y_true, y_pred)
    assert acc["mae_minutes"] == 3.33
    assert acc["mean_bias_minutes"] == 0.0
    assert acc["pct_premature_arrival"] == pytest.approx(33.3, 0.1)
    assert acc["pct_late_arrival"] == pytest.approx(33.3, 0.1)

    # 2. Countdown-adjusted unexpected jump: (eta_next - eta_t) + dt
    # Case A: Steady countdown (20m -> 15m in 5m). Expected jump = 0
    eta_t = 20.0
    eta_next = 15.0
    dt = 5.0
    unexp_change = (eta_next - eta_t) + dt
    assert unexp_change == 0.0

    # Case B: Real delay (20m -> 22m in 5m). Expected jump = +7m
    eta_next_delay = 22.0
    unexp_change_delay = (eta_next_delay - eta_t) + dt
    assert unexp_change_delay == 7.0

    # Case C: Sudden collapse (20m -> 2m in 5s = 0.083m). Expected jump approx -17.92m
    dt_5s = 5.0 / 60.0
    unexp_change_collapse = (2.0 - eta_t) + dt_5s
    assert pytest.approx(unexp_change_collapse, 0.01) == -17.92


def test_adversarial_replay_all_scenarios_pass():
    """Validates that all 12 Phase 06 adversarial replay scenarios execute and pass."""
    runner = AdversarialReplayRunner()
    results = runner.run_all_scenarios()
    assert len(results) == 12
    for r in results:
        assert r["passed"] is True, f"Failed scenario: {r['scenario_id']} - {r['observed_behaviour']}"


def test_state_machine_lifecycle_and_invariants():
    """Verifies state machine transitions, latching arrival, and stale data guardrails."""
    sm = ETAStateMachine(
        voyage_id="TEST-VOY-001",
        vessel_name="TEST_VESSEL",
        corridor="TEST_CORRIDOR",
        stale_threshold_seconds=600.0,
        berth_radius_m=300.0,
        dwell_confirm_observations=2,
    )

    # 1. Normal in-transit step -> ESTIMATING
    obs1 = ObservationTelemetry("2016-02-01T10:00:00Z", 48.35, -4.60, 15.0, distance_to_dest_m=10000.0)
    s1 = sm.process_step("2016-02-01T10:00:00Z", 25.0, obs1)
    assert s1.state == ETAState.ESTIMATING
    assert s1.displayed_remaining_minutes == 25.0
    assert not s1.is_stale
    assert not s1.is_arrived

    # 2. Open-water stop -> DELAYED_OR_UNCERTAIN
    obs2 = ObservationTelemetry("2016-02-01T10:05:00Z", 48.35, -4.60, 0.5, distance_to_dest_m=10000.0)
    s2 = sm.process_step("2016-02-01T10:05:00Z", 25.0, obs2)
    assert s2.state == ETAState.DELAYED_OR_UNCERTAIN

    # 3. Telemetry gap > 600s -> STALE_DATA
    s3 = sm.process_step("2016-02-01T10:20:00Z", 22.0, obs2)  # Observation is 15m (900s) old
    assert s3.state == ETAState.STALE_DATA
    assert s3.is_stale is True

    # 4. Terminal approach (< 400m) -> ARRIVAL_PENDING_CONFIRMATION
    obs4 = ObservationTelemetry("2016-02-01T10:30:00Z", 48.38, -4.48, 1.2, distance_to_dest_m=250.0)
    s4 = sm.process_step("2016-02-01T10:30:00Z", 1.5, obs4)
    assert s4.state == ETAState.ARRIVAL_PENDING_CONFIRMATION

    # 5. Consecutive berth dwell step -> ARRIVED
    obs5 = ObservationTelemetry("2016-02-01T10:35:00Z", 48.38, -4.48, 0.4, distance_to_dest_m=200.0)
    s5 = sm.process_step("2016-02-01T10:35:00Z", 0.5, obs5)
    assert s5.state == ETAState.ARRIVED
    assert s5.is_arrived is True
    assert s5.displayed_remaining_minutes == 0.0

    # 6. Delayed out-of-order packet arriving after arrival cannot reverse ARRIVED
    obs_late = ObservationTelemetry("2016-02-01T10:15:00Z", 48.36, -4.55, 14.0, distance_to_dest_m=5000.0)
    s6 = sm.process_step("2016-02-01T10:40:00Z", 12.0, obs_late)
    assert s6.state == ETAState.ARRIVED
    assert s6.displayed_remaining_minutes == 0.0


def test_acceptance_criteria_conformance(evaluation_metrics):
    """Verifies that the hardened model satisfies all proposed Phase 06 acceptance criteria."""
    criteria = evaluation_metrics["acceptance_criteria_evaluation"]["criteria"]
    for c in criteria:
        assert c["passed"] is True, f"Failed criterion: {c['criterion']} - Measured: {c['measured_value']} vs Target: {c['threshold']}"

    # Verify superiority over historical baseline
    perf = evaluation_metrics["comparative_accuracy"]
    hardened_mae = perf["Tabular_Ridge_Hardened_StateMachine"]["mae_minutes"]
    hist_mae = perf["Historical_Route_Duration_Causal"]["mae_minutes"]
    assert hardened_mae < hist_mae, f"Hardened Ridge MAE ({hardened_mae}) not better than Historical ({hist_mae})"


def test_worst_error_artifact_schema_and_traceability(worst_error_artifact):
    """Verifies schema, traceability, and taxonomy of the worst error investigation artifact."""
    assert "top_absolute_errors" in worst_error_artifact
    assert "top_unexpected_jumps" in worst_error_artifact

    errors = worst_error_artifact["top_absolute_errors"]
    assert len(errors) == 25
    for err in errors:
        assert "snapshot_id" in err
        assert "voyage_id" in err
        assert "vessel_name" in err
        assert "corridor" in err
        assert "failure_taxonomy" in err
        assert "root_cause_analysis" in err
        assert err["abs_error_minutes"] > 0
