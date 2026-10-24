"""Tests for Phase 01 GTFS loader and schedule normalizer.

Covers:
- Valid GTFS parsing from zip and directory
- Malformed files rejection (missing mandatory columns or corrupt time formats)
- Calendar exception handling (ADDED vs REMOVED dates)
- Services crossing midnight with duration calculation
- Corridor and vessel mapping enforcement (Rule 6: unmodelled services flagged tracking_supported=false)
"""

import csv
import json
import os
from pathlib import Path
import tempfile
import pytest

from src.timetable.gtfs_loader import (
    GTFSLoader,
    ServiceDefinition,
    parse_time_to_seconds,
    format_seconds_to_time,
    MODELLED_CORRIDORS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_DIR = Path(__file__).resolve().parents[1]
GTFS_ZIP = ML_DIR / "data" / "downloads" / "penn_ar_bed_gtfs.zip"
GTFS_DIR = ML_DIR / "data" / "timetable" / "gtfs"


def test_time_conversion_and_midnight_crossing():
    """Verify time string conversion to seconds and midnight rollover handling."""
    # Standard time
    assert parse_time_to_seconds("08:30:00") == 30600
    assert format_seconds_to_time(30600) == "08:30:00"

    # Midnight crossing time (24:15:00)
    assert parse_time_to_seconds("24:15:00") == 87300
    assert format_seconds_to_time(87300) == "00:15:00"

    # Malformed time format raises ValueError
    with pytest.raises(ValueError, match="Invalid GTFS time format"):
        parse_time_to_seconds("8am")


def test_load_valid_penn_ar_bed_gtfs():
    """Verify clean parsing of canonical Penn ar Bed GTFS archive."""
    assert GTFS_ZIP.exists()
    loader = GTFSLoader(str(GTFS_ZIP))
    services = loader.load_services()

    assert len(services) == 20
    for s in services:
        assert isinstance(s, ServiceDefinition)
        assert s.origin_terminal_id
        assert s.dest_terminal_id
        assert s.departure_time
        assert s.arrival_time
        assert s.duration_minutes > 0
        assert s.corridor == f"{s.origin_terminal_id}_{s.dest_terminal_id}"

        # Rule 6 check: If modelled corridor, tracking_supported must be True and vessel_id set.
        # Otherwise tracking_supported must be False.
        if s.corridor in MODELLED_CORRIDORS:
            assert s.tracking_supported is True
            assert s.vessel_id == MODELLED_CORRIDORS[s.corridor]["vessel_id"]
            assert s.vessel_name == MODELLED_CORRIDORS[s.corridor]["vessel_name"]
        else:
            assert s.tracking_supported is False
            assert s.vessel_id is None


def test_every_service_maps_to_corridor_or_unsupported():
    """Verify every service maps to exactly one corridor or is flagged unsupported."""
    loader = GTFSLoader(str(GTFS_ZIP))
    services = loader.load_services()

    for s in services:
        assert s.corridor is not None
        if not s.tracking_supported:
            # Summer Camaret or secondary routes must be flagged unsupported
            assert s.vessel_id is None


def test_calendar_exceptions_handling():
    """Verify calendar exceptions (holiday suspensions) are parsed correctly."""
    loader = GTFSLoader(str(GTFS_ZIP))
    services = loader.load_services()

    # Find year-round service
    year_round = next((s for s in services if s.service_id == "DAILY_YEAR_ROUND"), None)
    assert year_round is not None
    assert len(year_round.calendar_exceptions) > 0
    # Christmas suspension exception
    xmas = next((e for e in year_round.calendar_exceptions if e["date"] == "20261225"), None)
    assert xmas is not None
    assert xmas["exception_type"] == "REMOVED"


def test_malformed_gtfs_missing_columns():
    """Verify loader raises ValueError on malformed files missing required columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create incomplete routes.txt missing route_id
        with open(tmp_path / "routes.txt", "w", newline="") as f:
            f.write("route_name,agency_id\nTest,PAB\n")
        with open(tmp_path / "trips.txt", "w", newline="") as f:
            f.write("trip_id,route_id,service_id\nT1,R1,S1\n")
        with open(tmp_path / "stop_times.txt", "w", newline="") as f:
            f.write("trip_id,stop_id,stop_sequence,departure_time,arrival_time\nT1,A,1,08:00:00,08:30:00\n")
        with open(tmp_path / "calendar.txt", "w", newline="") as f:
            f.write("service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\nS1,1,1,1,1,1,1,1,20260101,20261231\n")

        loader = GTFSLoader(str(tmp_path))
        with pytest.raises(ValueError, match="missing columns"):
            loader.load_services()


def test_service_crossing_midnight():
    """Verify services crossing midnight calculate correct positive duration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with open(tmp_path / "routes.txt", "w", newline="") as f:
            f.write("route_id,route_short_name\nR_NIGHT,NIGHT\n")
        with open(tmp_path / "trips.txt", "w", newline="") as f:
            f.write("route_id,trip_id,service_id\nR_NIGHT,TRIP_NIGHT,DAILY\n")
        with open(tmp_path / "stop_times.txt", "w", newline="") as f:
            f.write("trip_id,stop_id,stop_sequence,departure_time,arrival_time\n")
            f.write("TRIP_NIGHT,BREST,1,23:30:00,23:30:00\n")
            f.write("TRIP_NIGHT,LE_CONQUET,2,00:45:00,00:45:00\n")
        with open(tmp_path / "calendar.txt", "w", newline="") as f:
            f.write("service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n")
            f.write("DAILY,1,1,1,1,1,1,1,20260101,20261231\n")

        loader = GTFSLoader(str(tmp_path))
        services = loader.load_services()
        assert len(services) == 1
        # 23:30 to 00:45 is 75 minutes
        assert services[0].duration_minutes == 75.0
        assert services[0].departure_time == "23:30:00"
        assert services[0].arrival_time == "00:45:00"
