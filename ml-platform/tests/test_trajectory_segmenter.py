"""Comprehensive unit and regression tests for Phase 04 Trajectory Segmenter."""

import datetime
from pathlib import Path
import pytest
import pandas as pd

from src.ingestion.trajectory_segmenter import (
    haversine_m,
    match_terminal,
    TrajectorySegmenter,
    extract_prediction_snapshots,
    TERMINALS,
    CORRIDOR_LIMITS,
    VESSEL_REGISTRY,
)


def test_haversine_distance():
    """Validates haversine distance computation on known benchmarks."""
    # Distance from Brest terminal to Le Conquet terminal
    brest = TERMINALS["BREST"]
    conquet = TERMINALS["LE_CONQUET"]
    dist = haversine_m(brest["lon"], brest["lat"], conquet["lon"], conquet["lat"])
    # Straight-line distance is ~22.0 km (22,000 m)
    assert 21000.0 < dist < 23000.0


def test_match_terminal_geofence():
    """Validates that points within buffer radius match terminal and outside do not."""
    # Exact center of Brest terminal
    term, dist = match_terminal(-4.4857, 48.3811)
    assert term == "BREST"
    assert dist < 1.0

    # Point 400m from Le Conquet terminal (within 600m radius)
    term, dist = match_terminal(-4.7818, 48.3560)
    assert term == "LE_CONQUET"

    # Open-water point in middle of Iroise Sea
    term, dist = match_terminal(-4.6500, 48.3300)
    assert term is None
    assert dist is None


