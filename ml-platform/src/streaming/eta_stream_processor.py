"""Integrated Streaming ETA Processor for Where Is My Ferry?

Connects incoming AIS-like event telemetry to feature derivation,
the trained Ridge ETA model, and the 6-state ETA lifecycle machine.
"""

from collections import deque
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.ingestion.trajectory_segmenter import TERMINALS, haversine_m
from src.models.eta_state_machine import (
    ETAState,
    ETAStateMachine,
    ObservationTelemetry,
    ETAPredictionSnapshot,
)
from src.models.evaluate_phase05 import VectorizedRidgeETAModel
from src.streaming.event_schema import (
    IncomingAISEvent,
    ETAResponsePayload,
    validate_ais_event,
    parse_utc_timestamp,
)


HISTORICAL_VESSEL_MAP: Dict[str, str] = {
    "V-FROMVEUR-SIM": "FROMVEUR II",
    "SIM_FROMVEUR_EXPRESS": "FROMVEUR II",
    "V-AZENOR-SIM": "ANDRE COLIN",
    "SIM_AZENOR_VOYAGER": "ANDRE COLIN",
    "V-OUESSANT-SIM": "ENEZ EUSSA 3",
    "SIM_IROISE_STAR": "ENEZ EUSSA 3",
    "V-SEIN-SIM": "ENEZ SUN 3",
    "SIM_SEIN_SHUTTLE": "ENEZ SUN 3",
}


class ActiveVesselTracker:
    """Maintains active journey tracking and state machine for a single vessel."""

    def __init__(self, mmsi: int, vessel_name: str, corridor: str, dest_terminal: str, historical_vessel_name: Optional[str] = None):
        self.mmsi = mmsi
        self.vessel_name = vessel_name
        self.historical_vessel_name = historical_vessel_name or HISTORICAL_VESSEL_MAP.get(vessel_name)
        self.corridor = corridor
        self.dest_terminal = dest_terminal
        dest_coords = TERMINALS.get(dest_terminal, {"lat": 48.3811, "lon": -4.4857})
        self.dest_lat = dest_coords["lat"]
        self.dest_lon = dest_coords["lon"]
        self.berth_radius_m = dest_coords.get("radius_m", 400.0)

        # State machine
        self.voyage_id = f"STREAM-{mmsi}-{int(time.time())}"
        self.state_machine = ETAStateMachine(
            voyage_id=self.voyage_id,
            vessel_name=vessel_name,
            corridor=corridor,
            berth_radius_m=self.berth_radius_m,
            stale_threshold_seconds=600.0,
        )

        # Temporal tracking
        self.departure_epoch_s: Optional[float] = None
        self.latest_event_epoch_s: Optional[float] = None
        self.observation_count: int = 0
        self.last_response: Optional[ETAResponsePayload] = None


