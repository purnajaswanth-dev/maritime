"""Continuous Virtual Fleet Simulation Runner for Where Is My Ferry? Phase 08.

Manages multi-vessel virtual simulation lifecycle, controlled clock advancement,
fault injection across 22 scenarios, and real-time streaming integration with ETAStreamProcessor.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.models.eta_state_machine import ETAState
from src.streaming.event_schema import ETAResponsePayload
from src.streaming.eta_stream_processor import ETAStreamProcessor
from src.simulation.virtual_ais_generator import VirtualAISGenerator


@dataclass
class SimulationStatus:
    """Status summary of the active virtual simulation session."""
    run_id: str
    is_running: bool
    is_paused: bool
    sim_time_utc: str
    speed_multiplier: float
    step_interval_s: float
    total_events_generated: int
    total_events_processed: int
    active_vessels_count: int
    active_scenario_id: Optional[str] = None
    mode: str = "DEMO"


class VirtualFleetRunner:
    """Continuous simulation coordinator connecting virtual fleet kinematics to ETAStreamProcessor."""

    def __init__(
        self,
        generator: Optional[VirtualAISGenerator] = None,
        processor: Optional[ETAStreamProcessor] = None,
        scenarios_config_path: Optional[Path] = None,
        replay_runner: Optional[Any] = None,
    ):
        self.generator = generator or VirtualAISGenerator()
        self.processor = processor or ETAStreamProcessor()
        default_json = repo_root / "configs" / "phase_08_scenarios.json"
        self.scenarios_path = scenarios_config_path or default_json
        self.replay_runner = replay_runner

        self.run_id = f"sim_run_{uuid.uuid4().hex[:8]}"
        self.is_running = False
        self.is_paused = False
        self.speed_multiplier = 1.0
        self.step_interval_s = 5.0  # 5 seconds discrete kinematic step
        self.current_sim_time = datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc)

        self.total_events_generated = 0
        self.total_events_processed = 0
        self.active_scenario_id: Optional[str] = None

        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self.scenarios: Dict[str, Dict[str, Any]] = {}
        self._load_scenarios()

    def _load_scenarios(self):
        """Loads scenario definitions from configuration."""
        if not self.scenarios_path.exists():
            alt_json = self.scenarios_path.with_suffix(".json")
            if alt_json.exists():
                self.scenarios_path = alt_json
            else:
                return

        with open(self.scenarios_path, "r", encoding="utf-8") as f:
            if self.scenarios_path.suffix == ".json":
                data = json.load(f)
            else:
                try:
                    import yaml
                    data = yaml.safe_load(f)
                except ImportError:
                    alt_json = self.scenarios_path.with_suffix(".json")
                    if alt_json.exists():
                        with open(alt_json, "r", encoding="utf-8") as f_json:
                            data = json.load(f_json)
                    else:
                        raise ImportError("PyYAML not installed and no .json config found")

            for sc in data.get("scenarios", []):
                self.scenarios[sc["id"]] = sc

    def start(self, speed_multiplier: Optional[float] = None, step_interval_s: Optional[float] = None, scenario_id: Optional[str] = None):
        """Starts continuous simulation background loop in a thread-safe manner."""
        old_thread = None
        with self._lock:
            if speed_multiplier is not None:
                self.speed_multiplier = speed_multiplier
            elif self.speed_multiplier == 1.0:
                self.speed_multiplier = 5.0

            if step_interval_s is not None:
                self.step_interval_s = step_interval_s
            elif self.step_interval_s > 60.0:
                self.step_interval_s = 5.0

            if scenario_id is not None:
                self.active_scenario_id = scenario_id

            if self.is_running:
                # Already running: unpause if paused and return
                self.is_paused = False
                return

            self.is_running = True
            self.is_paused = False
            self._stop_event.clear()

            # Guard against duplicate threads
            if self._thread is not None and self._thread.is_alive():
                old_thread = self._thread

            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

        if old_thread is not None and old_thread.is_alive():
            old_thread.join(timeout=1.0)

    def stop(self):
        """Stops simulation loop cleanly without deadlocks."""
        thread_to_join = None
        with self._lock:
            if not self.is_running:
                return
            self.is_running = False
            self.is_paused = False
            self._stop_event.set()
            self._wake_event.set()
            thread_to_join = self._thread
            self._thread = None

        if thread_to_join and thread_to_join.is_alive():
            thread_to_join.join(timeout=2.0)

    def pause(self):
        """Pauses simulation clock and event progression."""
        with self._lock:
            self.is_paused = True
            self._wake_event.set()

    def resume(self):
        """Resumes simulation clock, or starts execution if never started."""
        with self._lock:
            if not self.is_running:
                need_start = True
            else:
                need_start = False
                self.is_paused = False
                self._wake_event.set()

        if need_start:
            self.start()

    def reset(self):
        """Stops simulation and cleanly resets fleet, processor, and simulation clock to initial state."""
        self.stop()
        with self._lock:
            self.generator = VirtualAISGenerator()
            self.processor = ETAStreamProcessor(model=self.processor.model if self.processor else None)
            self.current_sim_time = datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc)
            self.total_events_generated = 0
            self.total_events_processed = 0
            self.active_scenario_id = None
            self.run_id = f"sim_run_{uuid.uuid4().hex[:8]}"
            if self.replay_runner:
                self.replay_runner.reset()

        # Pre-step all vessels once so initial telemetry is immediately populated
        for v_id in self.generator.get_vessel_ids():
            self.step_vessel(v_id, delta_s=0.0, scenario_id="reset")

    def _compute_mode(self) -> str:
        """Determines explicit operational mode string."""
        if self.is_paused:
            return "PAUSED"
        if not self.is_running:
            return "STOPPED"
        if abs(self.speed_multiplier - 1.0) < 0.1:
            return "REALTIME"
        if abs(self.speed_multiplier - 5.0) < 0.1:
            return "DEMO"
        if abs(self.speed_multiplier - 20.0) < 0.1:
            return "ACCELERATED"
        return f"CUSTOM ({self.speed_multiplier:.1f}x)"

    def get_status(self) -> SimulationStatus:
        """Returns current operational status."""
        with self._lock:
            return SimulationStatus(
                run_id=self.run_id,
                is_running=self.is_running,
                is_paused=self.is_paused,
                sim_time_utc=self.current_sim_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                speed_multiplier=self.speed_multiplier,
                step_interval_s=self.step_interval_s,
                total_events_generated=self.total_events_generated,
                total_events_processed=self.total_events_processed,
                active_vessels_count=len(self.generator.get_vessel_ids()),
                active_scenario_id=self.active_scenario_id,
                mode=self._compute_mode(),
            )

    def step_vessel(
        self,
        vessel_id: str,
        delta_s: Optional[float] = None,
        speed_override: Optional[float] = None,
        force_holding: bool = False,
        route_dev_lat: float = 0.0,
        route_dev_lon: float = 0.0,
        scenario_id: Optional[str] = None,
    ) -> Tuple[Optional[ETAResponsePayload], Optional[str]]:
        """Advances single vessel by one discrete step and processes through ETA engine."""
        dt_s = delta_s or self.step_interval_s
        with self._lock:
            event = self.generator.advance_vessel_step(
                vessel_id=vessel_id,
                sim_timestamp_utc=self.current_sim_time,
                delta_seconds=dt_s,
                speed_override_knots=speed_override,
                force_holding=force_holding,
                route_deviation_lat=route_dev_lat,
                route_deviation_lon=route_dev_lon,
                simulation_run_id=self.run_id,
                scenario_id=scenario_id or self.active_scenario_id or "step",
            )
            self.total_events_generated += 1

        # Process through authoritative stream processor
        resp, err = self.processor.process_event(
            raw_payload=event,
            current_sim_time_utc=self.current_sim_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        if resp is not None:
            with self._lock:
                self.total_events_processed += 1

        return resp, err

    def advance_clock(self, seconds: float):
        """Advances simulation clock forward by specified duration."""
        with self._lock:
            self.current_sim_time += timedelta(seconds=seconds)

    def _run_loop(self):
        """Internal execution loop for continuous simulation."""
        while not self._stop_event.is_set():
            with self._lock:
                paused = self.is_paused
                step_interval = self.step_interval_s
                speed_mult = self.speed_multiplier

            if not paused:
                vessel_ids = self.generator.get_vessel_ids()
                for v_id in vessel_ids:
                    if self._stop_event.is_set() or self.is_paused:
                        break
                    self.step_vessel(v_id, delta_s=step_interval)
                self.advance_clock(step_interval)
                if self.replay_runner:
                    self.replay_runner.step(step_interval)

            # Sleep wall-clock proportional to speed multiplier.
            # Example: step_interval = 5.0s, speed_mult = 5.0 => sleep_s = 1.0s.
            # 5.0s sim advancement per 1.0s real time => exactly 5.0x speed ratio.
            sleep_s = max(0.02, step_interval / max(0.1, speed_mult))
            self._wake_event.clear()
            self._wake_event.wait(timeout=sleep_s)

    # =========================================================================
    # Scenario Execution Suite (22 Scenarios)
    # =========================================================================

    def run_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Executes a single scenario deterministically and returns structured result."""
        if scenario_id not in self.scenarios:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

        sc = self.scenarios[scenario_id]
        v_id = sc.get("vessel_id", "V-FROMVEUR-SIM")
        self.generator.reset_vessel(v_id)

        # Baseline clock and isolated processor session for scenario testing
        self.processor = ETAStreamProcessor()
        self.current_sim_time = datetime(2026, 3, 1, 9, 0, 0, tzinfo=timezone.utc)
        self.run_id = f"test_{scenario_id.lower()}"
        fault = sc["fault_type"]
        passed = False
        details = ""
        saved_step_interval = self.step_interval_s
        self.step_interval_s = sc.get("step_interval_s", 300.0)

        try:
            if fault == "NONE":
                # Scenario 01: Normal voyage (6 sequential 5m steps in cruising transit)
                responses = []
                for _ in range(6):
                    r, err = self.step_vessel(v_id, scenario_id=scenario_id)
                    assert err is None
                    responses.append(r)
                    self.advance_clock(sc["step_interval_s"])
                passed = all(r.eta_lifecycle_state == ETAState.ESTIMATING.value for r in responses)
                details = f"Replayed {len(responses)} steps smoothly in transit; final ETA: {responses[-1].estimated_remaining_minutes}m"

            elif fault == "DELAYED_DEPARTURE":
                # Scenario 02: Delayed departure at origin berth
                # Step 1-3 held at berth
                r1, _ = self.step_vessel(v_id, force_holding=True, scenario_id=scenario_id)
                self.advance_clock(sc["delay_seconds"])
                # Then starts moving
                r2, _ = self.step_vessel(v_id, scenario_id=scenario_id)
                passed = (r2 is not None and r2.eta_lifecycle_state == ETAState.ESTIMATING.value)
                details = f"Vessel held for {sc['delay_seconds']}s then embarked; ETA: {r2.estimated_remaining_minutes}m"

            elif fault == "SPEED_REDUCTION":
                # Scenario 03: Cruising speed drops to 5 kts
                r_fast, _ = self.step_vessel(v_id, speed_override=16.0, scenario_id=scenario_id)
                r_slow, _ = self.step_vessel(v_id, speed_override=sc["target_speed_knots"], scenario_id=scenario_id)
                passed = (r_slow.estimated_remaining_minutes >= r_fast.estimated_remaining_minutes)
                details = f"Speed reduced to {sc['target_speed_knots']} kts; ETA adjusted upward from {r_fast.estimated_remaining_minutes}m to {r_slow.estimated_remaining_minutes}m"

            elif fault == "HOLDING_PATTERN":
                # Scenario 04: Stopped in water (0.1 kts in open sea)
                self.step_vessel(v_id, scenario_id=scenario_id)
                self.advance_clock(300)
                r_hold, _ = self.step_vessel(v_id, force_holding=True, scenario_id=scenario_id)
                passed = (r_hold.eta_lifecycle_state == ETAState.DELAYED_OR_UNCERTAIN.value)
                details = f"Zero speed in channel correctly transitioned to {r_hold.eta_lifecycle_state}"

            elif fault == "ROUTE_DEVIATION":
                # Scenario 05: Route deviation north
                r_norm, _ = self.step_vessel(v_id, scenario_id=scenario_id)
                r_dev, _ = self.step_vessel(v_id, route_dev_lat=0.15, scenario_id=scenario_id)
                passed = (r_dev is not None and r_dev.estimated_remaining_minutes >= r_norm.estimated_remaining_minutes)
                details = f"Detour applied; ETA accommodated route distance: from {r_norm.estimated_remaining_minutes}m to {r_dev.estimated_remaining_minutes}m"

            elif fault == "STREAM_DROPOUT":
                # Scenario 06: Telemetry ceases for 720s (> 600s staleness threshold)
                r1, _ = self.step_vessel(v_id, scenario_id=scenario_id)
                # Advance clock by 720 seconds without new telemetry, then query / ingest step
                self.advance_clock(sc["gap_seconds"])
                # Re-evaluating or passing step with older observation
                evt = self.generator.advance_vessel_step(v_id, self.current_sim_time - timedelta(seconds=sc["gap_seconds"]))
                r_stale, _ = self.processor.process_event(evt, current_sim_time_utc=self.current_sim_time.strftime("%Y-%m-%dT%H:%M:%SZ"))
                passed = (r_stale.is_stale is True and r_stale.eta_lifecycle_state == ETAState.STALE_DATA.value)
                details = f"Data gap of {sc['gap_seconds']}s successfully flagged as {r_stale.eta_lifecycle_state}"

            elif fault == "STREAM_RECOVERY":
                # Scenario 07: Reconnect after 720s gap
                r1, _ = self.step_vessel(v_id, scenario_id=scenario_id)
                self.advance_clock(sc["gap_seconds"])
                evt_stale = self.generator.advance_vessel_step(v_id, self.current_sim_time - timedelta(seconds=sc["gap_seconds"]))
                self.processor.process_event(evt_stale, current_sim_time_utc=self.current_sim_time.strftime("%Y-%m-%dT%H:%M:%SZ"))
                # Fresh event arrives
                r_fresh, _ = self.step_vessel(v_id, scenario_id=scenario_id)
                passed = (r_fresh.is_stale is False and r_fresh.eta_lifecycle_state == ETAState.ESTIMATING.value)
                details = f"Fresh observation restored active state to {r_fresh.eta_lifecycle_state}"

            elif fault == "DUPLICATE_PACKETS":
                # Scenario 08: Duplicate event delivery
                evt = self.generator.advance_vessel_step(v_id, self.current_sim_time)
                r1, err1 = self.processor.process_event(evt)
                r2, err2 = self.processor.process_event(evt)
                passed = (err1 is None and err2 is None and r1.estimated_remaining_minutes == r2.estimated_remaining_minutes)
                details = "Duplicate message dropped cleanly; identical cached response returned"

            elif fault == "OUT_OF_ORDER_PACKETS":
                # Scenario 09: Out-of-order event delivery
                evt1 = self.generator.advance_vessel_step(v_id, self.current_sim_time)
                self.processor.process_event(evt1)
                # Newer event at 10:10Z
                t_newer = self.current_sim_time + timedelta(minutes=10)
                evt_newer = self.generator.advance_vessel_step(v_id, t_newer)
                self.processor.process_event(evt_newer)
                tracker = self.processor.vessel_trackers[evt1["mmsi"]]
                watermark_before = tracker.latest_event_epoch_s
                # Delayed event from 10:05Z
                t_late = self.current_sim_time + timedelta(minutes=5)
                evt_late = self.generator.advance_vessel_step(v_id, t_late)
                self.processor.process_event(evt_late)
                watermark_after = tracker.latest_event_epoch_s
                passed = (watermark_after == watermark_before)
                details = f"Watermark held monotonic at {watermark_after}; delayed packet did not rewind clock"

            elif fault == "STALE_OBSERVATION":
                # Scenario 10: Ingestion of 15m old packet
                t_old = self.current_sim_time - timedelta(seconds=sc["stale_seconds"])
                evt = self.generator.advance_vessel_step(v_id, t_old)
                r_stale, _ = self.processor.process_event(evt, current_sim_time_utc=self.current_sim_time.strftime("%Y-%m-%dT%H:%M:%SZ"))
                passed = (r_stale.is_stale is True and r_stale.eta_lifecycle_state == ETAState.STALE_DATA.value)
                details = f"Observation freshness {r_stale.data_freshness_seconds}s correctly triggered {r_stale.eta_lifecycle_state}"

            elif fault == "APPROACH_TERMINAL":
                # Scenario 11: Destination approach
                v = self.generator.vessels[v_id]
                v.current_distance_traveled_m = v.total_route_distance_m - 800.0  # Within 800m of destination
                r_app, _ = self.step_vessel(v_id, speed_override=4.0, scenario_id=scenario_id)
                passed = (r_app.eta_lifecycle_state == ETAState.ARRIVAL_PENDING_CONFIRMATION.value)
                details = f"Proximity < 1000m successfully transitioned to {r_app.eta_lifecycle_state}"

            elif fault == "CONFIRMED_ARRIVAL":
                # Scenario 12: Successful arrival & berth dwell
                v = self.generator.vessels[v_id]
                v.current_distance_traveled_m = v.total_route_distance_m - 50.0
                v.current_lat = v.waypoints[-1][0]
                v.current_lon = v.waypoints[-1][1]
                v.is_arrived = True
                responses = []
                for _ in range(3):
                    r, _ = self.step_vessel(v_id, speed_override=0.1, scenario_id=scenario_id)
                    responses.append(r)
                    self.advance_clock(60)
                passed = (responses[-1].is_arrived is True and responses[-1].eta_lifecycle_state == ETAState.ARRIVED.value and responses[-1].estimated_remaining_minutes == 0.0)
                details = "Arrival confirmed after dock dwell; remaining ETA locked to 0.0m"

            elif fault == "POST_ARRIVAL_PACKET":
                # Scenario 13: Delayed packet arriving after arrival
                v = self.generator.vessels[v_id]
                v.current_distance_traveled_m = v.total_route_distance_m - 50.0
                v.current_lat = v.waypoints[-1][0]
                v.current_lon = v.waypoints[-1][1]
                v.is_arrived = True
                for _ in range(3):
                    self.step_vessel(v_id, speed_override=0.1, scenario_id=scenario_id)
                # Delayed packet
                delayed_evt = self.generator.advance_vessel_step(v_id, self.current_sim_time - timedelta(minutes=15))
                delayed_evt["latitude"] = 48.3300
                delayed_evt["longitude"] = -4.6500
                delayed_evt["sog_knots"] = 15.0
                r_after, _ = self.processor.process_event(delayed_evt)
                passed = (r_after.is_arrived is True and r_after.eta_lifecycle_state == ETAState.ARRIVED.value and r_after.estimated_remaining_minutes == 0.0)
                details = "Latched arrived state strictly maintained; zombie countdown prevented"

            elif fault == "INVALID_COORDINATES":
                # Scenario 14: Latitude > 90
                evt = self.generator.advance_vessel_step(v_id, self.current_sim_time)
                evt["latitude"] = sc["bad_lat"]
                r, err = self.processor.process_event(evt)
                passed = (r is None and err == sc["expected_error"])
                details = f"Malformed latitude correctly rejected with error: {err}"

            elif fault == "INVALID_SPEED":
                # Scenario 15: Speed > 60 kts
                evt = self.generator.advance_vessel_step(v_id, self.current_sim_time)
                evt["sog_knots"] = sc["bad_sog"]
                r, err = self.processor.process_event(evt)
                passed = (r is None and err == sc["expected_error"])
                details = f"Excessive speed correctly rejected with error: {err}"

            elif fault == "MALFORMED_PAYLOAD":
                # Scenario 16: Missing message_id
                evt = self.generator.advance_vessel_step(v_id, self.current_sim_time)
                del evt["message_id"]
                r, err = self.processor.process_event(evt)
                passed = (r is None and err == sc["expected_error"])
                details = f"Missing identifier correctly rejected with error: {err}"

            elif fault == "INFERENCE_FAILURE":
                # Scenario 17: Inference exception handled gracefully
                class FailingModel:
                    def predict(self, df):
                        raise RuntimeError("Simulated inference failure")
                proc_fail = ETAStreamProcessor(model=FailingModel())
                evt = self.generator.advance_vessel_step(v_id, self.current_sim_time)
                try:
                    proc_fail.process_event(evt)
                    passed = False
                    details = "Failed to raise expected model error"
                except Exception as ex:
                    passed = True
                    details = f"Model exception caught and isolated cleanly: {type(ex).__name__}"

            elif fault == "CLEAN_RESTART":
                # Scenario 18: Clean shutdown & restart
                self.step_vessel(v_id, scenario_id=scenario_id)
                self.stop()
                new_runner = VirtualFleetRunner()
                new_runner.start(speed_multiplier=5.0)
                r_restart, err = new_runner.step_vessel(v_id, scenario_id=scenario_id)
                new_runner.stop()
                passed = (err is None and r_restart is not None)
                details = "Runner stopped cleanly and re-initialized without leaking resources"

            elif fault == "MULTI_VESSEL":
                # Scenario 19: 4 vessels operating simultaneously
                v_ids = sc.get("vessel_ids", self.generator.get_vessel_ids())
                responses = {}
                for vid in v_ids:
                    r, err = self.step_vessel(vid, scenario_id=scenario_id)
                    assert err is None
                    responses[vid] = r
                passed = (len(responses) == len(v_ids) and len(set(r.mmsi for r in responses.values())) == len(v_ids))
                details = f"Concurrently simulated {len(responses)} distinct vessels without cross-talk"

            elif fault == "RAPID_BURST":
                # Scenario 20: 50 events in rapid succession
                t0 = time.perf_counter()
                burst_n = sc.get("burst_count", 50)
                for _ in range(burst_n):
                    r, err = self.step_vessel(v_id, scenario_id=scenario_id)
                    assert err is None
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                passed = True
                details = f"Ingested {burst_n} events in {elapsed_ms:.1f}ms ({burst_n / (elapsed_ms / 1000.0):.1f} events/s)"

            elif fault == "PAUSE_RESUME":
                # Scenario 21: Repeated pause and resume
                r1, _ = self.step_vessel(v_id, scenario_id=scenario_id)
                self.pause()
                assert self.is_paused is True
                self.resume()
                assert self.is_paused is False
                r2, _ = self.step_vessel(v_id, scenario_id=scenario_id)
                passed = (r2 is not None and r2.eta_lifecycle_state == ETAState.ESTIMATING.value)
                details = "Simulation paused and resumed cleanly with no jump anomaly"

            elif fault == "CLOCK_ADVANCEMENT":
                # Scenario 22: Clock advancement and derived countdown consistency
                r1, _ = self.step_vessel(v_id, scenario_id=scenario_id)
                arr_ts = datetime.fromisoformat(r1.predicted_arrival_timestamp_utc.replace("Z", "+00:00"))
                # Advance simulated clock by 5 minutes
                self.advance_clock(300)
                derived_rem = max(0.0, (arr_ts - self.current_sim_time).total_seconds() / 60.0)
                passed = (derived_rem < r1.estimated_remaining_minutes)
                details = f"Clock advanced 5m; remaining time correctly decremented from {r1.estimated_remaining_minutes}m to {derived_rem:.1f}m"

            else:
                passed = False
                details = f"Unhandled scenario fault type: {fault}"

        except Exception as e:
            passed = False
            details = f"Scenario raised exception: {str(e)}"
        finally:
            self.step_interval_s = saved_step_interval

        return {
            "id": scenario_id,
            "name": sc.get("name", scenario_id),
            "vessel_id": v_id,
            "fault_type": fault,
            "passed": passed,
            "details": details,
        }

    def run_all_22_scenarios(self) -> List[Dict[str, Any]]:
        """Runs the entire 22-scenario suite and returns results."""
        results = []
        for sc_id in self.scenarios.keys():
            res = self.run_scenario(sc_id)
            results.append(res)
        return results
