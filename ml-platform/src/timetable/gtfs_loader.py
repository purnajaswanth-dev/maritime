"""Authoritative GTFS schedule parser and normalizer for Where Is My Ferry?

Transforms GTFS stops, routes, trips, stop_times, calendar, and calendar_dates into
normalized service entities with corridor and vessel mapping.
Enforces Rule 6: Unmodelled services are strictly flagged tracking_supported=false.
"""

from dataclasses import asdict, dataclass
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import zipfile
import pandas as pd


# Authoritative mapping of modelled corridors to engine virtual vessels
MODELLED_CORRIDORS: Dict[str, Dict[str, Any]] = {
    "BREST_LE_CONQUET": {
        "vessel_id": "V-FROMVEUR-SIM",
        "vessel_name": "SIM_FROMVEUR_EXPRESS",
        "tracking_supported": True,
    },
    "LE_CONQUET_BREST": {
        "vessel_id": "V-AZENOR-SIM",
        "vessel_name": "SIM_AZENOR_VOYAGER",
        "tracking_supported": True,
    },
    "BREST_OUESSANT_STIFF": {
        "vessel_id": "V-OUESSANT-SIM",
        "vessel_name": "SIM_IROISE_STAR",
        "tracking_supported": True,
    },
    "AUDIERNE_ILE_DE_SEIN": {
        "vessel_id": "V-SEIN-SIM",
        "vessel_name": "SIM_SEIN_SHUTTLE",
        "tracking_supported": True,
    },
}

# Terminal stop ID normalization
TERMINAL_NORMALIZATION: Dict[str, str] = {
    "BREST": "BREST",
    "LE_CONQUET": "LE_CONQUET",
    "MOLENE": "MOLENE",
    "OUESSANT_STIFF": "OUESSANT_STIFF",
    "AUDIERNE": "AUDIERNE",
    "ILE_DE_SEIN": "ILE_DE_SEIN",
    "CAMARET": "CAMARET",
}


def parse_time_to_seconds(time_str: str) -> int:
    """Parses GTFS time string (HH:MM:SS) into total seconds from midnight.
    
    Supports times >= 24:00:00 (crossing midnight).
    """
    parts = time_str.strip().split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid GTFS time format: '{time_str}', expected HH:MM:SS")
    h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
    return h * 3600 + m * 60 + s


def format_seconds_to_time(total_seconds: int) -> str:
    """Formats total seconds into HH:MM:SS string, modulo 24 hours."""
    mod_seconds = total_seconds % 86400
    h = mod_seconds // 3600
    m = (mod_seconds % 3600) // 60
    s = mod_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


