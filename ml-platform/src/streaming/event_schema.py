"""Versioned Event Schema and Validation for Streaming AIS Telemetry."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional, Tuple


@dataclass
class IncomingAISEvent:
    """Validated AIS observation payload."""
    message_id: str
    mmsi: int
    vessel_name: str
    event_timestamp_utc: str
    receipt_timestamp_utc: str
    latitude: float
    longitude: float
    sog_knots: float
    cog_degrees: Optional[float] = None
    heading_degrees: Optional[float] = None
    nav_status: Optional[int] = None
    source_id: str = "datAcron_brest"
    is_synthetic_fixture: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ETAResponsePayload:
    """Authoritative ETA prediction payload produced by stream processor."""
    schema_version: str
    vessel_name: str
    mmsi: int
    corridor: str
    prediction_timestamp_utc: str
    predicted_arrival_timestamp_utc: str
    estimated_remaining_minutes: float
    raw_model_remaining_minutes: float
    eta_lifecycle_state: str
    latest_observation_timestamp_utc: str
    data_freshness_seconds: float
    is_stale: bool
    is_arrived: bool
    uncertainty_lower_minutes: float
    uncertainty_upper_minutes: float
    unexpected_jump_minutes: float
    reason_code: str
    processing_latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_utc_timestamp(ts_str: Any) -> Optional[datetime]:
    """Safely parses ISO timestamp string to UTC datetime."""
    if not isinstance(ts_str, str) or not ts_str:
        return None
    try:
        clean = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def validate_ais_event(payload: Dict[str, Any]) -> Tuple[Optional[IncomingAISEvent], Optional[str]]:
    """Validates raw incoming dictionary against Phase 07 event schema.

    Returns:
        (event, None) if valid.
        (None, error_reason) if invalid.
    """
    if not isinstance(payload, dict):
        return None, "PAYLOAD_NOT_A_DICTIONARY"

    # 1. Required identifier checks
    msg_id = payload.get("message_id")
    if not msg_id or not isinstance(msg_id, str):
        return None, "MISSING_OR_INVALID_MESSAGE_ID"

    mmsi = payload.get("mmsi")
    if not isinstance(mmsi, int) or mmsi <= 0 or len(str(mmsi)) != 9:
        return None, "INVALID_MMSI_MUST_BE_9_DIGIT_INTEGER"

    vessel_name = payload.get("vessel_name")
    if not vessel_name or not isinstance(vessel_name, str):
        return None, "MISSING_VESSEL_NAME"

    # 2. Timestamp validation
    event_ts_str = payload.get("event_timestamp_utc")
    dt_event = parse_utc_timestamp(event_ts_str)
    if dt_event is None:
        return None, "MALFORMED_EVENT_TIMESTAMP"

    receipt_ts_str = payload.get("receipt_timestamp_utc") or event_ts_str
    dt_receipt = parse_utc_timestamp(receipt_ts_str)
    if dt_receipt is None:
        return None, "MALFORMED_RECEIPT_TIMESTAMP"

    # 3. Coordinate validation
    lat = payload.get("latitude")
    if not isinstance(lat, (int, float)) or not (-90.0 <= lat <= 90.0):
        return None, "INVALID_LATITUDE_OUT_OF_BOUNDS"

    lon = payload.get("longitude")
    if not isinstance(lon, (int, float)) or not (-180.0 <= lon <= 180.0):
        return None, "INVALID_LONGITUDE_OUT_OF_BOUNDS"

    # 4. Speed & course validation
    sog = payload.get("sog_knots")
    if not isinstance(sog, (int, float)) or not (0.0 <= sog <= 60.0):
        return None, "INVALID_SOG_OUT_OF_BOUNDS"

    cog = payload.get("cog_degrees")
    if cog is not None and (not isinstance(cog, (int, float)) or not (0.0 <= cog <= 360.0)):
        return None, "INVALID_COG_OUT_OF_BOUNDS"

    heading = payload.get("heading_degrees")
    if heading is not None and (not isinstance(heading, (int, float)) or not (0.0 <= heading <= 360.0)):
        return None, "INVALID_HEADING_OUT_OF_BOUNDS"

    nav_status = payload.get("nav_status")
    if nav_status is not None and (not isinstance(nav_status, int) or not (0 <= nav_status <= 15)):
        return None, "INVALID_NAV_STATUS_CODE"

    event = IncomingAISEvent(
        message_id=msg_id,
        mmsi=mmsi,
        vessel_name=str(vessel_name).strip(),
        event_timestamp_utc=dt_event.strftime("%Y-%m-%dT%H:%M:%SZ"),
        receipt_timestamp_utc=dt_receipt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        latitude=float(lat),
        longitude=float(lon),
        sog_knots=float(sog),
        cog_degrees=float(cog) if cog is not None else None,
        heading_degrees=float(heading) if heading is not None else None,
        nav_status=nav_status,
        source_id=str(payload.get("source_id", "stream_ingestion")),
        is_synthetic_fixture=bool(payload.get("is_synthetic_fixture", False)),
    )
    return event, None
