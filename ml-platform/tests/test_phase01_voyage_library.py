"""Tests for Phase 01 historical voyage library and delay distributions.

Covers:
- Every voyage starts inside origin berth radius and ends inside destination berth radius
- Trajectory timestamps are strictly monotonic
- Train and test splits have zero overlap
- Test split contains exactly 204 voyages
- Covers all 4 modelled corridors with at least one voyage each
- Delay distribution non-empty per supported corridor with values in [-10, 120] minutes
- Manifest checksum verification and tampering detection
"""

import json
from pathlib import Path
import tempfile
import pytest

from src.ingestion.trajectory_segmenter import haversine_m, TERMINALS
from src.replay.voyage_library import VoyageLibrary, HistoricalVoyage

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_DIR = Path(__file__).resolve().parents[1]
REPLAY_DIR = ML_DIR / "data" / "replay"

MODELLED_CORRIDORS = [
    "BREST_LE_CONQUET",
    "LE_CONQUET_BREST",
    "BREST_OUESSANT_STIFF",
    "AUDIERNE_ILE_DE_SEIN",
]


@pytest.fixture(scope="module")
def loaded_library() -> VoyageLibrary:
    """Fixture providing a loaded VoyageLibrary from persisted replay assets."""
    assert (REPLAY_DIR / "manifest.json").exists(), "manifest.json must exist in data/replay"
    lib = VoyageLibrary(str(REPLAY_DIR))
    return lib


def test_voyage_library_counts_and_splits(loaded_library: VoyageLibrary):
    """Verify total, train, and test voyage counts, and zero overlap."""
    lib = loaded_library
    assert len(lib.voyages) == 889

    train_voyages = lib.get_voyages(split="train")
    test_voyages = lib.get_voyages(split="test")

    assert len(train_voyages) == 685
    assert len(test_voyages) == 204, "Test split must contain exactly 204 voyages"

    train_ids = {v.voyage_id for v in train_voyages}
    test_ids = {v.voyage_id for v in test_voyages}

    # Zero overlap check
    overlap = train_ids.intersection(test_ids)
    assert len(overlap) == 0, f"Found {len(overlap)} overlapping voyage IDs between train and test splits"


def test_modelled_corridors_coverage(loaded_library: VoyageLibrary):
    """Verify all 4 modelled corridors have at least one voyage in the library."""
    lib = loaded_library
    for corridor in MODELLED_CORRIDORS:
        voyages = lib.get_voyages(corridor=corridor)
        assert len(voyages) > 0, f"Modelled corridor {corridor} has zero historical voyages"


def test_berth_anchors_and_monotonicity(loaded_library: VoyageLibrary):
    """Verify that every voyage starts in origin berth, ends in dest berth, with monotonic times."""
    lib = loaded_library

    for vid, v in lib.voyages.items():
        assert len(v.trajectory) >= 2, f"Voyage {vid} has insufficient trajectory points"

        # 1. Monotonicity check
        times = [p["time_offset_s"] for p in v.trajectory]
        for i in range(len(times) - 1):
            assert times[i + 1] > times[i], f"Voyage {vid} non-monotonic timestamps at index {i}"

        # 2. Berth start radius check
        p0 = v.trajectory[0]
        dep_terminal = TERMINALS.get(v.dep_terminal)
        assert dep_terminal is not None, f"Unknown terminal {v.dep_terminal}"
        dist_start = haversine_m(dep_terminal["lon"], dep_terminal["lat"], p0["lon"], p0["lat"])
        # Must be strictly within the configured berth radius
        assert dist_start <= dep_terminal["radius_m"], (
            f"Voyage {vid} starts {dist_start:.1f}m away from {v.dep_terminal} berth "
            f"(radius {dep_terminal['radius_m']}m)"
        )

        # 3. Berth end radius check
        p_end = v.trajectory[-1]
        arr_terminal = TERMINALS.get(v.arr_terminal)
        assert arr_terminal is not None, f"Unknown terminal {v.arr_terminal}"
        dist_end = haversine_m(arr_terminal["lon"], arr_terminal["lat"], p_end["lon"], p_end["lat"])
        assert dist_end <= arr_terminal["radius_m"], (
            f"Voyage {vid} ends {dist_end:.1f}m away from {v.arr_terminal} berth "
            f"(radius {arr_terminal['radius_m']}m)"
        )


def test_delay_distributions(loaded_library: VoyageLibrary):
    """Verify delay distributions are non-empty per corridor with plausible values."""
    lib = loaded_library
    assert len(lib.delay_distributions) >= 4

    for corridor in MODELLED_CORRIDORS:
        assert corridor in lib.delay_distributions
        delays = lib.delay_distributions[corridor]
        assert len(delays) > 0, f"Corridor {corridor} has empty delay distribution"

        for d in delays:
            # Plausible range: -10 to +120 minutes
            assert -10.0 <= d <= 120.0, f"Corridor {corridor} has implausible delay: {d} min"

        # Sampling test
        sampled = lib.sample_delay(corridor)
        assert -10.0 <= sampled <= 120.0


def test_manifest_tampering_detection(tmp_path: Path, loaded_library: VoyageLibrary):
    """Verify that any modification to on-disk assets triggers a checksum integrity error."""
    lib = loaded_library

    # 1. Clean verify
    assert lib.verify_manifest_integrity() is True

    # 2. Copy assets to temp dir and tamper
    temp_dir = tmp_path / "replay_tamper"
    temp_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = temp_dir / "manifest.json"
    voyages_file = temp_dir / "voyages.json"
    delays_file = temp_dir / "delay_distributions.json"

    manifest_file.write_text((REPLAY_DIR / "manifest.json").read_text(encoding="utf-8"), encoding="utf-8")
    delays_file.write_text((REPLAY_DIR / "delay_distributions.json").read_text(encoding="utf-8"), encoding="utf-8")

    # Tamper with voyages.json (append dummy whitespace)
    orig_voyages_text = (REPLAY_DIR / "voyages.json").read_text(encoding="utf-8")
    voyages_file.write_text(orig_voyages_text + "   \n", encoding="utf-8")

    tampered_lib = VoyageLibrary()
    with pytest.raises(ValueError, match="Integrity check failed"):
        tampered_lib.load(str(temp_dir))
