"""Virtual AIS-Style Telemetry Generator for Where Is My Ferry? Phase 08.

Simulates physically plausible vessel movement along maritime route waypoints,
computes great-circle kinematics, speed variations, berth approach, and dwell,
and outputs versioned synthetic events conforming to Schema v1.0.0.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.streaming.event_schema import IncomingAISEvent, validate_ais_event


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates Haversine distance in meters between two coordinates."""
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0)**2
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def calculate_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates initial bearing (course over ground) in degrees from point 1 to 2."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    y = math.sin(dlam) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0


def interpolate_coordinates(lat1: float, lon1: float, lat2: float, lon2: float, fraction: float) -> Tuple[float, float]:
    """Linearly interpolates between two close coordinates on a spherical surface."""
    f = max(0.0, min(1.0, fraction))
    lat = lat1 + f * (lat2 - lat1)
    lon = lon1 + f * (lon2 - lon1)
    return lat, lon


@dataclass
class VirtualVesselState:
    """Internal kinematic and simulation state of a virtual vessel."""
    virtual_vessel_id: str
    synthetic_mmsi: int
    vessel_name: str
    route_id: str
    corridor: str
    origin_terminal: str
    dest_terminal: str
    nominal_speed_knots: float
    speed_variation_knots: float
    waypoints: List[Tuple[float, float]]
    historical_vessel_name: Optional[str] = None
    current_distance_traveled_m: float = 0.0
    total_route_distance_m: float = 0.0
    segment_lengths_m: List[float] = field(default_factory=list)
    current_lat: float = 0.0
    current_lon: float = 0.0
    current_sog_knots: float = 0.0
    current_cog_degrees: float = 0.0
    is_arrived: bool = False
    step_count: int = 0
    departure_time_utc: Optional[datetime] = None


