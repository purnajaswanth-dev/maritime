"""Exploratory unseen-vessel zero-shot case study (Protocol 2).

Evaluates generalization when holding out one vessel completely from training.
Documents vessel-route confounding and why Protocol 2 is not statistically conclusive with N=4 vessels.
"""

from pathlib import Path
import sys
import numpy as np
import pandas as pd

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.models.evaluate_phase05 import VectorizedRidgeETAModel, evaluate_predictions

snapshots_path = repo_root / "data" / "processed" / "phase_05_prediction_snapshots.parquet"
df_snaps = pd.read_parquet(snapshots_path)

print("=== Protocol 2: Exploratory Unseen-Vessel Holdout Case Study ===")
# Case Study A: Hold out ENEZ EUSSA 3 (operates on shared Brest-Ouessant routes)
held_out_vessel_a = "ENEZ EUSSA 3"
train_a = df_snaps[df_snaps["vessel_name"] != held_out_vessel_a].copy()
test_a = df_snaps[df_snaps["vessel_name"] == held_out_vessel_a].copy()

print(f"\nCase A: Hold out {held_out_vessel_a}")
print(f"  Train snapshots: {len(train_a)} ({train_a['vessel_name'].unique().tolist()})")
print(f"  Test snapshots:  {len(test_a)} ({test_a['vessel_name'].unique().tolist()})")

y_train_a = train_a["target_remaining_travel_time_minutes"].values
y_test_a = test_a["target_remaining_travel_time_minutes"].values

model_a = VectorizedRidgeETAModel(alpha=10.0)
model_a.fit(train_a, y_train_a)
pred_a = model_a.predict(test_a)

metrics_a = evaluate_predictions(y_test_a, pred_a)
print("  Zero-Shot Test Performance on ENEZ EUSSA 3:")
print(f"    MAE: {metrics_a['mae_minutes']} min | MedAE: {metrics_a['median_ae_minutes']} min | RMSE: {metrics_a['rmse_minutes']} min | Within 10m: {metrics_a['pct_within_10m']}%")

# Case Study B: Hold out ENEZ SUN 3 (operates exclusively on Audierne-Sein route)
held_out_vessel_b = "ENEZ SUN 3"
train_b = df_snaps[df_snaps["vessel_name"] != held_out_vessel_b].copy()
test_b = df_snaps[df_snaps["vessel_name"] == held_out_vessel_b].copy()

print(f"\nCase B: Hold out {held_out_vessel_b} (Route Confounded)")
print(f"  Train snapshots: {len(train_b)} ({train_b['vessel_name'].unique().tolist()})")
print(f"  Test snapshots:  {len(test_b)} ({test_b['vessel_name'].unique().tolist()})")

y_train_b = train_b["target_remaining_travel_time_minutes"].values
y_test_b = test_b["target_remaining_travel_time_minutes"].values

model_b = VectorizedRidgeETAModel(alpha=10.0)
model_b.fit(train_b, y_train_b)
pred_b = model_b.predict(test_b)

metrics_b = evaluate_predictions(y_test_b, pred_b)
print("  Zero-Shot Test Performance on ENEZ SUN 3 (Unseen Route + Unseen Vessel):")
print(f"    MAE: {metrics_b['mae_minutes']} min | MedAE: {metrics_b['median_ae_minutes']} min | RMSE: {metrics_b['rmse_minutes']} min | Within 10m: {metrics_b['pct_within_10m']}%")

# Save summary
out_summary = {
    "protocol": "Protocol 2 (Exploratory Unseen Vessel Holdout)",
    "limitation_note": "Statistically underpowered (N=4 vessels total). Evaluated strictly as exploratory case study.",
    "case_a_enez_eussa_3": metrics_a,
    "case_b_enez_sun_3_confounded": metrics_b,
}

import json
out_path = repo_root / "data" / "manifests" / "phase-05-protocol2-case-study.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out_summary, f, indent=2)
print(f"\nSaved Protocol 2 exploratory metrics to {out_path}")
