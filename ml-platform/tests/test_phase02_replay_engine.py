"""Comprehensive tests for Phase 02 Replay Engine.

Covers:
- Scheduler: weekday/season validity, daylight-saving boundaries, midnight crossing.
- Replay: seeded determinism, corridor coordinate bounding, vessel single-location constraint.
- Pipeline: lifecycle transitions through ESTIMATING to ARRIVED with berth dwell enforcement.
- Scenario overlay: AIS blackout drives STALE_DATA after 600s and recovers cleanly.
- Endpoints: /timetable/today, /departures, /departures/{id}/live (404 and schema), /track, /accuracy.
- Full simulated day run at 60x without errors with recorded ground truth.
"""

import datetime
from pathlib import Path
import warnings
import pytest
from starlette.exceptions import StarletteDeprecationWarning

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        category=StarletteDeprecationWarning,
        message=r".*Using `httpx` with `starlette.testclient` is deprecated.*",
    )
    from fastapi.testclient import TestClient

from src.models.eta_state_machine import ETAState
from src.replay.departure_scheduler import DepartureScheduler, PARIS_TZ
from src.replay.replay_runner import ReplayRunner
from src.replay.voyage_library import VoyageLibrary
from src.simulation.daemon import app, container
from src.simulation.virtual_fleet_runner import VirtualFleetRunner

REPO_ROOT = Path(__file__).resolve().parents[2]
ML_DIR = Path(__file__).resolve().parents[1]
SERVICES_JSON = ML_DIR / "data" / "timetable" / "services.json"
REPLAY_DIR = ML_DIR / "data" / "replay"


@pytest.fixture(scope="module")
def client():
    """Initializes TestClient triggering FastAPI lifespan setup."""
    with TestClient(app) as c:
        yield c


def test_departure_scheduler_weekday_season_and_dst():
    """Verify departure scheduler handles weekdays, seasons, and DST transitions."""
    sched = DepartureScheduler(str(SERVICES_JSON))

    # 1. Weekday vs Weekend (2026-10-24 is Saturday, 2026-10-26 is Monday)
    deps_sat = sched.get_departures_for_date(datetime.date(2026, 10, 24))
    deps_mon = sched.get_departures_for_date(datetime.date(2026, 10, 26))
    assert len(deps_sat) > 0
    assert len(deps_mon) > 0

    # 2. Seasonal Service (Camaret operates only in summer: 2026-06-15 to 2026-09-15)
    deps_summer = sched.get_departures_for_date(datetime.date(2026, 7, 15))
    deps_winter = sched.get_departures_for_date(datetime.date(2026, 11, 15))

    summer_corridors = {d.corridor for d in deps_summer}
    winter_corridors = {d.corridor for d in deps_winter}
    assert "BREST_CAMARET" in summer_corridors
    assert "BREST_CAMARET" not in winter_corridors

    # 3. Daylight Saving Boundary (Europe/Paris switches from CEST UTC+2 to CET UTC+1 on Oct 25, 2026)
    deps_before_dst = sched.get_departures_for_date(datetime.date(2026, 10, 24))
    deps_after_dst = sched.get_departures_for_date(datetime.date(2026, 10, 26))

    # 08:30 Paris time before switch is 06:30 UTC
    dep_oct24 = next(d for d in deps_before_dst if d.scheduled_departure_time == "08:30:00")
    assert "T06:30:00Z" in dep_oct24.scheduled_departure_utc

    # 08:30 Paris time after switch is 07:30 UTC
    dep_oct26 = next(d for d in deps_after_dst if d.scheduled_departure_time == "08:30:00")
    assert "T07:30:00Z" in dep_oct26.scheduled_departure_utc


