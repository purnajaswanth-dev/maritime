"""Internal FastAPI Daemon for Where Is My Ferry? Virtual Maritime Simulation & ML Inference.

Bound strictly to loopback 127.0.0.1:8000.
Exposes internal REST endpoints consumed by the Spring Boot gateway:
- GET  /internal/v1/health: Liveness, model provenance, and runner status.
- GET  /internal/v1/status: Simulation clock, speed multiplier, active scenario, event counters.
- GET  /internal/v1/fleet/snapshot: Real-time telemetry, coordinates, and ETA states for all virtual vessels.
- GET  /internal/v1/vessels/{vessel_id}/eta: Deep prediction provenance and state-machine transitions.
- POST /internal/v1/simulation/control: Lifecycle controls (start, stop, pause, resume, reset, speed).
- POST /internal/v1/simulation/scenarios/{scenario_id}: Adversarial and operational scenario triggers.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.models.evaluate_phase05 import (
    VectorizedRidgeETAModel,
    ModelArtifactTamperedError,
    UnsupportedModelSchemaVersionError,
)
from src.simulation.virtual_ais_generator import VirtualAISGenerator
from src.simulation.virtual_fleet_runner import VirtualFleetRunner
from src.streaming.eta_stream_processor import ETAStreamProcessor


# -----------------------------------------------------------------------------
# Pydantic Request & Response Schemas
# -----------------------------------------------------------------------------

class SimulationControlRequest(BaseModel):
    action: Literal["start", "stop", "pause", "resume", "reset", "speed"]
    speed_multiplier: Optional[float] = Field(default=None, gt=0.0, le=100.0)


class HealthResponse(BaseModel):
    status: Literal["HEALTHY", "DEGRADED", "UNAVAILABLE"]
    timestamp_utc: str
    model_loaded: bool
    model_name: Optional[str] = None
    model_alpha: Optional[float] = None
    model_weights_sha256: Optional[str] = None
    artifact_path: Optional[str] = None
    simulation_running: bool
    active_vessels_count: int


class StatusResponse(BaseModel):
    simulation_available: bool
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
    mode: Optional[str] = None
    provenance: str = "SIMULATED_LOCAL_MARITIME_ENGINE"


class VesselTelemetrySnapshot(BaseModel):
    vessel_id: str
    synthetic_mmsi: int
    name: str
    operator: str
    corridor: str
    origin_terminal_id: str
    destination_terminal_id: str
    lat: float
    lon: float
    sog_knots: float
    cog_degrees: float
    eta_lifecycle_state: str
    position_timestamp_utc: str
    prediction_timestamp_utc: Optional[str] = None
    predicted_arrival_utc: Optional[str] = None
    estimated_remaining_minutes: Optional[float] = None
    telemetry_age_seconds: float
    is_stale: bool
    is_arrived: bool
    data_provenance: str = "SIMULATED_SYNTHETIC"


class FleetSnapshotResponse(BaseModel):
    total_vessels: int
    timestamp_utc: str
    vessels: List[VesselTelemetrySnapshot]


class PredictionProvenanceResponse(BaseModel):
    schema_version: str = "1.0.0"
    vessel_id: str
    vessel_name: str
    synthetic_mmsi: int
    corridor: str
    timestamps: Dict[str, Any]
    predictions: Dict[str, Any]
    lifecycle: Dict[str, Any]
    provenance: Dict[str, Any]


# -----------------------------------------------------------------------------
# Global Service Container
# -----------------------------------------------------------------------------

class MaritimeServiceContainer:
    """Encapsulates the model, stream processor, and virtual fleet runner instances."""

    def __init__(self, artifact_path: Optional[Path] = None):
        self.artifact_path = artifact_path or (repo_root / "models" / "vectorized_ridge_model.json")
        self.model: Optional[VectorizedRidgeETAModel] = None
        self.processor: Optional[ETAStreamProcessor] = None
        self.generator: Optional[VirtualAISGenerator] = None
        self.runner: Optional[VirtualFleetRunner] = None
        self.model_metadata: Dict[str, Any] = {}
        self.load_error: Optional[str] = None

    def initialize(self):
        """Loads frozen model and connects to stream processor and simulation runner."""
        if os.getenv("SIMULATION_FORCE_MODEL_FAILURE") == "1":
            self.load_error = "SIMULATION_FORCE_MODEL_FAILURE simulated fault injection active"
            self.model = None
            return

        try:
            self.model = VectorizedRidgeETAModel.load_artifact(self.artifact_path)
            with open(self.artifact_path, "r", encoding="utf-8") as f:
                artifact_json = json.load(f)
            self.model_metadata = {
                "model_name": artifact_json.get("metadata", {}).get("model_name", "VectorizedRidgeETAModel"),
                "alpha": artifact_json.get("metadata", {}).get("alpha", 10.0),
                "weights_sha256": artifact_json.get("weights", {}).get("weights_sha256", ""),
                "artifact_path": str(self.artifact_path),
            }
            self.load_error = None
        except Exception as e:
            self.model = None
            self.load_error = str(e)
            return

        # Initialize processor with frozen model
        self.processor = ETAStreamProcessor(model=self.model)
        self.generator = VirtualAISGenerator()

        # Initialize timetable-driven historical replay runner
        try:
            from src.replay.replay_runner import ReplayRunner
            self.replay_runner = ReplayRunner(processor=self.processor)
        except Exception:
            self.replay_runner = None

        self.runner = VirtualFleetRunner(
            generator=self.generator,
            processor=self.processor,
            replay_runner=self.replay_runner,
        )

        # Pre-step all vessels once so initial telemetry is immediately populated
        for v_id in self.generator.get_vessel_ids():
            self.runner.step_vessel(v_id)

        # Auto-start runner loop when daemon server is launched
        if os.getenv("AUTO_START_SIMULATION", "0") == "1":
            self.runner.start(speed_multiplier=2.0)


container = MaritimeServiceContainer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes service on startup; cleanly terminates simulation on shutdown."""
    container.initialize()
    yield
    if container.runner and container.runner.is_running:
        container.runner.stop()


