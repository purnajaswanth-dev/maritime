"""Departure scheduler for expanding GTFS services into concrete daily departures.

Generates departures with standardized identifiers (e.g. DEP-20261024-BRE-CNQ-0830),
respects day-of-week active patterns, season boundaries, and holiday exceptions.
Anchored to Europe/Paris timezone with daylight-saving support.
"""

from dataclasses import asdict, dataclass
import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import zoneinfo

from src.timetable.gtfs_loader import GTFSLoader, ServiceDefinition

PARIS_TZ = zoneinfo.ZoneInfo("Europe/Paris")

# Terminal code lookup for clean departure IDs
TERMINAL_CODES = {
    "BREST": "BRE",
    "LE_CONQUET": "CNQ",
    "MOLENE": "MOL",
    "OUESSANT_STIFF": "OUE",
    "AUDIERNE": "AUD",
    "ILE_DE_SEIN": "SEI",
    "CAMARET": "CAM",
}

WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


@dataclass
class Departure:
    departure_id: str
    trip_id: str
    route_id: str
    corridor: str
    origin_terminal_id: str
    dest_terminal_id: str
    vessel_id: Optional[str]
    vessel_name: Optional[str]
    tracking_supported: bool
    service_date: str  # YYYY-MM-DD
    scheduled_departure_time: str  # HH:MM:SS
    scheduled_arrival_time: str  # HH:MM:SS
    scheduled_departure_utc: str  # ISO-8601
    scheduled_arrival_utc: str  # ISO-8601
    scheduled_departure_epoch_s: float
    scheduled_arrival_epoch_s: float
    duration_minutes: float
    status: str = "SCHEDULED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DepartureScheduler:
    """Expands timetable services into dated departures for any calendar day."""

    def __init__(self, services_or_path: Any):
        if isinstance(services_or_path, list):
            self.services = services_or_path
        elif isinstance(services_or_path, (str, Path)):
            p = Path(services_or_path)
            if p.suffix.lower() == ".json":
                with open(p, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self.services = [ServiceDefinition(**r) for r in raw]
            elif p.suffix.lower() == ".zip" or p.is_dir():
                loader = GTFSLoader(str(p))
                self.services = loader.load_services()
            else:
                raise ValueError(f"Unsupported services input path: {services_or_path}")
        else:
            raise TypeError("services_or_path must be a list of ServiceDefinition or a path string")

    def get_departures_for_date(self, target_date: datetime.date) -> List[Departure]:
        """Expands services into departures for target_date respecting calendar & exceptions."""
        date_str = target_date.strftime("%Y%m%d")
        date_iso = target_date.strftime("%Y-%m-%d")
        weekday_idx = target_date.weekday()
        weekday_name = WEEKDAY_NAMES[weekday_idx]

        departures: List[Departure] = []

        for s in self.services:
            # 1. Season validity check
            start_d = s.season_validity.get("start_date", "19700101")
            end_d = s.season_validity.get("end_date", "20991231")
            if not (start_d <= date_str <= end_d):
                continue

            # 2. Check calendar exceptions
            is_active = s.days_of_week.get(weekday_name, False)
            for exc in s.calendar_exceptions:
                if exc.get("date") == date_str:
                    if exc.get("exception_type") == "REMOVED":
                        is_active = False
                    elif exc.get("exception_type") == "ADDED":
                        is_active = True

            if not is_active:
                continue

            # 3. Construct departure ID: DEP-YYYYMMDD-ORIG-DEST-HHMM
            orig_code = TERMINAL_CODES.get(s.origin_terminal_id, s.origin_terminal_id[:3])
            dest_code = TERMINAL_CODES.get(s.dest_terminal_id, s.dest_terminal_id[:3])
            dep_hhmm = s.departure_time[:5].replace(":", "")
            dep_id = f"DEP-{date_str}-{orig_code}-{dest_code}-{dep_hhmm}"

            # 4. Calculate UTC timestamps via Paris timezone
            dep_h, dep_m, dep_s = [int(p) for p in s.departure_time.split(":")]
            dep_dt_paris = datetime.datetime(
                target_date.year, target_date.month, target_date.day,
                dep_h, dep_m, dep_s, tzinfo=PARIS_TZ
            )
            dep_dt_utc = dep_dt_paris.astimezone(datetime.timezone.utc)
            dep_epoch_s = dep_dt_utc.timestamp()

            arr_h, arr_m, arr_s = [int(p) for p in s.arrival_time.split(":")]
            # Check if arrival crosses midnight into next day
            arr_date = target_date
            if (arr_h * 3600 + arr_m * 60 + arr_s) < (dep_h * 3600 + dep_m * 60 + dep_s):
                arr_date = target_date + datetime.timedelta(days=1)

            arr_dt_paris = datetime.datetime(
                arr_date.year, arr_date.month, arr_date.day,
                arr_h, arr_m, arr_s, tzinfo=PARIS_TZ
            )
            arr_dt_utc = arr_dt_paris.astimezone(datetime.timezone.utc)
            arr_epoch_s = arr_dt_utc.timestamp()

            departures.append(Departure(
                departure_id=dep_id,
                trip_id=s.trip_id,
                route_id=s.route_id,
                corridor=s.corridor,
                origin_terminal_id=s.origin_terminal_id,
                dest_terminal_id=s.dest_terminal_id,
                vessel_id=s.vessel_id,
                vessel_name=s.vessel_name,
                tracking_supported=s.tracking_supported,
                service_date=date_iso,
                scheduled_departure_time=s.departure_time,
                scheduled_arrival_time=s.arrival_time,
                scheduled_departure_utc=dep_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                scheduled_arrival_utc=arr_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                scheduled_departure_epoch_s=dep_epoch_s,
                scheduled_arrival_epoch_s=arr_epoch_s,
                duration_minutes=s.duration_minutes,
                status="SCHEDULED",
            ))

        # Sort chronologically by scheduled departure time
        departures.sort(key=lambda d: d.scheduled_departure_epoch_s)
        return departures
