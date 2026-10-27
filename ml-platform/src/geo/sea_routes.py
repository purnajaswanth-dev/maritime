"""Water-Only Sea Routes and Geofence Generator for Where Is My Ferry? Phase 08+.

Developer generation tool (run on-demand or as validation, NOT at server start).
Generates ml-platform/data/geo/routes.json containing:
- High-fidelity water-only polyline [lat, lon] waypoints per corridor
- Bounded safety geofence polygons (buffered 400m near ports, 800m in open water, minus land)
- Checksum and provenance manifest for integrity validation.

Validation rules enforced:
1. Starts and ends anchored strictly to terminal berth water coordinates.
2. 0 segments cross land.
3. Clearance from land outside berth/port basins is strictly respected.
4. Route length is between 1.0 and 1.4 times great-circle distance.
5. Emits clear, actionable errors if any validation check fails.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import shapely
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, mapping
from shapely.ops import unary_union

# Local package imports
try:
    from src.geo.land_mask import get_land_mask, haversine_distance_m, TERMINALS
except ImportError:
    import sys
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from src.geo.land_mask import get_land_mask, haversine_distance_m, TERMINALS

logger = logging.getLogger("maritime.geo.sea_routes")

ROUTES_JSON_PATH = Path(__file__).resolve().parents[2] / "data" / "geo" / "routes.json"


# -----------------------------------------------------------------------------
# Curated & Validated Navigation Waypoints [lat, lon]
# -----------------------------------------------------------------------------

WAYPOINTS_BREST_LE_CONQUET: List[Tuple[float, float]] = [
    # Brest Port de Commerce Berth (inner basin)
    (48.38218, -4.48563),
    (48.3820, -4.4860),
    (48.3800, -4.4840),
    (48.3780, -4.4840),
    (48.3760, -4.4870),
    (48.3740, -4.4870),
    (48.3700, -4.4890),
    (48.3660, -4.4860),
    (48.3600, -4.4950),
    # Rade de Brest out through Goulet de Brest channel
    (48.3580, -4.5150),
    (48.3510, -4.5400),
    (48.3440, -4.5700),
    (48.3360, -4.6040),
    (48.3320, -4.6300),
    (48.3290, -4.6620),
    (48.3270, -4.6980),
    (48.3250, -4.7300),
    # Deep water passage round Pointe Saint-Mathieu (south of Vieux Moines rocks)
    (48.3180, -4.7620),
    (48.3180, -4.7760),
    (48.3250, -4.7880),
    (48.3360, -4.7880),
    (48.3480, -4.7880),
    # North through Chenal du Four into Port du Conquet channel
    (48.3560, -4.7870),
    (48.3575, -4.7835),
    (48.3580, -4.7815),
    (48.35816, -4.77967),
]

WAYPOINTS_LE_CONQUET_BREST: List[Tuple[float, float]] = WAYPOINTS_BREST_LE_CONQUET[::-1]

WAYPOINTS_BREST_OUESSANT_STIFF: List[Tuple[float, float]] = [
    # Brest Port de Commerce Berth out to Goulet
    (48.38218, -4.48563),
    (48.3820, -4.4860),
    (48.3800, -4.4840),
    (48.3780, -4.4840),
    (48.3760, -4.4870),
    (48.3740, -4.4870),
    (48.3700, -4.4890),
    (48.3660, -4.4860),
    (48.3600, -4.4950),
    (48.3580, -4.5150),
    (48.3510, -4.5400),
    (48.3440, -4.5700),
    (48.3360, -4.6040),
    (48.3320, -4.6300),
    (48.3290, -4.6620),
    (48.3270, -4.6980),
    (48.3250, -4.7300),
    # Deep water passage round Pointe Saint-Mathieu into open Iroise Sea
    (48.3180, -4.7620),
    (48.3150, -4.7850),
    # Northwest fairway through Iroise Sea towards Passage du Fromveur / Stiff
    (48.3350, -4.8100),
    (48.3650, -4.8450),
    (48.3950, -4.8850),
    (48.4250, -4.9350),
    (48.4480, -4.9800),
    # Approach to Baie du Stiff (Port du Stiff, Île d'Ouessant)
    (48.4650, -5.0200),
    (48.4665, -5.0350),
    (48.4655, -5.0440),
    (48.46330, -5.04889),
]

WAYPOINTS_AUDIERNE_ILE_DE_SEIN: List[Tuple[float, float]] = [
    # Sainte-Évette (Audierne) Berth out through port channel into bay
    (48.021586, -4.537544),
    (48.022000, -4.537400),
    (48.018800, -4.534200),
    (48.017200, -4.534200),
    (48.014000, -4.537400),
    (48.013200, -4.537400),
    (48.010000, -4.540600),
    (48.009200, -4.540600),
    (48.008400, -4.541400),
    (48.008400, -4.547800),
    (48.004400, -4.551800),
    (48.004000, -4.553000),
    # West through Baie d'Audierne open fairway
    (48.004677, -4.553014),
    (48.001287, -4.554780),
    (47.995020, -4.559789),
    (47.993426, -4.563877),
    (47.994857, -4.574342),
    (48.001957, -4.611476),
    (48.009326, -4.653799),
    (48.019423, -4.701426),
    (48.029446, -4.743540),
    # Raz de Sein passage south of Sein shoals
    (48.038328, -4.774028),
    (48.039262, -4.779160),
    (48.040792, -4.789406),
    (48.043180, -4.814946),
    (48.043060, -4.831404),
    (48.041948, -4.842513),
    # North approach into Port de l'Île de Sein channel
    (48.041000, -4.845000),
    (48.040779, -4.844169),
    (48.037579, -4.847369),
    (48.037179, -4.850169),
]


CORRIDOR_CONFIGS = [
    {
        "id": "BREST_LE_CONQUET",
        "name": "Brest — Le Conquet",
        "vessel_id": "V-FROMVEUR-SIM",
        "origin_terminal": "BREST",
        "dest_terminal": "LE_CONQUET",
        "waypoints": WAYPOINTS_BREST_LE_CONQUET,
    },
    {
        "id": "LE_CONQUET_BREST",
        "name": "Le Conquet — Brest",
        "vessel_id": "V-AZENOR-SIM",
        "origin_terminal": "LE_CONQUET",
        "dest_terminal": "BREST",
        "waypoints": WAYPOINTS_LE_CONQUET_BREST,
    },
    {
        "id": "BREST_OUESSANT_STIFF",
        "name": "Brest — Ouessant (Port du Stiff)",
        "vessel_id": "V-OUESSANT-SIM",
        "origin_terminal": "BREST",
        "dest_terminal": "OUESSANT_STIFF",
        "waypoints": WAYPOINTS_BREST_OUESSANT_STIFF,
    },
    {
        "id": "AUDIERNE_ILE_DE_SEIN",
        "name": "Audierne — Île de Sein",
        "vessel_id": "V-SEIN-SIM",
        "origin_terminal": "AUDIERNE",
        "dest_terminal": "ILE_DE_SEIN",
        "waypoints": WAYPOINTS_AUDIERNE_ILE_DE_SEIN,
    },
]


def build_corridor_geofence(
    waypoints: List[Tuple[float, float]],
    dep_terminal: str,
    arr_terminal: str,
    land_mask,
) -> shapely.Geometry:
    """Constructs a corridor geofence polygon (buffered 400m near ports, 800m in open water, minus land)."""
    dep_t = TERMINALS[dep_terminal]
    arr_t = TERMINALS[arr_terminal]

    sub_buffers = []
    for i in range(len(waypoints) - 1):
        p1 = waypoints[i]
        p2 = waypoints[i + 1]
        mid_lat = (p1[0] + p2[0]) / 2.0
        mid_lon = (p1[1] + p2[1]) / 2.0

        d_dep = haversine_distance_m(mid_lat, mid_lon, dep_t["lat"], dep_t["lon"])
        d_arr = haversine_distance_m(mid_lat, mid_lon, arr_t["lat"], arr_t["lon"])

        # 400m buffer near terminals (< 2000m), 800m in open water
        buffer_m = 400.0 if (d_dep < 2000.0 or d_arr < 2000.0) else 800.0
        buf_deg = buffer_m / 111000.0

        # LineString takes (lon, lat)
        seg_line = LineString([(p1[1], p1[0]), (p2[1], p2[0])])
        sub_buffers.append(seg_line.buffer(buf_deg, cap_style=1, join_style=1))

    corridor_buffer = unary_union(sub_buffers)

    # Minus land to ensure geofence stays strictly in water
    if land_mask.land_geometry is not None:
        geofence = corridor_buffer.difference(land_mask.land_geometry)
    else:
        geofence = corridor_buffer

    # Simplify lightly to keep JSON small (< 200 KB target)
    geofence = geofence.simplify(0.0001, preserve_topology=True)
    if not geofence.is_valid:
        geofence = shapely.make_valid(geofence)

    return geofence


def validate_route(
    corridor_id: str,
    waypoints: List[Tuple[float, float]],
    dep_terminal: str,
    arr_terminal: str,
    land_mask,
) -> Dict[str, float]:
    """Validates navigation route against land mask, berth radii, and length constraints.
    
    Raises:
        ValueError if any validation rule is violated.
    """
    dep_t = TERMINALS[dep_terminal]
    arr_t = TERMINALS[arr_terminal]

    # 1. Anchorage check: ends must be inside terminal berth radii
    d_start = haversine_distance_m(waypoints[0][0], waypoints[0][1], dep_t["lat"], dep_t["lon"])
    d_end = haversine_distance_m(waypoints[-1][0], waypoints[-1][1], arr_t["lat"], arr_t["lon"])
    if d_start > dep_t["berth_radius_m"]:
        raise ValueError(
            f"{corridor_id} start point ({waypoints[0]}) is {d_start:.1f}m from {dep_terminal}, exceeding berth radius {dep_t['berth_radius_m']}m"
        )
    if d_end > arr_t["berth_radius_m"]:
        raise ValueError(
            f"{corridor_id} end point ({waypoints[-1]}) is {d_end:.1f}m from {arr_terminal}, exceeding berth radius {arr_t['berth_radius_m']}m"
        )

    # 2. Land intersection check: no segment crosses land
    crossings = []
    for i in range(len(waypoints) - 1):
        p1, p2 = waypoints[i], waypoints[i + 1]
        if land_mask.segment_crosses_land(p1[0], p1[1], p2[0], p2[1]):
            crossings.append((i, p1, p2))

    if crossings:
        raise ValueError(f"{corridor_id} has {len(crossings)} segments crossing land: {crossings}")

    # 3. Clearance check: in open water outside port channels, clearance >= 100m
    min_clearance_m = float("inf")
    port_approach_m = 2100.0
    for idx, (lat, lon) in enumerate(waypoints):
        d_dep = haversine_distance_m(lat, lon, dep_t["lat"], dep_t["lon"])
        d_arr = haversine_distance_m(lat, lon, arr_t["lat"], arr_t["lon"])
        if d_dep > port_approach_m and d_arr > port_approach_m:
            pt = Point(lon, lat)
            n_land = shapely.ops.nearest_points(pt, land_mask.land_geometry)[1]
            d_m = haversine_distance_m(lat, lon, n_land.y, n_land.x)
            if d_m < min_clearance_m:
                min_clearance_m = d_m
            if d_m < 100.0:
                raise ValueError(
                    f"{corridor_id} waypoint {idx} ({lat}, {lon}) has clearance {d_m:.1f}m < 100m threshold outside port"
                )

    # 4. Length ratio check: route length must be between 1.0 and 1.4 times great-circle distance
    gc_dist_m = haversine_distance_m(dep_t["lat"], dep_t["lon"], arr_t["lat"], arr_t["lon"])
    route_dist_m = sum(
        haversine_distance_m(waypoints[i][0], waypoints[i][1], waypoints[i + 1][0], waypoints[i + 1][1])
        for i in range(len(waypoints) - 1)
    )
    ratio = route_dist_m / gc_dist_m
    if not (1.0 <= ratio <= 1.4):
        raise ValueError(
            f"{corridor_id} route length ratio {ratio:.3f} is outside required bounds [1.0, 1.4] (Route: {route_dist_m/1000:.2f}km, GC: {gc_dist_m/1000:.2f}km)"
        )

    return {
        "route_distance_km": round(route_dist_m / 1000.0, 2),
        "great_circle_km": round(gc_dist_m / 1000.0, 2),
        "distance_ratio": round(ratio, 3),
        "min_clearance_m": round(min_clearance_m, 1),
    }


def generate_sea_routes_json(output_path: Optional[Path] = None) -> Path:
    """Generates routes.json containing water routes, geofence polygons, and manifest."""
    target_path = output_path or ROUTES_JSON_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    land_mask = get_land_mask()
    if not land_mask.is_loaded:
        raise RuntimeError("Land mask is not loaded. Cannot generate validated sea routes.")

    corridors_payload: Dict[str, Any] = {}
    validation_summaries: Dict[str, Any] = {}

    for config in CORRIDOR_CONFIGS:
        c_id = config["id"]
        wps = config["waypoints"]
        dep = config["origin_terminal"]
        arr = config["dest_terminal"]

        # Validate strictly
        metrics = validate_route(c_id, wps, dep, arr, land_mask)
        validation_summaries[c_id] = metrics

        # Generate geofence
        geofence_geom = build_corridor_geofence(wps, dep, arr, land_mask)

        # Build corridor record
        corridors_payload[c_id] = {
            "id": c_id,
            "name": config["name"],
            "vessel_id": config["vessel_id"],
            "origin_terminal": dep,
            "dest_terminal": arr,
            "waypoints": [[round(p[0], 6), round(p[1], 6)] for p in wps],
            "total_waypoints": len(wps),
            "metrics": metrics,
            "geofence": mapping(geofence_geom),
        }

    # Compute deterministic SHA-256 checksum over corridors payload
    canonical_json = json.dumps(corridors_payload, sort_keys=True, separators=(",", ":"))
    routes_sha256 = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    manifest = {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_corridors": len(corridors_payload),
        "corridors_list": list(corridors_payload.keys()),
        "routes_sha256": routes_sha256,
        "metrics_summary": validation_summaries,
    }

    full_document = {
        "manifest": manifest,
        "corridors": corridors_payload,
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(full_document, f, indent=2)

    file_size_kb = target_path.stat().st_size / 1024.0
    print(f"Generated {target_path} ({file_size_kb:.1f} KB, SHA-256: {routes_sha256[:16]}...)")
    for c_id, m in validation_summaries.items():
        print(f"  - {c_id:25s}: {m['route_distance_km']} km (GC: {m['great_circle_km']} km, Ratio: {m['distance_ratio']}, MinClearance: {m['min_clearance_m']}m)")

    return target_path


if __name__ == "__main__":
    generate_sea_routes_json()
