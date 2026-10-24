"""Generates the authoritative Penn ar Bed GTFS schedule feed.

Covers:
- Year-round and seasonal services
- Terminals in Brest & Iroise Sea
- Modelled corridors with vessel links
- Unmodelled/seasonal services (e.g. Camaret summer service without AIS history)
"""

import os
import zipfile
import csv

def generate_gtfs():
    out_dir = os.path.normpath("c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/timetable/gtfs")
    os.makedirs(out_dir, exist_ok=True)
    zip_path = os.path.normpath("c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/downloads/penn_ar_bed_gtfs.zip")

    # 1. agency.txt
    agency_rows = [
        ["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang", "agency_phone"],
        ["PAB", "Penn ar Bed", "https://pennarbed.fr", "Europe/Paris", "fr", "0298807080"],
    ]
    with open(os.path.join(out_dir, "agency.txt"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(agency_rows)

    # 2. stops.txt
    stops_rows = [
        ["stop_id", "stop_name", "stop_lat", "stop_lon", "zone_id", "location_type"],
        ["BREST", "Gare Maritime de Brest", "48.3828", "-4.4855", "ZONE_BREST", "0"],
        ["LE_CONQUET", "Port du Conquet", "48.3585", "-4.7788", "ZONE_CONQUET", "0"],
        ["MOLENE", "Port de Molene", "48.3970", "-4.9965", "ZONE_MOLENE", "0"],
        ["OUESSANT_STIFF", "Port du Stiff (Ouessant)", "48.4632", "-5.0492", "ZONE_OUESSANT", "0"],
        ["AUDIERNE", "Port de Sainte-Evette (Audierne)", "48.0195", "-4.5385", "ZONE_AUDIERNE", "0"],
        ["ILE_DE_SEIN", "Port de l'Ile de Sein", "48.0375", "-4.8505", "ZONE_SEIN", "0"],
        ["CAMARET", "Port de Camaret-sur-Mer", "48.2780", "-4.5940", "ZONE_CAMARET", "0"],
    ]
    with open(os.path.join(out_dir, "stops.txt"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(stops_rows)

    # 3. routes.txt
    routes_rows = [
        ["route_id", "agency_id", "route_short_name", "route_long_name", "route_desc", "route_type", "route_color", "route_text_color"],
        ["R_BRE_CNQ", "PAB", "BRE-CNQ", "Brest - Le Conquet", "Liaison Brest Le Conquet", "4", "14B8A6", "FFFFFF"],
        ["R_CNQ_BRE", "PAB", "CNQ-BRE", "Le Conquet - Brest", "Liaison Le Conquet Brest", "4", "14B8A6", "FFFFFF"],
        ["R_BRE_OUE", "PAB", "BRE-OUE", "Brest - Ouessant", "Liaison Brest Ouessant Stiff", "4", "0D3045", "FFFFFF"],
        ["R_OUE_BRE", "PAB", "OUE-BRE", "Ouessant - Brest", "Liaison Ouessant Stiff Brest", "4", "0D3045", "FFFFFF"],
        ["R_CNQ_MOL", "PAB", "CNQ-MOL", "Le Conquet - Molene", "Liaison Le Conquet Molene", "4", "14B8A6", "FFFFFF"],
        ["R_MOL_CNQ", "PAB", "MOL-CNQ", "Molene - Le Conquet", "Liaison Molene Le Conquet", "4", "14B8A6", "FFFFFF"],
        ["R_MOL_OUE", "PAB", "MOL-OUE", "Molene - Ouessant", "Liaison Molene Ouessant", "4", "0D3045", "FFFFFF"],
        ["R_OUE_MOL", "PAB", "OUE-MOL", "Ouessant - Molene", "Liaison Ouessant Molene", "4", "0D3045", "FFFFFF"],
        ["R_AUD_SEI", "PAB", "AUD-SEI", "Audierne - Ile de Sein", "Liaison Audierne Sainte-Evette - Ile de Sein", "4", "14B8A6", "FFFFFF"],
        ["R_SEI_AUD", "PAB", "SEI-AUD", "Ile de Sein - Audierne", "Liaison Ile de Sein - Audierne Sainte-Evette", "4", "14B8A6", "FFFFFF"],
        ["R_BRE_CAM", "PAB", "BRE-CAM", "Brest - Camaret", "Liaison estivale Brest - Camaret", "4", "0D3045", "FFFFFF"],
        ["R_CAM_BRE", "PAB", "CAM-BRE", "Camaret - Brest", "Liaison estivale Camaret - Brest", "4", "0D3045", "FFFFFF"],
    ]
    with open(os.path.join(out_dir, "routes.txt"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(routes_rows)

    # 4. calendar.txt
    calendar_rows = [
        ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"],
        ["DAILY_YEAR_ROUND", "1", "1", "1", "1", "1", "1", "1", "20260101", "20261231"],
        ["WEEKDAY_REGULAR", "1", "1", "1", "1", "1", "0", "0", "20260101", "20261231"],
        ["WEEKEND_REGULAR", "0", "0", "0", "0", "0", "1", "1", "20260101", "20261231"],
        ["SUMMER_ONLY", "1", "1", "1", "1", "1", "1", "1", "20260615", "20260915"],
    ]
    with open(os.path.join(out_dir, "calendar.txt"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(calendar_rows)

    # 5. calendar_dates.txt
    calendar_dates_rows = [
        ["service_id", "date", "exception_type"],
        ["WEEKDAY_REGULAR", "20260501", "2"],  # Labour day
        ["WEEKDAY_REGULAR", "20260714", "2"],  # National day
        ["WEEKDAY_REGULAR", "20260815", "2"],  # Assumption
        ["DAILY_YEAR_ROUND", "20261225", "2"], # Christmas suspension
    ]
    with open(os.path.join(out_dir, "calendar_dates.txt"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(calendar_dates_rows)

    # 6. trips.txt
    trips_rows = [
        ["route_id", "service_id", "trip_id", "trip_headsign", "direction_id", "block_id"],
        # Brest -> Le Conquet
        ["R_BRE_CNQ", "DAILY_YEAR_ROUND", "TRIP_BRE_CNQ_0830", "Le Conquet", "0", "BLK_FROMVEUR"],
        ["R_BRE_CNQ", "DAILY_YEAR_ROUND", "TRIP_BRE_CNQ_1200", "Le Conquet", "0", "BLK_FROMVEUR"],
        ["R_BRE_CNQ", "DAILY_YEAR_ROUND", "TRIP_BRE_CNQ_1630", "Le Conquet", "0", "BLK_FROMVEUR"],
        # Le Conquet -> Brest
        ["R_CNQ_BRE", "DAILY_YEAR_ROUND", "TRIP_CNQ_BRE_1000", "Brest", "1", "BLK_AZENOR"],
        ["R_CNQ_BRE", "DAILY_YEAR_ROUND", "TRIP_CNQ_BRE_1400", "Brest", "1", "BLK_AZENOR"],
        ["R_CNQ_BRE", "DAILY_YEAR_ROUND", "TRIP_CNQ_BRE_1800", "Brest", "1", "BLK_AZENOR"],
        # Brest -> Ouessant
        ["R_BRE_OUE", "DAILY_YEAR_ROUND", "TRIP_BRE_OUE_0830", "Ouessant Stiff", "0", "BLK_OUESSANT"],
        ["R_BRE_OUE", "DAILY_YEAR_ROUND", "TRIP_BRE_OUE_1430", "Ouessant Stiff", "0", "BLK_OUESSANT"],
        # Ouessant -> Brest
        ["R_OUE_BRE", "DAILY_YEAR_ROUND", "TRIP_OUE_BRE_1100", "Brest", "1", "BLK_OUESSANT"],
        ["R_OUE_BRE", "DAILY_YEAR_ROUND", "TRIP_OUE_BRE_1700", "Brest", "1", "BLK_OUESSANT"],
        # Audierne -> Ile de Sein
        ["R_AUD_SEI", "DAILY_YEAR_ROUND", "TRIP_AUD_SEI_0930", "Ile de Sein", "0", "BLK_SEIN"],
        ["R_AUD_SEI", "DAILY_YEAR_ROUND", "TRIP_AUD_SEI_1600", "Ile de Sein", "0", "BLK_SEIN"],
        # Ile de Sein -> Audierne
        ["R_SEI_AUD", "DAILY_YEAR_ROUND", "TRIP_SEI_AUD_1100", "Audierne", "1", "BLK_SEIN"],
        ["R_SEI_AUD", "DAILY_YEAR_ROUND", "TRIP_SEI_AUD_1730", "Audierne", "1", "BLK_SEIN"],
        # Le Conquet <-> Molene
        ["R_CNQ_MOL", "DAILY_YEAR_ROUND", "TRIP_CNQ_MOL_0945", "Molene", "0", "BLK_LOCAL"],
        ["R_MOL_CNQ", "DAILY_YEAR_ROUND", "TRIP_MOL_CNQ_1545", "Le Conquet", "1", "BLK_LOCAL"],
        # Molene <-> Ouessant
        ["R_MOL_OUE", "DAILY_YEAR_ROUND", "TRIP_MOL_OUE_1020", "Ouessant", "0", "BLK_LOCAL"],
        ["R_OUE_MOL", "DAILY_YEAR_ROUND", "TRIP_OUE_MOL_1630", "Molene", "1", "BLK_LOCAL"],
        # Summer Brest <-> Camaret
        ["R_BRE_CAM", "SUMMER_ONLY", "TRIP_BRE_CAM_1000", "Camaret", "0", "BLK_SUMMER"],
        ["R_CAM_BRE", "SUMMER_ONLY", "TRIP_CAM_BRE_1730", "Brest", "1", "BLK_SUMMER"],
    ]
    with open(os.path.join(out_dir, "trips.txt"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(trips_rows)

    # 7. stop_times.txt
    stop_times_rows = [
        ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence"],
        # TRIP_BRE_CNQ_0830
        ["TRIP_BRE_CNQ_0830", "08:30:00", "08:30:00", "BREST", "1"],
        ["TRIP_BRE_CNQ_0830", "09:40:00", "09:40:00", "LE_CONQUET", "2"],
        # TRIP_BRE_CNQ_1200
        ["TRIP_BRE_CNQ_1200", "12:00:00", "12:00:00", "BREST", "1"],
        ["TRIP_BRE_CNQ_1200", "13:10:00", "13:10:00", "LE_CONQUET", "2"],
        # TRIP_BRE_CNQ_1630
        ["TRIP_BRE_CNQ_1630", "16:30:00", "16:30:00", "BREST", "1"],
        ["TRIP_BRE_CNQ_1630", "17:40:00", "17:40:00", "LE_CONQUET", "2"],
        # TRIP_CNQ_BRE_1000
        ["TRIP_CNQ_BRE_1000", "10:00:00", "10:00:00", "LE_CONQUET", "1"],
        ["TRIP_CNQ_BRE_1000", "11:10:00", "11:10:00", "BREST", "2"],
        # TRIP_CNQ_BRE_1400
        ["TRIP_CNQ_BRE_1400", "14:00:00", "14:00:00", "LE_CONQUET", "1"],
        ["TRIP_CNQ_BRE_1400", "15:10:00", "15:10:00", "BREST", "2"],
        # TRIP_CNQ_BRE_1800
        ["TRIP_CNQ_BRE_1800", "18:00:00", "18:00:00", "LE_CONQUET", "1"],
        ["TRIP_CNQ_BRE_1800", "19:10:00", "19:10:00", "BREST", "2"],
        # TRIP_BRE_OUE_0830
        ["TRIP_BRE_OUE_0830", "08:30:00", "08:30:00", "BREST", "1"],
        ["TRIP_BRE_OUE_0830", "10:45:00", "10:45:00", "OUESSANT_STIFF", "2"],
        # TRIP_BRE_OUE_1430
        ["TRIP_BRE_OUE_1430", "14:30:00", "14:30:00", "BREST", "1"],
        ["TRIP_BRE_OUE_1430", "16:45:00", "16:45:00", "OUESSANT_STIFF", "2"],
        # TRIP_OUE_BRE_1100
        ["TRIP_OUE_BRE_1100", "11:00:00", "11:00:00", "OUESSANT_STIFF", "1"],
        ["TRIP_OUE_BRE_1100", "13:15:00", "13:15:00", "BREST", "2"],
        # TRIP_OUE_BRE_1700
        ["TRIP_OUE_BRE_1700", "17:00:00", "17:00:00", "OUESSANT_STIFF", "1"],
        ["TRIP_OUE_BRE_1700", "19:15:00", "19:15:00", "BREST", "2"],
        # TRIP_AUD_SEI_0930
        ["TRIP_AUD_SEI_0930", "09:30:00", "09:30:00", "AUDIERNE", "1"],
        ["TRIP_AUD_SEI_0930", "10:30:00", "10:30:00", "ILE_DE_SEIN", "2"],
        # TRIP_AUD_SEI_1600
        ["TRIP_AUD_SEI_1600", "16:00:00", "16:00:00", "AUDIERNE", "1"],
        ["TRIP_AUD_SEI_1600", "17:00:00", "17:00:00", "ILE_DE_SEIN", "2"],
        # TRIP_SEI_AUD_1100
        ["TRIP_SEI_AUD_1100", "11:00:00", "11:00:00", "ILE_DE_SEIN", "1"],
        ["TRIP_SEI_AUD_1100", "12:00:00", "12:00:00", "AUDIERNE", "2"],
        # TRIP_SEI_AUD_1730
        ["TRIP_SEI_AUD_1730", "17:30:00", "17:30:00", "ILE_DE_SEIN", "1"],
        ["TRIP_SEI_AUD_1730", "18:30:00", "18:30:00", "AUDIERNE", "2"],
        # TRIP_CNQ_MOL_0945
        ["TRIP_CNQ_MOL_0945", "09:45:00", "09:45:00", "LE_CONQUET", "1"],
        ["TRIP_CNQ_MOL_0945", "10:15:00", "10:15:00", "MOLENE", "2"],
        # TRIP_MOL_CNQ_1545
        ["TRIP_MOL_CNQ_1545", "15:45:00", "15:45:00", "MOLENE", "1"],
        ["TRIP_MOL_CNQ_1545", "16:15:00", "16:15:00", "LE_CONQUET", "2"],
        # TRIP_MOL_OUE_1020
        ["TRIP_MOL_OUE_1020", "10:20:00", "10:20:00", "MOLENE", "1"],
        ["TRIP_MOL_OUE_1020", "10:50:00", "10:50:00", "OUESSANT_STIFF", "2"],
        # TRIP_OUE_MOL_1630
        ["TRIP_OUE_MOL_1630", "16:30:00", "16:30:00", "OUESSANT_STIFF", "1"],
        ["TRIP_OUE_MOL_1630", "17:00:00", "17:00:00", "MOLENE", "2"],
        # TRIP_BRE_CAM_1000
        ["TRIP_BRE_CAM_1000", "10:00:00", "10:00:00", "BREST", "1"],
        ["TRIP_BRE_CAM_1000", "10:50:00", "10:50:00", "CAMARET", "2"],
        # TRIP_CAM_BRE_1730
        ["TRIP_CAM_BRE_1730", "17:30:00", "17:30:00", "CAMARET", "1"],
        ["TRIP_CAM_BRE_1730", "18:20:00", "18:20:00", "BREST", "2"],
    ]
    with open(os.path.join(out_dir, "stop_times.txt"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(stop_times_rows)

    # Package into zip archive
    gtfs_files = ["agency.txt", "stops.txt", "routes.txt", "trips.txt", "stop_times.txt", "calendar.txt", "calendar_dates.txt"]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in gtfs_files:
            fpath = os.path.join(out_dir, fname)
            zf.write(fpath, arcname=fname)

    print(f"Penn ar Bed GTFS feed generated: {len(gtfs_files)} files written to {out_dir} and packaged to {zip_path}")

if __name__ == "__main__":
    generate_gtfs()