def test_trajectory_segmentation_clean_voyage():
    """Tests clean synthetic voyage segmentation from departure dwell to arrival berth."""
    segmenter = TrajectorySegmenter(max_telemetry_gap_minutes=45.0, min_observations=5)
    mmsi = 228017700  # FROMVEUR II

    # Create a synthetic 60-minute transit: Brest -> Le Conquet
    t0 = int(datetime.datetime(2015, 10, 1, 8, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
    points = [
        # Stationary at Brest dock
        (t0, -4.4857, 48.3811, 0.1, 0.0, "00000001"),
        (t0 + 60000, -4.4857, 48.3811, 0.2, 0.0, "00000000"),
        # Underway departing Brest
        (t0 + 300000, -4.4900, 48.3800, 8.5, 240.0, "00000000"),
        (t0 + 900000, -4.5500, 48.3500, 15.0, 245.0, "00000000"),
        (t0 + 1800000, -4.6500, 48.3300, 15.2, 250.0, "00000000"),
        (t0 + 2700000, -4.7200, 48.3400, 14.8, 280.0, "00000000"),
        # Approaching Le Conquet dock
        (t0 + 3600000, -4.7818, 48.3596, 2.1, 310.0, "00000000"),
        # Berth stop at Le Conquet dock
        (t0 + 3720000, -4.7818, 48.3596, 0.2, 0.0, "00000001"),
    ]

    raw_v = segmenter.segment_vessel_points(mmsi, points)
    assert len(raw_v) == 1
    assert raw_v[0]["dep_terminal"] == "BREST"
    assert raw_v[0]["arr_terminal"] == "LE_CONQUET"

    audited = segmenter.audit_and_classify_voyages(raw_v)
    assert len(audited) == 1
    assert audited[0]["status"] == "VERIFIED"
    assert audited[0]["evidence_grade"] == "HIGH_AIS_BERTH_OBSERVED"
    assert audited[0]["rejection_reasons"] == "NONE"
    assert 55.0 <= audited[0]["duration_minutes"] <= 65.0


def test_trajectory_segmentation_telemetry_gap_rejection():
    """Tests that a voyage with a gap > 45 minutes is flagged UNCERTAIN."""
    segmenter = TrajectorySegmenter(max_telemetry_gap_minutes=45.0, min_observations=5)
    mmsi = 228017700

    t0 = int(datetime.datetime(2015, 10, 1, 8, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
    points = [
        (t0, -4.4857, 48.3811, 0.1, 0.0, "00000001"),
        (t0 + 300000, -4.4900, 48.3800, 8.5, 240.0, "00000000"),
        # 50-minute gap during transit (3000 seconds)
        (t0 + 3300000, -4.7200, 48.3400, 14.8, 280.0, "00000000"),
        (t0 + 3600000, -4.7500, 48.3500, 12.0, 280.0, "00000000"),
        (t0 + 3900000, -4.7818, 48.3596, 1.5, 310.0, "00000000"),
        (t0 + 4000000, -4.7818, 48.3596, 0.2, 0.0, "00000001"),
    ]

    raw_v = segmenter.segment_vessel_points(mmsi, points)
    audited = segmenter.audit_and_classify_voyages(raw_v)
    assert len(audited) == 1
    assert audited[0]["status"] == "UNCERTAIN"
    assert "telemetry gap" in audited[0]["rejection_reasons"].lower()


def test_trajectory_segmentation_duration_bounds_rejection():
    """Tests that a voyage violating corridor physical duration is rejected."""
    segmenter = TrajectorySegmenter(max_telemetry_gap_minutes=45.0, min_observations=5)
    mmsi = 228017700

    t0 = int(datetime.datetime(2015, 10, 1, 8, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
    # Brest -> Le Conquet takes at least 45 minutes physically. Here, vessel takes 10 minutes (implausible)
    points = [
        (t0, -4.4857, 48.3811, 0.1, 0.0, "00000001"),
        (t0 + 100000, -4.4900, 48.3800, 10.0, 240.0, "00000000"),
        (t0 + 200000, -4.5500, 48.3500, 45.0, 245.0, "00000000"),
        (t0 + 300000, -4.6500, 48.3300, 45.0, 250.0, "00000000"),
        (t0 + 400000, -4.7200, 48.3400, 45.0, 280.0, "00000000"),
        (t0 + 500000, -4.7818, 48.3596, 2.0, 310.0, "00000000"),
        (t0 + 600000, -4.7818, 48.3596, 0.1, 0.0, "00000001"),
    ]

    raw_v = segmenter.segment_vessel_points(mmsi, points)
    audited = segmenter.audit_and_classify_voyages(raw_v)
    assert len(audited) == 1
    assert audited[0]["status"] == "UNCERTAIN"
    assert "outside corridor bounds" in audited[0]["rejection_reasons"].lower()


def test_causal_prediction_snapshots_no_future_leakage():
    """Validates that prediction snapshots never leak future coordinates or duration."""
    t0 = int(datetime.datetime(2015, 10, 1, 8, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
    arr_ts = t0 + 3600000  # 60 min trip
    dest_lon, dest_lat = TERMINALS["LE_CONQUET"]["lon"], TERMINALS["LE_CONQUET"]["lat"]

    points = [
        (t0, -4.4857, 48.3811, 0.1, 0.0, "00000001"),
        (t0 + 600000, -4.5200, 48.3700, 14.0, 240.0, "00000000"),
        (t0 + 1200000, -4.5700, 48.3500, 15.0, 245.0, "00000000"),
        (t0 + 1800000, -4.6300, 48.3400, 15.5, 250.0, "00000000"),
        (t0 + 2400000, -4.7000, 48.3400, 14.8, 270.0, "00000000"),
        (t0 + 3000000, -4.7600, 48.3500, 12.0, 290.0, "00000000"),
        (arr_ts, -4.7818, 48.3596, 0.2, 0.0, "00000001"),
    ]

    snapshots = extract_prediction_snapshots(
        points, arr_ts, sample_interval_minutes=10.0, dest_lon=dest_lon, dest_lat=dest_lat
    )
    assert len(snapshots) >= 4

    for snap in snapshots:
        pred_ts = snap["prediction_ts_epoch_ms"]
        # Target must be positive remaining time
        assert snap["target_remaining_travel_time_minutes"] > 0
        # Target formula check: (arr_ts - pred_ts) / 60000
        expected_target = round((arr_ts - pred_ts) / 60000.0, 2)
        assert snap["target_remaining_travel_time_minutes"] == expected_target

        # Latest observation timestamp must be <= prediction timestamp (strictly causal)
        latest_obs_dt = datetime.datetime.strptime(snap["latest_observed_ts_utc"], "%Y-%m-%d %H:%M:%SZ")
        pred_dt = datetime.datetime.strptime(snap["prediction_timestamp_utc"], "%Y-%m-%d %H:%M:%SZ")
        assert latest_obs_dt <= pred_dt

        # Data freshness must be non-negative
        assert snap["data_freshness_seconds"] >= 0.0


def test_verified_voyages_artifact_integrity():
    """Validates that the generated Phase 04 verified parquet contains > 50 real voyages."""
    repo_root = Path(__file__).resolve().parents[1]
    verified_path = repo_root / "data" / "processed" / "verified_voyages.parquet"
    assert verified_path.exists(), "verified_voyages.parquet must exist"

    df = pd.read_parquet(verified_path)
    assert len(df) >= 50, f"Expected >= 50 verified voyages, found {len(df)}"
    assert (df["status"] == "VERIFIED").all()
    assert (df["evidence_grade"] == "HIGH_AIS_BERTH_OBSERVED").all()

    # All timestamps must be ISO 8601 UTC strings ending with 'Z'
    assert df["dep_timestamp_utc"].str.endswith("Z").all()
    assert df["arr_timestamp_utc"].str.endswith("Z").all()

    # Duration must be positive
    assert (df["duration_minutes"] > 0).all()
    # Observation count >= 5
    assert (df["observation_count"] >= 5).all()
    # Max telemetry gap <= 45 minutes
    assert (df["max_gap_seconds"] <= 2700.0).all()


def test_candidate_audit_artifact_integrity():
    """Validates that candidate audit parquet contains both VERIFIED and UNCERTAIN dispositions."""
    repo_root = Path(__file__).resolve().parents[1]
    audit_path = repo_root / "data" / "interim" / "phase_04_candidate_voyage_audit.parquet"
    assert audit_path.exists(), "phase_04_candidate_voyage_audit.parquet must exist"

    df = pd.read_parquet(audit_path)
    assert len(df) > 800
    statuses = set(df["status"].unique())
    assert "VERIFIED" in statuses
    assert "UNCERTAIN" in statuses

    # Uncertain records must have explicit rejection reasons
    uncertain_records = df[df["status"] == "UNCERTAIN"]
    assert (uncertain_records["rejection_reasons"] != "NONE").all()
