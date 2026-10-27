"""High-performance Land Mask and Coastline Geometry Validation for Iroise Sea.

Loads committed GeoJSON polygons representing land in Finistère and the Iroise Sea
(Brest, Le Conquet, Ouessant, Molène, Pointe Saint-Mathieu, Audierne, Île de Sein).
Provides spatial queries using Shapely prepared geometries:
- is_on_land(lat, lon)
- nearest_water_point(lat, lon)
- segment_crosses_land(lat1, lon1, lat2, lon2)
- Port berth exemptions for terminals within specified berth radii.

Coordinates:
- Shapely operations strictly use (lon, lat) / (x, y).
- Function arguments and return values strictly use (lat, lon) standard maritime convention.
"""

from dataclasses import dataclass
import json
import logging
import math
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import shapely
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, box
from shapely.ops import nearest_points
from shapely.prepared import prep, PreparedGeometry

logger = logging.getLogger("maritime.geo.land_mask")

# Repository-relative path: ml-platform/src/geo/land_mask.py -> ml-platform/data/geo/iroise_land.geojson
DEFAULT_GEOJSON_PATH = Path(__file__).resolve().parents[2] / "data" / "geo" / "iroise_land.geojson"

# Bounding box for Iroise Sea
BBOX_LAT_MIN = 47.8
BBOX_LAT_MAX = 48.7
BBOX_LON_MIN = -5.5
BBOX_LON_MAX = -4.1

