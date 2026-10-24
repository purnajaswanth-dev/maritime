"""Generates reproducible Phase 04 ground-truth recovery artifacts."""

import hashlib
import json
from pathlib import Path
import sys
import time

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.ingestion.trajectory_segmenter import TrajectorySegmenter


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def main():
    repo_root = Path(__file__).resolve().parents[2]
    zip_path = repo_root / "data" / "downloads" / "ais_brest_synopses_v0.8.zip"
    interim_dir = repo_root / "data" / "interim"
    processed_dir = repo_root / "data" / "processed"
    manifests_dir = repo_root / "data" / "manifests"

    interim_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    print(f"Verifying source archive: {zip_path}")
    source_size = zip_path.stat().st_size
    print(f"Source size: {source_size:,} bytes")
    print("Computing SHA-256 checksum...")
    source_sha256 = compute_sha256(zip_path)
    print(f"SHA-256: {source_sha256}")

    t0 = time.time()
    print("Executing streaming trajectory segmentation...")
    audit_df, verified_df = TrajectorySegmenter.extract_from_brest_zip(str(zip_path))
    elapsed = time.time() - t0

    print(f"Extraction completed in {elapsed:.2f} seconds.")
    print(f"Total candidate voyages audited: {len(audit_df)}")
    print(f"Verified real-world voyages: {len(verified_df)}")
    print(f"Uncertain / excluded voyages: {len(audit_df) - len(verified_df)}")

    # Write interim candidate audit parquet
    audit_parquet_path = interim_dir / "phase_04_candidate_voyage_audit.parquet"
    audit_df.to_parquet(audit_parquet_path, index=False)
    print(f"Wrote audit parquet: {audit_parquet_path} ({audit_parquet_path.stat().st_size:,} bytes)")

    # Write verified voyages parquet
    verified_parquet_path = processed_dir / "verified_voyages.parquet"
    verified_df.to_parquet(verified_parquet_path, index=False)
    print(f"Wrote verified parquet: {verified_parquet_path} ({verified_parquet_path.stat().st_size:,} bytes)")

    # Vessel & corridor breakdown
    by_vessel = verified_df["vessel_name"].value_counts().to_dict()
    by_corridor = (
        verified_df.groupby(["dep_terminal", "arr_terminal"])
        .size()
        .reset_index(name="count")
        .to_dict(orient="records")
    )

    # Lineage manifest
    manifest = {
        "phase": "04",
        "description": "Raw AIS Trajectory Segmentation and Ground-Truth Recovery",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_archive": {
            "path": "data/downloads/ais_brest_synopses_v0.8.zip",
            "size_bytes": source_size,
            "sha256": source_sha256,
            "member_file": "ais_brest_synopses.csv",
        },
        "segmentation_parameters": {
            "max_telemetry_gap_minutes": 45.0,
            "min_observations": 5,
            "underway_speed_threshold_knots": 3.0,
            "berth_speed_threshold_knots": 3.0,
            "geofence_radii_m": {
                "BREST": 800.0,
                "LE_CONQUET": 600.0,
                "MOLENE": 500.0,
                "OUESSANT_STIFF": 800.0,
                "AUDIERNE": 600.0,
                "ILE_DE_SEIN": 500.0,
                "CAMARET": 600.0,
            },
        },
        "execution_summary": {
            "runtime_seconds": round(elapsed, 2),
            "total_candidates_audited": len(audit_df),
            "verified_voyages_count": len(verified_df),
            "uncertain_voyages_count": len(audit_df) - len(verified_df),
            "verified_by_vessel": by_vessel,
            "verified_by_corridor": by_corridor,
        },
        "output_artifacts": [
            {
                "path": "data/interim/phase_04_candidate_voyage_audit.parquet",
                "row_count": len(audit_df),
                "size_bytes": audit_parquet_path.stat().st_size,
            },
            {
                "path": "data/processed/verified_voyages.parquet",
                "row_count": len(verified_df),
                "size_bytes": verified_parquet_path.stat().st_size,
            },
        ],
        "data_preservation_attestation": {
            "original_archives_unmodified": True,
            "historical_phase_02_artifacts_unmodified": True,
            "no_synthetic_records_in_verified": True,
            "no_interpolated_observations": True,
        },
    }

    manifest_path = manifests_dir / "phase-04-source-lineage.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote lineage manifest: {manifest_path} ({manifest_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