class VirtualAISGenerator:
    """Generates synthetic AIS observation streams for virtual vessels."""

    def __init__(self, config_path: Optional[Path] = None):
        default_json = repo_root / "configs" / "phase_08_virtual_fleet.json"
        self.config_path = config_path or default_json
        self.fleet_config: Dict[str, Any] = {}
        self.vessels: Dict[str, VirtualVesselState] = {}
        self._load_config()

    def _load_config(self):
        """Loads virtual fleet and terminal configurations."""
        if not self.config_path.exists():
            # Try json counterpart
            alt_json = self.config_path.with_suffix(".json")
            if alt_json.exists():
                self.config_path = alt_json
            else:
                raise FileNotFoundError(f"Virtual fleet configuration missing: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            if self.config_path.suffix == ".json":
                self.fleet_config = json.load(f)
            else:
                try:
                    import yaml
                    self.fleet_config = yaml.safe_load(f)
                except ImportError:
                    alt_json = self.config_path.with_suffix(".json")
                    if alt_json.exists():
                        with open(alt_json, "r", encoding="utf-8") as f_json:
                            self.fleet_config = json.load(f_json)
                    else:
                        raise ImportError("PyYAML not installed and no .json config found")

        for v_conf in self.fleet_config.get("vessels", []):
            v_id = v_conf["virtual_vessel_id"]
            wps = [(float(p[0]), float(p[1])) for p in v_conf["waypoints"]]

            # Compute route segment distances
            seg_lengths = []
            total_dist = 0.0
            for i in range(len(wps) - 1):
                d = haversine_distance_m(wps[i][0], wps[i][1], wps[i + 1][0], wps[i + 1][1])
                seg_lengths.append(d)
                total_dist += d

            init_cog = calculate_bearing_deg(wps[0][0], wps[0][1], wps[1][0], wps[1][1]) if len(wps) > 1 else 90.0

            state = VirtualVesselState(
                virtual_vessel_id=v_id,
                synthetic_mmsi=int(v_conf["synthetic_mmsi"]),
                vessel_name=str(v_conf["vessel_name"]),
                route_id=str(v_conf["route_id"]),
                corridor=str(v_conf["corridor"]),
                origin_terminal=str(v_conf["origin_terminal"]),
                dest_terminal=str(v_conf["dest_terminal"]),
                nominal_speed_knots=float(v_conf["nominal_speed_knots"]),
                speed_variation_knots=float(v_conf.get("speed_variation_knots", 1.0)),
                waypoints=wps,
                historical_vessel_name=str(v_conf.get("historical_vessel_name")) if v_conf.get("historical_vessel_name") else None,
                total_route_distance_m=total_dist,
                segment_lengths_m=seg_lengths,
                current_lat=wps[0][0],
                current_lon=wps[0][1],
                current_sog_knots=0.2,  # Docked initially
                current_cog_degrees=init_cog,
            )
            self.vessels[v_id] = state

    def get_vessel_ids(self) -> List[str]:
        """Returns list of configured virtual vessel identifiers."""
        return list(self.vessels.keys())

    def reset_vessel(self, vessel_id: str):
        """Resets vessel kinematic state back to origin berth."""
        if vessel_id in self.vessels:
            v = self.vessels[vessel_id]
            v.current_distance_traveled_m = 0.0
            v.current_lat = v.waypoints[0][0]
            v.current_lon = v.waypoints[0][1]
            v.current_sog_knots = 0.2
            v.is_arrived = False
            v.step_count = 0
            v.departure_time_utc = None

    def advance_vessel_step(
        self,
        vessel_id: str,
        sim_timestamp_utc: datetime,
        delta_seconds: float = 300.0,
        speed_override_knots: Optional[float] = None,
        force_holding: bool = False,
        route_deviation_lat: float = 0.0,
        route_deviation_lon: float = 0.0,
        simulation_run_id: str = "sim_session_default",
        scenario_id: str = "nominal",
    ) -> Dict[str, Any]:
        """Advances vessel kinematics by delta_seconds along route and returns AIS event payload."""
        v = self.vessels[vessel_id]
        v.step_count += 1
        if v.departure_time_utc is None:
            v.departure_time_utc = sim_timestamp_utc

        remaining_m = max(0.0, v.total_route_distance_m - v.current_distance_traveled_m)

        # 1. Determine target speed
        if v.is_arrived:
            current_sog = 0.1
        elif force_holding:
            current_sog = 0.1  # Stopped in water
        elif speed_override_knots is not None:
            current_sog = max(0.0, speed_override_knots)
        elif remaining_m < 500.0:
            current_sog = 0.8  # Dock approach
        elif remaining_m < 2000.0:
            current_sog = 6.0  # Channel entrance deceleration
        else:
            # Nominal cruising speed with deterministic sinusoidal micro-variation
            var = math.sin(v.step_count * 0.7) * v.speed_variation_knots
            current_sog = max(5.0, v.nominal_speed_knots + var)

        v.current_sog_knots = round(current_sog, 2)

        # 2. Advance along route distance
        if not v.is_arrived and not force_holding:
            speed_mps = current_sog * 0.514444
            distance_step_m = speed_mps * delta_seconds
            v.current_distance_traveled_m = min(v.total_route_distance_m, v.current_distance_traveled_m + distance_step_m)

        if v.current_distance_traveled_m >= (v.total_route_distance_m - 50.0):
            v.is_arrived = True
            v.current_sog_knots = 0.1

        # 3. Interpolate position along waypoint segments
        traveled = v.current_distance_traveled_m
        curr_lat, curr_lon = v.waypoints[-1][0], v.waypoints[-1][1]
        curr_cog = v.current_cog_degrees

        cum_dist = 0.0
        for i, seg_len in enumerate(v.segment_lengths_m):
            if cum_dist + seg_len >= traveled:
                fraction = (traveled - cum_dist) / max(1.0, seg_len)
                wp1, wp2 = v.waypoints[i], v.waypoints[i + 1]
                curr_lat, curr_lon = interpolate_coordinates(wp1[0], wp1[1], wp2[0], wp2[1], fraction)
                curr_cog = calculate_bearing_deg(wp1[0], wp1[1], wp2[0], wp2[1])
                break
            cum_dist += seg_len

        # Apply lateral deviation if configured
        curr_lat += route_deviation_lat
        curr_lon += route_deviation_lon

        v.current_lat = round(curr_lat, 6)
        v.current_lon = round(curr_lon, 6)
        v.current_cog_degrees = round(curr_cog, 1)

        receipt_ts = sim_timestamp_utc + timedelta(seconds=1.5)

        event_payload = {
            "message_id": f"SIM-MSG-{v.virtual_vessel_id}-{v.step_count:04d}",
            "mmsi": v.synthetic_mmsi,
            "vessel_name": v.vessel_name,
            "historical_vessel_name": v.historical_vessel_name,
            "event_timestamp_utc": sim_timestamp_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "receipt_timestamp_utc": receipt_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latitude": v.current_lat,
            "longitude": v.current_lon,
            "sog_knots": v.current_sog_knots,
            "cog_degrees": v.current_cog_degrees,
            "heading_degrees": v.current_cog_degrees,
            "nav_status": 5 if v.is_arrived else (1 if force_holding else 0),  # 5=Moored, 1=At anchor, 0=Under way
            "source_id": "virtual_maritime_sim",
            "is_synthetic_fixture": True,
            "virtual_vessel_id": v.virtual_vessel_id,
            "route_id": v.route_id,
            "corridor": v.corridor,
            "dest_terminal": v.dest_terminal,
            "simulation_run_id": simulation_run_id,
            "scenario_id": scenario_id,
        }

        return event_payload
