"""Builds and persists Phase 01 assets:
- Normalised services.json and services.parquet
- Historical voyage library with trajectories
- Corridor delay distributions
- Data manifest with SHA-256 checksums
"""

import sys
from pathlib import Path
ml_root = Path("c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform")
sys.path.insert(0, str(ml_root))

from src.timetable.gtfs_loader import GTFSLoader
from src.replay.voyage_library import VoyageLibrary

def build_all():
    ml_root = Path("c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform")

    gtfs_source = ml_root / "data" / "downloads" / "penn_ar_bed_gtfs.zip"
    services_json = ml_root / "data" / "timetable" / "services.json"
    services_parquet = ml_root / "data" / "timetable" / "services.parquet"

    print("Step 1: Parsing and exporting normalized GTFS services...")
    loader = GTFSLoader(str(gtfs_source))
    services = loader.export_normalized_services(str(services_json), str(services_parquet))
    print(f"Exported {len(services)} services to {services_json}")

    print("\nStep 2: Building historical voyage library...")
    verified_voyages = ml_root / "data" / "processed" / "verified_voyages.parquet"
    snapshots = ml_root / "data" / "processed" / "phase_05_prediction_snapshots.parquet"
    test_predictions = ml_root / "data" / "processed" / "phase_05_test_predictions.parquet"
    replay_dir = ml_root / "data" / "replay"

    services_dicts = [s.to_dict() for s in services]
    lib = VoyageLibrary()
    lib.build_library(
        str(verified_voyages),
        str(snapshots),
        str(test_predictions),
        gtfs_services=services_dicts,
    )

    print("\nStep 3: Persisting voyage library and delay distributions to ml-platform/data/replay/...")
    manifest = lib.persist(str(replay_dir))
    print("Manifest successfully written:")
    print(f"  Total voyages: {manifest['total_voyages']}")
    print(f"  Train voyages: {manifest['train_voyages']}")
    print(f"  Test voyages: {manifest['test_voyages']}")
    print(f"  Corridors: {len(manifest['supported_corridors'])}")
    for corr, count in manifest['corridor_counts'].items():
        print(f"    - {corr}: {count} voyages")

if __name__ == "__main__":
    build_all()
