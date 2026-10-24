"""Unit tests for Phase 03 ETA baselines, target semantics, and leakage safety."""

import pandas as pd
import pytest

from src.models.baselines import (
    DescriptiveCorridorBaseline,
    HistoricalRouteDurationBaseline,
    PhysicalETABaseline,
)


def test_physical_eta_baseline_valid():
    """Validates physical ETA calculation for known speed and distance."""
    # 15 nm at 15 knots = 1.0 hour = 60.0 minutes
    res = PhysicalETABaseline.predict(remaining_distance_nm=15.0, current_speed_knots=15.0)
    assert res["status"] == "AVAILABLE"
    assert res["predicted_remaining_minutes"] == 60.0
    assert len(res["limitations"]) == 0

    # 10 nm at 20 knots = 0.5 hours = 30.0 minutes
    res2 = PhysicalETABaseline.predict(remaining_distance_nm=10.0, current_speed_knots=20.0)
    assert res2["status"] == "AVAILABLE"
    assert res2["predicted_remaining_minutes"] == 30.0


def test_physical_eta_straight_line_warning():
    """Validates that using straight-line distance flags explicit nautical limitations."""
    res = PhysicalETABaseline.predict(
        remaining_distance_nm=10.0, current_speed_knots=12.0, is_straight_line_distance=True
    )
    assert res["status"] == "AVAILABLE"
    assert any("Straight-line" in lim for lim in res["limitations"])


def test_physical_eta_invalid_speed():
    """Validates that zero, negative, missing, or implausible speed returns explicit status."""
    # Zero speed
    res_zero = PhysicalETABaseline.predict(remaining_distance_nm=10.0, current_speed_knots=0.0)
    assert res_zero["status"] == "UNAVAILABLE_SPEED"
    assert res_zero["predicted_remaining_minutes"] is None

    # Missing speed
    res_none = PhysicalETABaseline.predict(remaining_distance_nm=10.0, current_speed_knots=None)
    assert res_none["status"] == "UNAVAILABLE_SPEED"
    assert res_none["predicted_remaining_minutes"] is None

    # Implausible speed (> 50 knots)
    res_fast = PhysicalETABaseline.predict(remaining_distance_nm=10.0, current_speed_knots=65.0)
    assert res_fast["status"] == "IMPLAUSIBLE_SPEED"
    assert res_fast["predicted_remaining_minutes"] is None


def test_physical_eta_missing_distance():
    """Validates that missing or negative distance returns UNAVAILABLE_DISTANCE."""
    res = PhysicalETABaseline.predict(remaining_distance_nm=None, current_speed_knots=15.0)
    assert res["status"] == "UNAVAILABLE_DISTANCE"
    assert res["predicted_remaining_minutes"] is None

    res_neg = PhysicalETABaseline.predict(remaining_distance_nm=-5.0, current_speed_knots=15.0)
    assert res_neg["status"] == "UNAVAILABLE_DISTANCE"


def test_historical_route_duration_causality():
    """Validates that historical baseline strictly excludes future voyages and current voyage."""
    # Historical dataset with 4 past trips, 1 current trip, and 2 future trips
    data = [
        {"voyage_id": "V-01", "route_id": "R1", "departure_timestamp_utc": "2026-03-01 08:00:00", "actual_duration_minutes": 50.0},
        {"voyage_id": "V-02", "route_id": "R1", "departure_timestamp_utc": "2026-03-01 10:00:00", "actual_duration_minutes": 55.0},
        {"voyage_id": "V-03", "route_id": "R1", "departure_timestamp_utc": "2026-03-01 12:00:00", "actual_duration_minutes": 52.0},
        {"voyage_id": "V-04", "route_id": "R1", "departure_timestamp_utc": "2026-03-01 14:00:00", "actual_duration_minutes": 54.0},
        {"voyage_id": "V-05", "route_id": "R1", "departure_timestamp_utc": "2026-03-01 16:00:00", "actual_duration_minutes": 48.0},  # Current trip
        {"voyage_id": "V-06", "route_id": "R1", "departure_timestamp_utc": "2026-03-01 18:00:00", "actual_duration_minutes": 90.0},  # Future trip
        {"voyage_id": "V-07", "route_id": "R1", "departure_timestamp_utc": "2026-03-01 20:00:00", "actual_duration_minutes": 95.0},  # Future trip
    ]
    df = pd.DataFrame(data)

    baseline = HistoricalRouteDurationBaseline(min_history_count=3)
    pred_ts = "2026-03-01 16:20:00"  # 20 minutes into trip V-05
    res = baseline.predict(
        route_id="R1",
        elapsed_minutes=20.0,
        prediction_timestamp_utc=pred_ts,
        history_df=df,
        current_voyage_id="V-05",
    )

    assert res["status"] == "AVAILABLE"
    # Past trips prior to 16:20: V-01 (50), V-02 (55), V-03 (52), V-04 (54).
    # Note: V-05 departure is 16:00 < 16:20, but it is explicitly excluded by current_voyage_id!
    # Median of [50, 52, 54, 55] = 53.0
    assert res["sample_count"] == 4
    assert res["median_duration_minutes"] == 53.0
    # Remaining = 53.0 - 20.0 elapsed = 33.0
    assert res["predicted_remaining_minutes"] == 33.0