app = FastAPI(
    title="Where Is My Ferry? Maritime Simulation & Inference Daemon",
    version="1.0.0",
    description="Internal ML inference and virtual maritime fleet daemon bound strictly to 127.0.0.1:8000.",
    lifespan=lifespan,
)


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@app.get("/health", tags=["Diagnostics"], summary="Liveness probe")
@app.get(
    "/internal/v1/health",
    response_model=HealthResponse,
    tags=["Diagnostics"],
    summary="Health and model provenance check",
)
def get_health():
    """Checks process liveness, model load status, and frozen weight integrity."""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if container.model is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "UNAVAILABLE",
                "timestamp_utc": now_iso,
                "model_loaded": False,
                "error": container.load_error or "Model artifact not loaded",
                "simulation_running": False,
                "active_vessels_count": 0,
            },
        )

    is_running = container.runner.is_running if container.runner else False
    vessels_count = len(container.generator.get_vessel_ids()) if container.generator else 0

    return HealthResponse(
        status="HEALTHY",
        timestamp_utc=now_iso,
        model_loaded=True,
        model_name=container.model_metadata.get("model_name"),
        model_alpha=container.model_metadata.get("alpha"),
        model_weights_sha256=container.model_metadata.get("weights_sha256"),
        artifact_path=container.model_metadata.get("artifact_path"),
        simulation_running=is_running,
        active_vessels_count=vessels_count,
    )


@app.get(
    "/internal/v1/status",
    response_model=StatusResponse,
    tags=["Simulation"],
    summary="Operational simulation status",
)
def get_status():
    """Returns simulation clock, speed multiplier, and event processing counters."""
    if not container.runner or container.model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulation engine unavailable or model failed to load",
        )

    status_obj = container.runner.get_status()
    return StatusResponse(
        simulation_available=True,
        run_id=status_obj.run_id,
        is_running=status_obj.is_running,
        is_paused=status_obj.is_paused,
        sim_time_utc=status_obj.sim_time_utc,
        speed_multiplier=status_obj.speed_multiplier,
        step_interval_s=status_obj.step_interval_s,
        total_events_generated=status_obj.total_events_generated,
        total_events_processed=status_obj.total_events_processed,
        active_vessels_count=status_obj.active_vessels_count,
        active_scenario_id=status_obj.active_scenario_id,
        mode=status_obj.mode,
        provenance="SIMULATED_LOCAL_MARITIME_ENGINE",
    )


