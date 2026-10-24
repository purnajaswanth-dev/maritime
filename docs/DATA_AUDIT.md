# Data Audit and Baseline Report (Penn ar Bed & Iroise Sea)

**Date:** 2026-10-24  
**Project:** Where Is My Ferry?  
**Phase:** Phase 00 — Audit and Baseline  
**Scope:** Timetable (GTFS), AIS trajectory datasets, and collocated ocean current benchmarks.

---

## 1. Executive Summary

This data audit catalogues all timetable, AIS telemetry, and oceanographic data assets available to the **Where Is My Ferry?** platform. It establishes baseline record counts, date ranges, corridor mappings, and flags coverage gaps between scheduled services and observed AIS telemetry.

---

## 2. Inventory of Located Data Assets

### A. GTFS Timetable Feeds (`ml-platform/data/timetable/gtfs/` & `ml-platform/data/downloads/`)

| Asset / File | Format | Records / Size | Date Range | Primary Agency / Description |
|:---|:---|:---|:---|:---|
| `penn_ar_bed_gtfs.zip` | GTFS (ZIP) | 7 files, 20 trips | 2026-01-01 to 2026-12-31 | **Penn ar Bed** (Brest, Le Conquet, Molène, Ouessant, Audierne, Île de Sein, Camaret) |
| `agency.txt` | CSV | 1 agency | N/A | Penn ar Bed (Timezone: `Europe/Paris`) |
| `stops.txt` | CSV | 7 stops | N/A | 7 terminals with precise coordinates and berth polygons |
| `routes.txt` | CSV | 12 routes | N/A | Corridors across Iroise Sea (Route type: 4 - Ferry) |
| `trips.txt` | CSV | 20 trips | N/A | Scheduled trip definitions with block/vessel assignments |
| `stop_times.txt` | CSV | 40 stop times | N/A | Authoritative departure and arrival schedules |
| `calendar.txt` | CSV | 4 service IDs | 2026-01-01 to 2026-12-31 | Daily year-round, weekday, weekend, and summer patterns |
| `calendar_dates.txt` | CSV | 4 exceptions | 2026-05-01 to 2026-12-25 | French public holidays & Christmas operational adjustments |
| `mdb-2814-202508181628.zip` | GTFS (ZIP) | 7 files | 2025-08-18 to 2026-08-18 | Balearia Ferries (Benchmark reference) |
| `mdb-3522-202610131556.zip` | GTFS (ZIP) | 11 files | 2026-10-13 to 2027-10-13 | Los Reginas S.L. (Benchmark reference) |
| `mdb-690-202605270153.zip` | GTFS (ZIP) | 24 files | 2026-05-27 to 2026-10-15 | BC Ferries (Benchmark reference) |

### B. Historical AIS & Telemetry Datasets (`ml-platform/data/`)

| Asset / File | Format | Records | Date Range | Description / Provenance |
|:---|:---|:---|:---|:---|
| `verified_voyages.parquet` | Parquet | **889 verified voyages** | 2015-10-01 to 2016-03-31 | Segmented historical voyages in Iroise Sea with observed berth dwell |
| `phase_05_prediction_snapshots.parquet` | Parquet | **9,313 causal snapshots** | 2015-10-01 to 2016-03-31 | Causal features & remaining travel times for ML training/testing |
| `phase_05_test_predictions.parquet` | Parquet | **2,372 test predictions** (204 voyages) | 2016-02-01 to 2016-03-31 | Test partition used for frozen Ridge evaluation (MAE 5.20 min) |
| `ais_brest_synopses_v0.8.zip` | ZIP (CSV/JSON) | ~1.8M AIS messages | 2015-10-01 to 2016-03-31 | datAcron / NARI raw AIS synopses in Brest & Iroise Sea |
| `cmems_mod_glo_phy_my_0.083deg_P1D-m_1792083299167.nc` | NetCDF | 183 days (daily mean) | 2015-10-01 to 2016-03-31 | Copernicus surface currents ($u_o, v_o$) across North Atlantic & Iroise Sea |
| `AISVesselTracks2026-03.zip` | ZIP (GPKG) | 1,446,038 tracks | 2026-03-01 to 2026-03-31 | US MarineCadastre trackline benchmark |

---

## 3. Corridor Coverage & Mapping Matrix

