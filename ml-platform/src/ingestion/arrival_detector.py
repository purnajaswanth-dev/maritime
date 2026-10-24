"""Ground-truth arrival and departure event detector with geofencing and quality scoring."""

from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple


class EventType(str, Enum):
    SCHEDULED_DEPARTURE = "SCHEDULED_DEPARTURE"
    OBSERVED_DEPARTURE = "OBSERVED_DEPARTURE"
    SCHEDULED_ARRIVAL = "SCHEDULED_ARRIVAL"
    OBSERVED_ARRIVAL = "OBSERVED_ARRIVAL"
    INFERRED_PORT_ARRIVAL = "INFERRED_PORT_ARRIVAL"


class LabelQuality(str, Enum):
    SUPERVISED_USABLE = "SUPERVISED_USABLE"
    CANDIDATE_UNVERIFIED = "CANDIDATE_UNVERIFIED"
    UNLABELLED = "UNLABELLED"


class PortGeofence:
    """Calculates haversine distance to terminal and evaluates containment."""

    @staticmethod
    def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371000.0  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c


class ArrivalDetector:
    """Detects and scores departure and arrival events for ferry trajectories."""

    DEFAULT_BERTH_RADIUS_M = 800.0  # meters around port/terminal coordinates
    MAX_OBSERVATION_GAP_MINUTES = 30.0

    @classmethod
    def evaluate_trajectory_voyage(
        cls,
        track_id: str,
        mmsi: int,
        vessel_name: Optional[str],
        vessel_review_status: str,
        start_lon: float,
        start_lat: float,
        end_lon: float,
        end_lat: float,
        first_observed_time: str,
        last_observed_time: str,
        duration_minutes: float,
        scheduled_departure: Optional[str] = None,
        scheduled_arrival: Optional[str] = None,
        origin_port: Optional[Tuple[str, float, float]] = None,  # (Name, lat, lon)
        dest_port: Optional[Tuple[str, float, float]] = None,    # (Name, lat, lon)
        has_stop_start_event: bool = False,
        observation_gap_minutes: float = 0.0,
    ) -> Dict[str, Any]:
        """Evaluates ground-truth departure and arrival events.

        If arrival outcome is not defensible, marks voyage UNLABELLED and excludes from training.
        """
        exclusion_reasons = []

        # 1. Vessel Identity Check
        if vessel_review_status not in ["VERIFIED_PASSENGER_FERRY", "LIKELY_PASSENGER_FERRY"]:
            exclusion_reasons.append("Unverified vessel identity (not confirmed passenger ferry).")

        # 2. Origin Geofence Check
        origin_name = "UNKNOWN_ORIGIN"
        origin_dist = None
        if origin_port:
            p_name, p_lat, p_lon = origin_port
            dist = PortGeofence.haversine_distance_m(start_lat, start_lon, p_lat, p_lon)
            origin_dist = dist
            if dist <= cls.DEFAULT_BERTH_RADIUS_M:
                origin_name = p_name
            else:
                exclusion_reasons.append(f"Start coordinates {dist:.0f}m from nearest port (exceeds {cls.DEFAULT_BERTH_RADIUS_M}m buffer).")
        else:
            exclusion_reasons.append("No reference origin port available.")

        # 3. Destination Geofence Check
        dest_name = "UNKNOWN_DESTINATION"
        dest_dist = None
        if dest_port:
            p_name, p_lat, p_lon = dest_port
            dist = PortGeofence.haversine_distance_m(end_lat, end_lon, p_lat, p_lon)
            dest_dist = dist
            if dist <= cls.DEFAULT_BERTH_RADIUS_M:
                dest_name = p_name
            else:
                exclusion_reasons.append(f"End coordinates {dist:.0f}m from nearest port (open-water endpoint).")
        else:
            exclusion_reasons.append("No reference destination port available.")

        # 4. Observation Gap Check
        if observation_gap_minutes > cls.MAX_OBSERVATION_GAP_MINUTES:
            exclusion_reasons.append(f"Observation gap ({observation_gap_minutes:.1f} min) exceeds {cls.MAX_OBSERVATION_GAP_MINUTES} min threshold.")

        # 5. Determine Arrival Event Type
        arrival_event_type = None
        arrival_timestamp = None
        arrival_confidence = 0.0

        if dest_name != "UNKNOWN_DESTINATION":
            if has_stop_start_event:
                arrival_event_type = EventType.OBSERVED_ARRIVAL.value
                arrival_timestamp = last_observed_time
                arrival_confidence = 0.95
            else:
                arrival_event_type = EventType.INFERRED_PORT_ARRIVAL.value
                arrival_timestamp = last_observed_time
                arrival_confidence = 0.80

        # Determine Departure Event Type
        departure_event_type = EventType.OBSERVED_DEPARTURE.value if origin_name != "UNKNOWN_ORIGIN" else None
        departure_timestamp = first_observed_time if departure_event_type else None

        # 6. Final Usability Decision
        if not exclusion_reasons and arrival_event_type is not None:
            label_quality = LabelQuality.SUPERVISED_USABLE.value
        elif arrival_event_type is not None and vessel_review_status == "LIKELY_PASSENGER_FERRY":
            label_quality = LabelQuality.CANDIDATE_UNVERIFIED.value
        else:
            label_quality = LabelQuality.UNLABELLED.value

        return {
            "voyage_id": f"VOY-{track_id}",
            "mmsi": int(mmsi),
            "vessel_name": vessel_name,
            "vessel_review_status": vessel_review_status,
            "origin_port": origin_name,
            "destination_port": dest_name,
            "first_observed_time": first_observed_time,
            "last_observed_time": last_observed_time,
            "duration_minutes": float(duration_minutes),
            "scheduled_departure": scheduled_departure,
            "scheduled_arrival": scheduled_arrival,
            "departure_event_type": departure_event_type,
            "departure_timestamp": departure_timestamp,
            "arrival_event_type": arrival_event_type,
            "arrival_timestamp": arrival_timestamp,
            "arrival_confidence": arrival_confidence,
            "observation_gap_minutes": float(observation_gap_minutes),
            "label_quality": label_quality,
            "is_supervised_usable": label_quality == LabelQuality.SUPERVISED_USABLE.value,
            "exclusion_reasons": "; ".join(exclusion_reasons) if exclusion_reasons else None,
        }
