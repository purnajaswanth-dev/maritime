"""Safe, non-extracting inspector for large AIS GeoPackage archives using GDAL /vsizip/."""

import os
from typing import Any, Dict, List, Optional
import pyogrio
import pandas as pd


class AISGeoPackageProfiler:
    """Inspects GeoPackage files inside zip archives without extracting them."""

    def __init__(self, zip_path: str, internal_gpkg_name: str = "AISVesselTracks2026-03.gpkg"):
        self.zip_path = os.path.normpath(zip_path).replace("\\", "/")
        self.internal_gpkg_name = internal_gpkg_name
        self.vsi_path = f"/vsizip/{self.zip_path}/{self.internal_gpkg_name}"

    def get_layer_metadata(self) -> Dict[str, Any]:
        """Reads layer metadata, schema, CRS, total bounds, and feature count."""
        layers = pyogrio.list_layers(self.vsi_path)
        if len(layers) == 0:
            raise ValueError(f"No layers found in {self.vsi_path}")

        primary_layer = layers[0][0]
        info = pyogrio.read_info(self.vsi_path, layer=primary_layer)

        fields_dict = {}
        for name, dtype in zip(info["fields"], info["dtypes"]):
            fields_dict[name] = str(dtype)

        return {
            "layer_name": primary_layer,
            "geometry_type": info["geometry_type"],
            "feature_count": info["features"],
            "crs": str(info["crs"]),
            "total_bounds": list(info["total_bounds"]) if info["total_bounds"] else None,
            "fields": fields_dict,
            "fid_column": info["fid_column"],
            "capabilities": info["capabilities"],
        }

    def sample_vessel_types(self, sample_size: int = 5000) -> Dict[str, int]:
        """Reads a bounded attribute sample without geometry to profile vessel type distribution."""
        df = pyogrio.read_dataframe(
            self.vsi_path,
            read_geometry=False,
            columns=["vessel_type_name"],
            max_features=sample_size,
        )
        counts = df["vessel_type_name"].value_counts().to_dict()
        return counts

    def query_passenger_vessels(self, max_features: Optional[int] = 500) -> pd.DataFrame:
        """Queries passenger/ferry tracks without geometry for schema and temporal analysis."""
        df = pyogrio.read_dataframe(
            self.vsi_path,
            read_geometry=False,
            columns=[
                "mmsi",
                "vessel_name",
                "imo",
                "vessel_type_name",
                "start_time",
                "end_time",
                "duration_minutes",
                "vessel_length",
                "draft",
            ],
            where="vessel_type_name LIKE '%Passenger%'",
            max_features=max_features,
        )
        return df
