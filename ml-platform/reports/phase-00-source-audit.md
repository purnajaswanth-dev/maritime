# Phase 00 Source Audit Report: Workspace Inventory & Data Asset Verification

**Project:** Where Is My Ferry?  
**Audit Date:** 2026-10-15  
**Auditor:** Senior Data Engineer & ML Infrastructure Engineer  
**Status:** COMPLETED — Non-Destructive Source Audit  
**Manifests Generated:**  
- [file_inventory.json](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/file_inventory.json)
- [archive_inventory.json](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/archive_inventory.json)

---

## 1. Executive Summary

Phase 00 performed a non-destructive audit of the `where-is-my-ferry` repository. Every directory, file, GIS shapefile, tabular dataset, oceanographic NetCDF file, and compressed ZIP archive was inventoried and inspected without modifying, moving, extracting, or deleting any original assets.

### Key Audit Findings:
1. **Verified Project Root:** `c:/Users/sunka/OneDrive/coding/where-is-my-ferry`
2. **Workspace Inventory:** 9 directories and 34 pre-existing files across the repository.
3. **Archival Assets:** 11 ZIP archives (totalling 3.23 GB compressed, expanding to 28.38 GB uncompressed) located under `ml-platform/data/downloads/`. All 11 archives passed CRC32 integrity validation (`INTEGRITY_OK`).
4. **Extraction Safety:** Zero path traversal vulnerabilities (`..` or absolute paths) detected. However, **major uncompressed expansion risks** were identified: `ais_brest_synopses_v0.8.zip` expands to **24.24 GB** (12.15x ratio), and `AISVesselTracks2026-03.zip` expands to **4.12 GB** (3.38x ratio). Neither archive should be blindly extracted into the workspace.
5. **Feed Misclassification Uncovered:** Preliminary review of `mdb-2353-*.zip` revealed it is **Bee-Line Bus** (Westchester County Department of Transportation, Route Type 3), **not** a passenger ferry dataset. The other GTFS archives (`mdb-2814`, `mdb-3522`, `mdb-649`, `mdb-690`) are verified passenger ferry feeds (Route Type 4).
6. **Codebase Status:** The `backend/` and `frontend/` directories are verified empty. No Python source code, pipeline orchestration, model checkpoints, virtual environments, or dependency definitions (`requirements.txt`, `pyproject.toml`) existed prior to this phase.

---

## 2. Directory Structure Verification

The verified baseline directory hierarchy:

```text
where-is-my-ferry/
├── backend/                                [VERIFIED: Empty directory]
├── frontend/                               [VERIFIED: Empty directory]
├── ml-platform/
│   ├── data/
│   │   ├── downloads/                      [11 ZIP archives + 1 NetCDF file; 3.86 GB total]
│   │   ├── manifests/                      [Created Phase 00: file_inventory.json, archive_inventory.json]
│   │   └── raw/
│   │       ├── UpdatedPub150.csv           [3.33 MB NGA World Port Index]
│   │       ├── ne_10m_coastline/           [7 files, Natural Earth 1:10m coastline]
│   │       ├── ne_10m_land/                [7 files, Natural Earth 1:10m land polygons]
│   │       └── ne_10m_ocean/               [7 files, Natural Earth 1:10m ocean polygons]
│   └── reports/                            [Created Phase 00: phase-00-source-audit.md]
└── MEMORY.md                               [Created Phase 00: Project root persistent memory]
```

---

## 3. Detailed Archive Inventory & Integrity Audit

All 11 ZIP archives located under `ml-platform/data/downloads/` were verified using Python's `zipfile.ZipFile.testzip()`. Zero CRC mismatches, corrupt headers, or extraction traversal paths (`..` or root `/`) were discovered.

