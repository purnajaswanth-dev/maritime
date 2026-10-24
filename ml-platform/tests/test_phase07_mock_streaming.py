"""Phase 07 Mock Streaming Integration and Reliability Tests.

Tests:
1. Event schema validation and bounds checks.
2. Deduplication and idempotent caching.
3. Out-of-order packet watermark preservation.
4. Stale-data automatic detection and recovery.
5. Arrival state latching and post-arrival zombie protection.
6. Mock API server and client telemetry / query endpoints.
7. End-to-end deterministic mock stream execution across the 20 scenarios.
"""

from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import pytest

from src.models.eta_state_machine import ETAState
from src.streaming.event_schema import IncomingAISEvent, ETAResponsePayload, validate_ais_event
from src.streaming.eta_stream_processor import ETAStreamProcessor
from src.streaming.mock_stream_runner import MockStreamRunner
from src.streaming.mock_api_server import MockAPIService, MockAPIClient


@pytest.fixture
def base_valid_payload():
    return {
        "message_id": "MSG-TEST-001",
        "mmsi": 227705101,
        "vessel_name": "FROMVEUR II",
        "event_timestamp_utc": "2016-02-01T10:00:00Z",
        "receipt_timestamp_utc": "2016-02-01T10:00:02Z",
        "latitude": 48.3200,
        "longitude": -4.6500,
        "sog_knots": 14.5,
        "cog_degrees": 85.0,
        "heading_degrees": 86.0,
        "source_id": "test_unit",
        "is_synthetic_fixture": True,
    }


def test_schema_validation_valid(base_valid_payload):
    event, err = validate_ais_event(base_valid_payload)
    assert err is None
    assert event is not None
    assert event.mmsi == 227705101
    assert event.vessel_name == "FROMVEUR II"
    assert event.sog_knots == 14.5
    assert event.is_synthetic_fixture is True


def test_schema_validation_invalid_mmsi(base_valid_payload):
    payload = dict(base_valid_payload)
    payload["mmsi"] = 1234  # Not 9 digits
    event, err = validate_ais_event(payload)
    assert event is None
    assert err == "INVALID_MMSI_MUST_BE_9_DIGIT_INTEGER"


def test_schema_validation_invalid_coordinates(base_valid_payload):
    payload = dict(base_valid_payload)
    payload["latitude"] = 95.0
    event, err = validate_ais_event(payload)
    assert event is None
    assert err == "INVALID_LATITUDE_OUT_OF_BOUNDS"

    payload["latitude"] = 48.3200
    payload["longitude"] = -195.0
    event, err = validate_ais_event(payload)
    assert event is None
    assert err == "INVALID_LONGITUDE_OUT_OF_BOUNDS"


def test_schema_validation_invalid_timestamp(base_valid_payload):
    payload = dict(base_valid_payload)
    payload["event_timestamp_utc"] = "not-a-timestamp"
    event, err = validate_ais_event(payload)
    assert event is None
    assert err == "MALFORMED_EVENT_TIMESTAMP"


def test_schema_validation_invalid_speed(base_valid_payload):
    payload = dict(base_valid_payload)
    payload["sog_knots"] = 75.0  # Ferry speed > 60 kts invalid
    event, err = validate_ais_event(payload)
    assert event is None
    assert err == "INVALID_SOG_OUT_OF_BOUNDS"


def test_deduplication(base_valid_payload):
    processor = ETAStreamProcessor()
    # First ingest
    resp1, err1 = processor.process_event(base_valid_payload)
    assert err1 is None
    assert resp1 is not None

    # Duplicate ingest
    resp2, err2 = processor.process_event(base_valid_payload)
    assert err2 is None
    assert resp2 is not None
    assert resp2.mmsi == resp1.mmsi
    assert resp2.estimated_remaining_minutes == resp1.estimated_remaining_minutes


def test_out_of_order_watermark(base_valid_payload):
    processor = ETAStreamProcessor()
    # Step 1: 10:00:00Z
    resp1, err1 = processor.process_event(base_valid_payload)
    assert err1 is None

    # Step 2: Newer packet 10:10:00Z
    newer = dict(base_valid_payload)
    newer["message_id"] = "MSG-TEST-002"
    newer["event_timestamp_utc"] = "2016-02-01T10:10:00Z"
    resp2, err2 = processor.process_event(newer)
    assert err2 is None

    tracker = processor.vessel_trackers[227705101]
    watermark_epoch = tracker.latest_event_epoch_s

    # Step 3: Delayed out-of-order packet from 10:05:00Z
    late = dict(base_valid_payload)
    late["message_id"] = "MSG-TEST-003"
    late["event_timestamp_utc"] = "2016-02-01T10:05:00Z"
    resp3, err3 = processor.process_event(late)
    assert err3 is None

    # Watermark must NOT rewind
    assert tracker.latest_event_epoch_s == watermark_epoch