@app.get(
    "/internal/v1/fleet/snapshot",
    response_model=FleetSnapshotResponse,
    tags=["Fleet"],
    summary="Live virtual fleet snapshot",
)
def get_fleet_snapshot():
    """Returns real-time coordinates, telemetry, and ETA predictions for all active virtual vessels."""
    if not container.runner or not container.generator or container.model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulation engine or model inference pipeline unavailable",
        )

    now_dt = container.runner.current_sim_time
    now_iso = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    vessels_list: List[VesselTelemetrySnapshot] = []

    for vid, v in container.generator.vessels.items():
        tracker = container.processor.vessel_trackers.get(v.synthetic_mmsi) if container.processor else None
        last_resp = tracker.last_response if tracker else None

        is_arrived = v.is_arrived
        if tracker and tracker.latest_event_epoch_s is not None:
            freshness_sec = max(0.0, now_dt.timestamp() - tracker.latest_event_epoch_s)
        else:
            freshness_sec = last_resp.data_freshness_seconds if last_resp else 0.0

        is_stale = (freshness_sec > 600.0) if not is_arrived else False

        if is_arrived:
            lifecycle_state = "ARRIVED"
        elif is_stale:
            lifecycle_state = "STALE"
        else:
            lifecycle_state = last_resp.eta_lifecycle_state if last_resp else "SCHEDULED"

        pred_utc = last_resp.prediction_timestamp_utc if last_resp else None
        arr_utc = last_resp.predicted_arrival_timestamp_utc if last_resp else None
        rem_min = last_resp.estimated_remaining_minutes if last_resp else None

        vessels_list.append(
            VesselTelemetrySnapshot(
                vessel_id=vid,
                synthetic_mmsi=v.synthetic_mmsi,
                name=v.vessel_name,
                operator="Penn ar Bed (Simulated Fleet)",
                corridor=v.corridor,
                origin_terminal_id=v.origin_terminal,
                destination_terminal_id=v.dest_terminal,
                lat=round(v.current_lat, 5),
                lon=round(v.current_lon, 5),
                sog_knots=round(v.current_sog_knots, 1),
                cog_degrees=round(v.current_cog_degrees, 1),
                eta_lifecycle_state=lifecycle_state,
                position_timestamp_utc=now_iso,
                prediction_timestamp_utc=pred_utc,
                predicted_arrival_utc=arr_utc,
                estimated_remaining_minutes=rem_min,
                telemetry_age_seconds=round(freshness_sec, 1),
                is_stale=is_stale,
                is_arrived=is_arrived,
                data_provenance="SIMULATED_SYNTHETIC",
            )
        )

    return FleetSnapshotResponse(
        total_vessels=len(vessels_list),
        timestamp_utc=now_iso,
        vessels=vessels_list,
    )


@app.get(
    "/internal/v1/vessels/{vessel_id}/eta",
    response_model=PredictionProvenanceResponse,
    tags=["Fleet"],
    summary="Deep prediction provenance for a single vessel",
)
def get_vessel_eta(vessel_id: str):
    """Returns authoritative ETA prediction, state-machine metadata, and model provenance for a single vessel."""
    if not container.runner or not container.generator or container.model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulation engine or model inference pipeline unavailable",
        )

    vessel = container.generator.vessels.get(vessel_id)
    if not vessel:
        # Check by vessel_name or synthetic_mmsi
        for v in container.generator.vessels.values():
            if v.vessel_name == vessel_id or str(v.synthetic_mmsi) == str(vessel_id):
                vessel = v
                break

    if not vessel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Virtual vessel '{vessel_id}' not found in active simulation",
        )

    tracker = container.processor.vessel_trackers.get(vessel.synthetic_mmsi) if container.processor else None
    last_resp = tracker.last_response if tracker else None

    if not last_resp:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No active ETA prediction produced for vessel '{vessel_id}'",
        )

    now_dt = container.runner.current_sim_time
    if tracker and tracker.latest_event_epoch_s is not None:
        telemetry_age = max(0.0, now_dt.timestamp() - tracker.latest_event_epoch_s)
    else:
        telemetry_age = last_resp.data_freshness_seconds

    is_arrived = vessel.is_arrived
    is_stale = (telemetry_age > 600.0) if not is_arrived else False

    if is_arrived:
        state_val = "ARRIVED"
    elif is_stale:
        state_val = "STALE"
    else:
        state_val = last_resp.eta_lifecycle_state

    return PredictionProvenanceResponse(
        schema_version="1.0.0",
        vessel_id=vessel.virtual_vessel_id,
        vessel_name=vessel.vessel_name,
        synthetic_mmsi=vessel.synthetic_mmsi,
        corridor=vessel.corridor,
        timestamps={
            "position_timestamp_utc": last_resp.latest_observation_timestamp_utc,
            "prediction_timestamp_utc": last_resp.prediction_timestamp_utc,
            "predicted_arrival_utc": last_resp.predicted_arrival_timestamp_utc,
            "telemetry_age_seconds": round(telemetry_age, 1),
        },
        predictions={
            "raw_model_remaining_minutes": last_resp.raw_model_remaining_minutes,
            "displayed_remaining_minutes": last_resp.estimated_remaining_minutes,
            "uncertainty_lower_minutes": last_resp.uncertainty_lower_minutes,
            "uncertainty_upper_minutes": last_resp.uncertainty_upper_minutes,
            "unexpected_jump_minutes": last_resp.unexpected_jump_minutes,
        },
        lifecycle={
            "eta_lifecycle_state": state_val,
            "reason_code": last_resp.reason_code,
            "is_stale": is_stale,
            "is_arrived": is_arrived,
        },
        provenance={
            "is_synthetic": True,
            "model_name": container.model_metadata.get("model_name", "VectorizedRidgeETAModel"),
            "model_type": "L2_RIDGE_LINEAR",
            "alpha": container.model_metadata.get("alpha", 10.0),
            "weight_checksum_sha256": container.model_metadata.get("weights_sha256", ""),
            "prediction_source": "ML_MODEL_INFERENCE",
        },
    )


