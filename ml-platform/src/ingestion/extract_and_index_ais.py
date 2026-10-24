"""Safe extraction, local indexing, and validation for AISVesselTracks2026-03.gpkg."""

import logging
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import zipfile
from typing import Any, Dict, List, Optional
import pyogrio

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_default_temp_gpkg_path() -> str:
    """Returns the default external temporary path outside OneDrive."""
    local_app_data = os.environ.get("LOCALAPPDATA", tempfile.gettempdir())
    temp_dir = os.path.join(local_app_data, "Temp", "where-is-my-ferry-gpkg")
    return os.path.join(temp_dir, "AISVesselTracks2026-03.gpkg")


def preflight_check(
    src_zip: str = "data/downloads/AISVesselTracks2026-03.zip",
    dest_path: Optional[str] = None,
    min_free_gb: float = 15.0,
) -> Dict[str, Any]:
    """Runs preflight validation on source archive, disk space, and destination path."""
    if dest_path is None:
        dest_path = get_default_temp_gpkg_path()

    logger.info("Running preflight checks...")

    # 1. Source archive exists
    if not os.path.exists(src_zip):
        raise FileNotFoundError(f"Source archive not found at: {src_zip}")

    src_size = os.path.getsize(src_zip)

    # 2. Archive contains target member
    member_name = "AISVesselTracks2026-03.gpkg"
    with zipfile.ZipFile(src_zip, "r") as zf:
        members = zf.namelist()
        if member_name not in members:
            raise ValueError(f"Member {member_name} not found in {src_zip}. Members: {members}")
        info = zf.getinfo(member_name)
        uncompressed_bytes = info.file_size

    # 3. Check outside OneDrive
    if "onedrive" in os.path.abspath(dest_path).lower():
        raise ValueError(f"Destination path {dest_path} is inside OneDrive! Must be outside OneDrive.")

    # 4. Check disk space on destination drive
    drive = os.path.splitdrive(os.path.abspath(dest_path))[0]
    total, used, free = shutil.disk_usage(drive)
    free_gb = free / (1024**3)
    logger.info(f"Disk space on drive {drive}: {free_gb:.2f} GB free (required: >= {min_free_gb:.1f} GB)")
    if free_gb < min_free_gb:
        raise OSError(f"Insufficient disk space on {drive}: {free_gb:.2f} GB < {min_free_gb:.1f} GB required.")

    # 5. Check if destination already exists
    dest_exists = os.path.exists(dest_path)
    existing_valid = False
    existing_size = 0
    if dest_exists:
        existing_size = os.path.getsize(dest_path)
        logger.info(f"Existing file found at destination ({existing_size} bytes). Checking integrity...")
        if existing_size == uncompressed_bytes:
            # Check SQLite header
            try:
                with open(dest_path, "rb") as f:
                    hdr = f.read(16)
                    if hdr.startswith(b"SQLite format 3"):
                        existing_valid = True
                        logger.info("Existing file matches expected size and has valid SQLite format 3 header.")
            except Exception as e:
                logger.warning(f"Existing file could not be read: {e}")

    return {
        "src_zip": src_zip,
        "src_size_bytes": src_size,
        "member_name": member_name,
        "uncompressed_bytes": uncompressed_bytes,
        "dest_path": dest_path,
        "drive": drive,
        "free_gb": free_gb,
        "dest_exists": dest_exists,
        "existing_valid": existing_valid,
        "existing_size": existing_size,
    }


