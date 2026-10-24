"""Automated regression and audit verification tests for Phase 04A Independent Audit."""

from pathlib import Path
import pytest
import pandas as pd

from src.ingestion.trajectory_segmenter import CORRIDOR_LIMITS, TERMINALS


@pytest.fixture(scope="module")
def repo_root():
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def verified_df(repo_root):
    path = repo_root / "data" / "processed" / "verified_voyages.parquet"
    assert path.exists(), f"Missing verified dataset: {path}"
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def candidate_audit_df(repo_root):
    path = repo_root / "data" / "interim" / "phase_04_candidate_voyage_audit.parquet"
    assert path.exists(), f"Missing candidate audit dataset: {path}"
    return pd.read_parquet(path)


@pytest.fixture(scope="module")
def sampled_audit_df(repo_root):
    path = repo_root / "data" / "interim" / "phase_04a_sampled_voyage_audit.parquet"
    assert path.exists(), f"Missing sampled audit dataset: {path}"
    return pd.read_parquet(path)


def test_verified_voyages_exact_count(verified_df):
    """Verifies that exactly 889 voyages are in the verified dataset with 0 nulls."""
    assert len(verified_df) == 889
    assert verified_df.isnull().sum().sum() == 0
    assert not verified_df["voyage_id"].duplicated().any()


def test_candidate_audit_exact_count(candidate_audit_df):
    """Verifies that 1,364 total candidates are audited with 889 verified and 475 uncertain."""
    assert len(candidate_audit_df) == 1364
    counts = candidate_audit_df["status"].value_counts().to_dict()
    assert counts.get("VERIFIED") == 889
    assert counts.get("UNCERTAIN") == 475


def test_overnight_shutdown_gap_rejections(candidate_audit_df):
    """Verifies that overnight AIS transponder shutdowns (> 10h) are correctly rejected."""
    overnight_trips = candidate_audit_df[candidate_audit_df["duration_minutes"] > 300.0]
    assert len(overnight_trips) > 100
    # Every single overnight trip MUST be marked UNCERTAIN
    assert (overnight_trips["status"] == "UNCERTAIN").all()
    # Every overnight trip must cite either corridor bounds or telemetry gap
    assert overnight_trips["rejection_reasons"].str.contains("corridor bounds|telemetry gap", case=False).all()


def test_vessel_concentration_quantification(verified_df):
    """Audits the concentration of voyages across vessels."""
    vessel_counts = verified_df["vessel_name"].value_counts()
    # FROMVEUR II represents > 65% of the entire dataset
    fromveur_share = vessel_counts["FROMVEUR II"] / len(verified_df)
    assert 0.65 < fromveur_share < 0.70
    # Total independent vessels is exactly 4
    assert len(vessel_counts) == 4


def test_corridor_physical_duration_adherence(verified_df):
    """Verifies that every verified voyage respects the physical bounds of its corridor."""
    for _, row in verified_df.iterrows():
        corr = (row["dep_terminal"], row["arr_terminal"])
        dur = row["duration_minutes"]
        assert corr in CORRIDOR_LIMITS, f"Unexpected corridor: {corr}"
        min_d, max_d = CORRIDOR_LIMITS[corr]
        assert min_d <= dur <= max_d, f"Duration {dur} out of bounds [{min_d}, {max_d}] for {corr}"


def test_sampled_voyage_audit_artifact_conformance(sampled_audit_df):
    """Verifies that the independent audit artifact contains both verified and rejected samples."""
    assert len(sampled_audit_df) >= 50
    verdicts = set(sampled_audit_df["auditor_verdict"].unique())
    assert "VERIFIED_FROM_SOURCE_EVIDENCE" in verdicts
    assert "REJECTION_CONFIRMED_JUSTIFIED" in verdicts
