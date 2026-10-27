"""Test suite for water-only maritime routing, land mask validation, and runtime geofencing.

Verifies:
- Land mask correctness (known land vs water points, berth points).
- Route geometry validation across 4 corridors (berth radii, no land crossings, >=100m clearance, length ratio in [1.0, 1.4], SHA-256).
- Simulation property tests across 20 seeds and all 22 scenarios (zero land positions, zero geofence corrections, smooth COG, arrival latching).
- Runtime guard snapping and correction counter incrementing.
- Feature flag GEOFENCE_ENABLED=false and graceful error handling on missing routes.json.
- Axis order and bounding box constraints.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import pytest
from shapely.geometry import Point

from src.geo.land_mask import LandMask, TERMINALS, haversine_distance_m
from src.simulation.virtual_ais_generator import (
    VirtualAISGenerator,
    calculate_route_tangent_deg,
    point_along_polyline,
)

ml_root = Path(__file__).resolve().parents[1]
routes_path = ml_root / "data" / "geo" / "routes.json"
land_mask_path = ml_root / "data" / "geo" / "iroise_land.geojson"


def test_land_mask_classification():
    """Validates land mask against known terrestrial and maritime ground-truth locations."""
    mask = LandMask(land_mask_path)
    assert mask.is_loaded is True

    # Known land points in Finistère / Iroise Sea
    known_land = [
        (48.455, -5.097, "Ouessant Island Interior"),
        (48.240, -4.490, "Crozon Peninsula Mainland"),
        (48.375, -4.620, "Plouzane Peninsula Mainland"),
    ]
    for lat, lon, name in known_land:
        assert mask.is_on_land(lat, lon, check_port_exemption=False) is True, f"{name} ({lat}, {lon}) should be on land"

    # Known open water points
    known_water = [
        (48.250, -4.850, "Central Iroise Sea"),
        (48.435, -5.020, "Fromveur Passage"),
        (48.345, -4.560, "Goulet de Brest Fairway Channel"),
    ]
    for lat, lon, name in known_water:
        assert mask.is_on_land(lat, lon, check_port_exemption=False) is False, f"{name} ({lat}, {lon}) should be in water"

    # Pre-computed terminal berth points must be strictly in water and within berth radii
    for t_id, info in TERMINALS.items():
        bp = mask.get_berth_point(t_id)
        assert mask.is_on_land(bp[0], bp[1], check_port_exemption=False) is False, f"Berth point for {t_id} must be in water"
        dist = haversine_distance_m(bp[0], bp[1], info["lat"], info["lon"])
        assert dist <= info["berth_radius_m"], f"Berth point {bp} for {t_id} is {dist:.1f}m from terminal, exceeding radius {info['berth_radius_m']}m"


def test_corridor_routes_validation():
    """Validates that all corridors in routes.json meet geometric safety standards."""
    assert routes_path.exists(), f"routes.json missing at {routes_path}"
    with open(routes_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    manifest = data.get("manifest", {})
    corridors = data.get("corridors", {})
    expected_corridors = [
        "BREST_LE_CONQUET",
        "LE_CONQUET_BREST",
        "BREST_OUESSANT_STIFF",
        "AUDIERNE_ILE_DE_SEIN",
    ]
    assert set(corridors.keys()) == set(expected_corridors)

    # Verify SHA-256 checksum
    canonical_corridors = json.dumps(corridors, sort_keys=True, separators=(",", ":"))
    calculated_sha = hashlib.sha256(canonical_corridors.encode("utf-8")).hexdigest()
    assert calculated_sha == manifest["routes_sha256"], "Manifest SHA-256 checksum does not match corridors payload"

    mask = LandMask(land_mask_path)

    for c_id in expected_corridors:
        c_info = corridors[c_id]
        wps = c_info["waypoints"]
        dep = c_info["origin_terminal"]
        arr = c_info["dest_terminal"]

        # 1. Origin and destination endpoints inside berth radii
        p_start = wps[0]
        p_end = wps[-1]
        dep_dist = haversine_distance_m(p_start[0], p_start[1], TERMINALS[dep]["lat"], TERMINALS[dep]["lon"])
        arr_dist = haversine_distance_m(p_end[0], p_end[1], TERMINALS[arr]["lat"], TERMINALS[arr]["lon"])
        assert dep_dist <= TERMINALS[dep]["berth_radius_m"] + 5.0, f"{c_id} start point outside berth radius"
        assert arr_dist <= TERMINALS[arr]["berth_radius_m"] + 5.0, f"{c_id} end point outside berth radius"

        # 2. No segment crosses land
        for i in range(len(wps) - 1):
            assert not mask.segment_crosses_land(wps[i][0], wps[i][1], wps[i + 1][0], wps[i + 1][1], exempt_terminals=True), \
                f"{c_id} segment {i} ({wps[i]} -> {wps[i+1]}) crosses land"

        # 3. Ratio between route distance and great circle in [1.0, 1.4]
        metrics = c_info["metrics"]
        ratio = metrics["distance_ratio"]
        assert 1.0 <= ratio <= 1.4, f"{c_id} distance ratio {ratio} outside [1.0, 1.4]"

        # 4. Open sea clearance >= 100m
        assert metrics["min_clearance_m"] >= 100.0, f"{c_id} clearance {metrics['min_clearance_m']}m is below 100m"


def test_simulation_property_all_corridors_and_seeds():
    """Simulates full voyages for all 4 corridors across 20 distinct seeds at 5s steps.
    
    Asserts:
    - Zero land positions outside berth radii
    - All positions inside the corridor geofence
    - geofence_corrections == 0
    - Smooth COG (no jump above 30 degrees per step except at port manoeuvres)
    - SOG stays within safe kinematic limits
    - Voyage successfully latches ARRIVED via the dwell rule
    """
    gen = VirtualAISGenerator()
    assert gen.geofence_available is True
    mask = gen.land_mask

    for v_id in gen.get_vessel_ids():
        v = gen.vessels[v_id]
        corridor_id = v.corridor

        # Test across 20 seeds for each corridor
        for seed in range(20):
            gen.reset_vessel(v_id)
            # Deterministic micro-variation on departure speed
            v.nominal_speed_knots = float(v.nominal_speed_knots) + ((seed % 5) - 2) * 0.2
            sim_time = datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=seed * 15)

            steps = 0
            land_positions_outside_berth = 0
            outside_geofence_count = 0
            prev_cog = None
            max_cog_jump_open_sea = 0.0

            while not v.is_arrived and steps < 3500:
                payload = gen.advance_vessel_step(
                    vessel_id=v_id,
                    sim_timestamp_utc=sim_time,
                    delta_seconds=5.0,
                )
                sim_time += timedelta(seconds=5)
                steps += 1

                lat = payload["latitude"]
                lon = payload["longitude"]
                sog = payload["sog_knots"]
                cog = payload["cog_degrees"]
                pos_valid = payload.get("position_valid", True)

                assert pos_valid is True, f"Seed {seed}: emitted position_valid must be True"

                # Check land
                is_inside_berth = mask.is_inside_berth_radius(lat, lon) is not None
                if not is_inside_berth:
                    if mask.is_on_land(lat, lon, check_port_exemption=False):
                        land_positions_outside_berth += 1

                    # Check geofence
                    if v.prepared_geofence is not None:
                        if not v.prepared_geofence.contains(Point(lon, lat)):
                            outside_geofence_count += 1

                # Check smooth COG when cruising
                if prev_cog is not None and sog > 3.0 and not is_inside_berth:
                    jump = abs((cog - prev_cog + 180.0) % 360.0 - 180.0)
                    if jump > max_cog_jump_open_sea:
                        max_cog_jump_open_sea = jump
                    assert jump <= 30.0, f"{v_id} seed {seed} step {steps} COG jumped {jump:.1f} deg in open sea"

                assert 0.0 <= sog <= 25.0, f"Unphysical SOG {sog} knots"
                prev_cog = cog

            assert v.is_arrived is True, f"{v_id} seed {seed} did not arrive within {steps} steps"
            assert land_positions_outside_berth == 0, f"{v_id} seed {seed} had {land_positions_outside_berth} land points"
            assert outside_geofence_count == 0, f"{v_id} seed {seed} had {outside_geofence_count} points outside geofence"
            assert v.geofence_corrections == 0, f"{v_id} seed {seed} triggered {v.geofence_corrections} runtime corrections"


def test_simulation_all_22_scenarios():
    """Executes all 22 operational and adversarial scenarios and validates safety."""
    scenarios_path = ml_root / "configs" / "phase_08_scenarios.json"
    if not scenarios_path.exists():
        pytest.skip("phase_08_scenarios.json not found")

    with open(scenarios_path, "r", encoding="utf-8") as f:
        scenarios_data = json.load(f)

    gen = VirtualAISGenerator()
    mask = gen.land_mask

    for sc in scenarios_data.get("scenarios", []):
        sc_id = sc["id"]
        v_ids = [sc["vessel_id"]] if "vessel_id" in sc else sc.get("vessel_ids", ["V-FROMVEUR-SIM"])
        for v_id in v_ids:
            if v_id not in gen.vessels:
                continue

        gen.reset_vessel(v_id)
        v = gen.vessels[v_id]
        steps = sc.get("duration_steps", 10)
        dt_s = sc.get("step_interval_s", 300.0)

        # Apply fault parameters
        force_holding = (sc.get("fault_type") == "HOLDING_PATTERN")
        speed_override = sc.get("target_speed_knots")
        lat_offset = sc.get("lat_offset", 0.0)
        lon_offset = sc.get("lon_offset", 0.0)

        sim_time = datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc)

        for step in range(steps):
            payload = gen.advance_vessel_step(
                vessel_id=v_id,
                sim_timestamp_utc=sim_time,
                delta_seconds=dt_s,
                speed_override_knots=speed_override,
                force_holding=force_holding,
                route_deviation_lat=lat_offset,
                route_deviation_lon=lon_offset,
                scenario_id=sc_id,
            )
            sim_time += timedelta(seconds=dt_s)

            lat = payload["latitude"]
            lon = payload["longitude"]

            # Inside berth or in water
            is_inside_berth = (mask.is_inside_berth_radius(lat, lon) is not None)
            if not is_inside_berth:
                # Even if route deviation injected, runtime guard must ensure position is in water
                assert mask.is_on_land(lat, lon, check_port_exemption=False) is False, \
                    f"Scenario {sc_id} step {step} emitted point on land: ({lat}, {lon})"


def test_runtime_guard_snaps_injected_land_point():
    """Asserts that injected land coordinate is snapped to route polyline and increments corrections."""
    gen = VirtualAISGenerator()
    v_id = "V-FROMVEUR-SIM"
    gen.reset_vessel(v_id)
    v = gen.vessels[v_id]

    initial_corrections = v.geofence_corrections
    sim_time = datetime(2026, 3, 1, 8, 15, 0, tzinfo=timezone.utc)

    # Inject a large offset putting vessel directly onto mainland Plouzane (48.375, -4.620)
    payload = gen.advance_vessel_step(
        vessel_id=v_id,
        sim_timestamp_utc=sim_time,
        delta_seconds=5.0,
        route_deviation_lat=0.045,  # Shifts onto land
        route_deviation_lon=-0.045,
    )

    # Guard must snap position back to valid water route point
    snapped_lat = payload["latitude"]
    snapped_lon = payload["longitude"]

    assert v.geofence_corrections == initial_corrections + 1, "Runtime guard must increment geofence_corrections"
    assert payload["position_valid"] is False, "Snapped position must flag position_valid=False"
    assert gen.land_mask.is_on_land(snapped_lat, snapped_lon, check_port_exemption=True) is False, \
        f"Snapped point ({snapped_lat}, {snapped_lon}) must not be on land"


def test_feature_flag_disabled_reproduces_old_behavior():
    """Verifies that setting GEOFENCE_ENABLED=false loads previous config waypoints without error."""
    old_env = os.environ.get("GEOFENCE_ENABLED")
    try:
        os.environ["GEOFENCE_ENABLED"] = "false"
        gen = VirtualAISGenerator()
        assert gen.geofence_enabled is False

        # Waypoints should match config waypoints (6 points for V-FROMVEUR-SIM)
        v = gen.vessels["V-FROMVEUR-SIM"]
        assert len(v.waypoints) == 6
    finally:
        if old_env is not None:
            os.environ["GEOFENCE_ENABLED"] = old_env
        else:
            os.environ.pop("GEOFENCE_ENABLED", None)


def test_missing_routes_json_fails_gracefully():
    """Verifies that missing routes.json logs ERROR, falls back safely, and marks position_valid=False."""
    gen = VirtualAISGenerator()
    # Simulate missing data
    gen.geofence_available = False
    gen.routes_data = {}
    gen.land_mask = None
    gen._load_config()

    v = gen.vessels["V-FROMVEUR-SIM"]
    assert v.position_valid is False

    payload = gen.advance_vessel_step(
        "V-FROMVEUR-SIM",
        datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc),
        delta_seconds=5.0,
    )
    assert payload["position_valid"] is False


def test_axis_order_and_bounding_box():
    """Confirms latitude/longitude convention: lat within [47.8, 48.7], lon within [-5.5, -4.1]."""
    gen = VirtualAISGenerator()
    sim_time = datetime(2026, 3, 1, 8, 0, 0, tzinfo=timezone.utc)

    for v_id in gen.get_vessel_ids():
        gen.reset_vessel(v_id)
        for _ in range(20):
            payload = gen.advance_vessel_step(v_id, sim_time, delta_seconds=60.0)
            lat = payload["latitude"]
            lon = payload["longitude"]

            assert 47.8 <= lat <= 48.7, f"{v_id} latitude {lat} outside Iroise bounding box [47.8, 48.7]"
            assert -5.5 <= lon <= -4.1, f"{v_id} longitude {lon} outside Iroise bounding box [-5.5, -4.1]"
