"""Comprehensive verification tests for the frozen VectorizedRidgeETAModel artifact (Stage A)."""

import copy
import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from src.models.evaluate_phase05 import (
    VectorizedRidgeETAModel,
    UnsupportedModelSchemaVersionError,
    ModelArtifactTamperedError,
    ModelArtifactCorruptedError,
)


@pytest.fixture(scope="module")
def repo_root():
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def artifact_path(repo_root):
    path = repo_root / "models" / "vectorized_ridge_model.json"
    assert path.exists(), f"Frozen artifact must exist at {path}"
    return path


@pytest.fixture(scope="module")
def loaded_model(artifact_path):
    return VectorizedRidgeETAModel.load_artifact(artifact_path)


@pytest.fixture(scope="module")
def in_memory_model(repo_root):
    """Fits an in-memory reference model on the exact same historical partition."""
    snaps_p = repo_root / "data" / "processed" / "phase_05_prediction_snapshots.parquet"
    voy_p = repo_root / "data" / "processed" / "verified_voyages.parquet"

    df_snaps = pd.read_parquet(snaps_p)
    df_voy = pd.read_parquet(voy_p)

    cutoff_utc = "2016-02-01T00:00:00Z"
    voy_train_ids = set(df_voy[df_voy["dep_timestamp_utc"] < cutoff_utc]["voyage_id"])
    train_df = df_snaps[df_snaps["voyage_id"].isin(voy_train_ids)].copy()

    model = VectorizedRidgeETAModel(alpha=10.0)
    model.fit(train_df, train_df["target_remaining_travel_time_minutes"].values)
    return model


@pytest.fixture(scope="module")
def representative_vectors():
    """Constructs representative fixed inputs across voyage stages and environmental conditions."""
    return pd.DataFrame([
        # 1. Voyage Departure (High distance, low elapsed, high freshness)
        {
            "scenario": "origin_departure",
            "corridor": "BREST_LE_CONQUET",
            "vessel_name": "FROMVEUR II",
            "feature_distance_to_dest_m": 22000.0,
            "elapsed_time_minutes": 2.0,
            "feature_sog_knots": 12.5,
            "feature_observations_so_far": 3,
            "data_freshness_seconds": 15.0,
            "feature_along_track_current_knots": 0.0,
        },
        # 2. Mid-Route Steady Transit
        {
            "scenario": "mid_channel_cruise",
            "corridor": "BREST_LE_CONQUET",
            "vessel_name": "FROMVEUR II",
            "feature_distance_to_dest_m": 11000.0,
            "elapsed_time_minutes": 28.0,
            "feature_sog_knots": 15.2,
            "feature_observations_so_far": 45,
            "data_freshness_seconds": 30.0,
            "feature_along_track_current_knots": -0.8,
        },
        # 3. Terminal Approach (Low distance, slow speed)
        {
            "scenario": "terminal_approach",
            "corridor": "BREST_LE_CONQUET",
            "vessel_name": "FROMVEUR II",
            "feature_distance_to_dest_m": 800.0,
            "elapsed_time_minutes": 52.0,
            "feature_sog_knots": 3.5,
            "feature_observations_so_far": 85,
            "data_freshness_seconds": 10.0,
            "feature_along_track_current_knots": 0.1,
        },
        # 4. Severe Adverse Current Delay Condition
        {
            "scenario": "adverse_tidal_current",
            "corridor": "BREST_OUESSANT_STIFF",
            "vessel_name": "FROMVEUR II",
            "feature_distance_to_dest_m": 18000.0,
            "elapsed_time_minutes": 40.0,
            "feature_sog_knots": 9.0,
            "feature_observations_so_far": 60,
            "data_freshness_seconds": 60.0,
            "feature_along_track_current_knots": -3.5,
        },
        # 5. Slack Water Condition
        {
            "scenario": "slack_water_transit",
            "corridor": "AUDIERNE_ILE_DE_SEIN",
            "vessel_name": "ENEZ SUN 3",
            "feature_distance_to_dest_m": 9500.0,
            "elapsed_time_minutes": 20.0,
            "feature_sog_knots": 14.0,
            "feature_observations_so_far": 30,
            "data_freshness_seconds": 45.0,
            "feature_along_track_current_knots": 0.0,
        },
    ])


def test_frozen_vs_in_memory_numerical_equivalence(loaded_model, in_memory_model, representative_vectors):
    """Test 1 & 2: Compares frozen artifact predictions against in-memory model (tolerance <= 1e-6 min)."""
    preds_frozen = loaded_model.predict(representative_vectors)
    preds_in_memory = in_memory_model.predict(representative_vectors)

    max_diff = float(np.max(np.abs(preds_frozen - preds_in_memory)))
    assert max_diff <= 1e-6, f"Prediction discrepancy {max_diff} exceeded tolerance of 1e-6 minutes!"
    assert (preds_frozen > 0.0).all(), "Predictions must respect physical clamp (> 0)"


