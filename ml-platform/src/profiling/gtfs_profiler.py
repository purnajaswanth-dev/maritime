"""Safe, in-memory GTFS profiler for candidate ferry feeds."""

import csv
import io
import os
import zipfile
from typing import Any, Dict, List, Optional, Set, Tuple


class GTFSProfiler:
    """Profiles GTFS archives directly from zip files without unzipping to disk."""

    def __init__(self, zip_path: str):
        self.zip_path = os.path.normpath(zip_path).replace("\\", "/")
        self.filename = os.path.basename(self.zip_path)

    def _read_csv(self, member_name: str) -> List[Dict[str, str]]:
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            if member_name not in zf.namelist():
                return []
            with zf.open(member_name, "r") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", errors="replace"))
                return list(reader)

    def profile_feed(self) -> Dict[str, Any]:
        """Profiles agency, routes, stops, trips, date ranges, and license."""
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            members = set(zf.namelist())

        # 1. Agency
        agencies = self._read_csv("agency.txt")
        agency_names = [a.get("agency_name", "") for a in agencies]
        agency_urls = [a.get("agency_url", "") for a in agencies]
        agency_tzs = [a.get("agency_timezone", "") for a in agencies]

        # 2. Routes & Route Types
        routes = self._read_csv("routes.txt")
        route_types = set()
        for r in routes:
            rt = r.get("route_type", "").strip()
            if rt:
                route_types.add(rt)

        is_ferry_feed = "4" in route_types
        is_bus_feed = "3" in route_types and not is_ferry_feed

        # 3. Stops & Geographic Bounding Box
        stops = self._read_csv("stops.txt")
        lats, lons = [], []
        for s in stops:
            lat_str = s.get("stop_lat", "").strip()
            lon_str = s.get("stop_lon", "").strip()
            if lat_str and lon_str:
                try:
                    lats.append(float(lat_str))
                    lons.append(float(lon_str))
                except ValueError:
                    pass

        bounds = None
        if lats and lons:
            bounds = {
                "min_lat": min(lats),
                "min_lon": min(lons),
                "max_lat": max(lats),
                "max_lon": max(lons),
            }

        # 4. Trips
        trips = self._read_csv("trips.txt")

        # 5. Calendar / Schedule Date Ranges
        calendar = self._read_csv("calendar.txt")
        calendar_dates = self._read_csv("calendar_dates.txt")

        start_dates, end_dates = [], []
        for c in calendar:
            sd = c.get("start_date", "").strip()
            ed = c.get("end_date", "").strip()
            if sd: start_dates.append(sd)
            if ed: end_dates.append(ed)

        for cd in calendar_dates:
            d = cd.get("date", "").strip()
            if d:
                start_dates.append(d)
                end_dates.append(d)

        date_range = None
        if start_dates and end_dates:
            date_range = {
                "min_date": min(start_dates),
                "max_date": max(end_dates),
            }

        # 6. Feed Info & License / Attributions
        feed_info = self._read_csv("feed_info.txt")
        attributions = self._read_csv("attributions.txt")

        return {
            "archive_filename": self.filename,
            "agency_names": agency_names,
            "agency_urls": agency_urls,
            "timezones": agency_tzs,
            "route_types": sorted(list(route_types)),
            "is_ferry_feed": is_ferry_feed,
            "is_bus_feed": is_bus_feed,
            "route_count": len(routes),
            "stop_count": len(stops),
            "trip_count": len(trips),
            "geographic_bounds": bounds,
            "date_range": date_range,
            "has_feed_info": len(feed_info) > 0,
            "feed_info": feed_info[0] if feed_info else None,
            "attributions": attributions if attributions else None,
        }
