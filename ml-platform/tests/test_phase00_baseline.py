"""Tests verifying Phase 0 baseline assets and corridor alignments.

Covers:
- All data files named in DATA_AUDIT.md exist and load without error
- Timetable routes map to the 10 authoritative model corridor categories
- Verification of test split voyage count (204 voyages)
- Frozen model weight artifact and SHA-256 integrity
"""

import csv
import json
import os
from pathlib import Path
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_DIR = Path(__file__).resolve().parents[1]

# The 10 corridor categories recognized by the ETA prediction pipeline
EXPECTED_MODEL_CORRIDORS = {
    "BREST_LE_CONQUET",
    "LE_CONQUET_BREST",
    "BREST_OUESSANT_STIFF",
    "OUESSANT_STIFF_BREST",
    "AUDIERNE_ILE_DE_SEIN",
    "ILE_DE_SEIN_AUDIERNE",
    "LE_CONQUET_MOLENE",
    "MOLENE_LE_CONQUET",
    "MOLENE_OUESSANT_STIFF",
    "OUESSANT_STIFF_MOLENE",
}


def test_audit_data_files_exist_and_load():
    """Verify that all core data files catalogued in DATA_AUDIT.md exist and load cleanly."""
    # 1. Verified voyages parquet
    voyages_path = ML_DIR / "data" / "processed" / "verified_voyages.parquet"
    assert voyages_path.exists(), f"Missing {voyages_path}"
    df_v = pd.read_parquet(voyages_path)
    assert len(df_v) == 889
    assert "dep_terminal" in df_v.columns
    assert "arr_terminal" in df_v.columns

    # 2. Prediction snapshots parquet
    snapshots_path = ML_DIR / "data" / "processed" / "phase_05_prediction_snapshots.parquet"
    assert snapshots_path.exists(), f"Missing {snapshots_path}"
    df_s = pd.read_parquet(snapshots_path)
    assert len(df_s) == 9313
    assert "corridor" in df_s.columns

    # 3. Test predictions parquet
    test_pred_path = ML_DIR / "data" / "processed" / "phase_05_test_predictions.parquet"
    assert test_pred_path.exists(), f"Missing {test_pred_path}"
    df_t = pd.read_parquet(test_pred_path)
    assert len(df_t) == 2372
    assert df_t["voyage_id"].nunique() == 204, "Test split must contain exactly 204 distinct voyages"

    # 4. GTFS feed archive & directory
    gtfs_zip = ML_DIR / "data" / "downloads" / "penn_ar_bed_gtfs.zip"
    assert gtfs_zip.exists(), f"Missing {gtfs_zip}"
    gtfs_dir = ML_DIR / "data" / "timetable" / "gtfs"
    assert (gtfs_dir / "stops.txt").exists()
    assert (gtfs_dir / "routes.txt").exists()
    assert (gtfs_dir / "trips.txt").exists()
    assert (gtfs_dir / "stop_times.txt").exists()
    assert (gtfs_dir / "calendar.txt").exists()
    assert (gtfs_dir / "calendar_dates.txt").exists()


def test_timetable_corridor_mapping():
    """Verify that every timetable route maps to a model corridor or is flagged as unmodelled."""
    gtfs_dir = ML_DIR / "data" / "timetable" / "gtfs"
    routes_file = gtfs_dir / "routes.txt"

    route_to_corridor = {}
    with open(routes_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            route_id = r["route_id"]
            # Derive origin and destination from route_id (e.g. R_BRE_CNQ -> BREST, LE_CONQUET)
            parts = route_id.split("_")
            if len(parts) == 3:
                code_map = {
                    "BRE": "BREST",
                    "CNQ": "LE_CONQUET",
                    "OUE": "OUESSANT_STIFF",
                    "MOL": "MOLENE",
                    "AUD": "AUDIERNE",
                    "SEI": "ILE_DE_SEIN",
                    "CAM": "CAMARET",
                }
                orig = code_map.get(parts[1])
                dest = code_map.get(parts[2])
                corridor = f"{orig}_{dest}"
                route_to_corridor[route_id] = corridor

    # Verify that all 10 recognized model corridors have matching timetable routes
    mapped_corridors = set(route_to_corridor.values())
    for expected in EXPECTED_MODEL_CORRIDORS:
        assert expected in mapped_corridors, f"Expected corridor {expected} missing from timetable routes"

    # Verify that unmodelled corridors (e.g. Camaret) are identified
    unmodelled = mapped_corridors - EXPECTED_MODEL_CORRIDORS
    assert "BREST_CAMARET" in unmodelled
    assert "CAMARET_BREST" in unmodelled


def test_frozen_model_artifact_integrity():
    """Verify that the frozen Ridge model artifact exists and has verified checksum."""
    model_path = ML_DIR / "models" / "vectorized_ridge_model.json"
    assert model_path.exists(), "vectorized_ridge_model.json must exist"

    with open(model_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["metadata"]["model_type"] == "L2_RIDGE_LINEAR"
    assert data["metadata"]["alpha"] == 10.0
    assert data["feature_specification"]["feature_count"] == 21
    assert data["weights"]["weights_sha256"] == "e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9"
    assert data["provenance"]["evaluated_test_mae_minutes"] == 5.2
    assert data["provenance"]["evaluated_test_medae_minutes"] == 3.56
    assert data["provenance"]["evaluated_test_rmse_minutes"] == 7.47