def test_historical_route_duration_insufficient_samples():
    """Validates that route with fewer than min_history_count returns INSUFFICIENT_HISTORY."""
    data = [
        {"voyage_id": "V-01", "route_id": "R2", "departure_timestamp_utc": "2026-03-01 08:00:00", "actual_duration_minutes": 40.0},
    ]
    df = pd.DataFrame(data)

    baseline = HistoricalRouteDurationBaseline(min_history_count=3)
    res = baseline.predict(
        route_id="R2",
        elapsed_minutes=10.0,
        prediction_timestamp_utc="2026-03-01 09:00:00",
        history_df=df,
        current_voyage_id="V-02",
    )
    assert res["status"] == "INSUFFICIENT_HISTORY"
    assert res["sample_count"] == 1
    assert res["predicted_remaining_minutes"] is None


def test_target_semantics_positive_remaining():
    """Validates that remaining travel time is positive for in-progress snapshots."""
    dep_time = pd.to_datetime("2026-03-01 10:00:00", utc=True)
    arr_time = pd.to_datetime("2026-03-01 11:30:00", utc=True)
    pred_time = pd.to_datetime("2026-03-01 10:45:00", utc=True)

    # In-progress assertion
    assert dep_time <= pred_time < arr_time

    remaining_minutes = (arr_time - pred_time).total_seconds() / 60.0
    assert remaining_minutes == 45.0
    assert remaining_minutes > 0.0


def test_descriptive_corridor_baseline():
    """Validates descriptive corridor median calculation."""
    data = [
        {"corridor_id": "SALISH", "actual_duration_minutes": 100.0},
        {"corridor_id": "SALISH", "actual_duration_minutes": 110.0},
        {"corridor_id": "SALISH", "actual_duration_minutes": 120.0},
        {"corridor_id": "BREST", "actual_duration_minutes": 55.0},
    ]
    df = pd.DataFrame(data)

    res = DescriptiveCorridorBaseline.predict(
        corridor_id="SALISH",
        elapsed_minutes=30.0,
        history_df=df,
    )
    assert res["status"] == "AVAILABLE"
    assert res["corridor_median_minutes"] == 110.0
    assert res["predicted_remaining_minutes"] == 80.0
    assert res["corridor_sample_count"] == 3


def test_historical_route_duration_uncompleted_trip_exclusion():
    """Validates that a voyage departing before pred_ts but still underway at pred_ts is EXCLUDED."""
    data = [
        {"voyage_id": "V-COMPLETED-1", "route_id": "R1", "departure_timestamp_utc": "2026-03-01 08:00:00", "actual_duration_minutes": 50.0}, # Arrived 08:50
        {"voyage_id": "V-COMPLETED-2", "route_id": "R1", "departure_timestamp_utc": "2026-03-01 10:00:00", "actual_duration_minutes": 50.0}, # Arrived 10:50
        {"voyage_id": "V-COMPLETED-3", "route_id": "R1", "departure_timestamp_utc": "2026-03-01 12:00:00", "actual_duration_minutes": 50.0}, # Arrived 12:50
        # V-UNDERWAY departed at 13:30 (before pred_ts 14:00), but has duration 60.0 (arrives at 14:30 > pred_ts).
        # Its actual duration CANNOT be known at 14:00!
        {"voyage_id": "V-UNDERWAY", "route_id": "R1", "departure_timestamp_utc": "2026-03-01 13:30:00", "actual_duration_minutes": 120.0},
    ]
    df = pd.DataFrame(data)

    baseline = HistoricalRouteDurationBaseline(min_history_count=3)
    pred_ts = "2026-03-01 14:00:00"
    res = baseline.predict(
        route_id="R1",
        elapsed_minutes=15.0,
        prediction_timestamp_utc=pred_ts,
        history_df=df,
        current_voyage_id="V-CURRENT",
    )

    assert res["status"] == "AVAILABLE"
    # Only V-COMPLETED-1, 2, 3 must be included. V-UNDERWAY must be excluded!
    assert res["sample_count"] == 3
    assert res["median_duration_minutes"] == 50.0
    assert res["predicted_remaining_minutes"] == 35.0


def test_historical_route_duration_route_isolation():
    """Validates that trips on different routes or opposite directions are not mixed."""
    data = [
        {"voyage_id": "V-01", "route_id": "DukePoint_to_Tsawwassen", "departure_timestamp_utc": "2026-03-01 08:00:00", "actual_duration_minutes": 110.0},
        {"voyage_id": "V-02", "route_id": "DukePoint_to_Tsawwassen", "departure_timestamp_utc": "2026-03-01 10:00:00", "actual_duration_minutes": 112.0},
        {"voyage_id": "V-03", "route_id": "DukePoint_to_Tsawwassen", "departure_timestamp_utc": "2026-03-01 12:00:00", "actual_duration_minutes": 108.0},
        # Opposite direction
        {"voyage_id": "V-REV", "route_id": "Tsawwassen_to_DukePoint", "departure_timestamp_utc": "2026-03-01 09:00:00", "actual_duration_minutes": 140.0},
    ]
    df = pd.DataFrame(data)

    baseline = HistoricalRouteDurationBaseline(min_history_count=3)
    res = baseline.predict(
        route_id="DukePoint_to_Tsawwassen",
        elapsed_minutes=20.0,
        prediction_timestamp_utc="2026-03-01 14:00:00",
        history_df=df,
        current_voyage_id="V-NEW",
    )
    assert res["sample_count"] == 3
    assert res["median_duration_minutes"] == 110.0
    assert res["predicted_remaining_minutes"] == 90.0
