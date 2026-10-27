"""Virtual AIS-Style Telemetry Generator for Where Is My Ferry? Phase 08.

Simulates physically plausible vessel movement along maritime route waypoints,
computes great-circle kinematics, speed variations, berth approach, and dwell,
and outputs versioned synthetic events conforming to Schema v1.0.0.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

import shapely
from shapely.geometry import Point, LineString
from shapely.prepared import prep, PreparedGeometry

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.streaming.event_schema import IncomingAISEvent, validate_ais_event

logger = logging.getLogger("maritime.simulation.generator")

# Feature flag: default true
GEOFENCE_ENABLED_DEFAULT = os.environ.get("GEOFENCE_ENABLED", "true").lower() in ("true", "1", "yes")


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


def point_along_polyline(
    waypoints: List[Tuple[float, float]],
    segment_lengths_m: List[float],
    distance_m: float,
) -> Tuple[float, float, int]:
    """Interpolates (lat, lon, segment_index) at given along-track distance in meters."""
    if distance_m <= 0.0 or len(waypoints) <= 1:
        return waypoints[0][0], waypoints[0][1], 0

    cum_dist = 0.0
    for i, seg_len in enumerate(segment_lengths_m):
        if cum_dist + seg_len >= distance_m:
            frac = (distance_m - cum_dist) / max(1e-6, seg_len)
            p1, p2 = waypoints[i], waypoints[i + 1]
            lat = p1[0] + frac * (p2[0] - p1[0])
            lon = p1[1] + frac * (p2[1] - p1[1])
            return lat, lon, i
        cum_dist += seg_len

    return waypoints[-1][0], waypoints[-1][1], max(0, len(segment_lengths_m) - 1)


def calculate_route_tangent_deg(
    waypoints: List[Tuple[float, float]],
    segment_lengths_m: List[float],
    distance_m: float,
    total_distance_m: float,
    lookahead_m: float = 250.0,
) -> float:
    """Calculates smoothed course over ground (COG) tangent along route with lookahead window."""
    if len(waypoints) <= 1:
        return 90.0

    curr_lat, curr_lon, _ = point_along_polyline(waypoints, segment_lengths_m, distance_m)
    target_dist = min(total_distance_m, distance_m + lookahead_m)

    if target_dist > distance_m + 1.0:
        ahead_lat, ahead_lon, _ = point_along_polyline(waypoints, segment_lengths_m, target_dist)
        return calculate_bearing_deg(curr_lat, curr_lon, ahead_lat, ahead_lon)
    elif distance_m > lookahead_m + 1.0:
        behind_lat, behind_lon, _ = point_along_polyline(waypoints, segment_lengths_m, distance_m - lookahead_m)
        return calculate_bearing_deg(behind_lat, behind_lon, curr_lat, curr_lon)
    else:
        return calculate_bearing_deg(waypoints[-2][0], waypoints[-2][1], waypoints[-1][0], waypoints[-1][1])


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
    route_waypoints: List[Tuple[float, float]] = field(default_factory=list)
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
    geofence_corrections: int = 0
    position_valid: bool = True
    initial_waypoints: List[Tuple[float, float]] = field(default_factory=list)
    initial_route_waypoints: List[Tuple[float, float]] = field(default_factory=list)
    initial_origin_terminal: str = ""
    initial_dest_terminal: str = ""
    initial_nominal_speed_knots: float = 0.0
    route_linestring: Optional[Any] = None
    prepared_geofence: Optional[Any] = None


class VirtualAISGenerator:
    """Generates synthetic AIS observation streams for virtual vessels."""

    def __init__(self, config_path: Optional[Path] = None):
        default_json = repo_root / "configs" / "phase_08_virtual_fleet.json"
        self.config_path = config_path or default_json
        self.fleet_config: Dict[str, Any] = {}
        self.vessels: Dict[str, VirtualVesselState] = {}
        self.geofence_enabled: bool = os.environ.get("GEOFENCE_ENABLED", "true").lower() in ("true", "1", "yes")
        self.geofence_available: bool = False
        self.routes_data: Dict[str, Any] = {}
        self.land_mask: Optional[Any] = None

        if self.geofence_enabled:
            self._init_geofence_data()

        self._load_config()

    def _init_geofence_data(self):
        """Loads committed water routes and land mask. Never crashes on error."""
        routes_path = repo_root / "data" / "geo" / "routes.json"
        land_mask_path = repo_root / "data" / "geo" / "iroise_land.geojson"

        if not routes_path.exists():
            logger.error("Routes JSON file missing at %s; falling back to previous behavior.", routes_path)
            self.geofence_available = False
            return

        try:
            from src.geo.land_mask import LandMask
            self.land_mask = LandMask(land_mask_path)
            if not self.land_mask.is_loaded:
                logger.error("Land mask failed to load from %s; falling back to previous behavior.", land_mask_path)
                self.geofence_available = False
                return

            with open(routes_path, "r", encoding="utf-8") as f:
                raw_routes = json.load(f)

            corridors = raw_routes.get("corridors", {})
            if not corridors:
                logger.error("No corridors found in %s; falling back to previous behavior.", routes_path)
                self.geofence_available = False
                return

            self.routes_data = corridors
            self.geofence_available = True
            logger.info("Successfully loaded %d water routes and land mask for virtual fleet simulation.", len(corridors))
        except Exception as e:
            logger.error("Error initializing geofence data: %s; falling back to previous behavior.", e, exc_info=True)
            self.geofence_available = False
            self.routes_data = {}
            self.land_mask = None

    def _load_config(self):
        """Loads virtual fleet and terminal configurations."""
        if not self.config_path.exists():
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
            corridor_key = v_conf.get("corridor") or v_conf.get("route_id")
            config_wps = [(float(p[0]), float(p[1])) for p in v_conf["waypoints"]]

            # If geofence is enabled and available, load verified water route waypoints
            route_info = self.routes_data.get(corridor_key) if (self.geofence_enabled and self.geofence_available) else None
            prep_geofence = None
            if route_info and "waypoints" in route_info:
                nav_wps = [(float(p[0]), float(p[1])) for p in route_info["waypoints"]]
                geofence_geojson = route_info.get("geofence")
                if geofence_geojson:
                    try:
                        g_poly = shapely.from_geojson(json.dumps(geofence_geojson))
                        prep_geofence = prep(g_poly)
                    except Exception as e:
                        logger.warning("Could not prepare geofence for %s: %s", corridor_key, e)
            else:
                nav_wps = list(config_wps)

            # Compute route segment distances using nav_wps
            seg_lengths = []
            total_dist = 0.0
            for i in range(len(nav_wps) - 1):
                d = haversine_distance_m(nav_wps[i][0], nav_wps[i][1], nav_wps[i + 1][0], nav_wps[i + 1][1])
                seg_lengths.append(d)
                total_dist += d

            route_line = LineString([(p[1], p[0]) for p in nav_wps]) if len(nav_wps) > 1 else None

            if self.geofence_enabled and self.geofence_available:
                init_cog = calculate_route_tangent_deg(nav_wps, seg_lengths, 0.0, total_dist) if len(nav_wps) > 1 else 90.0
                pos_valid = True
            elif self.geofence_enabled and not self.geofence_available:
                init_cog = calculate_bearing_deg(nav_wps[0][0], nav_wps[0][1], nav_wps[1][0], nav_wps[1][1]) if len(nav_wps) > 1 else 90.0
                pos_valid = False
            else:
                init_cog = calculate_bearing_deg(nav_wps[0][0], nav_wps[0][1], nav_wps[1][0], nav_wps[1][1]) if len(nav_wps) > 1 else 90.0
                pos_valid = True

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
                waypoints=list(config_wps),
                route_waypoints=list(nav_wps),
                historical_vessel_name=str(v_conf.get("historical_vessel_name")) if v_conf.get("historical_vessel_name") else None,
                total_route_distance_m=total_dist,
                segment_lengths_m=seg_lengths,
                current_lat=nav_wps[0][0],
                current_lon=nav_wps[0][1],
                current_sog_knots=0.2,  # Docked initially
                current_cog_degrees=init_cog,
                geofence_corrections=0,
                position_valid=pos_valid,
                initial_waypoints=list(config_wps),
                initial_route_waypoints=list(nav_wps),
                initial_origin_terminal=str(v_conf["origin_terminal"]),
                initial_dest_terminal=str(v_conf["dest_terminal"]),
                initial_nominal_speed_knots=float(v_conf["nominal_speed_knots"]),
                route_linestring=route_line,
                prepared_geofence=prep_geofence,
            )
            self.vessels[v_id] = state

    def get_vessel_ids(self) -> List[str]:
        """Returns list of configured virtual vessel identifiers."""
        return list(self.vessels.keys())

    def get_total_geofence_corrections(self) -> int:
        """Returns aggregate number of runtime geofence/land corrections across all virtual vessels."""
        return sum(v.geofence_corrections for v in self.vessels.values())

    def _snap_to_route(
        self,
        lat: float,
        lon: float,
        route_line: Optional[Any],
        waypoints: List[Tuple[float, float]],
    ) -> Tuple[float, float]:
        """Snaps coordinates to the nearest water point on the route polyline."""
        if route_line is not None:
            pt = Point(lon, lat)
            projected = route_line.project(pt)
            nearest = route_line.interpolate(projected)
            return round(nearest.y, 6), round(nearest.x, 6)

        best_wp = waypoints[0]
        best_d = float("inf")
        for wp in waypoints:
            d = haversine_distance_m(lat, lon, wp[0], wp[1])
            if d < best_d:
                best_d = d
                best_wp = wp
        return best_wp[0], best_wp[1]

    def reset_vessel(self, vessel_id: str):
        """Resets vessel kinematic state back to origin berth."""
        if vessel_id in self.vessels:
            v = self.vessels[vessel_id]
            if v.initial_waypoints:
                v.waypoints = list(v.initial_waypoints)
            if v.initial_route_waypoints:
                v.route_waypoints = list(v.initial_route_waypoints)
            v.origin_terminal = v.initial_origin_terminal
            v.dest_terminal = v.initial_dest_terminal
            v.segment_lengths_m = [
                haversine_distance_m(v.route_waypoints[i][0], v.route_waypoints[i][1], v.route_waypoints[i + 1][0], v.route_waypoints[i + 1][1])
                for i in range(len(v.route_waypoints) - 1)
            ]
            v.total_route_distance_m = sum(v.segment_lengths_m)
            v.route_linestring = LineString([(p[1], p[0]) for p in v.route_waypoints]) if len(v.route_waypoints) > 1 else None

            v.current_distance_traveled_m = 0.0
            v.current_lat = v.route_waypoints[0][0]
            v.current_lon = v.route_waypoints[0][1]
            v.current_sog_knots = 0.2
            v.nominal_speed_knots = v.initial_nominal_speed_knots if v.initial_nominal_speed_knots > 0 else v.nominal_speed_knots
            v.is_arrived = False
            v.step_count = 0
            v.departure_time_utc = None
            v.geofence_corrections = 0
            v.position_valid = not (self.geofence_enabled and not self.geofence_available)
            if len(v.route_waypoints) > 1:
                if self.geofence_enabled and self.geofence_available:
                    v.current_cog_degrees = calculate_route_tangent_deg(
                        v.route_waypoints, v.segment_lengths_m, 0.0, v.total_route_distance_m
                    )
                else:
                    v.current_cog_degrees = calculate_bearing_deg(
                        v.route_waypoints[0][0], v.route_waypoints[0][1], v.route_waypoints[1][0], v.route_waypoints[1][1]
                    )

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

        # 2. Advance along route distance or turnaround after berth dwell
        if not v.is_arrived and not force_holding:
            speed_mps = current_sog * 0.514444
            distance_step_m = speed_mps * delta_seconds
            v.current_distance_traveled_m = min(v.total_route_distance_m, v.current_distance_traveled_m + distance_step_m)

        if v.current_distance_traveled_m >= (v.total_route_distance_m - 50.0):
            v.is_arrived = True
            v.current_sog_knots = 0.1
            # Berth dwell turnaround: after dwelling, depart on return voyage
            v.dwell_steps = getattr(v, "dwell_steps", 0) + 1
            if v.dwell_steps >= 12:
                v.dwell_steps = 0
                v.is_arrived = False
                v.current_distance_traveled_m = 0.0
                v.waypoints.reverse()
                v.route_waypoints.reverse()
                v.origin_terminal, v.dest_terminal = v.dest_terminal, v.origin_terminal
                v.segment_lengths_m = [
                    haversine_distance_m(v.route_waypoints[i][0], v.route_waypoints[i][1], v.route_waypoints[i + 1][0], v.route_waypoints[i + 1][1])
                    for i in range(len(v.route_waypoints) - 1)
                ]
                v.total_route_distance_m = sum(v.segment_lengths_m)
                v.route_linestring = LineString([(p[1], p[0]) for p in v.route_waypoints]) if len(v.route_waypoints) > 1 else None
                v.current_lat = v.route_waypoints[0][0]
                v.current_lon = v.route_waypoints[0][1]
                v.current_sog_knots = 0.2
                if len(v.route_waypoints) > 1:
                    if self.geofence_enabled and self.geofence_available:
                        v.current_cog_degrees = calculate_route_tangent_deg(
                            v.route_waypoints, v.segment_lengths_m, 0.0, v.total_route_distance_m
                        )
                    else:
                        v.current_cog_degrees = calculate_bearing_deg(
                            v.route_waypoints[0][0], v.route_waypoints[0][1], v.route_waypoints[1][0], v.route_waypoints[1][1]
                        )

        # 3. Interpolate position along route
        traveled = v.current_distance_traveled_m

        if self.geofence_enabled and self.geofence_available:
            curr_lat, curr_lon, _ = point_along_polyline(v.route_waypoints, v.segment_lengths_m, traveled)
            curr_cog = calculate_route_tangent_deg(
                v.route_waypoints, v.segment_lengths_m, traveled, v.total_route_distance_m
            )
        else:
            curr_lat, curr_lon = v.route_waypoints[-1][0], v.route_waypoints[-1][1]
            curr_cog = v.current_cog_degrees
            cum_dist = 0.0
            for i, seg_len in enumerate(v.segment_lengths_m):
                if cum_dist + seg_len >= traveled:
                    fraction = (traveled - cum_dist) / max(1.0, seg_len)
                    wp1, wp2 = v.route_waypoints[i], v.route_waypoints[i + 1]
                    curr_lat, curr_lon = interpolate_coordinates(wp1[0], wp1[1], wp2[0], wp2[1], fraction)
                    curr_cog = calculate_bearing_deg(wp1[0], wp1[1], wp2[0], wp2[1])
                    break
                cum_dist += seg_len

        # Apply lateral deviation if configured
        curr_lat += route_deviation_lat
        curr_lon += route_deviation_lon

        # Runtime guard: validate against geofence and land mask
        if self.geofence_enabled and self.geofence_available and self.land_mask:
            is_land = self.land_mask.is_on_land(curr_lat, curr_lon, check_port_exemption=True)
            in_geofence = True
            is_inside_berth = (self.land_mask.is_inside_berth_radius(curr_lat, curr_lon) is not None)
            if not is_inside_berth and v.prepared_geofence is not None:
                in_geofence = bool(v.prepared_geofence.contains(Point(curr_lon, curr_lat)))

            if is_land or not in_geofence:
                orig_lat, orig_lon = curr_lat, curr_lon
                curr_lat, curr_lon = self._snap_to_route(curr_lat, curr_lon, v.route_linestring, v.route_waypoints)
                v.geofence_corrections += 1
                v.position_valid = False
                logger.warning(
                    "Vessel %s position (%f, %f) violated land/geofence (land=%s, in_geofence=%s); snapped to (%f, %f)",
                    v.virtual_vessel_id, orig_lat, orig_lon, is_land, in_geofence, curr_lat, curr_lon
                )
            else:
                v.position_valid = True
        elif self.geofence_enabled and not self.geofence_available:
            v.position_valid = False
        else:
            v.position_valid = True

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
            "position_valid": v.position_valid,
        }

        return event_payload