def test_stale_data_transition_and_recovery(base_valid_payload):
    processor = ETAStreamProcessor()
    # Normal event in open water
    resp1, _ = processor.process_event(base_valid_payload)
    assert resp1.eta_lifecycle_state == ETAState.ESTIMATING.value

    # Stale observation: current sim time 15 minutes ahead of observation
    sim_time_stale = "2016-02-01T10:15:00Z"
    resp_stale, _ = processor.process_event(base_valid_payload, current_sim_time_utc=sim_time_stale)
    # Stale detection requires an active step or query; let's check with a new event 15m later but with stale obs time
    stale_event = dict(base_valid_payload)
    stale_event["message_id"] = "MSG-TEST-STALE-1"
    stale_event["event_timestamp_utc"] = "2016-02-01T10:00:00Z"
    stale_event["receipt_timestamp_utc"] = "2016-02-01T10:15:00Z"
    resp_stale2, _ = processor.process_event(stale_event, current_sim_time_utc="2016-02-01T10:15:00Z")
    assert resp_stale2.is_stale is True
    assert resp_stale2.eta_lifecycle_state == ETAState.STALE_DATA.value

    # Fresh observation restores ESTIMATING
    fresh_event = dict(base_valid_payload)
    fresh_event["message_id"] = "MSG-TEST-FRESH-1"
    fresh_event["event_timestamp_utc"] = "2016-02-01T10:15:00Z"
    fresh_event["receipt_timestamp_utc"] = "2016-02-01T10:15:02Z"
    resp_fresh, _ = processor.process_event(fresh_event, current_sim_time_utc="2016-02-01T10:15:02Z")
    assert resp_fresh.is_stale is False
    assert resp_fresh.eta_lifecycle_state == ETAState.ESTIMATING.value


def test_arrival_latching_and_zombie_protection(base_valid_payload):
    processor = ETAStreamProcessor()

    # Vessel arriving at dock: distance < 250m, speed < 1.0 kts for 3 consecutive steps
    terminal_lat, terminal_lon = 48.3828, -4.4855  # Brest terminal
    for i in range(3):
        t_str = f"2016-02-01T10:3{i}:00Z"
        evt = dict(base_valid_payload)
        evt["message_id"] = f"MSG-ARR-{i}"
        evt["event_timestamp_utc"] = t_str
        evt["receipt_timestamp_utc"] = t_str
        evt["latitude"] = terminal_lat
        evt["longitude"] = terminal_lon
        evt["sog_knots"] = 0.2
        resp, _ = processor.process_event(evt)

    assert resp.is_arrived is True
    assert resp.eta_lifecycle_state == ETAState.ARRIVED.value
    assert resp.estimated_remaining_minutes == 0.0

    # Delayed out-of-order packet arriving after confirmed arrival
    delayed_evt = dict(base_valid_payload)
    delayed_evt["message_id"] = "MSG-DELAYED-ZOMBIE"
    delayed_evt["event_timestamp_utc"] = "2016-02-01T10:25:00Z"  # Prior to arrival
    delayed_evt["receipt_timestamp_utc"] = "2016-02-01T10:35:00Z"  # Received after arrival
    delayed_evt["latitude"] = 48.3600
    delayed_evt["longitude"] = -4.5500
    delayed_evt["sog_knots"] = 14.0

    resp_after, _ = processor.process_event(delayed_evt)
    assert resp_after.is_arrived is True
    assert resp_after.eta_lifecycle_state == ETAState.ARRIVED.value
    assert resp_after.estimated_remaining_minutes == 0.0


def test_mock_api_service_and_client(base_valid_payload):
    processor = ETAStreamProcessor()
    service = MockAPIService(processor=processor)
    client = MockAPIClient(service=service)

    # 1. Post telemetry
    push_res = client.push_telemetry(base_valid_payload)
    assert push_res["status_code"] == 200
    assert push_res["body"]["mmsi"] == 227705101
    assert push_res["body"]["vessel_name"] == "FROMVEUR II"

    # 2. Query ETA
    query_res = client.query_eta(227705101)
    assert query_res["status_code"] == 200
    assert query_res["body"]["mmsi"] == 227705101
    assert "estimated_remaining_minutes" in query_res["body"]

    # 3. Query non-existent vessel
    missing_res = client.query_eta(999999999)
    assert missing_res["status_code"] == 404
    assert missing_res["body"]["error_code"] == "VESSEL_NOT_TRACKED"

    # 4. Post invalid payload
    bad_payload = dict(base_valid_payload)
    del bad_payload["message_id"]
    bad_res = client.push_telemetry(bad_payload)
    assert bad_res["status_code"] == 400
    assert "error" in bad_res["body"]


def test_all_20_scenarios_pass():
    runner = MockStreamRunner()
    results = runner.run_all_20_scenarios()
    assert len(results) == 20
    failed = [r for r in results if not r["passed"]]
    assert len(failed) == 0, f"Failed scenarios: {[f['id'] for f in failed]}"