| Archive Filename | Compressed Size | Uncompressed Size | Members | CRC32 Status | Extraction Risk | Preliminary Classification |
|---|---|---|---|---|---|---|
| `AISVesselTracks2026-03.zip` | 1,220,146,725 B (1.16 GB) | 4,123,795,456 B (3.84 GB) | 1 | INTEGRITY_OK | High disk consumption (4.12 GB single GPKG file) | AIS / vessel telemetry candidate (MarineCadastre GeoPackage) |
| `ais_brest_synopses_v0.8.zip` | 1,993,633,450 B (1.86 GB) | 24,236,795,478 B (22.57 GB) | 9 | INTEGRITY_OK | **Extreme expansion risk** (24.2 GB uncompressed; JSON files up to 14.8 GB) | AIS / vessel telemetry candidate (datAcron Brest benchmark) |
| `mdb-2353-202502041949.zip` | 3,821,245 B (3.64 MB) | 19,315,939 B (18.42 MB) | 8 | INTEGRITY_OK | None | **Bus transit feed** (Bee-Line Bus Westchester NY; Route Type 3) |
| `mdb-2353-202502270025.zip` | 3,821,246 B (3.64 MB) | 19,315,939 B (18.42 MB) | 8 | INTEGRITY_OK | None | **Bus transit feed** (Bee-Line Bus Westchester NY; Route Type 3) |
| `mdb-2353-202506170043.zip` | 3,569,641 B (3.40 MB) | 18,433,754 B (17.58 MB) | 8 | INTEGRITY_OK | None | **Bus transit feed** (Bee-Line Bus Westchester NY; Route Type 3) |
| `mdb-2814-202508181628.zip` | 290,347 B (0.28 MB) | 3,350,721 B (3.20 MB) | 7 | INTEGRITY_OK | None | Ferry schedule candidate (Balearia ferry operations Spain) |
| `mdb-3522-202610131556.zip` | 5,960 B (0.01 MB) | 24,365 B (0.02 MB) | 11 | INTEGRITY_OK | None | Ferry schedule candidate (Los Reginas S.L. Santander Spain) |
| `mdb-649-202406071512.zip` | 7,085 B (0.01 MB) | 26,571 B (0.03 MB) | 17 | INTEGRITY_OK | None | Ferry schedule candidate (Port Phillip Ferries Melbourne AU) |
| `mdb-690-202605270153.zip` | 73,159 B (0.07 MB) | 440,387 B (0.42 MB) | 24 | INTEGRITY_OK | None | Ferry schedule candidate (BC Ferries British Columbia CA) |
| `mdb-690-202607240152.zip` | 107,960 B (0.10 MB) | 623,943 B (0.59 MB) | 24 | INTEGRITY_OK | None | Ferry schedule candidate (BC Ferries British Columbia CA) |
| `mdb-690-202608210055.zip` | 110,878 B (0.10 MB) | 646,687 B (0.62 MB) | 24 | INTEGRITY_OK | None | Ferry schedule candidate (BC Ferries British Columbia CA) |

---

## 4. Deep Inspection of Downloaded Assets

### 4.1 AIS Trajectory Archives

#### A. `AISVesselTracks2026-03.zip`
- **Internal Member:** `AISVesselTracks2026-03.gpkg` (4,123,795,456 bytes).
- **Format:** OGC GeoPackage (SQLite 3 database container).
- **Layer Name:** `AIS_Tracks_2026_03`.
- **Primary Schema Fields:** `VesselName`, `IMO`, `MMSI`, `CallSign`, `VesselType` (e.g. `Pleasure Craft`, `Cargo - No additional information`), `TrackStartTime`, `TrackEndTime`, LineString geometry.
- **Extraction Protocol:** Do **not** extract this 4.12 GB file to disk. Python can stream read or attach directly via SQLite/GDAL/GeoPandas read interfaces.

#### B. `ais_brest_synopses_v0.8.zip`
- **Internal Members (9 files):**
  - `ais_brest_synopses_v0.8_ReadMe.txt` (12.8 KB)
  - `ais_brest_positions_raw.csv` (1.82 GB uncompressed / 239.7 MB compressed; 18,495,677 kinematic AIS points)
  - `ais_brest_locations.json` (14.81 GB uncompressed / 872.9 MB compressed; 16,356,036 points)
  - `ais_brest_locations.csv` (2.59 GB uncompressed / 481.0 MB compressed)
  - `ais_brest_synopses.json` (4.19 GB uncompressed / 248.5 MB compressed)
  - `ais_brest_synopses.csv` (733.2 MB uncompressed / 142.6 MB compressed)
  - `ais_brest_notifications.json` (80.2 MB uncompressed / 5.6 MB compressed)
  - `ais_brest_notifications.csv` (13.9 MB uncompressed / 3.2 MB compressed)
  - `critical_point.avsc` (8.9 KB; Apache Avro schema)