@app.post(
    "/internal/v1/simulation/control",
    tags=["Simulation"],
    summary="Controls simulation runner lifecycle",
)
def post_simulation_control(req: SimulationControlRequest):
    """Applies start, stop, pause, resume, reset, or speed multiplier changes."""
    if not container.runner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulation runner is not initialized",
        )

    action = req.action.lower()

    if action == "start":
        mult = req.speed_multiplier if req.speed_multiplier is not None else container.runner.speed_multiplier
        container.runner.start(speed_multiplier=mult)
        return {
            "status": "SUCCESS",
            "current_action": "start",
            "is_running": True,
            "is_paused": False,
            "speed_multiplier": mult,
        }

    elif action == "stop":
        container.runner.stop()
        return {
            "status": "SUCCESS",
            "current_action": "stop",
            "is_running": False,
            "is_paused": False,
        }

    elif action == "pause":
        container.runner.pause()
        return {
            "status": "SUCCESS",
            "current_action": "pause",
            "is_running": container.runner.is_running,
            "is_paused": True,
        }

    elif action == "resume":
        container.runner.resume()
        return {
            "status": "SUCCESS",
            "current_action": "resume",
            "is_running": container.runner.is_running,
            "is_paused": False,
        }

    elif action == "speed":
        if req.speed_multiplier is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Action 'speed' requires a valid 'speed_multiplier' (> 0.0, <= 100.0)",
            )
        with container.runner._lock:
            container.runner.speed_multiplier = req.speed_multiplier
        return {
            "status": "SUCCESS",
            "current_action": "speed",
            "is_running": container.runner.is_running,
            "is_paused": container.runner.is_paused,
            "speed_multiplier": req.speed_multiplier,
        }

    elif action == "reset":
        container.runner.reset()
        container.generator = container.runner.generator
        container.processor = container.runner.processor
        return {
            "status": "SUCCESS",
            "current_action": "reset",
            "is_running": False,
            "is_paused": False,
            "message": "Simulation reset to initial dock state",
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported action: {req.action}",
    )


@app.post(
    "/internal/v1/simulation/scenarios/{scenario_id}",
    tags=["Simulation"],
    summary="Triggers simulation scenarios",
)
def post_scenario_trigger(scenario_id: str):
    """Applies scenario fault injection to active simulation runner."""
    if not container.runner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Simulation runner is not initialized",
        )

    target_sc_id = scenario_id
    if target_sc_id not in container.runner.scenarios:
        # Resolve aliases like scenario-1, scenario_1, or 1 -> SCENARIO_01_...
        suffix = scenario_id.replace("scenario-", "").replace("scenario_", "").replace("SCENARIO_", "")
        if suffix.isdigit():
            padded = suffix.zfill(2)
            for k in container.runner.scenarios.keys():
                if f"SCENARIO_{padded}" in k or f"scenario_{padded}" in k.lower():
                    target_sc_id = k
                    break

    if target_sc_id not in container.runner.scenarios:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found. Available scenarios: {list(container.runner.scenarios.keys())[:5]}...",
        )

    sc_def = container.runner.scenarios[target_sc_id]
    container.runner.active_scenario_id = target_sc_id

    # If scenario specifies target vessel and speed override, apply immediately
    target_vessel = sc_def.get("vessel_id")
    if target_vessel and target_vessel in container.generator.vessels:
        fault = sc_def.get("fault_type")
        gap = sc_def.get("gap_seconds", 0)
        if gap > 0:
            container.runner.advance_clock(gap)
        elif fault == "CONFIRMED_ARRIVAL":
            v = container.generator.vessels[target_vessel]
            v.current_distance_traveled_m = v.total_route_distance_m - 50.0
            v.current_lat = v.waypoints[-1][0]
            v.current_lon = v.waypoints[-1][1]
            v.is_arrived = True
            for _ in range(3):
                container.runner.step_vessel(target_vessel, speed_override=0.1, scenario_id=target_sc_id)
                container.runner.advance_clock(60)
        else:
            container.runner.step_vessel(
                vessel_id=target_vessel,
                speed_override=sc_def.get("speed_override_knots"),
                scenario_id=target_sc_id,
            )

    return {
        "status": "APPLIED",
        "scenario_id": target_sc_id,
        "title": sc_def.get("title", sc_def.get("name", target_sc_id)),
        "target_vessel": target_vessel,
    }


