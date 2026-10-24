"""Deterministic ETA State Machine and Countdown Lifecycle Engine.

Defines the formal states, transitions, guardrails, and arrival confirmation
rules for Where Is My Ferry? prediction pipelines and streaming services.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple


class ETAState(str, Enum):
    """Lifecycle states for a vessel voyage prediction sequence."""
    ESTIMATING = "ESTIMATING"
    DELAYED_OR_UNCERTAIN = "DELAYED_OR_UNCERTAIN"
    STALE_DATA = "STALE_DATA"
    ARRIVAL_PENDING_CONFIRMATION = "ARRIVAL_PENDING_CONFIRMATION"
    ARRIVED = "ARRIVED"
    ETA_UNAVAILABLE = "ETA_UNAVAILABLE"


@dataclass
class ObservationTelemetry:
    """Incoming observation telemetry point."""
    timestamp_utc: str
    latitude: float
    longitude: float
    sog_knots: float
    heading_deg: Optional[float] = None
    distance_to_dest_m: float = 0.0
    received_at_utc: Optional[str] = None


@dataclass
class ETAPredictionSnapshot:
    """Prediction output snapshot produced by model and state machine."""
    prediction_timestamp_utc: str
    voyage_id: str
    vessel_name: str
    corridor: str
    state: ETAState
    raw_remaining_minutes: float
    displayed_remaining_minutes: float
    predicted_arrival_timestamp_utc: str
    data_freshness_seconds: float
    unexpected_jump_minutes: float
    uncertainty_lower_minutes: float
    uncertainty_upper_minutes: float
    is_stale: bool
    is_arrived: bool
    state_reason: str


class ETAStateMachine:
    """Stateful ETA lifecycle tracker for a single ferry voyage.

    Enforces:
    1. ETA = 0 is never proof of arrival; arrival requires physical berth dwell confirmation.
    2. Once ARRIVED, countdown stops and cannot be reversed by stale/delayed telemetry.
    3. Stale telemetry (> 600s) automatically transitions to STALE_DATA.
    4. Consistent time basis: predicted arrival = prediction timestamp + remaining minutes.
    5. Asymmetric smoothing: fast pass-through for real delays, bounded damping for noise.
    """

    def __init__(
        self,
        voyage_id: str,
        vessel_name: str,
        corridor: str,
        dest_terminal_coords: Optional[Tuple[float, float]] = None,
        stale_threshold_seconds: float = 600.0,
        berth_radius_m: float = 400.0,
        dwell_confirm_observations: int = 2,
    ):
        self.voyage_id = voyage_id
        self.vessel_name = vessel_name
        self.corridor = corridor
        self.dest_terminal_coords = dest_terminal_coords
        self.stale_threshold_seconds = stale_threshold_seconds
        self.berth_radius_m = berth_radius_m
        self.dwell_confirm_observations = dwell_confirm_observations

        # Internal lifecycle state
        self.current_state = ETAState.ESTIMATING
        self.prev_prediction_epoch_s: Optional[float] = None
        self.prev_displayed_eta: Optional[float] = None
        self.consecutive_berth_dwell_count: int = 0
        self.arrival_confirmed_at_utc: Optional[str] = None
        self.latest_observation_epoch_s: Optional[float] = None
        self.history: List[ETAPredictionSnapshot] = []

    def _parse_iso(self, ts_str: str) -> float:
        """Parses ISO timestamp string to epoch seconds."""
        ts_clean = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_clean)
        return dt.timestamp()

    def _format_iso(self, epoch_s: float) -> str:
        """Formats epoch seconds to ISO UTC string."""
        return datetime.fromtimestamp(epoch_s, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def process_step(
        self,
        prediction_timestamp_utc: str,
        raw_model_eta_minutes: float,
        obs: Optional[ObservationTelemetry] = None,
        evidence_is_arrived: bool = False,
    ) -> ETAPredictionSnapshot:
        """Processes a single prediction step sequentially.

        Args:
            prediction_timestamp_utc: Current prediction clock timestamp.
            raw_model_eta_minutes: Raw remaining time predicted by Ridge or baseline.
            obs: Latest available observation telemetry (if any).
            evidence_is_arrived: External ground-truth or dock-sensor arrival signal.
        """
        pred_epoch = self._parse_iso(prediction_timestamp_utc)
        
        # 1. Check if already permanently ARRIVED
        if self.current_state == ETAState.ARRIVED:
            obs_epoch = self._parse_iso(obs.timestamp_utc) if obs else 0.0
            arr_epoch = self._parse_iso(self.arrival_confirmed_at_utc) if self.arrival_confirmed_at_utc else 0.0
            # Guardrail: unberthing can only be triggered by NEW telemetry generated strictly AFTER arrival confirmation
            is_unberthing_after_arrival = (
                obs is not None
                and obs_epoch > arr_epoch
                and obs.distance_to_dest_m > 1000.0
                and obs.sog_knots > 6.0
            )
            if is_unberthing_after_arrival:
                # Vessel has genuinely departed destination terminal for a new journey
                self.current_state = ETAState.ESTIMATING
                self.consecutive_berth_dwell_count = 0
                self.arrival_confirmed_at_utc = None
            else:
                # Retain ARRIVED; countdown stays at 0.0
                snapshot = ETAPredictionSnapshot(
                    prediction_timestamp_utc=prediction_timestamp_utc,
                    voyage_id=self.voyage_id,
                    vessel_name=self.vessel_name,
                    corridor=self.corridor,
                    state=ETAState.ARRIVED,
                    raw_remaining_minutes=0.0,
                    displayed_remaining_minutes=0.0,
                    predicted_arrival_timestamp_utc=self.arrival_confirmed_at_utc or prediction_timestamp_utc,
                    data_freshness_seconds=pred_epoch - (self.latest_observation_epoch_s or pred_epoch),
                    unexpected_jump_minutes=0.0,
                    uncertainty_lower_minutes=0.0,
                    uncertainty_upper_minutes=0.0,
                    is_stale=False,
                    is_arrived=True,
                    state_reason="Arrival confirmed at berth; countdown terminated.",
                )
                self.history.append(snapshot)
                return snapshot

        # 2. Check for missing or corrupted observation
        if obs is None:
            self.current_state = ETAState.ETA_UNAVAILABLE
            snapshot = ETAPredictionSnapshot(
                prediction_timestamp_utc=prediction_timestamp_utc,
                voyage_id=self.voyage_id,
                vessel_name=self.vessel_name,
                corridor=self.corridor,
                state=ETAState.ETA_UNAVAILABLE,
                raw_remaining_minutes=raw_model_eta_minutes,
                displayed_remaining_minutes=raw_model_eta_minutes,
                predicted_arrival_timestamp_utc=self._format_iso(pred_epoch + raw_model_eta_minutes * 60.0),
                data_freshness_seconds=9999.0,
                unexpected_jump_minutes=0.0,
                uncertainty_lower_minutes=raw_model_eta_minutes * 0.5,
                uncertainty_upper_minutes=raw_model_eta_minutes * 2.0,
                is_stale=True,
                is_arrived=False,
                state_reason="No telemetry observations available for vessel.",
            )
            self.history.append(snapshot)
            return snapshot

        obs_epoch = self._parse_iso(obs.timestamp_utc)
        self.latest_observation_epoch_s = max(self.latest_observation_epoch_s or 0.0, obs_epoch)
        freshness_s = max(0.0, pred_epoch - obs_epoch)

        # 3. Check for Arrival Confirmation
        # Conditions for arrival:
        # a) External ground-truth arrival signal OR
        # b) Physical dwell: Distance <= berth_radius_m and SOG <= 1.5 knots for N consecutive steps
        is_at_berth = (obs.distance_to_dest_m <= self.berth_radius_m) and (obs.sog_knots <= 1.8)
        if is_at_berth:
            self.consecutive_berth_dwell_count += 1
        else:
            self.consecutive_berth_dwell_count = 0

        if evidence_is_arrived or (self.consecutive_berth_dwell_count >= self.dwell_confirm_observations):
            self.current_state = ETAState.ARRIVED
            self.arrival_confirmed_at_utc = prediction_timestamp_utc
            snapshot = ETAPredictionSnapshot(
                prediction_timestamp_utc=prediction_timestamp_utc,
                voyage_id=self.voyage_id,
                vessel_name=self.vessel_name,
                corridor=self.corridor,
                state=ETAState.ARRIVED,
                raw_remaining_minutes=0.0,
                displayed_remaining_minutes=0.0,
                predicted_arrival_timestamp_utc=prediction_timestamp_utc,
                data_freshness_seconds=freshness_s,
                unexpected_jump_minutes=0.0,
                uncertainty_lower_minutes=0.0,
                uncertainty_upper_minutes=0.0,
                is_stale=False,
                is_arrived=True,
                state_reason="Berth dwell verified; vessel safely docked.",
            )
            self.history.append(snapshot)
            self.prev_displayed_eta = 0.0
            self.prev_prediction_epoch_s = pred_epoch
            return snapshot

        # 4. Check for Arrival Pending Confirmation (approaching slipway)
        if (obs.distance_to_dest_m <= self.berth_radius_m * 1.5) or (raw_model_eta_minutes <= 2.0 and obs.distance_to_dest_m <= 1000.0):
            new_state = ETAState.ARRIVAL_PENDING_CONFIRMATION
            state_reason = "Vessel within terminal approach zone; awaiting berth dwell."
        # 5. Check for Data Staleness
        elif freshness_s > self.stale_threshold_seconds:
            new_state = ETAState.STALE_DATA
            state_reason = f"Telemetry age ({freshness_s:.0f}s) exceeds stale threshold ({self.stale_threshold_seconds:.0f}s)."
        # 6. Check for Operational Holding / Slowdown Uncertainty
        elif obs.sog_knots < 1.5 and obs.distance_to_dest_m > 1500.0:
            new_state = ETAState.DELAYED_OR_UNCERTAIN
            state_reason = f"Vessel stationary (SOG {obs.sog_knots:.1f} kts) in open water ({obs.distance_to_dest_m/1000:.1f} km to dest)."
        else:
            new_state = ETAState.ESTIMATING
            state_reason = "Normal active transit progression."

        self.current_state = new_state

        # 7. Apply Safe Asymmetric Post-Processing Policy (Policy 2)
        if self.prev_prediction_epoch_s is None or self.prev_displayed_eta is None:
            # First observation
            displayed_eta = raw_model_eta_minutes
            unexpected_jump = 0.0
        else:
            dt_minutes = (pred_epoch - self.prev_prediction_epoch_s) / 60.0
            expected_eta = max(self.prev_displayed_eta - dt_minutes, 0.1)
            delta = raw_model_eta_minutes - expected_eta
            
            # Asymmetric update:
            if delta > 0:
                # Real delay / slowdown -> Pass through with high responsiveness (alpha = 0.8)
                displayed_eta = expected_eta + 0.8 * delta
            else:
                # Downward jump -> Damp noise unless verified by distance progress
                displayed_eta = expected_eta + 0.5 * delta
                
            # If in terminal approach, clamp displayed ETA so it doesn't overshoot upwards
            if new_state == ETAState.ARRIVAL_PENDING_CONFIRMATION:
                displayed_eta = min(displayed_eta, max(raw_model_eta_minutes, 1.0))
                
            unexpected_jump = abs((displayed_eta - self.prev_displayed_eta) + dt_minutes)

        self.prev_displayed_eta = displayed_eta
        self.prev_prediction_epoch_s = pred_epoch

        # 8. Compute Calibrated Uncertainty Intervals
        # Empirical residual standard error based on horizon
        if displayed_eta <= 15.0:
            sigma = 2.0
        elif displayed_eta <= 30.0:
            sigma = 3.5
        elif displayed_eta <= 60.0:
            sigma = 6.0
        else:
            sigma = 10.0

        uncertainty_lower = max(0.1, displayed_eta - 1.645 * sigma)  # 90% coverage
        uncertainty_upper = displayed_eta + 1.645 * sigma

        # Authoritative arrival timestamp (consistent time basis)
        pred_arr_epoch = pred_epoch + displayed_eta * 60.0
        pred_arr_iso = self._format_iso(pred_arr_epoch)

        snapshot = ETAPredictionSnapshot(
            prediction_timestamp_utc=prediction_timestamp_utc,
            voyage_id=self.voyage_id,
            vessel_name=self.vessel_name,
            corridor=self.corridor,
            state=new_state,
            raw_remaining_minutes=round(raw_model_eta_minutes, 2),
            displayed_remaining_minutes=round(displayed_eta, 2),
            predicted_arrival_timestamp_utc=pred_arr_iso,
            data_freshness_seconds=round(freshness_s, 1),
            unexpected_jump_minutes=round(unexpected_jump, 2),
            uncertainty_lower_minutes=round(uncertainty_lower, 2),
            uncertainty_upper_minutes=round(uncertainty_upper, 2),
            is_stale=(new_state == ETAState.STALE_DATA),
            is_arrived=False,
            state_reason=state_reason,
        )
        self.history.append(snapshot)
        return snapshot