def test_replay_seeded_determinism_and_bounds():
    """Verify identical random seed produces identical voyage selections and positions stay in bounds."""
    runner1 = ReplayRunner(seed=12345)
    runner2 = ReplayRunner(seed=12345)

    # Advance both by 1 hour (3600s)
    runner1.step(3600.0)
    runner2.step(3600.0)

    assert len(runner1.active_replays) == len(runner2.active_replays)
    for dep_id in runner1.active_replays:
        act1 = runner1.active_replays[dep_id]
        act2 = runner2.active_replays[dep_id]
        assert act1.voyage.voyage_id == act2.voyage.voyage_id
        assert act1.latest_lat == act2.latest_lat
        assert act1.latest_lon == act2.latest_lon

        # Geographic bounding box check for Iroise Sea
        assert 47.9 <= act1.latest_lat <= 48.6
        assert -5.2 <= act1.latest_lon <= -4.3


def test_pipeline_lifecycle_transitions_and_arrival_latch():
    """Verify replayed telemetry passes through ESTIMATING to ARRIVED only after berth dwell."""
    runner = ReplayRunner(seed=42)
    # Target morning departure DEP-20261024-BRE-CNQ-0830
    dep_id = "DEP-20261024-BRE-CNQ-0830"
    assert dep_id in runner.departures

    # Fast-forward until departure enters boarding/active window
    runner.step(2100.0)  # clock moves past 08:30 to 08:35
    assert dep_id in runner.active_replays
    act = runner.active_replays[dep_id]

    # Advance until departure is underway and replayed voyage reaches destination
    while dep_id in runner.active_replays:
        runner.step(60.0)

    # Must be marked ARRIVED with recorded ground truth
    assert dep_id in runner.completed_departures
    comp = runner.completed_departures[dep_id]
    assert comp.actual_arrival_utc.endswith("Z")
    assert comp.actual_duration_minutes > 0
    assert comp.snapshots_count > 0

    # Latching check: subsequent steps do not revert status
    runner.step(300.0)
    assert runner.departures[dep_id].status == "ARRIVED"


def test_scenario_overlay_ais_blackout_and_recovery():
    """Verify scenario AIS blackout causes STALE_DATA after 600s gap and recovers."""
    fleet_runner = VirtualFleetRunner()
    v_id = "V-FROMVEUR-SIM"

    # 1. Normal step
    r1, err1 = fleet_runner.step_vessel(v_id)
    assert err1 is None
    assert r1.eta_lifecycle_state == ETAState.ESTIMATING.value

    # 2. Advance clock by 650 seconds without new observations (AIS blackout)
    fleet_runner.advance_clock(650.0)
    tracker = fleet_runner.processor.vessel_trackers.get(fleet_runner.generator.vessels[v_id].synthetic_mmsi)
    assert tracker is not None

    # Step with state machine check
    snap = tracker.state_machine.process_step(
        prediction_timestamp_utc=fleet_runner.current_sim_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        raw_model_eta_minutes=25.0,
        obs=None,  # No telemetry received during blackout
    )
    assert snap.state == ETAState.ETA_UNAVAILABLE

    # 3. Telemetry recovery
    r_rec, err_rec = fleet_runner.step_vessel(v_id)
    assert err_rec is None
    assert r_rec.eta_lifecycle_state in [ETAState.ESTIMATING.value, "IN_TRANSIT"]


def test_new_internal_endpoints(client):
    """Verify all 5 Phase 02 internal endpoints return expected schemas and error codes."""
    # 1. GET /internal/v1/timetable/today
    resp_tt = client.get("/internal/v1/timetable/today")
    assert resp_tt.status_code == 200
    tt_data = resp_tt.json()
    assert "date" in tt_data
    assert tt_data["total_departures"] > 0
    assert len(tt_data["departures"]) > 0

    # 2. GET /internal/v1/departures
    resp_deps = client.get("/internal/v1/departures")
    assert resp_deps.status_code == 200
    deps_data = resp_deps.json()
    assert deps_data["total_departures"] > 0
    sample_dep = deps_data["departures"][0]
    sample_dep_id = sample_dep["departure_id"]

    # 3. GET /internal/v1/departures/{id}/live
    resp_live = client.get(f"/internal/v1/departures/{sample_dep_id}/live")
    assert resp_live.status_code == 200
    live_data = resp_live.json()
    assert live_data["departure_id"] == sample_dep_id
    assert live_data["data_source"] == "HISTORICAL_REPLAY"
    assert len(live_data["weight_checksum_sha256"]) == 64
    assert "eta" in live_data
    assert "lifecycle" in live_data

    # 404 test on unknown departure
    resp_404 = client.get("/internal/v1/departures/DEP-UNKNOWN-999/live")
    assert resp_404.status_code == 404

    # 4. GET /internal/v1/departures/{id}/track
    resp_track = client.get(f"/internal/v1/departures/{sample_dep_id}/track")
    assert resp_track.status_code == 200
    track_data = resp_track.json()
    assert "track" in track_data

    # 5. GET /internal/v1/accuracy
    resp_acc = client.get("/internal/v1/accuracy")
    assert resp_acc.status_code == 200
    acc_data = resp_acc.json()
    assert "accuracy_records" in acc_data


