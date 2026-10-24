"""Materializes causal prediction snapshots from verified voyages."""

from collections import defaultdict
import datetime
import json
import math
from pathlib import Path
import sys
import time
import zipfile
import numpy as np
import pandas as pd
import xarray as xr

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.ingestion.trajectory_segmenter import TERMINALS, haversine_m

# Load verified voyages
verified_df = pd.read_parquet(repo_root / "data" / "processed" / "verified_voyages.parquet")
print(f"Loaded {len(verified_df)} verified voyages.")

# Create index of voyages by mmsi
voyage_lookup = defaultdict(list)
for _, r in verified_df.iterrows():
    voyage_lookup[r["mmsi"]].append({
        "voyage_id": r["voyage_id"],
        "mmsi": r["mmsi"],
        "vessel_name": r["vessel_name"],
        "dep_terminal": r["dep_terminal"],
        "arr_terminal": r["arr_terminal"],
        "dep_ts": r["dep_ts_epoch_ms"],
        "arr_ts": r["arr_ts_epoch_ms"],
        "duration_minutes": r["duration_minutes"],
        "evidence_grade": r["evidence_grade"],
    })

# Sort voyages by dep_ts
for m in voyage_lookup:
    voyage_lookup[m].sort(key=lambda x: x["dep_ts"])

# Extract pings for these vessels
zip_path = repo_root / "data" / "downloads" / "ais_brest_synopses_v0.8.zip"
target_bytes = {str(m).encode("utf-8"): m for m in voyage_lookup}
vessel_pts = {m: [] for m in voyage_lookup}

print("Scanning ais_brest_synopses.csv to extract points for snapshot generation...")
t0 = time.time()
with zipfile.ZipFile(zip_path, "r") as zf:
    with zf.open("ais_brest_synopses.csv") as f:
        f.readline()
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

for m in vessel_pts:
    vessel_pts[m].sort(key=lambda x: x[0])
print(f"Loaded points in {time.time() - t0:.2f}s.")

# Preload regional Copernicus ocean currents into memory (Brest / Iroise Sea bounding box)
nc_path = repo_root / "data" / "downloads" / "cmems_mod_glo_phy_my_0.083deg_P1D-m_1792083299167.nc"
print("Preloading regional Copernicus ocean current grid into memory...")
t_nc = time.time()
ds_nc = xr.open_dataset(nc_path, engine="h5netcdf")
reg_currents = ds_nc[["uo", "vo"]].sel(
    latitude=slice(47.9, 48.6),
    longitude=slice(-5.2, -4.3)
).load()
print(f"Loaded regional ocean grid in {time.time() - t_nc:.2f}s.")

# Generate snapshots at 5-minute interval
sample_interval_ms = 5 * 60 * 1000
snapshots = []
rejected_snapshots = []

print("Generating prediction snapshots under strict causal contract...")
t1 = time.time()

