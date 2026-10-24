"""Defensible raw AIS trajectory segmentation and ground-truth voyage recovery.

Extracts evidence-linked passenger ferry voyages from raw/synopsis AIS data,
enforces terminal geofencing, berth dwell detection, physical corridor bounds,
and strict telemetry gap thresholds.
"""

from collections import defaultdict
import datetime
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import zipfile

import pandas as pd


# Authoritative Passenger Ferry Registry for Brittany / Iroise Sea
VESSEL_REGISTRY: Dict[int, Dict[str, Any]] = {
    228017700: {
        "name": "FROMVEUR II",
        "imo": "IMO9613147",
        "type": "PASSENGER_FERRY",
        "operator": "Penn ar Bed",
        "review_status": "VERIFIED_PASSENGER_FERRY",
    },
    227003050: {
        "name": "ENEZ EUSSA 3",
        "imo": None,
        "type": "PASSENGER_FERRY",
        "operator": "Penn ar Bed",
        "review_status": "VERIFIED_PASSENGER_FERRY",
    },
    227002630: {
        "name": "ENEZ SUN 3",
        "imo": "IMO9019884",
        "type": "PASSENGER_FERRY",
        "operator": "Penn ar Bed",
        "review_status": "VERIFIED_PASSENGER_FERRY",
    },
    227002330: {
        "name": "ANDRE COLIN",
        "imo": "IMO9134957",
        "type": "PASSENGER_FERRY",
        "operator": "Penn ar Bed",
        "review_status": "VERIFIED_PASSENGER_FERRY",
    },
}

# Reference Ferry Terminals and Berth Coordinates (CRS: EPSG:4326)
TERMINALS: Dict[str, Dict[str, Any]] = {
    "BREST": {"lon": -4.4857, "lat": 48.3811, "radius_m": 800.0},
    "LE_CONQUET": {"lon": -4.7818, "lat": 48.3596, "radius_m": 600.0},
    "MOLENE": {"lon": -4.9565, "lat": 48.4022, "radius_m": 500.0},
    "OUESSANT_STIFF": {"lon": -5.0545, "lat": 48.4691, "radius_m": 800.0},
    "AUDIERNE": {"lon": -4.5524, "lat": 48.0061, "radius_m": 600.0},
    "ILE_DE_SEIN": {"lon": -4.8486, "lat": 48.0390, "radius_m": 500.0},
    "CAMARET": {"lon": -4.5940, "lat": 48.2780, "radius_m": 600.0},
}

