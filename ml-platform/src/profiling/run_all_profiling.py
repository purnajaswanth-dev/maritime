"""Driver script executing all safe profiling tasks and dumping structured JSON metadata."""

import json
import os
import sys

from src.profiling.ais_brest import AISBrestProfiler
from src.profiling.ais_geopackage import AISGeoPackageProfiler
from src.profiling.copernicus_netcdf import CopernicusNetCDFProfiler
from src.profiling.gtfs_profiler import GTFSProfiler


def run():
    print("=" * 60)
    print("RUNNING COMPREHENSIVE DATA PROFILING (PHASE 01)")
    print("=" * 60)

    # 1. Copernicus NetCDF
    print("\n--- Task 3: Profiling Copernicus NetCDF ---")
    nc_path = "data/downloads/cmems_mod_glo_phy_my_0.083deg_P1D-m_1792083299167.nc"
    nc_prof = CopernicusNetCDFProfiler(nc_path)
    nc_data = nc_prof.profile_dataset()
    print(f"File: {nc_data['filename']} ({nc_data['file_size_bytes']} bytes)")
    print(f"Dimensions: {nc_data['dimensions']}")
    print(f"Time coverage: {nc_data['time_coverage']}")
    print(f"Spatial bounds: {nc_data['spatial_bounds']}")
    print(f"Depth info: {nc_data['depth_info']}")
    print(f"Data variables: {list(nc_data['data_variables'].keys())}")
    for vname, vinfo in nc_data["data_variables"].items():
        print(f"  - {vname}: dims={vinfo['dims']}, units={vinfo['units']}, name={vinfo['long_name']}")
    print(f"Contains uo/vo currents: {nc_data['contains_uo_vo_currents']}")

    # 2. GTFS profiling
    print("\n--- Task 2: Profiling GTFS Archives ---")
    downloads = "data/downloads"
    gtfs_results = []
    for f in sorted(os.listdir(downloads)):
        if f.startswith("mdb-") and f.endswith(".zip"):
            p = os.path.join(downloads, f)
            gprof = GTFSProfiler(p)
            res = gprof.profile_feed()
            gtfs_results.append(res)
            print(f"\nFeed: {f}")
            print(f"  Agency: {res['agency_names']} | Route Types: {res['route_types']}")
            print(f"  Is Ferry: {res['is_ferry_feed']} | Is Bus: {res['is_bus_feed']}")
            print(f"  Routes: {res['route_count']}, Stops: {res['stop_count']}, Trips: {res['trip_count']}")
            print(f"  Spatial Bounds: {res['geographic_bounds']}")
            print(f"  Date Range: {res['date_range']}")
            if res.get("feed_info"):
                print(f"  Feed Info: {res['feed_info']}")
            if res.get("attributions"):
                print(f"  Attributions: {res['attributions']}")

    # 3. Save comprehensive profiling JSON
    output_path = "reports/phase-01-profiling-summary.json"
    summary = {
        "copernicus_netcdf": nc_data,
        "gtfs_feeds": gtfs_results,
    }
    with open(output_path, "w", encoding="utf-8") as out_f:
        json.dump(summary, out_f, indent=2)
    print(f"\nSaved profiling summary to {output_path}")


if __name__ == "__main__":
    run()