def extract_gpkg_member(
    src_zip: str = "data/downloads/AISVesselTracks2026-03.zip",
    dest_path: Optional[str] = None,
    chunk_size: int = 16 * 1024 * 1024,  # 16 MB chunks
) -> Dict[str, Any]:
    """Safely extracts only the GeoPackage member to destination outside OneDrive."""
    if dest_path is None:
        dest_path = get_default_temp_gpkg_path()

    pre = preflight_check(src_zip, dest_path)
    dest_dir = os.path.dirname(dest_path)
    os.makedirs(dest_dir, exist_ok=True)

    member_name = pre["member_name"]
    expected_bytes = pre["uncompressed_bytes"]

    # If existing file is already complete and valid, reuse it safely
    if pre["existing_valid"]:
        logger.info(f"Reusing existing valid extraction at: {dest_path}")
        return {
            "status": "REUSED_EXISTING",
            "dest_path": dest_path,
            "extracted_bytes": pre["existing_size"],
            "extraction_seconds": 0.0,
            "expected_bytes": expected_bytes,
        }

    logger.info(f"Extracting '{member_name}' ({expected_bytes / (1024**3):.2f} GB) to {dest_path}...")
    t0 = time.time()
    bytes_written = 0

    with zipfile.ZipFile(src_zip, "r") as zf:
        with zf.open(member_name, "r") as src_stream:
            with open(dest_path, "wb") as dst_stream:
                while True:
                    buf = src_stream.read(chunk_size)
                    if not buf:
                        break
                    dst_stream.write(buf)
                    bytes_written += len(buf)
                    if bytes_written % (256 * 1024 * 1024) == 0:
                        pct = (bytes_written / expected_bytes) * 100
                        logger.info(f"Extracted {bytes_written / (1024**3):.2f} GB ({pct:.1f}%)...")

    duration = time.time() - t0
    logger.info(f"Extraction completed in {duration:.2f}s ({bytes_written} bytes written).")

    # Validate output
    if bytes_written != expected_bytes:
        raise OSError(f"Extraction byte mismatch: wrote {bytes_written}, expected {expected_bytes}")

    # Validate SQLite integrity
    con = sqlite3.connect(dest_path)
    try:
        cur = con.cursor()
        cur.execute("PRAGMA quick_check;")
        check_res = cur.fetchone()[0]
        logger.info(f"SQLite PRAGMA quick_check: {check_res}")
        if check_res != "ok":
            raise ValueError(f"SQLite integrity check failed: {check_res}")
    finally:
        con.close()

    return {
        "status": "EXTRACTED_NEW",
        "dest_path": dest_path,
        "extracted_bytes": bytes_written,
        "extraction_seconds": duration,
        "expected_bytes": expected_bytes,
    }


