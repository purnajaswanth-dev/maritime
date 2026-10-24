"""Unit tests for profiling modules."""

import os
import pytest
from src.profiling.ais_brest import AISBrestProfiler
from src.profiling.ais_geopackage import AISGeoPackageProfiler
from src.profiling.copernicus_netcdf import CopernicusNetCDFProfiler
from src.profiling.gtfs_profiler import GTFSProfiler


def test_copernicus_netcdf_metadata():
    nc_path = "data/downloads/cmems_mod_glo_phy_my_0.083deg_P1D-m_1792083299167.nc"
    if not os.path.exists(nc_path):
        pytest.skip("Copernicus NetCDF file not present")

    profiler = CopernicusNetCDFProfiler(nc_path)
    res = profiler.profile_dataset()

    assert res["filename"] == os.path.basename(nc_path)
    assert "time" in res["dimensions"]
    assert res["dimensions"]["time"] == 183
    assert res["contains_uo_vo_currents"] is True
    assert "uo" in res["data_variables"]
    assert "vo" in res["data_variables"]
    assert res["spatial_bounds"]["lat_min"] == 25.0
    assert res["spatial_bounds"]["lat_max"] == 60.0
    assert res["time_coverage"]["time_min"].startswith("2015-10-01")
    assert res["time_coverage"]["time_max"].startswith("2016-03-31")


def test_gtfs_ferry_vs_bus_profiling():
    # Test a ferry feed
    ferry_zip = "data/downloads/mdb-3522-202610131556.zip"
    if os.path.exists(ferry_zip):
        f_prof = GTFSProfiler(ferry_zip)
        f_res = f_prof.profile_feed()
        assert f_res["is_ferry_feed"] is True
        assert f_res["is_bus_feed"] is False
        assert "4" in f_res["route_types"]
        assert f_res["geographic_bounds"] is not None

    # Test bus feed (Bee-Line Bus)
    bus_zip = "data/downloads/mdb-2353-202502041949.zip"
    if os.path.exists(bus_zip):
        b_prof = GTFSProfiler(bus_zip)
        b_res = b_prof.profile_feed()
        assert b_res["is_ferry_feed"] is False
        assert b_res["is_bus_feed"] is True
        assert "3" in b_res["route_types"]
        assert "Bee-Line Bus" in b_res["agency_names"]


def test_ais_brest_streaming_sample():
    brest_zip = "data/downloads/ais_brest_synopses_v0.8.zip"
    if not os.path.exists(brest_zip):
        pytest.skip("Brest archive not present")

    profiler = AISBrestProfiler(brest_zip)
    readme = profiler.inspect_readme()
    assert "datACRON" in readme
    assert "Brest area" in readme

    sample = profiler.sample_csv_member("ais_brest_synopses.csv", max_rows=5)
    assert sample["header"][0] == "id"
    assert sample["header"][1] == "timestamp"
    assert sample["header"][2] == "longitude"
    assert sample["header"][3] == "latitude"
    assert len(sample["sample_rows"]) == 5


def test_ais_geopackage_metadata():
    gpkg_zip = "data/downloads/AISVesselTracks2026-03.zip"
    if not os.path.exists(gpkg_zip):
        pytest.skip("AIS GeoPackage archive not present")

    profiler = AISGeoPackageProfiler(gpkg_zip)
    meta = profiler.get_layer_metadata()
    assert meta["layer_name"] == "AIS_Tracks_2026_03"
    assert meta["crs"] == "EPSG:4326"
    assert meta["feature_count"] == 1446038
    assert "mmsi" in meta["fields"]
    assert "start_time" in meta["fields"]
    assert "end_time" in meta["fields"]
