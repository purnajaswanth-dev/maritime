"""Unit tests for Phase 05 snapshot contract, Protocol 1 split, baselines, and tabular model evaluation."""

import json
import os
import numpy as np
import pandas as pd
import pytest

from pathlib import Path
from src.models.evaluate_phase05 import VectorizedRidgeETAModel

repo_dir = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def snapshots_df():
    path = repo_dir / "data" / "processed" / "phase_05_prediction_snapshots.parquet"
    assert path.exists(), f"Phase 05 snapshots missing at {path}"
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def test_predictions_df():
    path = repo_dir / "data" / "processed" / "phase_05_test_predictions.parquet"
    assert path.exists(), f"Phase 05 test predictions missing at {path}"
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def evaluation_metrics():
    path = repo_dir / "data" / "manifests" / "phase-05-evaluation-metrics.json"
    assert path.exists(), f"Phase 05 metrics missing at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_snapshots_contract_conformance(snapshots_df):
    """Verifies that all 9,313 materialized snapshots strictly adhere to contract."""
    assert len(snapshots_df) == 9313
    
    # Required columns
    required_cols = [
        "snapshot_id", "voyage_id", "mmsi", "vessel_name", "dep_terminal",
        "arr_terminal", "corridor", "prediction_timestamp_utc",
        "prediction_ts_epoch_ms", "latest_observed_ts_utc",
        "latest_observed_ts_epoch_ms", "data_freshness_seconds",
        "elapsed_time_minutes", "feature_latitude", "feature_longitude",
        "feature_sog_knots", "feature_heading", "feature_distance_to_dest_m",
        "feature_observations_so_far", "feature_uo_current_ms",
        "feature_vo_current_ms", "feature_current_magnitude_ms",
        "feature_along_track_current_knots",
        "target_remaining_travel_time_minutes", "evidence_grade"
    ]
    for col in required_cols:
        assert col in snapshots_df.columns, f"Missing required column {col}"

    # Target semantics: remaining_time_minutes must be strictly positive (no snapshots at/after arrival)
    assert (snapshots_df["target_remaining_travel_time_minutes"] > 0).all(), "Found snapshots with non-positive remaining time"

    # Observation age: latest observation must be at or before prediction timestamp
    assert (snapshots_df["data_freshness_seconds"] >= 0).all(), "Future observation entered snapshot"

    # Causality: latest observation timestamp must be <= prediction timestamp
    pred_epoch = snapshots_df["prediction_ts_epoch_ms"]
    obs_epoch = snapshots_df["latest_observed_ts_epoch_ms"]
    assert (obs_epoch <= pred_epoch).all(), "Future telemetry entered snapshot"


def test_protocol_1_chronological_split(snapshots_df):
    """Verifies strict train/test separation under Protocol 1 with zero voyage leakage."""
    # Split by voyage departure timestamp to ensure whole voyages are kept together
    verified_path = repo_dir / "data" / "processed" / "verified_voyages.parquet"
    assert verified_path.exists()
    df_voy = pd.read_parquet(verified_path)
    
    train_split_cutoff = "2016-02-01T00:00:00Z"
    voy_train_ids = set(df_voy[df_voy["dep_timestamp_utc"] < train_split_cutoff]["voyage_id"])
    voy_test_ids = set(df_voy[df_voy["dep_timestamp_utc"] >= train_split_cutoff]["voyage_id"])

    # Double check no overlap
    assert len(voy_train_ids.intersection(voy_test_ids)) == 0, "FATAL: Voyage overlap across train/test splits!"

    df_train = snapshots_df[snapshots_df["voyage_id"].isin(voy_train_ids)]
    df_test = snapshots_df[snapshots_df["voyage_id"].isin(voy_test_ids)]

    assert len(df_train) == 6941
    assert len(df_test) == 2372
    assert len(df_train) + len(df_test) == len(snapshots_df)

    # Whole voyages kept together: voyage ID sets must be completely disjoint
    train_voyages = set(df_train["voyage_id"])
    test_voyages = set(df_test["voyage_id"])
    overlap = train_voyages.intersection(test_voyages)
    assert len(overlap) == 0, f"Found {len(overlap)} voyages overlapping across train/test splits"

    assert len(train_voyages) == 685
    assert len(test_voyages) == 204