def test_deterministic_inference(loaded_model, representative_vectors):
    """Test 3: Evaluates multiple passes to guarantee mathematical determinism."""
    pass_1 = loaded_model.predict(representative_vectors)
    pass_2 = loaded_model.predict(representative_vectors)
    pass_3 = loaded_model.predict(representative_vectors)

    np.testing.assert_array_equal(pass_1, pass_2)
    np.testing.assert_array_equal(pass_2, pass_3)


def test_feature_ordering_and_column_shuffling(loaded_model, representative_vectors):
    """Test 4: Verifies that passing DataFrames with shuffled columns produces identical predictions."""
    normal_preds = loaded_model.predict(representative_vectors)

    shuffled_cols = list(representative_vectors.columns)
    np.random.seed(42)
    np.random.shuffle(shuffled_cols)
    shuffled_df = representative_vectors[shuffled_cols]

    shuffled_preds = loaded_model.predict(shuffled_df)
    max_diff = float(np.max(np.abs(normal_preds - shuffled_preds)))
    assert max_diff <= 1e-12, f"Column order affected prediction! Diff: {max_diff}"


def test_missing_artifact_raises_file_not_found(repo_root):
    """Test 5: Loading a non-existent artifact raises FileNotFoundError with explicit error message."""
    missing_path = repo_root / "models" / "non_existent_model_file.json"
    with pytest.raises(FileNotFoundError) as exc_info:
        VectorizedRidgeETAModel.load_artifact(missing_path)
    assert "Model artifact not found" in str(exc_info.value)


def test_tampered_weights_fail_sha256_validation(artifact_path, tmp_path):
    """Test 6: Tampering with a single weight coefficient triggers ModelArtifactTamperedError."""
    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Tamper with the intercept
    data["weights"]["coefficients"][0] += 1.0

    tampered_file = tmp_path / "tampered_model.json"
    with open(tampered_file, "w", encoding="utf-8") as f:
        json.dump(data, f)

    with pytest.raises(ModelArtifactTamperedError) as exc_info:
        VectorizedRidgeETAModel.load_artifact(tampered_file)
    assert "SHA-256 mismatch" in str(exc_info.value)


def test_unsupported_schema_version_rejection(artifact_path, tmp_path):
    """Test 7: Unsupported schema version (e.g. '2.0.0') triggers UnsupportedModelSchemaVersionError."""
    with open(artifact_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["schema_version"] = "2.0.0"

    invalid_version_file = tmp_path / "invalid_version_model.json"
    with open(invalid_version_file, "w", encoding="utf-8") as f:
        json.dump(data, f)

    with pytest.raises(UnsupportedModelSchemaVersionError) as exc_info:
        VectorizedRidgeETAModel.load_artifact(invalid_version_file)
    assert "Unsupported model schema version: 2.0.0" in str(exc_info.value)


def test_voyage_level_split_has_zero_overlap(repo_root):
    """Test 8: Confirms that training and test splits have exactly zero overlapping voyage IDs."""
    voy_p = repo_root / "data" / "processed" / "verified_voyages.parquet"
    df_voy = pd.read_parquet(voy_p)

    cutoff_utc = "2016-02-01T00:00:00Z"
    voy_train_ids = set(df_voy[df_voy["dep_timestamp_utc"] < cutoff_utc]["voyage_id"])
    voy_test_ids = set(df_voy[df_voy["dep_timestamp_utc"] >= cutoff_utc]["voyage_id"])

    overlap = voy_train_ids.intersection(voy_test_ids)
    assert len(overlap) == 0, f"Found {len(overlap)} overlapping voyage IDs across splits!"
    assert len(voy_train_ids) == 685, f"Expected 685 train voyages, found {len(voy_train_ids)}"
    assert len(voy_test_ids) == 204, f"Expected 204 test voyages, found {len(voy_test_ids)}"


def test_historical_test_partition_evaluation(loaded_model, repo_root):
    """Test 9: Evaluates the frozen artifact against the held-out test partition and verifies MAE."""
    snaps_p = repo_root / "data" / "processed" / "phase_05_prediction_snapshots.parquet"
    voy_p = repo_root / "data" / "processed" / "verified_voyages.parquet"

    df_snaps = pd.read_parquet(snaps_p)
    df_voy = pd.read_parquet(voy_p)

    cutoff_utc = "2016-02-01T00:00:00Z"
    voy_test_ids = set(df_voy[df_voy["dep_timestamp_utc"] >= cutoff_utc]["voyage_id"])
    test_df = df_snaps[df_snaps["voyage_id"].isin(voy_test_ids)].copy()

    preds = loaded_model.predict(test_df)
    y_test = test_df["target_remaining_travel_time_minutes"].values

    mae = float(np.mean(np.abs(preds - y_test)))
    assert round(mae, 2) == 5.20, f"Test MAE {mae} deviates from verified historical baseline of 5.20m!"