def inspect_schema_and_create_index(
    gpkg_path: Optional[str] = None,
    table_name: str = "AIS_Tracks_2026_03",
    column_name: str = "mmsi",
    index_name: str = "idx_ais_tracks_mmsi",
) -> Dict[str, Any]:
    """Inspects table schema and creates B-tree index on mmsi column if not exists."""
    if gpkg_path is None:
        gpkg_path = get_default_temp_gpkg_path()

    if not os.path.exists(gpkg_path):
        raise FileNotFoundError(f"GeoPackage file not found at: {gpkg_path}")

    logger.info(f"Opening SQLite database at {gpkg_path}...")
    con = sqlite3.connect(gpkg_path)
    cur = con.cursor()

    try:
        # 1. Verify table exists
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
            (table_name,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Table '{table_name}' does not exist in {gpkg_path}")

        # 2. Verify column exists and get type
        cur.execute(f"PRAGMA table_info([{table_name}]);")
        columns = cur.fetchall()
        col_names = [c[1] for c in columns]
        col_types = {c[1]: c[2] for c in columns}
        if column_name not in col_names:
            raise ValueError(f"Column '{column_name}' not in table '{table_name}'. Columns: {col_names}")

        logger.info(f"Verified table [{table_name}], column '{column_name}' type: {col_types[column_name]}")

        # 3. Check existing indexes
        cur.execute(f"PRAGMA index_list([{table_name}]);")
        existing_indexes = cur.fetchall()
        index_names = [i[1] for i in existing_indexes]
        index_already_existed = index_name in index_names

        # 4. Create index if needed
        t0 = time.time()
        if not index_already_existed:
            logger.info(f"Creating index [{index_name}] ON [{table_name}]([{column_name}])...")
            cur.execute(f"CREATE INDEX IF NOT EXISTS [{index_name}] ON [{table_name}]([{column_name}]);")
            con.commit()
            indexing_duration = time.time() - t0
            logger.info(f"Index created in {indexing_duration:.2f}s.")
        else:
            indexing_duration = 0.0
            logger.info(f"Index [{index_name}] already exists.")

        # 5. Confirm index in sqlite_master
        cur.execute(
            "SELECT sql FROM sqlite_master WHERE type='index' AND name=?;",
            (index_name,),
        )
        idx_sql = cur.fetchone()
        if not idx_sql:
            raise RuntimeError(f"Index '{index_name}' could not be verified in sqlite_master!")

        # 6. Verify with EXPLAIN QUERY PLAN
        explain_sql = f"EXPLAIN QUERY PLAN SELECT OBJECTID, mmsi, vessel_name FROM [{table_name}] WHERE [{column_name}] = 316011408;"
        cur.execute(explain_sql)
        query_plan = cur.fetchall()
        plan_str = " | ".join([str(p[-1]) for p in query_plan])
        logger.info(f"EXPLAIN QUERY PLAN: {plan_str}")
        uses_index = any(index_name in str(p[-1]) for p in query_plan)

        # Database size
        file_size_bytes = os.path.getsize(gpkg_path)

        return {
            "gpkg_path": gpkg_path,
            "table_name": table_name,
            "column_name": column_name,
            "column_type": col_types[column_name],
            "index_name": index_name,
            "index_sql": idx_sql[0],
            "index_already_existed": index_already_existed,
            "indexing_duration_seconds": indexing_duration,
            "query_plan": plan_str,
            "uses_index": uses_index,
            "file_size_bytes": file_size_bytes,
        }
    finally:
        con.close()


def validate_candidate_queries(
    gpkg_path: Optional[str] = None,
    candidate_mmsis: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """Tests indexed lookups for candidate MMSIs and validates performance."""
    if gpkg_path is None:
        gpkg_path = get_default_temp_gpkg_path()

    if candidate_mmsis is None:
        candidate_mmsis = [316011408, 316001245, 366709770]

    logger.info(f"Running indexed query validation on candidate MMSIs: {candidate_mmsis}...")
    results = []

    for mmsi in candidate_mmsis:
        t0 = time.time()
        # Query using pyogrio directly on the extracted, indexed GeoPackage
        df = pyogrio.read_dataframe(
            gpkg_path,
            read_geometry=True,
            columns=[
                "mmsi",
                "vessel_name",
                "imo",
                "vessel_type_name",
                "start_time",
                "end_time",
                "duration_minutes",
                "vessel_length",
            ],
            where=f"mmsi = {mmsi}",
        )
        elapsed = time.time() - t0

        vessel_names = df["vessel_name"].dropna().unique().tolist()
        total_tracks = len(df)
        time_min = str(df["start_time"].min()) if total_tracks > 0 else None
        time_max = str(df["end_time"].max()) if total_tracks > 0 else None
        bounds = list(df.total_bounds) if total_tracks > 0 else None

        logger.info(
            f"MMSI {mmsi}: {total_tracks} tracks found in {elapsed:.3f}s. "
            f"Vessel: {vessel_names}, Range: [{time_min} to {time_max}]"
        )

        results.append({
            "mmsi": mmsi,
            "matching_tracks": total_tracks,
            "vessel_names": vessel_names,
            "execution_seconds": elapsed,
            "start_time_min": time_min,
            "end_time_max": time_max,
            "total_bounds": bounds,
            "null_vessel_names": int(df["vessel_name"].isna().sum()) if total_tracks > 0 else 0,
            "sample_record": df.iloc[0].to_dict() if total_tracks > 0 else None,
        })

    return results


def run_pipeline():
    logger.info("=" * 60)
    logger.info("EXECUTING SAFE AIS EXTRACTION & INDEXING WORKFLOW")
    logger.info("=" * 60)

    # Step 1: Preflight
    pre = preflight_check()
    logger.info(f"Preflight OK: Free space = {pre['free_gb']:.2f} GB on {pre['drive']}")

    # Step 2: Extract
    ext = extract_gpkg_member()
    logger.info(f"Extraction result: {ext['status']} ({ext['extracted_bytes'] / (1024**3):.2f} GB in {ext['extraction_seconds']:.2f}s)")

    # Step 3 & 4: Schema & Index
    idx_res = inspect_schema_and_create_index()
    logger.info(f"Index result: Plan = '{idx_res['query_plan']}', Uses Index = {idx_res['uses_index']}")

    # Step 5: Validate Queries
    queries = validate_candidate_queries()

    logger.info("=" * 60)
    logger.info("AIS EXTRACTION & INDEXING COMPLETE")
    logger.info("=" * 60)
    return {
        "preflight": pre,
        "extraction": ext,
        "indexing": idx_res,
        "queries": queries,
    }


if __name__ == "__main__":
    run_pipeline()