for mmsi, voyages in voyage_lookup.items():
    pts = vessel_pts[mmsi]
    if not pts:
        continue
    
    pt_idx = 0
    n_pts = len(pts)
    
    for v in voyages:
        v_id = v["voyage_id"]
        v_dep = v["dep_ts"]
        v_arr = v["arr_ts"]
        dep_term = v["dep_terminal"]
        arr_term = v["arr_terminal"]
        dest_coords = TERMINALS.get(arr_term, {"lon": 0.0, "lat": 0.0})
        
        while pt_idx < n_pts and pts[pt_idx][0] < v_dep:
            pt_idx += 1
            
        voyage_pts = []
        p_scan = pt_idx
        while p_scan < n_pts and pts[p_scan][0] <= v_arr:
            voyage_pts.append(pts[p_scan])
            p_scan += 1
            
        if len(voyage_pts) < 2:
            rejected_snapshots.append({"voyage_id": v_id, "reason": "Insufficient points in voyage window"})
            continue
            
        cur_pred_ts = v_dep + sample_interval_ms
        while cur_pred_ts < v_arr:
            avail = [p for p in voyage_pts if p[0] <= cur_pred_ts]
            if not avail:
                cur_pred_ts += sample_interval_ms
                continue
                
            latest = avail[-1]
            latest_ts = latest[0]
            lat = latest[2]
            lon = latest[1]
            sog = latest[3]
            heading = latest[4] if latest[4] is not None else 0.0
            
            data_freshness_sec = (cur_pred_ts - latest_ts) / 1000.0
            elapsed_min = (cur_pred_ts - v_dep) / 60000.0
            dist_to_dest_m = haversine_m(lon, lat, dest_coords["lon"], dest_coords["lat"])
            remaining_min = (v_arr - cur_pred_ts) / 60000.0
            
            if remaining_min <= 0:
                rejected_snapshots.append({"voyage_id": v_id, "pred_ts": cur_pred_ts, "reason": "Non-positive remaining time"})
                cur_pred_ts += sample_interval_ms
                continue
                
            dt_pred = datetime.datetime.fromtimestamp(cur_pred_ts / 1000.0, tz=datetime.timezone.utc)
            date_str = dt_pred.strftime("%Y-%m-%d")
            dt_pred_iso = dt_pred.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Fast in-memory ocean current lookup
            try:
                curr_pt = reg_currents.sel(time=date_str, latitude=lat, longitude=lon, method="nearest")
                uo = float(curr_pt["uo"].values.squeeze())
                vo = float(curr_pt["vo"].values.squeeze())
                curr_mag = float(np.sqrt(uo**2 + vo**2))
                
                hdg_rad = math.radians(heading)
                along_track_curr_knots = float((uo * math.sin(hdg_rad) + vo * math.cos(hdg_rad)) * 1.94384)
            except Exception:
                uo, vo, curr_mag, along_track_curr_knots = None, None, None, None
                
            snapshots.append({
                "snapshot_id": f"{v_id}_SNAP_{cur_pred_ts}",
                "voyage_id": v_id,
                "mmsi": mmsi,
                "vessel_name": v["vessel_name"],
                "dep_terminal": dep_term,
                "arr_terminal": arr_term,
                "corridor": f"{dep_term}_{arr_term}",
                "prediction_timestamp_utc": dt_pred_iso,
                "prediction_ts_epoch_ms": cur_pred_ts,
                "latest_observed_ts_utc": datetime.datetime.fromtimestamp(latest_ts / 1000.0, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "latest_observed_ts_epoch_ms": latest_ts,
                "data_freshness_seconds": round(data_freshness_sec, 1),
                "elapsed_time_minutes": round(elapsed_min, 2),
                "feature_latitude": lat,
                "feature_longitude": lon,
                "feature_sog_knots": sog,
                "feature_heading": heading,
                "feature_distance_to_dest_m": round(dist_to_dest_m, 1),
                "feature_observations_so_far": len(avail),
                "feature_uo_current_ms": round(uo, 4) if uo is not None else None,
                "feature_vo_current_ms": round(vo, 4) if vo is not None else None,
                "feature_current_magnitude_ms": round(curr_mag, 4) if curr_mag is not None else None,
                "feature_along_track_current_knots": round(along_track_curr_knots, 3) if along_track_curr_knots is not None else None,
                "target_remaining_travel_time_minutes": round(remaining_min, 2),
                "evidence_grade": v["evidence_grade"],
            })
            
            cur_pred_ts += sample_interval_ms

print(f"Generated {len(snapshots):,} snapshots in {time.time() - t1:.2f}s. Rejected snapshots: {len(rejected_snapshots)}.")
snap_df = pd.DataFrame(snapshots)
output_path = repo_root / "data" / "processed" / "phase_05_prediction_snapshots.parquet"
snap_df.to_parquet(output_path, index=False)
print(f"Saved snapshot dataset to {output_path} ({output_path.stat().st_size:,} bytes).")

# Save rejected snapshots audit log if any
rej_path = repo_root / "data" / "interim" / "phase_05_rejected_snapshots.parquet"
rej_df = pd.DataFrame(rejected_snapshots)
rej_df.to_parquet(rej_path, index=False)
print(f"Saved rejected snapshots log to {rej_path} ({len(rej_df)} rows).")
