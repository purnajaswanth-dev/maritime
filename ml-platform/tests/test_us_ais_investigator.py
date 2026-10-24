"""Unit tests for USAISInvestigator indexed queries, guardrails, and error handling."""

import os
import sqlite3
import tempfile
import pytest
import pandas as pd

from src.ingestion.us_ais_investigator import USAISInvestigator, get_default_temp_gpkg_path


@pytest.fixture
def indexed_gpkg_path():
    path = get_default_temp_gpkg_path()
    if not os.path.exists(path):
        pytest.skip(f"Extracted GeoPackage not found at: {path}")
    return path


def test_indexed_mmsi_lookup(indexed_gpkg_path):
    """Verifies that an indexed MMSI lookup executes in milliseconds and returns expected tracks."""
    inv = USAISInvestigator(extracted_gpkg_path=indexed_gpkg_path)

    # Coastal Inspiration
    df = inv.query_by_mmsi(316011408)
    assert len(df) == 777
    assert "COASTAL INSPIRATION" in df["vessel_name"].values
    assert "geometry" in df.columns

    # Queen of Alberni
    df_alberni = inv.query_by_mmsi(316001245)
    assert len(df_alberni) == 553
    assert "QUEEN OF ALBERNI" in df_alberni["vessel_name"].values

    # WSF Chelan
    df_chelan = inv.query_by_mmsi(366709770)
    assert len(df_chelan) == 69
    assert "WSF CHELAN" in df_chelan["vessel_name"].values


def test_missing_mmsi_query(indexed_gpkg_path):
    """Verifies that querying a non-existent MMSI returns an empty DataFrame gracefully."""
    inv = USAISInvestigator(extracted_gpkg_path=indexed_gpkg_path)
    # 999999998 is verified absent (note: 999999999 exists as unassigned/dummy in US AIS)
    df = inv.query_by_mmsi(999999998)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0


def test_missing_database_path():
    """Verifies that pointing to a non-existent database file raises FileNotFoundError."""
    fake_path = os.path.join(tempfile.gettempdir(), "non_existent_where_is_my_ferry.gpkg")
    inv = USAISInvestigator(extracted_gpkg_path=fake_path)
    with pytest.raises(FileNotFoundError, match="Configured extracted GeoPackage path does not exist"):
        inv.query_by_mmsi(316011408)


def test_unindexed_vsizip_guardrail():
    """Verifies that attempting query_by_mmsi without an extracted local copy raises a guardrail RuntimeError."""
    inv = USAISInvestigator(extracted_gpkg_path=None)
    # Manually ensure extracted_gpkg_path is None to test guardrail
    inv.extracted_gpkg_path = None
    with pytest.raises(RuntimeError, match="Cannot query MMSI .* over unindexed virtual stream '/vsizip/'"):
        inv.query_by_mmsi(316011408)


def test_missing_index_detection():
    """Verifies that a database lacking the mmsi index raises RuntimeError."""
    with tempfile.NamedTemporaryFile(suffix=".gpkg", delete=False) as tf:
        temp_db = tf.name

    try:
        con = sqlite3.connect(temp_db)
        con.execute("CREATE TABLE [AIS_Tracks_2026_03] (mmsi INTEGER, vessel_name TEXT);")
        con.commit()
        con.close()

        inv = USAISInvestigator(extracted_gpkg_path=temp_db)
        with pytest.raises(RuntimeError, match="Index on column 'mmsi' is missing in table 'AIS_Tracks_2026_03'"):
            inv.query_by_mmsi(316011408)
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)