- **Provenance:** datAcron EU Project / Naval Academy Research Institute (NARI, France). AIS collected around Brest, Brittany, France from October 1, 2015 to March 31, 2016.
- **Extraction Protocol:** **DO NOT EXTRACT.** At 24.24 GB uncompressed, extracting this archive into OneDrive will cause massive disk thrashing and sync latency. Specific CSV/JSON streams should be processed via streaming iterators.

---

### 4.2 Oceanographic Physics Reanalysis

#### `cmems_mod_glo_phy_my_0.083deg_P1D-m_1792083299167.nc`
- **Location:** `ml-platform/data/downloads/`
- **Size:** 665,677,789 bytes (634.84 MB).
- **Format:** NetCDF-4 / HDF5 binary format.
- **Data Source:** Copernicus Marine Environment Monitoring Service (CMEMS).
- **Product Identification:** Global Ocean Physics Multi-Year Reanalysis (`cmems_mod_glo_phy_my_0.083deg_P1D-m`, e.g., GLORYS12V1).
- **Characteristics:** 1/12° spatial resolution (~8 km grid), daily-mean (`P1D-m`) physics (sea surface height, water velocity U/V, sea water potential temperature, salinity).
- **Role in Platform:** Serves as environmental feature source for ocean current and weather drag modeling on ferry voyage duration.

---

### 4.3 Mobility Database GTFS Feeds (Schedules)

| Archive | Agency Name | Route Types | Stop Count | Trip Count | Service Geographic Coverage |
|---|---|---|---|---|---|
| `mdb-2353-202502041949.zip` | Bee-Line Bus | Type 3 (Bus) | 2,788 | 4,175 | Westchester County, New York, USA |
| `mdb-2353-202502270025.zip` | Bee-Line Bus | Type 3 (Bus) | 2,788 | 4,175 | Westchester County, New York, USA |
| `mdb-2353-202506170043.zip` | Bee-Line Bus | Type 3 (Bus) | 2,803 | 4,182 | Westchester County, New York, USA |
| `mdb-2814-202508181628.zip` | Balearia | Type 4 (Ferry) | 19 | 24,242 | Spain mainland & Balearic Islands |
| `mdb-3522-202610131556.zip` | Los Reginas S.L. | Type 4 (Ferry) | 4 | 84 | Santander Bay, Cantabria, Spain |
| `mdb-649-202406071512.zip` | Port Phillip Ferries | Type 4 (Ferry) | 3 | 27 | Melbourne & Port Phillip Bay, Victoria, Australia |
| `mdb-690-202605270153.zip` | BC Ferries | Type 4 (Ferry) | 96 | 872 | British Columbia coastal waterways, Canada |
| `mdb-690-202607240152.zip` | BC Ferries | Type 4 (Ferry) | 96 | 1,342 | British Columbia coastal waterways, Canada |
| `mdb-690-202608210055.zip` | BC Ferries | Type 4 (Ferry) | 96 | 1,394 | British Columbia coastal waterways, Canada |

**Critical Observation:** `mdb-2353` contains zero ferry routes (`route_type` is exclusively `3`). It must be excluded from ferry schedule ingestion pipelines.

---

## 5. Inspection of Existing Raw Assets

### 5.1 Natural Earth 1:10,000,000 GIS Datasets

All three directories contain complete, intact 7-file ESRI shapefile suites:

| Dataset Directory | Version | CRS | CPG Encoding | Primary Files | Uncompressed Size |
|---|---|---|---|---|---|
| `ne_10m_coastline` | 5.0.0-pre9 | WGS 84 (`EPSG:4326`) | UTF-8 | `.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`, `.README.html`, `.VERSION.txt` | 7.27 MB |
| `ne_10m_land` | 5.1.1 | WGS 84 (`EPSG:4326`) | UTF-8 | `.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`, `.README.html`, `.VERSION.txt` | 7.24 MB |
| `ne_10m_ocean` | 5.1.1 | WGS 84 (`EPSG:4326`) | UTF-8 | `.shp`, `.shx`, `.dbf`, `.prj`, `.cpg`, `.README.html`, `.VERSION.txt` | 7.25 MB |

