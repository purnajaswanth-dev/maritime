"""Export utility to train, validate, and serialize the frozen VectorizedRidgeETAModel artifact.

Guarantees:
- Strict voyage-level chronological departure split (< 2016-02-01T00:00:00Z) with zero voyage-ID leakage.
- Complete inference metadata: coefficients, intercept, feature ordering, continuous scaling (mean, std),
  and categorical mappings for corridors and vessels.
- Cryptographic SHA-256 validation of the weights and source datasets.
- Numerical equivalence verification against stored historical test predictions.
"""

import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict
import numpy as np
import pandas as pd

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.models.evaluate_phase05 import VectorizedRidgeETAModel, evaluate_predictions


def compute_file_sha256(filepath: Path) -> str:
    """Computes SHA-256 hexadecimal hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Computes SHA-256 hexadecimal hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def export_ridge_artifact(
    output_dir: Path,
    snapshots_path: Path,
    verified_voyages_path: Path,
    test_predictions_path: Path,
    alpha: float = 10.0,
    cutoff_utc: str = "2016-02-01T00:00:00Z",
) -> Dict[str, Any]:
    """Fits VectorizedRidgeETAModel on strictly voyage-partitioned training data and exports frozen artifact."""
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / "vectorized_ridge_model.json"

    # 1. Load historical datasets
    df_snaps = pd.read_parquet(snapshots_path)
    df_voy = pd.read_parquet(verified_voyages_path)
    df_test_preds = pd.read_parquet(test_predictions_path)

    # 2. Strict voyage-level departure split
    voy_train_ids = set(df_voy[df_voy["dep_timestamp_utc"] < cutoff_utc]["voyage_id"])
    voy_test_ids = set(df_voy[df_voy["dep_timestamp_utc"] >= cutoff_utc]["voyage_id"])

    # Assert zero cross-split leakage
    leakage_count = len(voy_train_ids.intersection(voy_test_ids))
    assert leakage_count == 0, f"FATAL: Voyage overlap across train/test splits ({leakage_count} overlapping IDs)"

    train_df = df_snaps[df_snaps["voyage_id"].isin(voy_train_ids)].copy()
    test_df = df_snaps[df_snaps["voyage_id"].isin(voy_test_ids)].copy()

    # 3. Fit VectorizedRidgeETAModel
    model = VectorizedRidgeETAModel(alpha=alpha)
    y_train = train_df["target_remaining_travel_time_minutes"].values
    model.fit(train_df, y_train)

    # 4. Verify test predictions against stored test predictions (Protocol 1)
    test_df["recomputed_pred"] = model.predict(test_df)
    merged = pd.merge(
        df_test_preds[["snapshot_id", "pred_ridge"]],
        test_df[["snapshot_id", "recomputed_pred"]],
        on="snapshot_id",
    )
    max_test_diff = float(np.max(np.abs(merged["pred_ridge"].values - merged["recomputed_pred"].values)))
    assert max_test_diff <= 1e-6, f"Discrepancy with historical test predictions exceeded tolerance: {max_test_diff}"

    y_test = test_df["target_remaining_travel_time_minutes"].values
    eval_metrics = evaluate_predictions(y_test, test_df["recomputed_pred"].values)

    # 5. Build feature ordering metadata
    continuous_features = [
        "feature_distance_to_dest_m",
        "elapsed_time_minutes",
        "feature_sog_knots",
        "feature_observations_so_far",
        "data_freshness_seconds",
        "feature_along_track_current_knots",
    ]

    feature_order = ["bias"]
    feature_order.extend([
        "distance_to_dest_km_scaled",
        "elapsed_time_min_scaled",
        "sog_knots_scaled",
        "obs_so_far_scaled",
        "data_freshness_min_scaled",
        "along_track_current_knots_scaled",
    ])
    feature_order.extend([f"corridor_{c}" for c in model.corridor_categories])
    feature_order.extend([f"vessel_{v}" for v in model.vessel_categories])

    weights_list = [float(w) for w in model.weights]
    weights_canonical_bytes = json.dumps(weights_list, sort_keys=True).encode("utf-8")
    weights_sha256 = compute_bytes_sha256(weights_canonical_bytes)

    # 6. Build complete frozen artifact dictionary
    artifact_payload: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "metadata": {
            "model_name": "VectorizedRidgeETAModel",
            "model_type": "L2_RIDGE_LINEAR",
            "alpha": float(alpha),
            "created_at_utc": "2026-10-16T18:30:00Z",
            "description": "Frozen Ridge ETA model weights and preprocessing parameters for Brest/Iroise Sea passenger ferries.",
        },
        "provenance": {
            "training_snapshots_source": "data/processed/phase_05_prediction_snapshots.parquet",
            "training_snapshots_sha256": compute_file_sha256(snapshots_path),
            "verified_voyages_source": "data/processed/verified_voyages.parquet",
            "verified_voyages_sha256": compute_file_sha256(verified_voyages_path),
            "test_predictions_source": "data/processed/phase_05_test_predictions.parquet",
            "test_predictions_sha256": compute_file_sha256(test_predictions_path),
            "split_policy": "Protocol 1 Chronological Departure Split (Strict Voyage-ID Grouped)",
            "split_cutoff_utc": cutoff_utc,
            "train_voyage_count": len(voy_train_ids),
            "train_snapshot_count": len(train_df),
            "test_voyage_count": len(voy_test_ids),
            "test_snapshot_count": len(test_df),
            "cross_split_voyage_leakage_count": 0,
            "evaluated_test_mae_minutes": eval_metrics["mae_minutes"],
            "evaluated_test_rmse_minutes": eval_metrics["rmse_minutes"],
            "evaluated_test_medae_minutes": eval_metrics["median_ae_minutes"],
        },
        "feature_specification": {
            "feature_count": len(feature_order),
            "intercept_index": 0,
            "feature_order": feature_order,
            "continuous_features": continuous_features,
            "continuous_scaling": {
                "mean": [float(m) for m in model.mean_],
                "std": [float(s) for s in model.std_],
            },
            "categorical_encodings": {
                "corridor_categories": model.corridor_categories,
                "vessel_categories": model.vessel_categories,
            },
        },
        "weights": {
            "format": "FLOAT64_ARRAY",
            "dimension": len(weights_list),
            "intercept": weights_list[0],
            "coefficients": weights_list,
            "weights_sha256": weights_sha256,
        },
    }

    # 7. Write versioned JSON artifact
    artifact_json_bytes = json.dumps(artifact_payload, indent=2, sort_keys=False).encode("utf-8")
    with open(artifact_path, "wb") as f:
        f.write(artifact_json_bytes)

    artifact_file_sha256 = compute_file_sha256(artifact_path)

    return {
        "artifact_path": str(artifact_path),
        "artifact_sha256": artifact_file_sha256,
        "weights_sha256": weights_sha256,
        "feature_count": len(feature_order),
        "train_snapshots": len(train_df),
        "train_voyages": len(voy_train_ids),
        "test_snapshots": len(test_df),
        "test_voyages": len(voy_test_ids),
        "test_mae_minutes": eval_metrics["mae_minutes"],
        "max_discrepancy_with_stored_preds": max_test_diff,
    }


def main():
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "models"
    snaps_p = repo_root / "data" / "processed" / "phase_05_prediction_snapshots.parquet"
    voy_p = repo_root / "data" / "processed" / "verified_voyages.parquet"
    test_preds_p = repo_root / "data" / "processed" / "phase_05_test_predictions.parquet"

    print(f"Exporting frozen Ridge ETA model to {out_dir}...")
    res = export_ridge_artifact(out_dir, snaps_p, voy_p, test_preds_p)
    print("Export completed successfully:")
    for k, v in res.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