@dataclass
class ServiceDefinition:
    service_id: str
    trip_id: str
    route_id: str
    route_name: str
    origin_terminal_id: str
    dest_terminal_id: str
    corridor: str
    departure_time: str
    arrival_time: str
    duration_minutes: float
    days_of_week: Dict[str, bool]
    season_validity: Dict[str, str]
    calendar_exceptions: List[Dict[str, str]]
    vessel_id: Optional[str]
    vessel_name: Optional[str]
    tracking_supported: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GTFSLoader:
    """Parses and normalizes raw GTFS archives or directories into queryable services."""

    def __init__(self, source_path: str):
        self.source_path = Path(source_path)
        if not self.source_path.exists():
            raise FileNotFoundError(f"GTFS source path does not exist: {source_path}")

    def _read_table(self, filename: str) -> pd.DataFrame:
        """Reads a CSV table from a zip archive or directory."""
        if self.source_path.is_file() and self.source_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(self.source_path, "r") as zf:
                if filename not in zf.namelist():
                    raise FileNotFoundError(f"Required GTFS table '{filename}' missing from archive.")
                with zf.open(filename, "r") as f:
                    return pd.read_csv(f, dtype=str)
        elif self.source_path.is_dir():
            file_path = self.source_path / filename
            if not file_path.exists():
                raise FileNotFoundError(f"Required GTFS table '{filename}' missing from directory.")
            return pd.read_csv(file_path, dtype=str)
        else:
            raise ValueError(f"Unsupported GTFS source: {self.source_path}")

    def load_services(self) -> List[ServiceDefinition]:
        """Loads and normalizes all trips into concrete ServiceDefinition records."""
        # 1. Load mandatory tables
        routes_df = self._read_table("routes.txt")
        trips_df = self._read_table("trips.txt")
        stop_times_df = self._read_table("stop_times.txt")
        calendar_df = self._read_table("calendar.txt")

        # 2. Optional calendar_dates table
        try:
            calendar_dates_df = self._read_table("calendar_dates.txt")
        except FileNotFoundError:
            calendar_dates_df = pd.DataFrame(columns=["service_id", "date", "exception_type"])

        # Validate mandatory columns
        req_routes = {"route_id"}
        req_trips = {"route_id", "trip_id", "service_id"}
        req_stop_times = {"trip_id", "stop_id", "stop_sequence", "departure_time", "arrival_time"}
        req_calendar = {"service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"}

        if not req_routes.issubset(routes_df.columns):
            raise ValueError(f"routes.txt missing columns: {req_routes - set(routes_df.columns)}")
        if not req_trips.issubset(trips_df.columns):
            raise ValueError(f"trips.txt missing columns: {req_trips - set(trips_df.columns)}")
        if not req_stop_times.issubset(stop_times_df.columns):
            raise ValueError(f"stop_times.txt missing columns: {req_stop_times - set(stop_times_df.columns)}")
        if not req_calendar.issubset(calendar_df.columns):
            raise ValueError(f"calendar.txt missing columns: {req_calendar - set(calendar_df.columns)}")

        # Build index lookups
        routes_lookup = {}
        for _, r in routes_df.iterrows():
            r_id = r["route_id"]
            r_name = r.get("route_long_name") or r.get("route_short_name") or r_id
            routes_lookup[r_id] = r_name

        calendar_lookup = {}
        for _, c in calendar_df.iterrows():
            s_id = c["service_id"]
            calendar_lookup[s_id] = {
                "days_of_week": {
                    "monday": c["monday"] == "1",
                    "tuesday": c["tuesday"] == "1",
                    "wednesday": c["wednesday"] == "1",
                    "thursday": c["thursday"] == "1",
                    "friday": c["friday"] == "1",
                    "saturday": c["saturday"] == "1",
                    "sunday": c["sunday"] == "1",
                },
                "season_validity": {
                    "start_date": c["start_date"],
                    "end_date": c["end_date"],
                },
            }

        exceptions_lookup = {}
        for _, cd in calendar_dates_df.iterrows():
            s_id = cd["service_id"]
            if s_id not in exceptions_lookup:
                exceptions_lookup[s_id] = []
            exceptions_lookup[s_id].append({
                "date": cd["date"],
                "exception_type": "ADDED" if cd["exception_type"] == "1" else "REMOVED",
            })

        # Process stop_times per trip
        stop_times_df["stop_sequence"] = pd.to_numeric(stop_times_df["stop_sequence"])
        stop_times_grouped = stop_times_df.sort_values("stop_sequence").groupby("trip_id")

        services: List[ServiceDefinition] = []

        for _, trip in trips_df.iterrows():
            trip_id = trip["trip_id"]
            route_id = trip["route_id"]
            service_id = trip["service_id"]

            if trip_id not in stop_times_grouped.groups:
                continue

            trip_stops = stop_times_grouped.get_group(trip_id)
            if len(trip_stops) < 2:
                continue

            origin_stop = trip_stops.iloc[0]["stop_id"].strip()
            dest_stop = trip_stops.iloc[-1]["stop_id"].strip()

            dep_time_raw = trip_stops.iloc[0]["departure_time"].strip()
            arr_time_raw = trip_stops.iloc[-1]["arrival_time"].strip()

            # Calculate seconds & handle midnight crossing
            dep_sec = parse_time_to_seconds(dep_time_raw)
            arr_sec = parse_time_to_seconds(arr_time_raw)

            if arr_sec < dep_sec:
                # Trip crossed midnight into the next day
                arr_sec += 86400

            duration_min = round((arr_sec - dep_sec) / 60.0, 2)

            dep_time_formatted = format_seconds_to_time(dep_sec)
            arr_time_formatted = format_seconds_to_time(arr_sec)

            corridor = f"{origin_stop}_{dest_stop}"
            route_name = routes_lookup.get(route_id, route_id)

            cal_data = calendar_lookup.get(service_id, {
                "days_of_week": {d: True for d in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]},
                "season_validity": {"start_date": "20260101", "end_date": "20261231"},
            })

            exceptions = exceptions_lookup.get(service_id, [])

            # Corridor & vessel mapping (Rule 6 enforcement)
            if corridor in MODELLED_CORRIDORS:
                mapping = MODELLED_CORRIDORS[corridor]
                vessel_id = mapping["vessel_id"]
                vessel_name = mapping["vessel_name"]
                tracking_supported = True
            else:
                vessel_id = None
                vessel_name = None
                tracking_supported = False

            services.append(ServiceDefinition(
                service_id=service_id,
                trip_id=trip_id,
                route_id=route_id,
                route_name=route_name,
                origin_terminal_id=origin_stop,
                dest_terminal_id=dest_stop,
                corridor=corridor,
                departure_time=dep_time_formatted,
                arrival_time=arr_time_formatted,
                duration_minutes=duration_min,
                days_of_week=cal_data["days_of_week"],
                season_validity=cal_data["season_validity"],
                calendar_exceptions=exceptions,
                vessel_id=vessel_id,
                vessel_name=vessel_name,
                tracking_supported=tracking_supported,
            ))

        return services

    def export_normalized_services(self, output_json_path: str, output_parquet_path: Optional[str] = None) -> List[ServiceDefinition]:
        """Parses services and writes them to normalized services.json and optional parquet."""
        services = self.load_services()
        data = [s.to_dict() for s in services]

        out_json = Path(output_json_path)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        if output_parquet_path:
            out_pq = Path(output_parquet_path)
            out_pq.parent.mkdir(parents=True, exist_ok=True)
            # Flatten dicts for clean parquet serialization
            flat_rows = []
            for s in services:
                r = s.to_dict()
                r["days_of_week_json"] = json.dumps(r["days_of_week"])
                r["season_validity_json"] = json.dumps(r["season_validity"])
                r["calendar_exceptions_json"] = json.dumps(r["calendar_exceptions"])
                del r["days_of_week"]
                del r["season_validity"]
                del r["calendar_exceptions"]
                flat_rows.append(r)
            df = pd.DataFrame(flat_rows)
            df.to_parquet(out_pq, index=False)

        return services
