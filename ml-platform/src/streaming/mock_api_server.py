"""Mock API Interface and Client for Where Is My Ferry? Phase 07 & Phase 08.

Exposes REST-like dispatch handlers for:
1. POST /api/v1/telemetry: Ingests raw AIS telemetry and produces updated ETA.
2. GET /api/v1/eta/{mmsi}: Returns current authoritative ETA, countdown, and lifecycle state.
3. GET /api/v1/simulation/status: Returns operational status of the simulation session.
4. GET /api/v1/vessels: Lists all virtual vessels, routes, positions, and current states.
5. GET /api/v1/vessels/{vessel_id}: Returns detailed trajectory and ETA for a specific vessel.
6. POST /api/v1/simulation/control: Controls runner lifecycle (start, stop, pause, resume, reset).
7. POST /api/v1/simulation/scenario/{scenario_id}: Triggers a deterministic scenario execution.
"""

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.streaming.eta_stream_processor import ETAStreamProcessor
from src.streaming.event_schema import ETAResponsePayload


class MockAPIService:
    """In-memory service dispatch interface simulating backend HTTP endpoints."""

    def __init__(self, processor: Optional[ETAStreamProcessor] = None, runner: Optional[Any] = None):
        self.processor = processor or ETAStreamProcessor()
        self.runner = runner  # Optional VirtualFleetRunner instance

    def handle_telemetry_post(self, payload: Dict[str, Any], current_sim_time: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        """Handles POST /api/v1/telemetry ingestion."""
        response, err = self.processor.process_event(payload, current_sim_time_utc=current_sim_time)
        if err:
            return 400, {
                "error": True,
                "error_code": err,
                "message": f"Telemetry rejected: {err}",
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        return 200, response.to_dict()

    def handle_eta_get(self, mmsi: int, client_request_time: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        """Handles GET /api/v1/eta/{mmsi} passenger query."""
        tracker = self.processor.vessel_trackers.get(mmsi)
        if tracker is None or tracker.last_response is None:
            return 404, {
                "error": True,
                "error_code": "VESSEL_NOT_TRACKED",
                "message": f"No active ETA tracking found for MMSI {mmsi}",
                "timestamp_utc": client_request_time or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

        # Check client countdown derivation
        resp = tracker.last_response.to_dict()
        if client_request_time:
            # Dynamic countdown re-synchronization based on authoritative predicted arrival timestamp
            dt_req = datetime.fromisoformat(client_request_time.replace("Z", "+00:00"))
            dt_arr = datetime.fromisoformat(resp["predicted_arrival_timestamp_utc"].replace("Z", "+00:00"))
            derived_remaining = max(0.0, (dt_arr - dt_req).total_seconds() / 60.0)
            if resp["is_arrived"]:
                derived_remaining = 0.0
            resp["client_derived_remaining_minutes"] = round(derived_remaining, 2)
            resp["client_query_timestamp_utc"] = client_request_time

        return 200, resp

    def handle_simulation_status_get(self) -> Tuple[int, Dict[str, Any]]:
        """Handles GET /api/v1/simulation/status."""
        if not self.runner:
            return 200, {
                "simulation_available": False,
                "status": "NO_RUNNER_ATTACHED",
                "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        status = self.runner.get_status()
        return 200, {
            "simulation_available": True,
            "run_id": status.run_id,
            "is_running": status.is_running,
            "is_paused": status.is_paused,
            "sim_time_utc": status.sim_time_utc,
            "speed_multiplier": status.speed_multiplier,
            "step_interval_s": status.step_interval_s,
            "total_events_generated": status.total_events_generated,
            "total_events_processed": status.total_events_processed,
            "active_vessels_count": status.active_vessels_count,
            "active_scenario_id": status.active_scenario_id,
            "provenance": "SIMULATED_LOCAL_MARITIME_ENGINE",
        }

    def handle_vessels_get(self) -> Tuple[int, Dict[str, Any]]:
        """Handles GET /api/v1/vessels."""
        if not self.runner:
            return 200, {"vessels": [], "total_vessels": 0}

        fleet = []
        for vid, v in self.runner.generator.vessels.items():
            tracker = self.processor.vessel_trackers.get(v.synthetic_mmsi)
            state = tracker.last_response.eta_lifecycle_state if (tracker and tracker.last_response) else "SCHEDULED"
            rem_min = tracker.last_response.estimated_remaining_minutes if (tracker and tracker.last_response) else None
            arr_ts = tracker.last_response.predicted_arrival_timestamp_utc if (tracker and tracker.last_response) else None

            fleet.append({
                "virtual_vessel_id": vid,
                "synthetic_mmsi": v.synthetic_mmsi,
                "vessel_name": v.vessel_name,
                "route_id": v.route_id,
                "corridor": v.corridor,
                "origin_terminal": v.origin_terminal,
                "dest_terminal": v.dest_terminal,
                "latitude": v.current_lat,
                "longitude": v.current_lon,
                "sog_knots": v.current_sog_knots,
                "cog_degrees": v.current_cog_degrees,
                "is_arrived": v.is_arrived,
                "lifecycle_state": state,
                "estimated_remaining_minutes": rem_min,
                "predicted_arrival_timestamp_utc": arr_ts,
                "data_provenance": "SIMULATED_SYNTHETIC",
            })

        return 200, {"vessels": fleet, "total_vessels": len(fleet)}

    def handle_vessel_detail_get(self, vessel_id: str) -> Tuple[int, Dict[str, Any]]:
        """Handles GET /api/v1/vessels/{vessel_id}."""
        if not self.runner or vessel_id not in self.runner.generator.vessels:
            return 404, {
                "error": True,
                "error_code": "VIRTUAL_VESSEL_NOT_FOUND",
                "message": f"Virtual vessel '{vessel_id}' not found in active fleet",
            }
        v = self.runner.generator.vessels[vessel_id]
        tracker = self.processor.vessel_trackers.get(v.synthetic_mmsi)
        eta_payload = tracker.last_response.to_dict() if (tracker and tracker.last_response) else None

        return 200, {
            "virtual_vessel_id": v.virtual_vessel_id,
            "synthetic_mmsi": v.synthetic_mmsi,
            "vessel_name": v.vessel_name,
            "route_id": v.route_id,
            "corridor": v.corridor,
            "origin_terminal": v.origin_terminal,
            "dest_terminal": v.dest_terminal,
            "nominal_speed_knots": v.nominal_speed_knots,
            "latitude": v.current_lat,
            "longitude": v.current_lon,
            "sog_knots": v.current_sog_knots,
            "cog_degrees": v.current_cog_degrees,
            "distance_traveled_m": round(v.current_distance_traveled_m, 1),
            "total_route_distance_m": round(v.total_route_distance_m, 1),
            "is_arrived": v.is_arrived,
            "eta_prediction": eta_payload,
            "data_provenance": "SIMULATED_SYNTHETIC",
        }

    def handle_simulation_control_post(self, action: str, params: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
        """Handles POST /api/v1/simulation/control."""
        if not self.runner:
            return 503, {"error": True, "message": "No VirtualFleetRunner attached to service"}

        params = params or {}
        action = action.lower()
        if action == "start":
            multiplier = float(params.get("speed_multiplier", 1.0))
            self.runner.start(speed_multiplier=multiplier)
            return 200, {"action": "start", "status": "RUNNING", "speed_multiplier": multiplier}
        elif action == "stop":
            self.runner.stop()
            return 200, {"action": "stop", "status": "STOPPED"}
        elif action == "pause":
            self.runner.pause()
            return 200, {"action": "pause", "status": "PAUSED"}
        elif action == "resume":
            self.runner.resume()
            return 200, {"action": "resume", "status": "RUNNING"}
        elif action == "reset":
            for vid in self.runner.generator.get_vessel_ids():
                self.runner.generator.reset_vessel(vid)
            self.processor.vessel_trackers.clear()
            self.processor.seen_message_ids.clear()
            return 200, {"action": "reset", "status": "RESET_COMPLETE"}
        else:
            return 400, {"error": True, "error_code": "INVALID_SIMULATION_ACTION", "action": action}

    def handle_scenario_trigger_post(self, scenario_id: str) -> Tuple[int, Dict[str, Any]]:
        """Handles POST /api/v1/simulation/scenario/{scenario_id}."""
        if not self.runner:
            return 503, {"error": True, "message": "No VirtualFleetRunner attached to service"}
        if scenario_id not in self.runner.scenarios:
            return 404, {"error": True, "error_code": "UNKNOWN_SCENARIO", "scenario_id": scenario_id}

        result = self.runner.run_scenario(scenario_id)
        return 200, result


class MockAPIClient:
    """Executable test client simulating mobile/web passenger queries and operator feed."""

    def __init__(self, service: MockAPIService):
        self.service = service

    def push_telemetry(self, raw_event: Dict[str, Any], sim_time: Optional[str] = None) -> Dict[str, Any]:
        status, body = self.service.handle_telemetry_post(raw_event, current_sim_time=sim_time)
        return {"status_code": status, "body": body}

    def query_eta(self, mmsi: int, client_time: Optional[str] = None) -> Dict[str, Any]:
        status, body = self.service.handle_eta_get(mmsi, client_request_time=client_time)
        return {"status_code": status, "body": body}

    def get_simulation_status(self) -> Dict[str, Any]:
        status, body = self.service.handle_simulation_status_get()
        return {"status_code": status, "body": body}

    def list_vessels(self) -> Dict[str, Any]:
        status, body = self.service.handle_vessels_get()
        return {"status_code": status, "body": body}

    def get_vessel_detail(self, vessel_id: str) -> Dict[str, Any]:
        status, body = self.service.handle_vessel_detail_get(vessel_id)
        return {"status_code": status, "body": body}

    def control_simulation(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        status, body = self.service.handle_simulation_control_post(action, params=params)
        return {"status_code": status, "body": body}

    def trigger_scenario(self, scenario_id: str) -> Dict[str, Any]:
        status, body = self.service.handle_scenario_trigger_post(scenario_id)
        return {"status_code": status, "body": body}