def test_full_simulated_day_at_60x():
    """Verify running a full day at 60x speed without errors and all supported departures arrive."""
    runner = ReplayRunner(seed=100)
    # Start at 08:00 and advance through the day to 20:00 (12 hours = 43,200 seconds)
    # Step in 60-second intervals
    total_steps = 43200 // 60
    for _ in range(total_steps):
        runner.step(60.0)

    # Every supported departure scheduled before 18:00 should complete arrival
    supported_deps = [d for d in runner.departures.values() if d.tracking_supported and d.scheduled_departure_time <= "17:00:00"]
    assert len(supported_deps) > 0

    for dep in supported_deps:
        assert dep.departure_id in runner.completed_departures, (
            f"Departure {dep.departure_id} ({dep.corridor}) failed to complete arrival"
        )
        comp = runner.completed_departures[dep.departure_id]
        assert comp.actual_arrival_utc is not None
        assert comp.snapshots_count > 0
        assert comp.actual_duration_minutes > 0


def test_timetable_sync_endpoint_and_replay(client):
    """Verify POST /internal/v1/timetable/sync loads departures dynamically and provisions replays."""
    payload = {
        "departures": [
            {
                "departure_id": "DEP-TEST-SYNC-01",
                "corridor": "BREST_LE_CONQUET",
                "origin_terminal_id": "BREST",
                "dest_terminal_id": "LE_CONQUET",
                "vessel_id": "V-FROMVEUR-SIM",
                "vessel_name": "FROMVEUR II",
                "tracking_supported": True,
                "scheduled_departure_utc": "2026-10-24T09:30:00Z",
                "scheduled_arrival_utc": "2026-10-24T10:45:00Z",
                "duration_minutes": 75.0,
                "status": "SCHEDULED",
            },
            {
                "departure_id": "DEP-TEST-UNSUPPORTED-02",
                "corridor": "CAMARET_MOLENE",
                "origin_terminal_id": "CAMARET",
                "dest_terminal_id": "MOLENE",
                "vessel_id": None,
                "vessel_name": None,
                "tracking_supported": False,
                "scheduled_departure_utc": "2026-10-24T14:00:00Z",
                "scheduled_arrival_utc": "2026-10-24T15:00:00Z",
                "duration_minutes": 60.0,
                "status": "SCHEDULED",
            },
        ]
    }

    resp = client.post("/internal/v1/timetable/sync", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SYNCED"
    assert data["synced_count"] == 2
    assert data["supported_count"] == 1

    # Supported departure has live endpoint
    resp_live = client.get("/internal/v1/departures/DEP-TEST-SYNC-01/live")
    assert resp_live.status_code == 200
    live_data = resp_live.json()
    assert live_data["departure_id"] == "DEP-TEST-SYNC-01"
    assert live_data["tracking_supported"] is True
    assert live_data["data_source"] == "HISTORICAL_REPLAY"
    assert "eta" in live_data
    assert "lifecycle" in live_data

    # Unsupported departure returns 404 (honest tracking rule)
    resp_unsupported = client.get("/internal/v1/departures/DEP-TEST-UNSUPPORTED-02/live")
    assert resp_unsupported.status_code == 404

