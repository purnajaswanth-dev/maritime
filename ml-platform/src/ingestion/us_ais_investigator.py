"""Safe queries and sampling on the US MarineCadastre GeoPackage tracklines."""

import logging
import os
import sqlite3
import tempfile
import time
from typing import Any, Dict, List, Optional
import warnings
import numpy as np
import pandas as pd
import pyogrio

logger = logging.getLogger(__name__)


def get_default_temp_gpkg_path() -> str:
    """Returns the default external temporary path outside OneDrive dynamically."""
    base_temp = os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()
    temp_dir = os.path.join(base_temp, "Temp" if "LOCALAPPDATA" in os.environ else "", "where-is-my-ferry-gpkg")
    return os.path.normpath(os.path.join(temp_dir, "AISVesselTracks2026-03.gpkg"))


class USAISInvestigator:
    """Investigation and query engine for US AIS vessel tracks.

    Supports both:
    1. Safe bounded virtual sampling via /vsizip/ (initial slices, spatial bbox).
    2. High-speed indexed querying via a local extracted GeoPackage copy.
    """

    def __init__(
        self,
        zip_path: str = "data/downloads/AISVesselTracks2026-03.zip",
        extracted_gpkg_path: Optional[str] = None,
    ):
        self.zip_path = os.path.normpath(zip_path).replace("\\", "/")
        self.internal_gpkg = "AISVesselTracks2026-03.gpkg"
        self.vsi_path = f"/vsizip/{self.zip_path}/{self.internal_gpkg}"

        # Configurable extracted path (or env var, or default outside OneDrive)
        if extracted_gpkg_path:
            self.extracted_gpkg_path = os.path.normpath(extracted_gpkg_path)
        else:
            env_path = os.environ.get("AIS_INDEXED_GPKG_PATH")
            if env_path and os.path.exists(env_path):
                self.extracted_gpkg_path = os.path.normpath(env_path)
            else:
                default_path = get_default_temp_gpkg_path()
                self.extracted_gpkg_path = default_path if os.path.exists(default_path) else None

    def compute_vessel_type_distribution(self, sample_size: int = 20000) -> Dict[str, Any]:
        """Calculates vessel type distribution with binomial standard error and timing."""
        t0 = time.time()
        logger.info(f"Sampling {sample_size} features via /vsizip/...")
        df = pyogrio.read_dataframe(
            self.vsi_path,
            read_geometry=False,
            columns=["vessel_type_name"],
            max_features=sample_size,
        )
        elapsed = time.time() - t0
        logger.info(f"Sampled {len(df)} features in {elapsed:.2f}s.")

        total = len(df)
        counts = df["vessel_type_name"].value_counts()

        distribution = {}
        for vtype, count in counts.items():
            p = count / total
            se = np.sqrt(p * (1 - p) / total)
            moe = 1.96 * se
            distribution[str(vtype)] = {
                "sample_count": int(count),
                "proportion": float(p),
                "margin_of_error_95pct": float(moe),
                "ci_lower": float(max(0, p - moe)),
                "ci_upper": float(min(1, p + moe)),
            }

        return {
            "sample_size": total,
            "elapsed_seconds": elapsed,
            "sampling_method": "Sequential initial read of first N features from GPKG table",
            "uncertainty_notes": (
                "Initial slice sampling assumes features are roughly uniformly distributed across "
                "the table. True spatial variance may introduce clustering; proportions should be "
                "interpreted as indicative sample estimates, not absolute global population counts."
            ),
            "distribution": distribution,
        }

    def query_passenger_vessels(
        self, limit: Optional[int] = 1000, name_contains: Optional[str] = None
    ) -> pd.DataFrame:
        """Queries passenger records with strict limit to prevent runaway scans."""
        t0 = time.time()
        where_clause = "vessel_type_name LIKE '%Passenger%'"
        if name_contains:
            where_clause += f" AND vessel_name LIKE '%{name_contains}%'"

        source_path = self.extracted_gpkg_path or self.vsi_path
        logger.info(f"Querying passenger vessels from {source_path} (limit={limit})...")
        df = pyogrio.read_dataframe(
            source_path,
            read_geometry=False,
            columns=[
                "mmsi",
                "vessel_name",
                "imo",
                "call_sign",
                "vessel_type",
                "vessel_type_name",
                "vessel_length",
                "width",
                "draft",
                "duration_minutes",
                "start_time",
                "end_time",
            ],
            where=where_clause,
            max_features=limit,
        )
        elapsed = time.time() - t0
        logger.info(f"Returned {len(df)} passenger records in {elapsed:.2f}s.")
        return df

    def query_spatial_window(
        self, min_lon: float, min_lat: float, max_lon: float, max_lat: float, limit: int = 1000
    ) -> pd.DataFrame:
        """Executes a spatial bounding box query using GDAL R-tree spatial filter with timing."""
        t0 = time.time()
        source_path = self.extracted_gpkg_path or self.vsi_path
        logger.info(f"Running spatial RTree query on [{min_lon}, {min_lat}, {max_lon}, {max_lat}] (limit={limit})...")
        df = pyogrio.read_dataframe(
            source_path,
            bbox=(min_lon, min_lat, max_lon, max_lat),
            read_geometry=True,
            columns=[
                "mmsi",
                "vessel_name",
                "vessel_type_name",
                "start_time",
                "end_time",
                "duration_minutes",
            ],
            max_features=limit,
        )
        elapsed = time.time() - t0
        logger.info(f"Spatial query returned {len(df)} features in {elapsed:.2f}s.")
        return df

    def query_by_mmsi(
        self,
        mmsi: int,
        columns: Optional[List[str]] = None,
        read_geometry: bool = True,
    ) -> pd.DataFrame:
        """Queries track records for a specific vessel MMSI using the local indexed GeoPackage.

        Fails with clear messages if:
        1. Local copy is missing.
        2. Index on 'mmsi' is missing.
        3. An unindexed /vsizip/ query is attempted.
        """
        # Guardrail: Never attempt unindexed /vsizip/ full-table scan
        if not self.extracted_gpkg_path:
            raise RuntimeError(
                f"Cannot query MMSI {mmsi} over unindexed virtual stream '/vsizip/'. "
                "The raw GeoPackage inside the ZIP lacks an attribute index on 'mmsi', and an "
                "unindexed full-table scan across 1,446,038 features causes severe I/O thrashing. "
                "Provide an extracted GeoPackage path via constructor parameter 'extracted_gpkg_path' "
                "or set environment variable 'AIS_INDEXED_GPKG_PATH' pointing to the locally indexed copy."
            )

        if not os.path.exists(self.extracted_gpkg_path):
            raise FileNotFoundError(
                f"Configured extracted GeoPackage path does not exist: {self.extracted_gpkg_path}"
            )

        # Verify index exists on the database
        self._verify_mmsi_index(self.extracted_gpkg_path)

        if columns is None:
            columns = [
                "mmsi",
                "vessel_name",
                "imo",
                "call_sign",
                "vessel_type_name",
                "start_time",
                "end_time",
                "duration_minutes",
                "vessel_length",
                "draft",
            ]

        t0 = time.time()
        logger.info(f"Executing indexed query for MMSI {mmsi} against {self.extracted_gpkg_path}...")
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=RuntimeWarning,
                message="Non-conformant content for record.*",
            )
            df = pyogrio.read_dataframe(
                self.extracted_gpkg_path,
                read_geometry=read_geometry,
                columns=columns,
                where=f"mmsi = {int(mmsi)}",
            )
        elapsed = time.time() - t0
        logger.info(f"MMSI {mmsi}: returned {len(df)} tracks in {elapsed:.4f}s.")
        return df

    @staticmethod
    def _verify_mmsi_index(gpkg_path: str, table_name: str = "AIS_Tracks_2026_03", col_name: str = "mmsi") -> None:
        """Verifies that an index on column exists in sqlite_master."""
        con = sqlite3.connect(gpkg_path)
        try:
            cur = con.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql LIKE ?;",
                (table_name, f"%{col_name}%"),
            )
            rows = cur.fetchall()
            if not rows:
                raise RuntimeError(
                    f"Index on column '{col_name}' is missing in table '{table_name}' at {gpkg_path}! "
                    "Run extract_and_index_ais.py to build 'idx_ais_tracks_mmsi' before querying."
                )
        finally:
            con.close()