# Standard terminal coordinates, names, and berth clearance radii (meters)
TERMINALS: Dict[str, Dict[str, float]] = {
    "BREST": {
        "lat": 48.3828,
        "lon": -4.4855,
        "berth_radius_m": 250.0,
    },
    "LE_CONQUET": {
        "lat": 48.3585,
        "lon": -4.7788,
        "berth_radius_m": 250.0,
    },
    "OUESSANT_STIFF": {
        "lat": 48.4632,
        "lon": -5.0492,
        "berth_radius_m": 300.0,
    },
    "MOLENE": {
        "lat": 48.3970,
        "lon": -4.9965,
        "berth_radius_m": 250.0,
    },
    "AUDIERNE": {
        "lat": 48.0195,
        "lon": -4.5385,
        "berth_radius_m": 250.0,
    },
    "ILE_DE_SEIN": {
        "lat": 48.0375,
        "lon": -4.8505,
        "berth_radius_m": 250.0,
    },
}


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance in meters between two coordinates via Haversine formula."""
    r = 6371000.0  # Earth mean radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class LandMask:
    """Encapsulates spatial land mask index and query methods."""

    def __init__(self, geojson_path: Optional[Path] = None):
        self.geojson_path = geojson_path or DEFAULT_GEOJSON_PATH
        self.land_geometry: Optional[shapely.Geometry] = None
        self.water_geometry: Optional[shapely.Geometry] = None
        self._prepared_land: Optional[PreparedGeometry] = None
        self.is_loaded: bool = False
        self.berth_points: Dict[str, Tuple[float, float]] = {}

        self._load_mask()

    def _load_mask(self):
        """Loads and prepares land geometry from GeoJSON. Never crashes on error."""
        if not self.geojson_path.exists():
            logger.error("Land mask GeoJSON file missing at %s. Land checks disabled.", self.geojson_path)
            self.is_loaded = False
            return

        try:
            with open(self.geojson_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            geometries = []
            features = data.get("features", [])
            if not features and data.get("type") in ("Polygon", "MultiPolygon"):
                geometries.append(shapely.from_geojson(json.dumps(data)))
            else:
                for feat in features:
                    geom_json = feat.get("geometry")
                    if geom_json:
                        geom = shapely.from_geojson(json.dumps(geom_json))
                        geometries.append(geom)

            if not geometries:
                logger.error("No valid geometries found in %s", self.geojson_path)
                self.is_loaded = False
                return

            self.land_geometry = shapely.unary_union(geometries)
            if not self.land_geometry.is_valid:
                self.land_geometry = shapely.make_valid(self.land_geometry)

            self._prepared_land = prep(self.land_geometry)

            # Compute bounding water geometry: bbox minus land
            bbox_geom = box(BBOX_LON_MIN, BBOX_LAT_MIN, BBOX_LON_MAX, BBOX_LAT_MAX)
            self.water_geometry = bbox_geom.difference(self.land_geometry)

            self.is_loaded = True
            logger.info("Successfully loaded land mask from %s", self.geojson_path)

            # Pre-compute valid water berth points for each terminal
            self._compute_berth_points()

        except Exception as e:
            logger.error("Failed to load land mask from %s: %s", self.geojson_path, e, exc_info=True)
            self.land_geometry = None
            self.water_geometry = None
            self._prepared_land = None
            self.is_loaded = False

    def _compute_berth_points(self):
        """Precomputes the nearest water point for each terminal."""
        for t_id, t_info in TERMINALS.items():
            t_lat = t_info["lat"]
            t_lon = t_info["lon"]
            self.berth_points[t_id] = self.nearest_water_point(t_lat, t_lon)

    def is_inside_berth_radius(self, lat: float, lon: float) -> Optional[str]:
        """Returns terminal ID if (lat, lon) is within any terminal's berth radius, else None."""
        for t_id, t_info in TERMINALS.items():
            dist = haversine_distance_m(lat, lon, t_info["lat"], t_info["lon"])
            if dist <= t_info["berth_radius_m"]:
                return t_id
        return None

    def get_berth_point(self, terminal_id: str) -> Tuple[float, float]:
        """Returns (lat, lon) of the nearest water point to terminal berth."""
        if terminal_id in self.berth_points:
            return self.berth_points[terminal_id]
        if terminal_id in TERMINALS:
            t = TERMINALS[terminal_id]
            return self.nearest_water_point(t["lat"], t["lon"])
        return (48.3828, -4.4855)

    def is_on_land(self, lat: float, lon: float, check_port_exemption: bool = True) -> bool:
        """Determines if (lat, lon) is on land.
        
        Args:
            lat: Latitude degrees
            lon: Longitude degrees
            check_port_exemption: If True, positions inside any terminal's berth radius
                                 are exempted (return False).
        Returns:
            True if position is on land, False if in water or exempted.
        """
        if not self.is_loaded or self._prepared_land is None:
            return False

        # Port exemption check
        if check_port_exemption and self.is_inside_berth_radius(lat, lon) is not None:
            return False

        # Shapely Point takes (x, y) = (lon, lat)
        pt = Point(lon, lat)
        return bool(self._prepared_land.contains(pt))

    def nearest_water_point(self, lat: float, lon: float) -> Tuple[float, float]:
        """Finds the closest water point to (lat, lon).
        
        If already in water, returns (lat, lon).
        If on land, projects onto the nearest water geometry.
        """
        if not self.is_loaded or self.water_geometry is None:
            return (lat, lon)

        # Check if already in water (ignoring port exemption to be exact)
        pt = Point(lon, lat)
        if not self.is_on_land(lat, lon, check_port_exemption=False):
            return (lat, lon)

        # Project onto water polygon boundary / interior
        pt_land, pt_water = nearest_points(pt, self.water_geometry)
        # Offset slightly into water away from the exact boundary line (5 meters)
        # to ensure it strictly lies inside water
        n_lon, n_lat = pt_water.x, pt_water.y
        d_lon = n_lon - pt.x
        d_lat = n_lat - pt.y
        mag = math.hypot(d_lon, d_lat)
        if mag > 1e-7:
            # Shift 5 meters along vector into water
            # 5 meters in degrees ≈ 5 / 111000
            scale = 0.00005 / mag
            n_lon += d_lon * scale
            n_lat += d_lat * scale

        return (round(n_lat, 6), round(n_lon, 6))

    def segment_crosses_land(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        exempt_terminals: bool = True,
    ) -> bool:
        """Determines if the straight-line segment from (lat1, lon1) to (lat2, lon2) crosses land.
        
        If exempt_terminals is True, segment portions inside berth radii are clipped out.
        """
        if not self.is_loaded or self._prepared_land is None:
            return False

        line = LineString([(lon1, lat1), (lon2, lat2)])

        if not exempt_terminals:
            return bool(self._prepared_land.intersects(line))

        # Check terminal exemptions: if endpoints are inside berth radii,
        # we only test the portion outside all berth radii.
        berth_disks = []
        for t_info in TERMINALS.values():
            # Convert berth radius to approx degree buffer: 1 deg ≈ 111,000 m
            deg_radius = t_info["berth_radius_m"] / 111000.0
            berth_disks.append(Point(t_info["lon"], t_info["lat"]).buffer(deg_radius))

        if berth_disks:
            exempt_union = shapely.unary_union(berth_disks)
            clipped_line = line.difference(exempt_union)
            if clipped_line.is_empty:
                return False
            return bool(self._prepared_land.intersects(clipped_line))

        return bool(self._prepared_land.intersects(line))


# Singleton instance for platform-wide reuse
_global_land_mask: Optional[LandMask] = None


def get_land_mask() -> LandMask:
    """Returns the global LandMask singleton instance."""
    global _global_land_mask
    if _global_land_mask is None:
        _global_land_mask = LandMask()
    return _global_land_mask


def is_on_land(lat: float, lon: float, check_port_exemption: bool = True) -> bool:
    """Module-level convenience function querying global land mask."""
    return get_land_mask().is_on_land(lat, lon, check_port_exemption=check_port_exemption)


def nearest_water_point(lat: float, lon: float) -> Tuple[float, float]:
    """Module-level convenience function querying global land mask."""
    return get_land_mask().nearest_water_point(lat, lon)


def segment_crosses_land(lat1: float, lon1: float, lat2: float, lon2: float, exempt_terminals: bool = True) -> bool:
    """Module-level convenience function querying global land mask."""
    return get_land_mask().segment_crosses_land(lat1, lon1, lat2, lon2, exempt_terminals=exempt_terminals)