def test_test_predictions_schema_and_integrity(test_predictions_df):
    """Verifies that test predictions artifact conforms to schema and has no NaN/infinite predictions."""
    assert len(test_predictions_df) == 2372

    pred_cols = [
        "pred_ridge",
        "pred_physical",
        "pred_historical",
        "err_ridge",
        "err_physical",
        "err_historical",
    ]
    for col in pred_cols:
        assert col in test_predictions_df.columns, f"Missing prediction column {col}"
        assert not test_predictions_df[col].isna().any(), f"NaN values found in {col}"
        assert not np.isinf(test_predictions_df[col]).any(), f"Infinite values found in {col}"

    # All predicted remaining times must be non-negative
    for col in ["pred_ridge", "pred_physical", "pred_historical"]:
        assert (test_predictions_df[col] >= 0).all(), f"Negative remaining time predicted in {col}"


def test_ridge_model_superiority_over_physical_baseline(evaluation_metrics):
    """Verifies that the tabular Ridge model outperforms the physical baseline on MAE and RMSE."""
    perf = evaluation_metrics["overall_performance"]
    
    physical_mae = perf["Physical_ETA_Pure"]["mae_minutes"]
    historical_mae = perf["Historical_Route_Duration_Causal"]["mae_minutes"]
    ridge_mae = perf["Tabular_Ridge_ETA"]["mae_minutes"]

    physical_rmse = perf["Physical_ETA_Pure"]["rmse_minutes"]
    ridge_rmse = perf["Tabular_Ridge_ETA"]["rmse_minutes"]

    assert ridge_mae < physical_mae, f"Ridge MAE ({ridge_mae}) not better than Physical ({physical_mae})"
    assert ridge_mae < historical_mae, f"Ridge MAE ({ridge_mae}) not better than Historical ({historical_mae})"
    assert ridge_rmse < physical_rmse, f"Ridge RMSE ({ridge_rmse}) not better than Physical ({physical_rmse})"

    # Catastrophic error rate (>15 min error) must be drastically lower for Ridge
    physical_large_err = perf["Physical_ETA_Pure"]["pct_over_15m"]
    ridge_large_err = perf["Tabular_Ridge_ETA"]["pct_over_15m"]
    assert ridge_large_err < physical_large_err / 3.0, "Ridge did not reduce large errors by at least 3x"


def test_ridge_model_train_predict_determinism():
    """Verifies VectorizedRidgeETAModel is deterministic and handles predictions reliably."""
    df_sample = pd.DataFrame({
        "feature_distance_to_dest_m": [10000.0, 20000.0, 5000.0, 15000.0],
        "elapsed_time_minutes": [10.0, 20.0, 5.0, 15.0],
        "feature_sog_knots": [12.0, 15.0, 10.0, 14.0],
        "feature_observations_so_far": [3, 5, 2, 4],
        "data_freshness_seconds": [30.0, 60.0, 10.0, 45.0],
        "feature_along_track_current_knots": [0.5, -0.2, 0.1, 0.0],
        "corridor": ["BREST_LE_CONQUET", "BREST_LE_CONQUET", "AUDIERNE_SEIN", "AUDIERNE_SEIN"],
        "vessel_name": ["FROMVEUR II", "ENEZ EUSSA 3", "FROMVEUR II", "ENEZ SUN 3"],
    })
    y_train = np.array([30.0, 50.0, 18.0, 40.0])

    model = VectorizedRidgeETAModel(alpha=10.0)
    model.fit(df_sample, y_train)

    preds1 = model.predict(df_sample)
    preds2 = model.predict(df_sample)
    assert np.allclose(preds1, preds2), "Model predictions are non-deterministic"
    assert (preds1 > 0).all()