class ETAStreamProcessor:
    """Core real-time stream processor for ferry ETA prediction."""

    def __init__(
        self,
        model: Optional[VectorizedRidgeETAModel] = None,
        snapshots_path: Optional[Path] = None,
        diagnostics_log_path: Optional[Path] = None,
        reset_diagnostics: bool = False,
    ):
        self.snapshots_path = snapshots_path or (repo_root / "data" / "processed" / "phase_05_prediction_snapshots.parquet")
        self.diagnostics_log_path = diagnostics_log_path or (repo_root / "data" / "manifests" / "phase-07-stream-diagnostics.jsonl")

        # Initialize or train model
        if model is not None:
            self.model = model
        else:
            self.model = self._train_baseline_ridge()

        # In-memory deduplication and vessel registries
        self.seen_message_ids: set = set()
        self.vessel_trackers: Dict[Any, ActiveVesselTracker] = {}
        self.processing_latencies_ms: List[float] = []

        # Ensure diagnostics directory exists
        self.diagnostics_log_path.parent.mkdir(parents=True, exist_ok=True)
        if reset_diagnostics and self.diagnostics_log_path.exists():
            self.diagnostics_log_path.unlink()

    def _train_baseline_ridge(self) -> VectorizedRidgeETAModel:
        """Trains VectorizedRidgeETAModel on Protocol 1 training partition."""
        if not self.snapshots_path.exists():
            # Fallback dummy model for lightweight unit tests if parquet missing
            m = VectorizedRidgeETAModel(alpha=10.0)
            return m

        df_snaps = pd.read_parquet(self.snapshots_path)
        # Training split: dep_timestamp < 2016-02-01
        train_mask = pd.to_datetime(df_snaps["prediction_timestamp_utc"]) < "2016-02-01T00:00:00Z"
        df_train = df_snaps[train_mask].copy()

        model = VectorizedRidgeETAModel(alpha=10.0)
        y_train = df_train["target_remaining_travel_time_minutes"].values
        model.fit(df_train, y_train)
        return model

    def _log_diagnostic(self, record: Dict[str, Any]):
        """Appends structured diagnostic record to JSONL log."""
        record["logged_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(self.diagnostics_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def _infer_corridor_and_dest(self, lat: float, lon: float, vessel_name: str, cog: Optional[float] = None) -> Tuple[str, str]:
        """Infers active corridor and destination terminal based on position, vessel, and course."""
        # Audierne - Sein corridor
        if "SUN" in vessel_name or lat < 48.2:
            # If moving West (cog between 200 and 340) -> heading to ILE_DE_SEIN
            if cog is not None and (200.0 <= cog <= 340.0):
                return "AUDIERNE_ILE_DE_SEIN", "ILE_DE_SEIN"
            elif cog is not None and (20.0 <= cog <= 160.0):
                return "ILE_DE_SEIN_AUDIERNE", "AUDIERNE"
            d_aud = haversine_m(lat, lon, TERMINALS["AUDIERNE"]["lat"], TERMINALS["AUDIERNE"]["lon"])
            d_sein = haversine_m(lat, lon, TERMINALS["ILE_DE_SEIN"]["lat"], TERMINALS["ILE_DE_SEIN"]["lon"])
            if d_aud < d_sein:
                return "ILE_DE_SEIN_AUDIERNE", "AUDIERNE"
            return "AUDIERNE_ILE_DE_SEIN", "ILE_DE_SEIN"

        # Brest - Le Conquet - Molene - Ouessant
        # If moving East (cog between 45 and 135) -> heading to BREST
        if cog is not None and (45.0 <= cog <= 135.0):
            return "LE_CONQUET_BREST", "BREST"
        elif cog is not None and (225.0 <= cog <= 315.0):
            d_ouess = haversine_m(lat, lon, TERMINALS["OUESSANT_STIFF"]["lat"], TERMINALS["OUESSANT_STIFF"]["lon"])
            d_conquet = haversine_m(lat, lon, TERMINALS["LE_CONQUET"]["lat"], TERMINALS["LE_CONQUET"]["lon"])
            if d_ouess < d_conquet:
                return "BREST_OUESSANT_STIFF", "OUESSANT_STIFF"
            return "BREST_LE_CONQUET", "LE_CONQUET"

        # Coordinate distance heuristic fallback
        d_brest = haversine_m(lat, lon, TERMINALS["BREST"]["lat"], TERMINALS["BREST"]["lon"])
        d_conquet = haversine_m(lat, lon, TERMINALS["LE_CONQUET"]["lat"], TERMINALS["LE_CONQUET"]["lon"])
        d_ouess = haversine_m(lat, lon, TERMINALS["OUESSANT_STIFF"]["lat"], TERMINALS["OUESSANT_STIFF"]["lon"])

        if d_brest < d_conquet and d_brest < d_ouess:
            return "LE_CONQUET_BREST", "BREST"
        elif d_ouess < d_conquet:
            return "BREST_OUESSANT_STIFF", "OUESSANT_STIFF"
        else:
            return "BREST_LE_CONQUET", "LE_CONQUET"

    def process_event(self, raw_payload: Dict[str, Any], current_sim_time_utc: Optional[str] = None) -> Tuple[Optional[ETAResponsePayload], Optional[str]]:
        """Processes an incoming AIS event through the end-to-end pipeline."""
        start_t = time.perf_counter()

        # 1. Validate Schema
        event, val_err = validate_ais_event(raw_payload)
        if val_err:
            self._log_diagnostic({
                "event_type": "VALIDATION_REJECTED",
                "error_reason": val_err,
                "raw_payload": raw_payload,
            })
            return None, val_err

        # 2. Deduplication Check
        tracker_key = raw_payload.get("voyage_id") or event.mmsi
        if event.message_id in self.seen_message_ids:
            self._log_diagnostic({
                "event_type": "DUPLICATE_DROPPED",
                "message_id": event.message_id,
                "mmsi": event.mmsi,
            })
            tracker = self.vessel_trackers.get(tracker_key) or self.vessel_trackers.get(event.mmsi)
            if tracker and tracker.last_response:
                return tracker.last_response, None
            return None, "DUPLICATE_MESSAGE_ID"

        self.seen_message_ids.add(event.message_id)

        # 3. Retrieve or Initialize Active Vessel Tracker
        dt_event = parse_utc_timestamp(event.event_timestamp_utc)
        event_epoch_s = dt_event.timestamp()

        tracker = self.vessel_trackers.get(tracker_key)
        if tracker is None:
            corridor = raw_payload.get("corridor")
            dest_terminal = raw_payload.get("dest_terminal")
            if not corridor or not dest_terminal:
                corridor, dest_terminal = self._infer_corridor_and_dest(
                    event.latitude, event.longitude, event.vessel_name, event.cog_degrees
                )
            historical_vessel_name = (
                raw_payload.get("historical_vessel_name")
                or HISTORICAL_VESSEL_MAP.get(event.vessel_name)
                or HISTORICAL_VESSEL_MAP.get(tracker_key)
            )
            tracker = ActiveVesselTracker(
                event.mmsi,
                event.vessel_name,
                corridor,
                dest_terminal,
                historical_vessel_name=historical_vessel_name,
            )
            tracker.departure_epoch_s = event_epoch_s
            self.vessel_trackers[tracker_key] = tracker
            self.vessel_trackers[event.mmsi] = tracker

        # 4. Out-of-Order Telemetry Check
        is_out_of_order = False
        if tracker.latest_event_epoch_s is not None and event_epoch_s < tracker.latest_event_epoch_s:
            is_out_of_order = True
            self._log_diagnostic({
                "event_type": "OUT_OF_ORDER_TELEMETRY",
                "mmsi": event.mmsi,
                "message_id": event.message_id,
                "event_timestamp_utc": event.event_timestamp_utc,
                "latest_event_timestamp_utc": datetime.fromtimestamp(tracker.latest_event_epoch_s, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
            # Per contract: Process for audit but DO NOT rewind watermark
        else:
            tracker.latest_event_epoch_s = event_epoch_s

        tracker.observation_count += 1

        # 5. Feature Derivation (strictly causal)
        dist_to_dest_m = haversine_m(event.latitude, event.longitude, tracker.dest_lat, tracker.dest_lon)
        elapsed_min = max(0.0, (event_epoch_s - (tracker.departure_epoch_s or event_epoch_s)) / 60.0)

        # Reference time for prediction: current_sim_time_utc or event's receipt time
        ref_time_str = current_sim_time_utc or event.receipt_timestamp_utc
        dt_ref = parse_utc_timestamp(ref_time_str)
        ref_epoch_s = dt_ref.timestamp() if dt_ref else event_epoch_s
        freshness_s = max(0.0, ref_epoch_s - event_epoch_s)

        hist_name = (
            raw_payload.get("historical_vessel_name")
            or tracker.historical_vessel_name
            or HISTORICAL_VESSEL_MAP.get(event.vessel_name)
            or HISTORICAL_VESSEL_MAP.get(tracker_key)
            or event.vessel_name
        )

        # Single-row DataFrame for model inference
        df_feature = pd.DataFrame([{
            "feature_distance_to_dest_m": dist_to_dest_m,
            "elapsed_time_minutes": elapsed_min,
            "feature_sog_knots": event.sog_knots,
            "feature_observations_so_far": tracker.observation_count,
            "data_freshness_seconds": freshness_s,
            "feature_along_track_current_knots": 0.0,
            "corridor": tracker.corridor,
            "vessel_name": hist_name,
        }])

        # 6. Model Inference
        raw_pred = float(self.model.predict(df_feature)[0])

        # 7. State Machine Execution
        obs = ObservationTelemetry(
            timestamp_utc=event.event_timestamp_utc,
            latitude=event.latitude,
            longitude=event.longitude,
            sog_knots=event.sog_knots,
            distance_to_dest_m=dist_to_dest_m,
            received_at_utc=event.receipt_timestamp_utc,
        )

        state_snap: ETAPredictionSnapshot = tracker.state_machine.process_step(
            prediction_timestamp_utc=ref_time_str,
            raw_model_eta_minutes=raw_pred,
            obs=obs,
        )

        latency_ms = (time.perf_counter() - start_t) * 1000.0
        self.processing_latencies_ms.append(latency_ms)

        response = ETAResponsePayload(
            schema_version="1.0.0",
            vessel_name=tracker.vessel_name,
            mmsi=tracker.mmsi,
            corridor=tracker.corridor,
            prediction_timestamp_utc=ref_time_str,
            predicted_arrival_timestamp_utc=state_snap.predicted_arrival_timestamp_utc,
            estimated_remaining_minutes=state_snap.displayed_remaining_minutes,
            raw_model_remaining_minutes=state_snap.raw_remaining_minutes,
            eta_lifecycle_state=state_snap.state.value,
            latest_observation_timestamp_utc=event.event_timestamp_utc,
            data_freshness_seconds=state_snap.data_freshness_seconds,
            is_stale=state_snap.is_stale,
            is_arrived=state_snap.is_arrived,
            uncertainty_lower_minutes=state_snap.uncertainty_lower_minutes,
            uncertainty_upper_minutes=state_snap.uncertainty_upper_minutes,
            unexpected_jump_minutes=state_snap.unexpected_jump_minutes,
            reason_code=state_snap.state_reason,
            processing_latency_ms=round(latency_ms, 3),
        )

        tracker.last_response = response

        # Log transition or state update
        self._log_diagnostic({
            "event_type": "ETA_UPDATE_PRODUCED",
            "message_id": event.message_id,
            "mmsi": event.mmsi,
            "state": state_snap.state.value,
            "displayed_eta_min": state_snap.displayed_remaining_minutes,
            "raw_eta_min": state_snap.raw_remaining_minutes,
            "freshness_seconds": state_snap.data_freshness_seconds,
            "unexpected_jump_min": state_snap.unexpected_jump_minutes,
            "latency_ms": round(latency_ms, 2),
        })

        return response, None
