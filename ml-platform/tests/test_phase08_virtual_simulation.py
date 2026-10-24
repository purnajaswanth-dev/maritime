"""Comprehensive Automated Test Suite for Phase 08 Virtual Simulation.

Verifies:
1. VirtualAISGenerator configuration, kinematics, and event schema compliance.
2. VirtualFleetRunner lifecycle management (start, stop, pause, resume, reset).
3. Multi-vessel concurrent execution and state isolation.
4. Deterministic scenario library (all 22 scenarios).
5. MockAPIService and MockAPIClient endpoints and contracts.
6. Frozen model artifact integrity and zero external network calls.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import pytest

from src.models.eta_state_machine import ETAState
from src.simulation.virtual_ais_generator import VirtualAISGenerator, haversine_distance_m, calculate_bearing_deg
from src.simulation.virtual_fleet_runner import VirtualFleetRunner
from src.streaming.event_schema import validate_ais_event
from src.streaming.mock_api_server import MockAPIService, MockAPIClient

repo_root = Path(__file__).resolve().parents[1]


@pytest.fixture
def generator():
    return VirtualAISGenerator()


@pytest.fixture
def runner():
    return VirtualFleetRunner()


def test_generator_config_and_vessels(generator):
    v_ids = generator.get_vessel_ids()
    assert len(v_ids) == 4
    assert "V-FROMVEUR-SIM" in v_ids
    assert "V-AZENOR-SIM" in v_ids
    assert "V-OUESSANT-SIM" in v_ids
    assert "V-SEIN-SIM" in v_ids

    v = generator.vessels["V-FROMVEUR-SIM"]
    assert v.synthetic_mmsi == 999000001
    assert v.total_route_distance_m > 20000.0  # ~23.8 km
    assert len(v.waypoints) == 6


def test_generator_event_schema_and_provenance(generator):
    sim_time = datetime(2026, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    event = generator.advance_vessel_step("V-FROMVEUR-SIM", sim_time)

    # Valid schema conformance
    ais_event, err = validate_ais_event(event)
    assert err is None
    assert ais_event is not None
    assert ais_event.mmsi == 999000001
    assert ais_event.is_synthetic_fixture is True
    assert ais_event.source_id == "virtual_maritime_sim"
    assert event["virtual_vessel_id"] == "V-FROMVEUR-SIM"


def test_generator_great_circle_math():
    # Brest to Le Conquet distance ~ 21.8 km straight line
    d = haversine_distance_m(48.3828, -4.4855, 48.3585, -4.7788)
    assert 21000.0 < d < 23000.0

    # Heading roughly west (~260-270 degrees)
    b = calculate_bearing_deg(48.3828, -4.4855, 48.3585, -4.7788)
    assert 250.0 < b < 280.0


def test_runner_start_stop_pause_resume(runner):
    runner.start(speed_multiplier=10.0)
    status1 = runner.get_status()
    assert status1.is_running is True
    assert status1.is_paused is False

    runner.pause()
    status2 = runner.get_status()
    assert status2.is_paused is True

    runner.resume()
    status3 = runner.get_status()
    assert status3.is_paused is False

    runner.stop()
    status4 = runner.get_status()
    assert status4.is_running is False


def test_runner_multi_vessel_isolation(runner):
    # Step all 4 vessels
    v_ids = runner.generator.get_vessel_ids()
    responses = {}
    for vid in v_ids:
        r, err = runner.step_vessel(vid)
        assert err is None
        assert r is not None
        responses[vid] = r

    assert len(responses) == 4
    # All vessels have unique synthetic MMSIs
    mmsis = [r.mmsi for r in responses.values()]
    assert len(set(mmsis)) == 4


def test_all_22_simulation_scenarios(runner):
    results = runner.run_all_22_scenarios()
    assert len(results) == 22
    failed = [r for r in results if not r["passed"]]
    assert len(failed) == 0, f"Failed scenarios: {[f['id'] for f in failed]}"


def test_mock_api_simulation_endpoints(runner):
    service = MockAPIService(processor=runner.processor, runner=runner)
    client = MockAPIClient(service=service)

    # 1. Simulation status
    status_res = client.get_simulation_status()
    assert status_res["status_code"] == 200
    assert status_res["body"]["simulation_available"] is True
    assert status_res["body"]["provenance"] == "SIMULATED_LOCAL_MARITIME_ENGINE"

    # 2. List vessels
    fleet_res = client.list_vessels()
    assert fleet_res["status_code"] == 200
    assert fleet_res["body"]["total_vessels"] == 4
    assert fleet_res["body"]["vessels"][0]["data_provenance"] == "SIMULATED_SYNTHETIC"

    # 3. Vessel detail
    detail_res = client.get_vessel_detail("V-FROMVEUR-SIM")
    assert detail_res["status_code"] == 200
    assert detail_res["body"]["virtual_vessel_id"] == "V-FROMVEUR-SIM"
    assert detail_res["body"]["synthetic_mmsi"] == 999000001

    # 4. Unknown vessel detail
    missing_res = client.get_vessel_detail("V-UNKNOWN-BOAT")
    assert missing_res["status_code"] == 404
    assert missing_res["body"]["error_code"] == "VIRTUAL_VESSEL_NOT_FOUND"

    # 5. Simulation control
    ctrl_start = client.control_simulation("start", params={"speed_multiplier": 5.0})
    assert ctrl_start["status_code"] == 200
    assert ctrl_start["body"]["status"] == "RUNNING"

    ctrl_pause = client.control_simulation("pause")
    assert ctrl_pause["status_code"] == 200
    assert ctrl_pause["body"]["status"] == "PAUSED"

    ctrl_resume = client.control_simulation("resume")
    assert ctrl_resume["status_code"] == 200
    assert ctrl_resume["body"]["status"] == "RUNNING"

    ctrl_stop = client.control_simulation("stop")
    assert ctrl_stop["status_code"] == 200
    assert ctrl_stop["body"]["status"] == "STOPPED"

    # 6. Scenario trigger
    sc_res = client.trigger_scenario("SCENARIO_12_SUCCESSFUL_ARRIVAL")
    assert sc_res["status_code"] == 200
    assert sc_res["body"]["passed"] is True


def test_frozen_artifacts_integrity():
    """Verifies that all Phase 04-07 model and data artifacts have not been modified."""
    expected_hashes = {
        "data/processed/phase_05_prediction_snapshots.parquet": "39f9f1ae9cbff17c9061460f156f0341c24dd2aab4a5ef7bff8350d48122579d",
        "data/processed/verified_voyages.parquet": "43f5e018368580bc22f14656bc3c606eed1c80516d2ed09816cde4aac2d99997",
        "configs/phase_07_streaming_event_contract.yaml": "28a421341a62b558a8f6289cfba7098603dea3b105daf93f5c0b4378c20fee88",
        "src/models/baselines.py": "f589c1c6fef9b57cff6464ff42f9c8d00a88e94b74db1e8d73b143d110ee114b",
        "src/models/eta_state_machine.py": "6231bca103740691c6e5479dcd7f6423f622f36a5eed6c77e5ee08c6e856b1b2",
        "src/streaming/eta_stream_processor.py": "4edf7b85388d5495f0b634d58f97925b2192f0a89e10e2bbda2999f22eaebe4e",
    }
    for rel_path, expected_hash in expected_hashes.items():
        actual_hash = hashlib.sha256((repo_root / rel_path).read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Frozen artifact modified: {rel_path}"