**Projection Check:** All `.prj` files specify standard geographic coordinates on the WGS 84 ellipsoid (`DATUM["D_WGS_1984"]`, `UNIT["Degree", 0.0174532925199433]`).

### 5.2 World Port Index (`UpdatedPub150.csv`)
- **File Location:** `ml-platform/data/raw/UpdatedPub150.csv`
- **File Size:** 3,326,893 bytes (~3.33 MB).
- **Encoding:** UTF-8.
- **Row Metrics:** 3,825 total lines (1 header line + 3,824 port records).
- **Column Count:** 107 columns (105 attribute columns + `Latitude` + `Longitude`).
- **Coordinate Integrity:** 3,824 out of 3,824 records (100.0%) possess valid float coordinates.
- **Latitude Extent:** `[-77.85, 78.928333]` (Antarctic McMurdo Station to Arctic Svalbard).
- **Longitude Extent:** `[-177.366667, 179.3675]` (Global Pacific/Atlantic coverage).
- **Relevance:** Essential reference dataset for geofencing ferry departure/arrival berths, identifying Ro-Ro infrastructure (`Facilities - Ro-Ro`), harbor shelteredness, and draft limits.

---

## 6. Data Source Provenance, Licensing & Commercial Status

| Asset / Source | Upstream Originator | Verified License Status | Commercial Use Allowed? | Action Required |
|---|---|---|---|---|
| Natural Earth (Coastline, Land, Ocean) | Natural Earth / NACIS | Public Domain (CC0 equivalent) | **YES (VERIFIED)** | None. Attribution appreciated but not legally required. |
| World Port Index (Pub 150) | US National Geospatial-Intelligence Agency (NGA) | US Public Domain | **YES (VERIFIED)** | None. US Government work. |
| AIS Vessel Tracks 2026-03 | MarineCadastre.gov (BOEM & NOAA) | US Public Domain | **YES (VERIFIED)** | None. US Government work. |
| Copernicus Marine Physical NetCDF | E.U. Copernicus Programme (Mercator Ocean) | Open License (Copernicus Marine Data Policy) | **YES (VERIFIED)** with mandatory attribution | Must display Copernicus Marine attribution notice. |
| BC Ferries GTFS (`mdb-690`) | British Columbia Ferry Services / Mobility Database | Open Data / Public Transit Schedule | **UNVERIFIED** (Requires formal license verification) | Verify specific BC Ferries Terms of Use before commercial distribution. |
| Balearia GTFS (`mdb-2814`) | Balearia Eurolineas Maritimas / Mobility Database | GTFS Feed | **UNVERIFIED** | Inspect Balearia schedule terms of service. |
| Los Reginas GTFS (`mdb-3522`) | Los Reginas S.L. / Mobility Database | GTFS Feed | **UNVERIFIED** | Inspect operator redistribution rights. |
| Port Phillip Ferries GTFS (`mdb-649`) | Port Phillip Ferries / Mobility Database | GTFS Feed | **UNVERIFIED** | Inspect operator redistribution rights. |
| datAcron Brest AIS (`ais_brest_synopses_v0.8.zip`) | datAcron EU H2020 / NARI / Univ. of Piraeus | Academic Research Benchmark | **UNVERIFIED / RESTRICTED** | Retain strictly for model R&D benchmark; do not redistribute commercially without explicit clearance. |
| Bee-Line Bus GTFS (`mdb-2353`) | Westchester County DOT | Public Transit Schedule | **N/A** (Irrelevant: bus transit, not ferry). | Exclude from ferry platform. |

---

## 7. Verified Facts vs. Unverified Assumptions

