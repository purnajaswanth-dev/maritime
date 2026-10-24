"""Safe, lazy metadata profiler for Copernicus Marine NetCDF physics datasets using xarray."""

import os
from typing import Any, Dict, List, Optional
import xarray as xr


class CopernicusNetCDFProfiler:
    """Lazily inspects NetCDF-4/HDF5 ocean physics datasets without loading arrays into memory."""

    def __init__(self, nc_path: str):
        self.nc_path = os.path.normpath(nc_path).replace("\\", "/")
        self.filename = os.path.basename(self.nc_path)

    def profile_dataset(self) -> Dict[str, Any]:
        """Opens dataset lazily with h5netcdf engine and extracts comprehensive metadata."""
        with xr.open_dataset(self.nc_path, engine="h5netcdf", decode_times=True) as ds:
            # 1. Dimensions
            dimensions = {str(k): int(v) for k, v in ds.sizes.items()}

            # 2. Coordinates
            coords = {}
            for c_name, c_val in ds.coords.items():
                coord_info = {
                    "dtype": str(c_val.dtype),
                    "size": int(c_val.size),
                    "attrs": {str(k): str(v) for k, v in c_val.attrs.items()},
                }
                coords[str(c_name)] = coord_info

            # 3. Time coverage and resolution
            time_coverage = None
            if "time" in ds.coords:
                time_var = ds["time"]
                t_min = str(time_var.values.min())
                t_max = str(time_var.values.max())
                time_coverage = {
                    "time_min": t_min,
                    "time_max": t_max,
                    "time_steps": int(time_var.size),
                    "frequency": ds.attrs.get("time_coverage_resolution", "P1D (Daily)"),
                }

            # 4. Spatial Bounds & Resolution
            spatial_bounds = None
            if "latitude" in ds.coords and "longitude" in ds.coords:
                lat = ds["latitude"].values
                lon = ds["longitude"].values
                spatial_bounds = {
                    "lat_min": float(lat.min()),
                    "lat_max": float(lat.max()),
                    "lat_resolution_deg": float(abs(lat[1] - lat[0])) if len(lat) > 1 else None,
                    "lon_min": float(lon.min()),
                    "lon_max": float(lon.max()),
                    "lon_resolution_deg": float(abs(lon[1] - lon[0])) if len(lon) > 1 else None,
                }

            # 5. Depth dimension & Surface levels
            depth_info = None
            if "depth" in ds.coords:
                depth_vals = ds["depth"].values
                depth_info = {
                    "levels_count": int(len(depth_vals)),
                    "surface_level_m": float(depth_vals.min()),
                    "max_depth_m": float(depth_vals.max()),
                    "depth_levels_m": [float(d) for d in depth_vals[:5]],
                }

            # 6. Data Variables
            data_vars = {}
            for v_name, v_da in ds.data_vars.items():
                var_info = {
                    "dims": [str(d) for d in v_da.dims],
                    "dtype": str(v_da.dtype),
                    "standard_name": v_da.attrs.get("standard_name", ""),
                    "long_name": v_da.attrs.get("long_name", ""),
                    "units": v_da.attrs.get("units", ""),
                    "_FillValue": str(v_da.attrs.get("_FillValue", "NaN")),
                }
                data_vars[str(v_name)] = var_info

            # 7. Check for ocean currents uo and vo
            has_currents = "uo" in ds.data_vars and "vo" in ds.data_vars

            return {
                "filename": self.filename,
                "file_size_bytes": os.path.getsize(self.nc_path),
                "global_attributes": {str(k): str(v) for k, v in ds.attrs.items()},
                "dimensions": dimensions,
                "coordinates": coords,
                "time_coverage": time_coverage,
                "spatial_bounds": spatial_bounds,
                "depth_info": depth_info,
                "data_variables": data_vars,
                "contains_uo_vo_currents": has_currents,
            }
