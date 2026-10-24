"""Collocation engine for ocean current features enforcing temporal and spatial validity."""

from typing import Any, Dict, Optional, Tuple
import numpy as np
import xarray as xr


class OceanFeatureCollocator:
    """Collocates vessel trajectories with ocean current components uo/vo from NetCDF."""

    def __init__(self, nc_path: str = "data/downloads/cmems_mod_glo_phy_my_0.083deg_P1D-m_1792083299167.nc"):
        self.nc_path = nc_path
        self._ds: Optional[xr.Dataset] = None

    def _get_dataset(self) -> xr.Dataset:
        if self._ds is None:
            self._ds = xr.open_dataset(self.nc_path, engine="h5netcdf", decode_times=True)
        return self._ds

    def collocate_point(
        self, timestamp_iso: str, lat: float, lon: float
    ) -> Dict[str, Any]:
        """Interpolates daily surface currents for a space-time coordinate.

        Strictly rejects timestamps outside the Copernicus coverage window (Oct 2015 - Mar 2016).
        """
        # Temporal check
        date_str = timestamp_iso[:10]
        if date_str < "2015-10-01" or date_str > "2016-03-31":
            return {
                "collocation_status": "EXCLUDED_TEMPORAL_OUT_OF_BOUNDS",
                "uo_eastward_current_ms": None,
                "vo_northward_current_ms": None,
                "current_magnitude_ms": None,
                "explanation": (
                    f"Timestamp {timestamp_iso} is outside the 2015-10-01 to 2016-03-31 coverage of this Copernicus file. "
                    "Cannot use historical 2015 reanalysis for 2026 or other year observations."
                ),
            }

        ds = self._get_dataset()

        # Spatial check
        lat_min = float(ds["latitude"].min())
        lat_max = float(ds["latitude"].max())
        lon_min = float(ds["longitude"].min())
        lon_max = float(ds["longitude"].max())

        if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
            return {
                "collocation_status": "EXCLUDED_SPATIAL_OUT_OF_BOUNDS",
                "uo_eastward_current_ms": None,
                "vo_northward_current_ms": None,
                "current_magnitude_ms": None,
                "explanation": f"Coordinate ({lat}, {lon}) falls outside Copernicus grid [{lat_min}, {lat_max}], [{lon_min}, {lon_max}].",
            }

        try:
            # Nearest neighbor / bilinear slice on daily reanalysis
            pt_ds = ds.sel(
                time=date_str,
                latitude=lat,
                longitude=lon,
                method="nearest"
            )
            uo = float(pt_ds["uo"].values.squeeze())
            vo = float(pt_ds["vo"].values.squeeze())
            magnitude = float(np.sqrt(uo**2 + vo**2))

            return {
                "collocation_status": "COLLOCATED_DAILY_REANALYSIS",
                "uo_eastward_current_ms": uo,
                "vo_northward_current_ms": vo,
                "current_magnitude_ms": magnitude,
                "explanation": (
                    "Collocated from daily-mean Copernicus GLORYS12V1 reanalysis. Note: Daily resolution "
                    "does not resolve micro-tidal currents or real-time harbour conditions."
                ),
            }
        except Exception as e:
            return {
                "collocation_status": f"ERROR_{type(e).__name__}",
                "uo_eastward_current_ms": None,
                "vo_northward_current_ms": None,
                "current_magnitude_ms": None,
                "explanation": str(e),
            }