# Realistic Physical Corridor Limits in Minutes: (min_duration_min, max_duration_min)
CORRIDOR_LIMITS: Dict[Tuple[str, str], Tuple[float, float]] = {
    ("BREST", "LE_CONQUET"): (45.0, 120.0),
    ("LE_CONQUET", "BREST"): (45.0, 120.0),
    ("LE_CONQUET", "MOLENE"): (20.0, 60.0),
    ("MOLENE", "LE_CONQUET"): (20.0, 60.0),
    ("MOLENE", "OUESSANT_STIFF"): (20.0, 75.0),
    ("OUESSANT_STIFF", "MOLENE"): (20.0, 75.0),
    ("BREST", "OUESSANT_STIFF"): (90.0, 210.0),
    ("OUESSANT_STIFF", "BREST"): (90.0, 210.0),
    ("AUDIERNE", "ILE_DE_SEIN"): (35.0, 150.0),
    ("ILE_DE_SEIN", "AUDIERNE"): (35.0, 150.0),
    ("BREST", "CAMARET"): (30.0, 90.0),
    ("CAMARET", "BREST"): (30.0, 90.0),
    ("CAMARET", "MOLENE"): (30.0, 90.0),
    ("MOLENE", "CAMARET"): (30.0, 90.0),
}


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculates great-circle distance between two points on WGS-84 ellipsoid approximation."""
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def match_terminal(lon: float, lat: float) -> Tuple[Optional[str], Optional[float]]:
    """Matches given coordinates to nearest terminal geofence if within buffer radius."""
    for name, term in TERMINALS.items():
        dist = haversine_m(lon, lat, term["lon"], term["lat"])
        if dist <= term["radius_m"]:
            return name, dist
    return None, None


class TrajectorySegmenter:
    """Segments raw or synopsis AIS streams into verified real-world ferry voyages."""

    def __init__(
        self,
        max_telemetry_gap_minutes: float = 45.0,
        min_observations: int = 5,
        underway_speed_threshold_knots: float = 3.0,
        berth_speed_threshold_knots: float = 3.0,
    ):
        self.max_gap_s = max_telemetry_gap_minutes * 60.0
        self.min_observations = min_observations
        self.underway_sog = underway_speed_threshold_knots
        self.berth_sog = berth_speed_threshold_knots

    def segment_vessel_points(
        self,
        mmsi: int,
        points: List[Tuple[int, float, float, float, Optional[float], str]],
    ) -> List[Dict[str, Any]]:
        """Segments a chronologically sorted sequence of AIS points for a single vessel.

        Point format: (epoch_ms, lon, lat, sog, heading, annot)
        """
        if not points:
            return []

        vinfo = VESSEL_REGISTRY.get(mmsi, {
            "name": f"UNKNOWN_{mmsi}",
            "review_status": "UNKNOWN",
        })

        # Ensure strict chronological order
        points = sorted(points, key=lambda x: x[0])

        voyages = []
        current_voyage: Optional[Dict[str, Any]] = None
        last_term: Optional[str] = None

        for i, p in enumerate(points):
            ts, lon, lat, sog, heading, annot = p
            term, dist = match_terminal(lon, lat)

            if current_voyage is None:
                if term is not None:
                    last_term = term
                elif last_term is not None and sog >= self.underway_sog:
                    # Departure transition detected
                    dep_point = points[i - 1] if i > 0 else p
                    current_voyage = {
                        "mmsi": mmsi,
                        "vessel_name": vinfo["name"],
                        "dep_terminal": last_term,
                        "dep_ts": dep_point[0],
                        "dep_lon": dep_point[1],
                        "dep_lat": dep_point[2],
                        "points": [dep_point, p],
                        "max_gap_s": (ts - dep_point[0]) / 1000.0,
                    }
            else:
                prev_ts = current_voyage["points"][-1][0]
                gap_s = (ts - prev_ts) / 1000.0
                if gap_s > current_voyage["max_gap_s"]:
                    current_voyage["max_gap_s"] = gap_s
                current_voyage["points"].append(p)

                if term is not None and term != current_voyage["dep_terminal"]:
                    # Reached destination terminal
                    is_stop = annot.endswith("1") or sog < self.berth_sog
                    if is_stop:
                        current_voyage["arr_terminal"] = term
                        current_voyage["arr_ts"] = ts
                        current_voyage["arr_lon"] = lon
                        current_voyage["arr_lat"] = lat
                        voyages.append(current_voyage)
                        last_term = term
                        current_voyage = None
                elif term is not None and term == current_voyage["dep_terminal"]:
                    # Vessel returned to departure terminal
                    max_d = max(
                        haversine_m(pt[1], pt[2], current_voyage["dep_lon"], current_voyage["dep_lat"])
                        for pt in current_voyage["points"]
                    )
                    if max_d < 2000.0:
                        # Harbor maneuvering or berth shifting
                        current_voyage = None
                    elif sog < 2.0:
                        current_voyage["arr_terminal"] = term
                        current_voyage["arr_ts"] = ts
                        current_voyage["arr_lon"] = lon
                        current_voyage["arr_lat"] = lat
                        voyages.append(current_voyage)
                        last_term = term
                        current_voyage = None

        return voyages

    def audit_and_classify_voyages(self, raw_voyages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Audits candidate voyages against physical corridor limits, gap bounds, and observation counts."""
        audited = []
        voyage_counter: Dict[str, int] = defaultdict(int)

        for v in raw_voyages:
            mmsi = v["mmsi"]
            dep_ts = v["dep_ts"]
            arr_ts = v["arr_ts"]
            dur_min = (arr_ts - dep_ts) / 60000.0
            n_pts = len(v["points"])
            max_gap_min = v["max_gap_s"] / 60.0
            dep_term = v["dep_terminal"]
            arr_term = v["arr_terminal"]
            corr = (dep_term, arr_term)

            dt_dep = datetime.datetime.fromtimestamp(dep_ts / 1000.0, tz=datetime.timezone.utc)
            dt_arr = datetime.datetime.fromtimestamp(arr_ts / 1000.0, tz=datetime.timezone.utc)
            date_str = dt_dep.strftime("%Y%m%d")

            voyage_counter[f"{date_str}_{mmsi}"] += 1
            v_idx = voyage_counter[f"{date_str}_{mmsi}"]
            voyage_id = f"VOY-BREST-{date_str}-{mmsi}-{v_idx:03d}"

            rejection_reasons = []

            # 1. Terminal corridor plausibility
            if corr not in CORRIDOR_LIMITS:
                rejection_reasons.append(f"Non-standard corridor: {corr}")
            else:
                min_d, max_d = CORRIDOR_LIMITS[corr]
                if not (min_d <= dur_min <= max_d):
                    rejection_reasons.append(
                        f"Duration {dur_min:.1f}m outside corridor bounds [{min_d:.0f}m, {max_d:.0f}m]"
                    )

            # 2. Telemetry gap check
            if v["max_gap_s"] > self.max_gap_s:
                rejection_reasons.append(
                    f"Max telemetry gap {max_gap_min:.1f}m exceeds {self.max_gap_s / 60.0:.0f}m limit"
                )

            # 3. Observation density check
            if n_pts < self.min_observations:
                rejection_reasons.append(f"Insufficient observations: {n_pts} < {self.min_observations}")

            # 4. Identity validation
            vinfo = VESSEL_REGISTRY.get(mmsi)
            if not vinfo or vinfo["review_status"] != "VERIFIED_PASSENGER_FERRY":
                rejection_reasons.append(f"Unverified passenger ferry identity for MMSI {mmsi}")

            status = "VERIFIED" if not rejection_reasons else "UNCERTAIN"
            evidence_grade = (
                "HIGH_AIS_BERTH_OBSERVED" if status == "VERIFIED" else "UNCERTAIN_HEURISTIC_EXCLUDED"
            )

            record = {
                "voyage_id": voyage_id,
                "mmsi": mmsi,
                "vessel_name": v["vessel_name"],
                "dep_terminal": dep_term,
                "arr_terminal": arr_term,
                "dep_timestamp_utc": dt_dep.strftime("%Y-%m-%d %H:%M:%SZ"),
                "arr_timestamp_utc": dt_arr.strftime("%Y-%m-%d %H:%M:%SZ"),
                "dep_ts_epoch_ms": dep_ts,
                "arr_ts_epoch_ms": arr_ts,
                "duration_minutes": round(dur_min, 2),
                "observation_count": n_pts,
                "max_gap_seconds": round(v["max_gap_s"], 1),
                "dep_lat": v["dep_lat"],
                "dep_lon": v["dep_lon"],
                "arr_lat": v["arr_lat"],
                "arr_lon": v["arr_lon"],
                "status": status,
                "evidence_grade": evidence_grade,
                "rejection_reasons": "; ".join(rejection_reasons) if rejection_reasons else "NONE",
                "source_archive": "ais_brest_synopses_v0.8.zip",
                "source_member": "ais_brest_synopses.csv",
                "points": v["points"],
            }
            audited.append(record)

        return audited

    @classmethod
    def extract_from_brest_zip(
        cls,
        zip_path: str,
        target_mmsis: Optional[List[int]] = None,
        max_rows: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Performs streaming extraction from ais_brest_synopses.csv, audits candidates, and returns dataframes.

        Returns: (candidate_audit_df, verified_voyages_df)
        """
        if target_mmsis is None:
            target_mmsis = list(VESSEL_REGISTRY.keys())
        target_bytes = {str(m).encode("utf-8"): m for m in target_mmsis}

        vessel_pts: Dict[int, List[Tuple[int, float, float, float, Optional[float], str]]] = defaultdict(list)

        with zipfile.ZipFile(zip_path, "r") as zf:
            with zf.open("ais_brest_synopses.csv") as f:
                f.readline()  # header
                row_idx = 0
                for line in f:
                    parts = line.split(b",")
                    mmsi_b = parts[0]
                    if mmsi_b in target_bytes:
                        mmsi = target_bytes[mmsi_b]
                        ts = int(parts[1])
                        lon = float(parts[2])
                        lat = float(parts[3])
                        sog = float(parts[5])
                        heading = float(parts[6]) if parts[6] else None
                        annot = parts[4].decode("utf-8", errors="replace")
                        vessel_pts[mmsi].append((ts, lon, lat, sog, heading, annot))

                    row_idx += 1
                    if max_rows and row_idx >= max_rows:
                        break

        segmenter = cls()
        all_raw_voyages = []
        for mmsi, pts in vessel_pts.items():
            raw_v = segmenter.segment_vessel_points(mmsi, pts)
            all_raw_voyages.extend(raw_v)

        audited_records = segmenter.audit_and_classify_voyages(all_raw_voyages)

        # Separate verified vs audit table (drop raw points from tabular dataframe summary)
        summary_rows = []
        verified_rows = []
        for r in audited_records:
            row_copy = {k: v for k, v in r.items() if k != "points"}
            summary_rows.append(row_copy)
            if r["status"] == "VERIFIED":
                verified_rows.append(row_copy)

        audit_df = pd.DataFrame(summary_rows)
        verified_df = pd.DataFrame(verified_rows)
        return audit_df, verified_df


def extract_prediction_snapshots(
    voyage_points: List[Tuple[int, float, float, float, Optional[float], str]],
    arr_ts_epoch_ms: int,
    sample_interval_minutes: float = 5.0,
    dest_lon: float = 0.0,
    dest_lat: float = 0.0,
) -> List[Dict[str, Any]]:
    """Generates strictly causal intermediate ETA prediction snapshots.

    Enforces:
    - Only observations with obs_time <= prediction_time are exposed.
    - True arrival time is strictly separated as the supervision target.
    - Remaining travel time is positive and computed relative to prediction timestamp.
    """
    if len(voyage_points) < 2:
        return []

    t_start = voyage_points[0][0]
    t_end = arr_ts_epoch_ms
    step_ms = int(sample_interval_minutes * 60.0 * 1000.0)

    snapshots = []
    # Evaluate at regular intervals while underway
    cur_pred_ts = t_start + step_ms
    while cur_pred_ts < t_end:
        available_pts = [p for p in voyage_points if p[0] <= cur_pred_ts]
        if not available_pts:
            cur_pred_ts += step_ms
            continue

        latest = available_pts[-1]
        latest_ts = latest[0]
        data_freshness_sec = (cur_pred_ts - latest_ts) / 1000.0

        # Target in minutes
        remaining_minutes = (t_end - cur_pred_ts) / 60000.0
        dist_to_dest_m = haversine_m(latest[1], latest[2], dest_lon, dest_lat) if (dest_lon and dest_lat) else None

        snapshots.append({
            "prediction_timestamp_utc": datetime.datetime.fromtimestamp(
                cur_pred_ts / 1000.0, tz=datetime.timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%SZ"),
            "prediction_ts_epoch_ms": cur_pred_ts,
            "latest_observed_ts_utc": datetime.datetime.fromtimestamp(
                latest_ts / 1000.0, tz=datetime.timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%SZ"),
            "data_freshness_seconds": round(data_freshness_sec, 1),
            "feature_latitude": latest[2],
            "feature_longitude": latest[1],
            "feature_sog_knots": latest[3],
            "feature_heading": latest[4],
            "feature_distance_to_dest_m": round(dist_to_dest_m, 1) if dist_to_dest_m is not None else None,
            "feature_observations_so_far": len(available_pts),
            "target_remaining_travel_time_minutes": round(remaining_minutes, 2),
        })

        cur_pred_ts += step_ms

    return snapshots