# -----------------------------------------------------------------------------
# Timetable & Historical Replay Endpoints (Phase 02)
# -----------------------------------------------------------------------------

@app.get(
    "/internal/v1/timetable/today",
    tags=["Timetable"],
    summary="Today's scheduled departures from timetable",
)
def get_timetable_today():
    """Returns today's scheduled departures expanded from the GTFS timetable."""
    if not container.replay_runner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Historical replay runner is not initialized",
        )
    return {
        "date": container.replay_runner.sim_date.strftime("%Y-%m-%d"),
        "total_departures": len(container.replay_runner.departures),
        "departures": container.replay_runner.get_timetable_today(),
    }


@app.get(
    "/internal/v1/departures",
    tags=["Departures"],
    summary="List all departures and operational statuses for today",
)
def get_departures():
    """Returns all departures for today with operational replay statuses and ground truth."""
    if not container.replay_runner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Historical replay runner is not initialized",
        )
    return {
        "date": container.replay_runner.sim_date.strftime("%Y-%m-%d"),
        "total_departures": len(container.replay_runner.departures),
        "departures": container.replay_runner.get_departures(),
    }


@app.get(
    "/internal/v1/departures/{departure_id}/live",
    tags=["Departures"],
    summary="Live vessel state, ETA, and model provenance for departure",
)
def get_departure_live(departure_id: str):
    """Returns live telemetry, ETA predictions, and weight checksum for a specific departure."""
    if not container.replay_runner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Historical replay runner is not initialized",
        )
    res = container.replay_runner.get_departure_live(departure_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Departure '{departure_id}' not found",
        )
    return res


@app.get(
    "/internal/v1/departures/{departure_id}/track",
    tags=["Departures"],
    summary="Coordinates track so far for departure",
)
def get_departure_track(departure_id: str):
    """Returns breadcrumb coordinates path so far for active or completed departure."""
    if not container.replay_runner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Historical replay runner is not initialized",
        )
    res = container.replay_runner.get_departure_track(departure_id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Departure '{departure_id}' not found",
        )
    return res


@app.get(
    "/internal/v1/accuracy",
    tags=["ML Diagnostics"],
    summary="Predicted vs actual accuracy records for completed departures",
)
def get_accuracy():
    """Returns historical prediction snapshots vs actual ground truth arrivals."""
    if not container.replay_runner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Historical replay runner is not initialized",
        )
    return {
        "total_completed": len(container.replay_runner.completed_departures),
        "accuracy_records": container.replay_runner.get_accuracy_records(),
    }


# -----------------------------------------------------------------------------
# Main Execution Entrypoint (Loopback Only)
# -----------------------------------------------------------------------------

def run_daemon(host: str = "127.0.0.1", port: int = 8000):
    """Starts Uvicorn server bound strictly to loopback interface."""
    import uvicorn

    if host not in ("127.0.0.1", "localhost"):
        raise ValueError(f"SECURITY VIOLATION: Internal daemon may only bind to 127.0.0.1, not '{host}'!")

    os.environ.setdefault("AUTO_START_SIMULATION", "1")
    print(f"Starting Where Is My Ferry? Internal Maritime Daemon on http://{host}:{port} (Loopback Only)...")
    uvicorn.run(app, host=host, port=port, reload=False, log_level="info")


if __name__ == "__main__":
    run_daemon()
