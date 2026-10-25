"""Comprehensive unit tests validating Phase 02 Ground-Truth Feasibility workflows."""

import os
import pandas as pd
import pytest

pytest.importorskip("xarray")

from src.ingestion.arrival_detector import ArrivalDetector, EventType, LabelQuality, PortGeofence
from src.ingestion.ocean_collocation import OceanFeatureCollocator
from src.ingestion.schedule_matcher import MatchDecision, ScheduleMatcher
from src.ingestion.vessel_registry import LicenseStatus, ReviewStatus, VesselRegistryBuilder


def test_vessel_identity_classification():
    """Validates strict classification and ensures proximity never forces a ferry label."""
    # 1. Authoritative French ferry (Fromveur II)
    rec1 = VesselRegistryBuilder.classify_vessel(mmsi=228017700)
    assert rec1["review_status"] == ReviewStatus.VERIFIED_PASSENGER_FERRY.value
    assert rec1["vessel_name"] == "FROMVEUR II"
    assert rec1["imo"] == "IMO9613147"
    assert rec1["identity_confidence"] == "HIGH"

    # 2. Known French non-ferry (Abeille Bourbon rescue tug)
    rec2 = VesselRegistryBuilder.classify_vessel(mmsi=228064900)
    assert rec2["review_status"] == ReviewStatus.NON_FERRY.value
    assert rec2["normalized_vessel_type"] == "EMERGENCY_TOWING_VESSEL"

    # 3. Unidentified Brest MMSI
    rec3 = VesselRegistryBuilder.classify_vessel(mmsi=259019000)
    assert rec3["review_status"] == ReviewStatus.UNKNOWN.value
    assert rec3["identity_confidence"] == "NONE"

    # 4. US MarineCadastre Verified Ferry with IMO
    rec4 = VesselRegistryBuilder.classify_vessel(
        mmsi=316011408,
        vessel_name="COASTAL INSPIRATION",
        imo="IMO9332767",
        raw_type="Passenger",
    )
    assert rec4["review_status"] == ReviewStatus.VERIFIED_PASSENGER_FERRY.value
    assert rec4["normalized_vessel_type"] == "PASSENGER_FERRY"


def test_gtfs_service_type_filtering_and_match_rejection():
    """Validates that bus feeds and temporal mismatches are rejected with explicit reasons."""
    # Rejection of bus feed
    audit_bus = ScheduleMatcher.evaluate_match(
        track_id="TRK-001",
        mmsi=316011408,
        vessel_name="COASTAL INSPIRATION",
        vessel_review_status="VERIFIED_PASSENGER_FERRY",
        track_start_time="2026-03-01 10:00:00",
        track_end_time="2026-03-01 11:30:00",
        feed_id="mdb-2353-202502041949",
        feed_is_ferry=False,
        feed_calendar_start="20240903",
        feed_calendar_end="20250316",
    )
    assert audit_bus.decision == MatchDecision.REJECTED_NON_FERRY_SERVICE
    assert "non-ferry" in audit_bus.rejection_reason.lower()

    # Rejection of unverified vessel
    audit_unverified = ScheduleMatcher.evaluate_match(
        track_id="TRK-002",
        mmsi=999999999,
        vessel_name=None,
        vessel_review_status="UNKNOWN",
        track_start_time="2026-03-01 10:00:00",
        track_end_time="2026-03-01 11:30:00",
        feed_id="mdb-690-202605270153",
        feed_is_ferry=True,
        feed_calendar_start="20260512",
        feed_calendar_end="20270331",
    )
    assert audit_unverified.decision == MatchDecision.REJECTED_UNVERIFIED_VESSEL

    # Rejection of March 2026 AIS vs May 2026 GTFS release
    audit_temporal = ScheduleMatcher.evaluate_match(
        track_id="TRK-003",
        mmsi=316011408,
        vessel_name="COASTAL INSPIRATION",
        vessel_review_status="VERIFIED_PASSENGER_FERRY",
        track_start_time="2026-03-01 14:15:00",
        track_end_time="2026-03-01 16:05:00",
        feed_id="mdb-690-202605270153",
        feed_is_ferry=True,
        feed_calendar_start="20260512",
        feed_calendar_end="20270331",
    )
    assert audit_temporal.decision == MatchDecision.REJECTED_SCHEDULE_POSTDATES_AIS


