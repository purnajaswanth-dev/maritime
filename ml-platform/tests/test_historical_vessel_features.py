"""Tests verifying the restoration and activation of historical vessel-category features.

Ensures that virtual simulation vessels activate their exact historical one-hot dummy features
in the frozen Ridge model without altering frozen weights.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from src.models.evaluate_phase05 import VectorizedRidgeETAModel
from src.simulation.virtual_ais_generator import VirtualAISGenerator
from src.streaming.eta_stream_processor import ETAStreamProcessor, HISTORICAL_VESSEL_MAP

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_ARTIFACT = REPO_ROOT / "models" / "vectorized_ridge_model.json"


def test_frozen_weights_integrity():
    """Verify that model weights artifact has not been modified or overwritten."""
    assert MODEL_ARTIFACT.exists(), f"Model artifact not found: {MODEL_ARTIFACT}"
    with open(MODEL_ARTIFACT, "r", encoding="utf-8") as f:
        data = json.load(f)

    weights_info = data["weights"]
    coeffs = weights_info["coefficients"]
    coeffs_bytes = json.dumps(coeffs, sort_keys=True).encode("utf-8")
    current_sha256 = hashlib.sha256(coeffs_bytes).hexdigest()

    expected_sha256 = weights_info["weights_sha256"]
    assert current_sha256 == expected_sha256, (
        f"Model weights hash mismatch: expected {expected_sha256}, got {current_sha256}. "
        "Frozen weights must never be altered."
    )


def test_historical_vessel_mapping_contract():
    """Verify the 4 virtual fleet vessels correctly map to the 4 historical training vessels."""
    expected_mappings = {
        "V-FROMVEUR-SIM": "FROMVEUR II",
        "SIM_FROMVEUR_EXPRESS": "FROMVEUR II",
        "V-AZENOR-SIM": "ANDRE COLIN",
        "SIM_AZENOR_VOYAGER": "ANDRE COLIN",
        "V-OUESSANT-SIM": "ENEZ EUSSA 3",
        "SIM_IROISE_STAR": "ENEZ EUSSA 3",
        "V-SEIN-SIM": "ENEZ SUN 3",
        "SIM_SEIN_SHUTTLE": "ENEZ SUN 3",
    }
    for vessel_key, expected_hist_name in expected_mappings.items():
        mapped = HISTORICAL_VESSEL_MAP.get(vessel_key)
        assert mapped == expected_hist_name, (
            f"Vessel key '{vessel_key}' mapped to '{mapped}', expected '{expected_hist_name}'"
        )


def test_generator_emits_historical_vessel_name():
    """Verify that VirtualAISGenerator includes historical_vessel_name in its generated event payloads."""
    gen = VirtualAISGenerator()
    sim_time = datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc)

    expected_pairs = [
        ("V-FROMVEUR-SIM", "FROMVEUR II"),
        ("V-AZENOR-SIM", "ANDRE COLIN"),
        ("V-OUESSANT-SIM", "ENEZ EUSSA 3"),
        ("V-SEIN-SIM", "ENEZ SUN 3"),
    ]

    for v_id, expected_hist_name in expected_pairs:
        event = gen.advance_vessel_step(
            vessel_id=v_id,
            sim_timestamp_utc=sim_time,
            delta_seconds=0.0,
            simulation_run_id="test_run",
            scenario_id="unit_test",
        )
        assert "historical_vessel_name" in event, f"Missing historical_vessel_name in event for {v_id}"
        assert event["historical_vessel_name"] == expected_hist_name, (
            f"Expected {expected_hist_name} for {v_id}, got {event['historical_vessel_name']}"
        )


def test_one_hot_feature_activation_for_each_vessel():
    """Verify that feature construction activates the exact one-hot category for each vessel."""
    model = VectorizedRidgeETAModel.load_artifact(MODEL_ARTIFACT)
    categories = model.vessel_categories
    assert categories == ["ANDRE COLIN", "ENEZ EUSSA 3", "ENEZ SUN 3", "FROMVEUR II"]

    generator = VirtualAISGenerator()
    processor = ETAStreamProcessor(model=model)
    sim_time = datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc)

    # Expected index in vessel_categories:
    # "ANDRE COLIN" -> 0
    # "ENEZ EUSSA 3" -> 1
    # "ENEZ SUN 3" -> 2
    # "FROMVEUR II" -> 3
    expected_active_indices = {
        "V-AZENOR-SIM": 0,
        "V-OUESSANT-SIM": 1,
        "V-SEIN-SIM": 2,
        "V-FROMVEUR-SIM": 3,
    }

    for v_id, expected_cat_idx in expected_active_indices.items():
        event = generator.advance_vessel_step(
            vessel_id=v_id,
            sim_timestamp_utc=sim_time,
            delta_seconds=60.0,
            simulation_run_id="test_one_hot",
            scenario_id="test",
        )
        resp, err = processor.process_event(
            raw_payload=event,
            current_sim_time_utc=sim_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        assert err is None
        assert resp is not None

        # Verify through active tracker and direct feature evaluation
        tracker = processor.vessel_trackers[event["mmsi"]]
        hist_name = tracker.historical_vessel_name
        assert hist_name == categories[expected_cat_idx]

        # Construct single-row DataFrame identically to processor
        df = pd.DataFrame([{
            "feature_distance_to_dest_m": 5000.0,
            "elapsed_time_minutes": 10.0,
            "feature_sog_knots": 14.5,
            "feature_observations_so_far": 2,
            "data_freshness_seconds": 0.0,
            "feature_along_track_current_knots": 0.0,
            "corridor": tracker.corridor,
            "vessel_name": hist_name,
        }])
        X = model._prepare_features(df, is_training=False)

        # Structure of X: [bias(1), num_scaled(6), corr_dummies(len=10), vess_dummies(len=4)]
        # Total columns = 1 + 6 + 10 + 4 = 21
        assert X.shape[1] == 21
        vess_slice = X[0, 17:21]

        # Verify exactly one category is 1.0, and it matches expected_cat_idx
        assert np.sum(vess_slice) == 1.0, f"Expected 1 one-hot active, got {vess_slice}"
        assert vess_slice[expected_cat_idx] == 1.0, (
            f"Vessel {v_id} ({hist_name}) did not activate index {expected_cat_idx}. Slice: {vess_slice}"
        )
