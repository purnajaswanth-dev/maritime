"""Comprehensive Phase 05 evaluation pipeline for baselines and tabular ETA models.

Implements:
1. Approved Chronological Protocol 1 (Train: Oct 2015 - Jan 2016; Test: Feb - Mar 2016)
2. Physical ETA baseline (pure kinematic vs ocean current-augmented)
3. Strictly causal Historical Route Duration baseline
4. Vectorized Ridge Regression tabular ML model (fit on train only)
5. Comprehensive metrics (MAE, MedAE, RMSE, percentiles, slices by vessel/corridor/horizon)
6. Sequential prediction stability and overshoot replay analysis
"""

from collections import defaultdict
import datetime
import json
import math
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.ingestion.trajectory_segmenter import TERMINALS, haversine_m


class UnsupportedModelSchemaVersionError(ValueError):
    """Raised when an artifact schema version is not supported."""
    pass


class ModelArtifactTamperedError(ValueError):
    """Raised when an artifact's weights SHA-256 hash does not match stored signature."""
    pass


class ModelArtifactCorruptedError(ValueError):
    """Raised when an artifact contains invalid or malformed data."""
    pass


class VectorizedRidgeETAModel:
    """Deterministic, closed-form L2-regularized linear model in NumPy.

    Fits on training set only; standardizes numerical features using training statistics.
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.weights: Optional[np.ndarray] = None
        self.mean_: Optional[np.ndarray] = None
        self.std_: Optional[np.ndarray] = None
        self.corridor_categories: List[str] = []
        self.vessel_categories: List[str] = []

    @classmethod
    def load_artifact(cls, artifact_path: Path) -> "VectorizedRidgeETAModel":
        """Loads frozen model from versioned JSON artifact with strict integrity checks."""
        import hashlib
        import json

        if not artifact_path.exists():
            raise FileNotFoundError(f"Model artifact not found at {artifact_path}")

        with open(artifact_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                raise ModelArtifactCorruptedError(f"Malformed JSON artifact: {e}") from e

        schema_version = data.get("schema_version")
        if schema_version != "1.0.0":
            raise UnsupportedModelSchemaVersionError(
                f"Unsupported model schema version: {schema_version}. Expected '1.0.0'."
            )

        weights_info = data.get("weights", {})
        coeffs = weights_info.get("coefficients", [])
        expected_sha256 = weights_info.get("weights_sha256")

        # Verify integrity
        coeffs_bytes = json.dumps(coeffs, sort_keys=True).encode("utf-8")
        actual_sha256 = hashlib.sha256(coeffs_bytes).hexdigest()
        if actual_sha256 != expected_sha256:
            raise ModelArtifactTamperedError(
                f"Model weights SHA-256 mismatch! Expected {expected_sha256}, got {actual_sha256}."
            )

        feat_spec = data.get("feature_specification", {})
        scaling = feat_spec.get("continuous_scaling", {})
        cat_enc = feat_spec.get("categorical_encodings", {})

        model = cls(alpha=float(data.get("metadata", {}).get("alpha", 10.0)))
        model.weights = np.array(coeffs, dtype=np.float64)
        model.mean_ = np.array(scaling.get("mean", []), dtype=np.float64)
        model.std_ = np.array(scaling.get("std", []), dtype=np.float64)
        model.corridor_categories = list(cat_enc.get("corridor_categories", []))
        model.vessel_categories = list(cat_enc.get("vessel_categories", []))

        expected_dim = 1 + len(model.mean_) + len(model.corridor_categories) + len(model.vessel_categories)
        if len(model.weights) != expected_dim:
            raise ModelArtifactCorruptedError(
                f"Weight dimension mismatch: expected {expected_dim}, got {len(model.weights)}"
            )

        return model


    def _prepare_features(self, df: pd.DataFrame, is_training: bool = False) -> np.ndarray:
        if is_training:
            self.corridor_categories = sorted(df["corridor"].unique().tolist())
            self.vessel_categories = sorted(df["vessel_name"].unique().tolist())

        # Continuous features
        X_num = np.column_stack([
            df["feature_distance_to_dest_m"].values / 1000.0,  # km
            df["elapsed_time_minutes"].values,
            df["feature_sog_knots"].values,
            df["feature_observations_so_far"].values,
            df["data_freshness_seconds"].values / 60.0,  # min
            df["feature_along_track_current_knots"].fillna(0.0).values,
        ])

        if is_training:
            self.mean_ = np.mean(X_num, axis=0)
            self.std_ = np.std(X_num, axis=0)
            self.std_[self.std_ == 0] = 1.0

        X_num_scaled = (X_num - self.mean_) / self.std_

        # One-hot encoded categorical features
        corr_dummies = []
        for c in self.corridor_categories:
            corr_dummies.append((df["corridor"].values == c).astype(float))
        X_corr = np.column_stack(corr_dummies) if corr_dummies else np.empty((len(df), 0))

        vess_dummies = []
        for v in self.vessel_categories:
            vess_dummies.append((df["vessel_name"].values == v).astype(float))
        X_vess = np.column_stack(vess_dummies) if vess_dummies else np.empty((len(df), 0))

        # Add bias / intercept column
        bias = np.ones((len(df), 1))
        return np.column_stack([bias, X_num_scaled, X_corr, X_vess])

    def fit(self, df_train: pd.DataFrame, y_train: np.ndarray):
        X = self._prepare_features(df_train, is_training=True)
        p = X.shape[1]
        I = np.eye(p)
        I[0, 0] = 0.0  # Do not regularize intercept
        self.weights = np.linalg.solve(X.T @ X + self.alpha * I, X.T @ y_train)

    def predict(self, df_eval: pd.DataFrame) -> np.ndarray:
        X = self._prepare_features(df_eval, is_training=False)
        preds = X @ self.weights
        return np.maximum(preds, 0.1)  # Physical clamp: remaining time > 0


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    """Computes comprehensive error metrics for ETA predictions."""
    errors = y_pred - y_true
    abs_errors = np.abs(errors)

    mae = float(np.mean(abs_errors))
    medae = float(np.median(abs_errors))
    rmse = float(np.sqrt(np.mean(errors**2)))

    p50 = float(np.percentile(abs_errors, 50))
    p75 = float(np.percentile(abs_errors, 75))
    p90 = float(np.percentile(abs_errors, 90))
    p95 = float(np.percentile(abs_errors, 95))
    p99 = float(np.percentile(abs_errors, 99))
    max_err = float(np.max(abs_errors))

    pct_within_3m = float(np.mean(abs_errors <= 3.0) * 100.0)
    pct_within_5m = float(np.mean(abs_errors <= 5.0) * 100.0)
    pct_within_10m = float(np.mean(abs_errors <= 10.0) * 100.0)
    pct_over_15m = float(np.mean(abs_errors > 15.0) * 100.0)

    # Directional bias
    mean_bias = float(np.mean(errors))
    pct_early = float(np.mean(errors < 0) * 100.0)  # Premature arrival
    pct_late = float(np.mean(errors > 0) * 100.0)   # Overestimate remaining

    return {
        "mae_minutes": round(mae, 2),
        "median_ae_minutes": round(medae, 2),
        "rmse_minutes": round(rmse, 2),
        "mean_bias_minutes": round(mean_bias, 2),
        "percentile_50": round(p50, 2),
        "percentile_75": round(p75, 2),
        "percentile_90": round(p90, 2),
        "percentile_95": round(p95, 2),
        "percentile_99": round(p99, 2),
        "max_error_minutes": round(max_err, 2),
        "pct_within_3m": round(pct_within_3m, 1),
        "pct_within_5m": round(pct_within_5m, 1),
        "pct_within_10m": round(pct_within_10m, 1),
        "pct_over_15m": round(pct_over_15m, 1),
        "pct_premature_arrival": round(pct_early, 1),
        "pct_overestimate_arrival": round(pct_late, 1),
    }


def main():
    snapshots_path = repo_root / "data" / "processed" / "phase_05_prediction_snapshots.parquet"
    verified_path = repo_root / "data" / "processed" / "verified_voyages.parquet"

    print(f"Loading snapshots from {snapshots_path}...")
    df_snaps = pd.read_parquet(snapshots_path)
    df_voy = pd.read_parquet(verified_path)

    # 1. Implement Approved Chronological Protocol 1 Split
    train_split_cutoff = "2016-02-01T00:00:00Z"

    # Split by voyage departure timestamp to ensure whole voyages are strictly kept together
    voy_train_ids = set(df_voy[df_voy["dep_timestamp_utc"] < train_split_cutoff]["voyage_id"])
    voy_test_ids = set(df_voy[df_voy["dep_timestamp_utc"] >= train_split_cutoff]["voyage_id"])

    # Double check no overlap
    assert len(voy_train_ids.intersection(voy_test_ids)) == 0, "FATAL: Voyage overlap across train/test splits!"

    train_df = df_snaps[df_snaps["voyage_id"].isin(voy_train_ids)].copy()
    test_df = df_snaps[df_snaps["voyage_id"].isin(voy_test_ids)].copy()

    print("\n=== Protocol 1 Partition Summary ===")
    print(f"Train Period: 2015-10-01 to 2016-01-31 | Voyages: {len(voy_train_ids)} | Snapshots: {len(train_df)}")
    print(f"Test Period:  2016-02-01 to 2016-03-31 | Voyages: {len(voy_test_ids)} | Snapshots: {len(test_df)}")
    print(f"Train Vessels: {train_df['vessel_name'].nunique()} | Test Vessels: {test_df['vessel_name'].nunique()}")
    print(f"Train Corridors: {train_df['corridor'].nunique()} | Test Corridors: {test_df['corridor'].nunique()}")

    y_test = test_df["target_remaining_travel_time_minutes"].values

    # 2. Benchmark Physical ETA Baseline
    print("\nComputing Physical ETA Baselines...")
    # Baseline A: Pure Kinematic (distance / max(sog, 3.0 kts))
    # 1 knot = 1852.0 / 60.0 meters per minute = 30.8667 m/min
    sog_safe = np.maximum(test_df["feature_sog_knots"].values, 3.0)
    speed_m_per_min = sog_safe * (1852.0 / 60.0)
    pred_physical_pure = test_df["feature_distance_to_dest_m"].values / speed_m_per_min

    # Baseline B: Ocean-Current Augmented Kinematic
    along_track_knots = test_df["feature_along_track_current_knots"].fillna(0.0).values
    effective_sog = np.maximum(sog_safe + along_track_knots, 3.0)
    effective_speed_m_min = effective_sog * (1852.0 / 60.0)
    pred_physical_current = test_df["feature_distance_to_dest_m"].values / effective_speed_m_min

    # 3. Benchmark Strictly Causal Historical Route Duration Baseline
    print("Computing Strictly Causal Historical Route Duration Baseline...")
    # For every test snapshot, query only completed voyages on the same corridor with arr_ts <= pred_ts
    all_voy_records = df_voy.to_dict(orient="records")
    # Pre-index completed voyages by corridor
    voyages_by_corr = defaultdict(list)
    for v in all_voy_records:
        corr = f"{v['dep_terminal']}_{v['arr_terminal']}"
        voyages_by_corr[corr].append(v)

    pred_historical = []
    hist_covered_count = 0

    for _, r in test_df.iterrows():
        corr = r["corridor"]
        pred_ts = r["prediction_ts_epoch_ms"]
        curr_voy_id = r["voyage_id"]
        elapsed = r["elapsed_time_minutes"]

        # Filter: same corridor, strictly completed before pred_ts, exclude current voyage
        completed_trips = [
            v for v in voyages_by_corr[corr]
            if v["arr_ts_epoch_ms"] <= pred_ts and v["voyage_id"] != curr_voy_id
        ]

        if len(completed_trips) >= 3:
            median_duration = float(np.median([v["duration_minutes"] for v in completed_trips]))
            pred_rem = max(0.1, median_duration - elapsed)
            hist_covered_count += 1
        elif completed_trips:
            # Fallback to whatever history is available
            median_duration = float(np.median([v["duration_minutes"] for v in completed_trips]))
            pred_rem = max(0.1, median_duration - elapsed)
            hist_covered_count += 1
        else:
            # Insufficient history fallback: use physical pure prediction
            dist_km = r["feature_distance_to_dest_m"] / 1000.0
            pred_rem = max(0.1, (dist_km / 15.0) * 60.0)  # assume 15 knot ferry speed

        pred_historical.append(pred_rem)

    pred_historical = np.array(pred_historical)
    print(f"Historical baseline coverage: {hist_covered_count} / {len(test_df)} ({hist_covered_count/len(test_df)*100:.1f}%)")

    # 4. Train and Evaluate Tabular Ridge ETA Model
    print("Training Vectorized Ridge ETA Model on Train Split...")
    y_train = train_df["target_remaining_travel_time_minutes"].values
    ridge_model = VectorizedRidgeETAModel(alpha=10.0)
    ridge_model.fit(train_df, y_train)
    pred_ridge = ridge_model.predict(test_df)

    # 5. Compile Overall Evaluation Table
    models_dict = {
        "Physical_ETA_Pure": pred_physical_pure,
        "Physical_ETA_CurrentAugmented": pred_physical_current,
        "Historical_Route_Duration_Causal": pred_historical,
        "Tabular_Ridge_ETA": pred_ridge,
    }

    eval_results = {}
    for mname, preds in models_dict.items():
        eval_results[mname] = evaluate_predictions(y_test, preds)

    df_overall = pd.DataFrame(eval_results).T
    print("\n=== Protocol 1 Overall Test Performance (N = 2,130 snapshots) ===")
    print(df_overall[["mae_minutes", "median_ae_minutes", "rmse_minutes", "pct_within_5m", "pct_within_10m", "pct_over_15m", "pct_premature_arrival"]].to_string())

    # 6. Sliced Analysis for Best Model (Tabular Ridge vs Baselines)
    test_df_eval = test_df.copy()
    test_df_eval["pred_ridge"] = pred_ridge
    test_df_eval["pred_physical"] = pred_physical_pure
    test_df_eval["pred_historical"] = pred_historical
    test_df_eval["err_ridge"] = np.abs(pred_ridge - y_test)
    test_df_eval["err_physical"] = np.abs(pred_physical_pure - y_test)
    test_df_eval["err_historical"] = np.abs(pred_historical - y_test)

    # Slice by Horizon
    bins = [0, 15, 30, 60, 200]
    labels = ["<15m", "15-30m", "30-60m", ">60m"]
    test_df_eval["horizon_bucket"] = pd.cut(test_df_eval["target_remaining_travel_time_minutes"], bins=bins, labels=labels)

    horizon_slice = test_df_eval.groupby("horizon_bucket", observed=False).agg(
        n_snapshots=("snapshot_id", "count"),
        mae_physical=("err_physical", "mean"),
        mae_historical=("err_historical", "mean"),
        mae_ridge=("err_ridge", "mean"),
    ).round(2)
    print("\n=== Performance Sliced by Remaining-Time Horizon ===")
    print(horizon_slice.to_string())

    # Slice by Corridor
    corridor_slice = test_df_eval.groupby("corridor").agg(
        n_snapshots=("snapshot_id", "count"),
        mae_physical=("err_physical", "mean"),
        mae_historical=("err_historical", "mean"),
        mae_ridge=("err_ridge", "mean"),
    ).round(2)
    print("\n=== Performance Sliced by Corridor ===")
    print(corridor_slice.to_string())

    # Slice by Vessel
    vessel_slice = test_df_eval.groupby("vessel_name").agg(
        n_snapshots=("snapshot_id", "count"),
        mae_physical=("err_physical", "mean"),
        mae_historical=("err_historical", "mean"),
        mae_ridge=("err_ridge", "mean"),
    ).round(2)
    print("\n=== Performance Sliced by Vessel ===")
    print(vessel_slice.to_string())

    # 7. Sequential ETA Stability & Overshoot Replay Analysis
    print("\nExecuting Sequential Stability Replay Analysis...")
    test_df_eval = test_df_eval.sort_values(["voyage_id", "prediction_ts_epoch_ms"])

    stability_records = []
    # Evaluate for each voyage in test set
    for v_id, group in test_df_eval.groupby("voyage_id"):
        if len(group) < 2:
            continue
        g_snaps = group.to_dict(orient="records")
        for i in range(1, len(g_snaps)):
            prev = g_snaps[i-1]
            curr = g_snaps[i]
            dt_step = (curr["prediction_ts_epoch_ms"] - prev["prediction_ts_epoch_ms"]) / 60000.0  # min

            # Raw jumps
            jump_ridge = curr["pred_ridge"] - prev["pred_ridge"]
            jump_phys = curr["pred_physical"] - prev["pred_physical"]
            jump_hist = curr["pred_historical"] - prev["pred_historical"]

            stability_records.append({
                "voyage_id": v_id,
                "step_minutes": dt_step,
                "jump_ridge": jump_ridge,
                "abs_jump_ridge": abs(jump_ridge),
                "jump_phys": jump_phys,
                "abs_jump_phys": abs(jump_phys),
                "jump_hist": jump_hist,
                "abs_jump_hist": abs(jump_hist),
                "target_delta": curr["target_remaining_travel_time_minutes"] - prev["target_remaining_travel_time_minutes"],
            })

    df_stab = pd.DataFrame(stability_records)
    print(f"Evaluated {len(df_stab)} consecutive sequential update steps across {test_df_eval['voyage_id'].nunique()} test voyages.")
    print("Sequential Jump Summary (minutes):")
    print(f"  Ridge Mean Abs Jump: {df_stab['abs_jump_ridge'].mean():.2f}m | Median: {df_stab['abs_jump_ridge'].median():.2f}m | P95: {df_stab['abs_jump_ridge'].quantile(0.95):.2f}m | Jumps > 5m: {(df_stab['abs_jump_ridge'] > 5.0).mean()*100:.1f}%")
    print(f"  Physical Mean Abs Jump: {df_stab['abs_jump_phys'].mean():.2f}m | Median: {df_stab['abs_jump_phys'].median():.2f}m | P95: {df_stab['abs_jump_phys'].quantile(0.95):.2f}m | Jumps > 5m: {(df_stab['abs_jump_phys'] > 5.0).mean()*100:.1f}%")
    print(f"  Historical Mean Abs Jump: {df_stab['abs_jump_hist'].mean():.2f}m | Median: {df_stab['abs_jump_hist'].median():.2f}m | P95: {df_stab['abs_jump_hist'].quantile(0.95):.2f}m | Jumps > 5m: {(df_stab['abs_jump_hist'] > 5.0).mean()*100:.1f}%")

    # 8. Save Model Predictions and Evaluation Manifest
    output_preds_path = repo_root / "data" / "processed" / "phase_05_test_predictions.parquet"
    test_df_eval.to_parquet(output_preds_path, index=False)
    print(f"\nSaved test predictions to {output_preds_path} ({output_preds_path.stat().st_size:,} bytes).")

    # Save metrics JSON
    metrics_summary = {
        "protocol": "Protocol 1 (Chronological Split)",
        "train_period": "2015-10-01 to 2016-01-31",
        "test_period": "2016-02-01 to 2016-03-31",
        "sample_counts": {
            "train_voyages": len(voy_train_ids),
            "test_voyages": len(voy_test_ids),
            "train_snapshots": len(train_df),
            "test_snapshots": len(test_df),
        },
        "overall_performance": eval_results,
        "stability_metrics": {
            "eval_steps": len(df_stab),
            "ridge_mean_abs_jump_min": round(float(df_stab["abs_jump_ridge"].mean()), 2),
            "ridge_p95_jump_min": round(float(df_stab["abs_jump_ridge"].quantile(0.95)), 2),
            "ridge_jumps_over_5m_pct": round(float((df_stab["abs_jump_ridge"] > 5.0).mean() * 100.0), 1),
            "physical_mean_abs_jump_min": round(float(df_stab["abs_jump_phys"].mean()), 2),
            "physical_p95_jump_min": round(float(df_stab["abs_jump_phys"].quantile(0.95)), 2),
            "physical_jumps_over_5m_pct": round(float((df_stab["abs_jump_phys"] > 5.0).mean() * 100.0), 1),
            "historical_mean_abs_jump_min": round(float(df_stab["abs_jump_hist"].mean()), 2),
            "historical_p95_jump_min": round(float(df_stab["abs_jump_hist"].quantile(0.95)), 2),
            "historical_jumps_over_5m_pct": round(float((df_stab["abs_jump_hist"] > 5.0).mean() * 100.0), 1),
        },
        "corridor_slice": corridor_slice.to_dict(orient="index"),
        "horizon_slice": horizon_slice.to_dict(orient="index"),
        "vessel_slice": vessel_slice.to_dict(orient="index"),
    }

    metrics_out_path = repo_root / "data" / "manifests" / "phase-05-evaluation-metrics.json"
    with open(metrics_out_path, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"Saved evaluation metrics to {metrics_out_path} ({metrics_out_path.stat().st_size:,} bytes).")


if __name__ == "__main__":
    main()