The ML model recognizes **10 historical corridor categories** in the Iroise Sea. The table below maps each scheduled GTFS route to these corridors and documents historical voyage counts:

| Timetable Route (`route_id`) | Model Corridor Category | GTFS Daily Sailings | Historical AIS Voyages | Verified Vessels | Model Tracking Support |
|:---|:---|:---:|:---:|:---|:---:|
| `R_BRE_CNQ` (Brest &rarr; Le Conquet) | `BREST_LE_CONQUET` | 3 | **131** | *FROMVEUR II* | **Yes (Active Model)** |
| `R_CNQ_BRE` (Le Conquet &rarr; Brest) | `LE_CONQUET_BREST` | 3 | **113** | *FROMVEUR II*, *ANDRE COLIN* | **Yes (Active Model)** |
| `R_BRE_OUE` (Brest &rarr; Ouessant) | `BREST_OUESSANT_STIFF` | 2 | **4** | *FROMVEUR II*, *ENEZ EUSSA 3* | **Yes (Active Model)** |
| `R_AUD_SEI` (Audierne &rarr; Île de Sein) | `AUDIERNE_ILE_DE_SEIN` | 2 | **127** | *ENEZ SUN 3* | **Yes (Active Model)** |
| `R_OUE_BRE` (Ouessant &rarr; Brest) | `OUESSANT_STIFF_BREST` | 2 | **17** | *FROMVEUR II*, *ENEZ EUSSA 3* | Secondary (Schedule only) |
| `R_SEI_AUD` (Île de Sein &rarr; Audierne) | `ILE_DE_SEIN_AUDIERNE` | 2 | **14** | *ENEZ SUN 3* | Secondary (Schedule only) |
| `R_CNQ_MOL` (Le Conquet &rarr; Molène) | `LE_CONQUET_MOLENE` | 1 | **146** | *FROMVEUR II*, *ENEZ EUSSA 3* | Secondary (Schedule only) |
| `R_MOL_CNQ` (Molène &rarr; Le Conquet) | `MOLENE_LE_CONQUET` | 1 | **135** | *FROMVEUR II*, *ENEZ EUSSA 3* | Secondary (Schedule only) |
| `R_MOL_OUE` (Molène &rarr; Ouessant) | `MOLENE_OUESSANT_STIFF` | 1 | **76** | *FROMVEUR II*, *ENEZ EUSSA 3* | Secondary (Schedule only) |
| `R_OUE_MOL` (Ouessant &rarr; Molène) | `OUESSANT_STIFF_MOLENE` | 1 | **126** | *FROMVEUR II*, *ENEZ EUSSA 3* | Secondary (Schedule only) |
| `R_BRE_CAM` (Brest &rarr; Camaret) | `BREST_CAMARET` | 1 (Summer) | **0** | None (Summer only) | **No (`tracking_supported=false`)** |
| `R_CAM_BRE` (Camaret &rarr; Brest) | `CAMARET_BREST` | 1 (Summer) | **0** | None (Summer only) | **No (`tracking_supported=false`)** |

---

## 4. Identified Data Gaps & Architectural Guardrails

1. **Seasonal Summer Gap (Brest &harr; Camaret):**
   - The datAcron dataset spans strictly from **October 1, 2015 to March 31, 2016** (winter navigation window).
   - The tourist route between Brest and Camaret-sur-Mer operates strictly during summer months (`SUMMER_ONLY`: June 15 to September 15).
   - **Resolution:** As mandated by Non-Negotiable Rule 6, summer sailings between Brest and Camaret show timetable schedule only with the honest label: `Live tracking not available for this service`.

2. **Vessel Observation Asymmetry:**
   - *FROMVEUR II* (MMSI 228017700) accounts for 603 of the 889 voyages (67.8%).
   - *ANDRE COLIN* (MMSI 227002330) accounts for only 7 verified voyages.
   - *ENEZ SUN 3* (MMSI 227002630) handles the Audierne &harr; Île de Sein corridor exclusively (141 voyages).
   - **Resolution:** Replay runner draws from verified historical voyages matching each corridor and vessel type.

3. **Absence of Live AIS Feed:**
   - Real-time commercial AIS feeds are not available.
   - **Resolution:** As designed, all operational tracking runs on a timetable-driven historical replay of verified AIS tracks passing through the frozen Ridge model and state machine, labelled `Historical replay (simulated live)`.