### Verified Facts
1. The project root is `c:/Users/sunka/OneDrive/coding/where-is-my-ferry`.
2. `backend/` and `frontend/` directories exist but are completely empty.
3. No ML training scripts, data pipeline code, or model weights currently exist in the repository.
4. Python 3.13.6 is available with `geopandas`, `shapely`, and `pyproj`. `netCDF4`, `xarray`, `h5py`, `fiona`, and `rasterio` are not currently installed.
5. All 11 ZIP archives are physically uncorrupted (100% pass rate in CRC32 checks).
6. Total compressed archive size is 3.23 GB; total uncompressed size is 28.38 GB.
7. `mdb-2353` is an urban bus feed, not a passenger ferry feed.
8. `mdb-2814`, `mdb-3522`, `mdb-649`, and `mdb-690` represent genuine ferry operations with Route Type 4.
9. `UpdatedPub150.csv` has 3,824 global ports with 100% valid coordinate coverage.
10. `ne_10m_*` shapefiles are in EPSG:4326 (WGS 84) coordinate reference system.

### Unverified Assumptions
1. **Ferry Matching Assumption:** It is assumed that trajectories in `AISVesselTracks2026-03.gpkg` overlap spatially and temporally with the BC Ferries routes in `mdb-690-2026*.zip`. *(Unverified until spatio-temporal intersection is executed in Phase 01/02).*
2. **datAcron Passenger Ferry Fraction:** It is assumed that some fraction of trajectories in `ais_brest_synopses_v0.8.zip` correspond to passenger ferries in Brest Harbor (e.g. Penn ar Bed). *(Unverified until MMSI vessel types are cross-referenced).*
3. **Copernicus Reanalysis Spatial/Temporal Alignment:** It is assumed that the physical ocean variables in `cmems_mod_glo_phy_my_0.083deg_P1D-m_1792083299167.nc` span the same geographic bounds and time windows as the candidate AIS voyages. *(Unverified until NetCDF dimensions and coordinate arrays are parsed).*
4. **Commercial Use Rights for Schedule Data:** It is assumed that GTFS schedules obtained from Mobility Database can be redistributed in a commercial consumer app. *(Unverified until each operator's terms are verified).*

---

## 8. Acceptance Criteria Evaluation

| # | Acceptance Criterion | Evaluation | Evidence / Notes |
|---|---|---|---|
| 1 | Actual workspace root is verified | **PASS** | Verified as `c:/Users/sunka/OneDrive/coding/where-is-my-ferry`. |
| 2 | All discoverable project files and directories are inventoried | **PASS** | 45 items recorded in `file_inventory.json` with sizes, types, formats, and categories. |
| 3 | Every ZIP under workspace has an inventory entry with integrity check | **PASS** | All 11 archives evaluated; 100% passed CRC32 checks in `archive_inventory.json`. |
| 4 | Existing raw geography and port data inspected without modification | **PASS** | Natural Earth coastline, land, ocean, and Pub 150 inspected; timestamps and contents untouched. |
| 5 | Existing ML source code and artifacts identified | **PASS** | Full audit confirms zero existing ML code, pipelines, or checkpoints. |
| 6 | Source-audit report exists and separates facts from assumptions | **PASS** | This document (`phase-00-source-audit.md`) explicitly segregates verified facts from assumptions. |
| 7 | `MEMORY.md` exists and accurately records phase state | **PASS** | Root `MEMORY.md` created with all 12 mandatory sections. |
| 8 | No source archive extracted, modified, moved, or deleted | **PASS** | All 11 archives remain unextracted in their original download paths. |
| 9 | No model trained | **PASS** | ML training strictly avoided. |
| 10 | Final report states PASS, PARTIAL, or FAIL for each criterion | **PASS** | Criteria 1 through 10 all evaluate to **PASS**. |

---

## 9. Recommended Next Action for Phase 01

Phase 00 is complete. The exact next action is **Phase 01: Environment Foundation, Data Pipeline Scaffolding, and Spatio-Temporal Data Profiling**.
Prior to data pipeline execution:
1. Establish a dedicated virtual environment or dependency manifest (`pyproject.toml` or `requirements.txt`) including `netCDF4` or `h5py` for NetCDF parsing and `pyogrio` for high-speed GeoPackage access.
2. Build non-extracting or streaming inspect tools for the large GeoPackage and datAcron archives.
3. Filter out non-ferry transit feeds (`mdb-2353`).