def test_separation_of_scheduled_and_actual_event_times():
    """Ensures scheduled timetable arrival is never substituted for actual observed arrival."""
    voyage = ArrivalDetector.evaluate_trajectory_voyage(
        track_id="TRK-TIME-TEST",
        mmsi=316011408,
        vessel_name="COASTAL INSPIRATION",
        vessel_review_status="VERIFIED_PASSENGER_FERRY",
        start_lon=-123.8910,
        start_lat=49.1620,
        end_lon=-123.1294,
        end_lat=49.0069,
        first_observed_time="2026-03-01 14:15:00",
        last_observed_time="2026-03-01 16:05:00",
        duration_minutes=110.0,
        scheduled_departure="2026-03-01 14:00:00",  # Scheduled 15m earlier
        scheduled_arrival="2026-03-01 16:00:00",    # Scheduled 5m earlier
        origin_port=("Duke Point", 49.1620, -123.8910),
        dest_port=("Tsawwassen", 49.0069, -123.1294),
    )

    assert voyage["scheduled_arrival"] == "2026-03-01 16:00:00"
    assert voyage["arrival_timestamp"] == "2026-03-01 16:05:00"
    assert voyage["arrival_event_type"] == EventType.INFERRED_PORT_ARRIVAL.value
    # Assert strictly distinct
    assert voyage["arrival_timestamp"] != voyage["scheduled_arrival"]


def test_exclusion_of_unlabelled_voyages():
    """Ensures voyages with open-water endpoints or missing identity are marked UNLABELLED."""
    # Open water endpoint (no destination port match)
    voyage_open_water = ArrivalDetector.evaluate_trajectory_voyage(
        track_id="TRK-OPEN-WATER",
        mmsi=316011408,
        vessel_name="COASTAL INSPIRATION",
        vessel_review_status="VERIFIED_PASSENGER_FERRY",
        start_lon=-123.8910,
        start_lat=49.1620,
        end_lon=-123.5000,
        end_lat=49.1000,  # Mid-strait open water
        first_observed_time="2026-03-01 14:15:00",
        last_observed_time="2026-03-01 15:15:00",
        duration_minutes=60.0,
        origin_port=("Duke Point", 49.1620, -123.8910),
        dest_port=("Tsawwassen", 49.0069, -123.1294),  # Distant from end coordinates
    )

    assert voyage_open_water["label_quality"] == LabelQuality.UNLABELLED.value
    assert voyage_open_water["is_supervised_usable"] is False
    assert "open-water" in voyage_open_water["exclusion_reasons"].lower()


def test_ocean_collocation_time_boundary():
    """Validates that 2026 US observations are strictly rejected from 2015 Copernicus data."""
    collocator = OceanFeatureCollocator()

    # 1. 2026 observation must be rejected
    res_2026 = collocator.collocate_point(
        timestamp_iso="2026-03-01 14:15:00", lat=49.08, lon=-123.50
    )
    assert res_2026["collocation_status"] == "EXCLUDED_TEMPORAL_OUT_OF_BOUNDS"
    assert res_2026["uo_eastward_current_ms"] is None

    # 2. 2015 Brest observation must succeed
    res_2015 = collocator.collocate_point(
        timestamp_iso="2015-10-01 08:30:00", lat=48.36, lon=-4.60
    )
    assert res_2015["collocation_status"] == "COLLOCATED_DAILY_REANALYSIS"
    assert isinstance(res_2015["uo_eastward_current_ms"], float)
    assert isinstance(res_2015["vo_northward_current_ms"], float)


def test_interim_parquets_exist_and_conform():
    """Validates that intermediate parquet files exist and conform to required schemas."""
    reg_path = "data/interim/vessel_registry_candidates.parquet"
    voy_path = "data/interim/voyage_candidates.parquet"
    audit_path = "data/interim/voyage_match_audit.parquet"
    lineage_path = "data/manifests/phase-02-source-lineage.json"

    assert os.path.exists(reg_path), "vessel_registry_candidates.parquet missing"
    assert os.path.exists(voy_path), "voyage_candidates.parquet missing"
    assert os.path.exists(audit_path), "voyage_match_audit.parquet missing"
    assert os.path.exists(lineage_path), "phase-02-source-lineage.json missing"

    df_reg = pd.read_parquet(reg_path)
    required_reg_cols = [
        "mmsi", "imo", "vessel_name", "vessel_type_raw",
        "normalized_vessel_type", "identity_source",
        "identity_confidence", "license_status", "review_status"
    ]
    for col in required_reg_cols:
        assert col in df_reg.columns, f"Missing {col} in vessel registry"

    df_voy = pd.read_parquet(voy_path)
    required_voy_cols = [
        "voyage_id", "mmsi", "vessel_name", "vessel_review_status",
        "origin_port", "destination_port", "first_observed_time",
        "last_observed_time", "duration_minutes", "arrival_event_type",
        "arrival_timestamp", "label_quality", "is_supervised_usable"
    ]
    for col in required_voy_cols:
        assert col in df_voy.columns, f"Missing {col} in voyage candidates"
