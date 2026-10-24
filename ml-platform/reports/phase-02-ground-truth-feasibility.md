# Phase 02: Voyage Extraction and Ground-Truth Dataset Feasibility Report

**Project:** Where Is My Ferry?  
**Audit & Analysis Date:** 2026-10-15  
**Engineer:** Senior Data Engineer & ML Infrastructure Engineer  
**Status:** COMPLETED — Phase 02 Feasibility Assessment  
**Overall Ground-Truth Feasibility Verdict:** **PARTIAL / CONDITIONALLY FEASIBLE**  
**Generated Intermediate Artifacts:**  
- [vessel_registry_candidates.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/vessel_registry_candidates.parquet) (23 validated vessel entries)  
- [voyage_match_audit.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/voyage_match_audit.parquet) (5 schedule audit cases)  
- [voyage_candidates.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/voyage_candidates.parquet) (7 candidate voyages with quality labels)  
- [phase-02-source-lineage.json](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/manifests/phase-02-source-lineage.json) (Traceable source lineage manifest)  

---

## 1. Executive Summary & Feasibility Verdict

Phase 02 evaluated whether the existing public datasets support a defensible real-world passenger-ferry ETA dataset without relying on synthetic labels, unverified assumptions, or uncontrolled archive extraction.

### Overall Verdict: PARTIAL / CONDITIONALLY FEASIBLE
A supervised passenger-ferry ETA dataset is **feasible under strict corridor-specific constraints**, but **not as a single monolithic dataset across all downloaded files**. 

Two distinct corridors were identified, each with specific strengths and hard limitations:

1. **Corridor A — Brest / Iroise Sea (2015–2016):**
   - *Strengths:* Perfect spatio-temporal collocation between real-world AIS trajectories (`ais_brest_synopses_v0.8.zip`) and daily ocean current components (`uo`, `vo` from `cmems_mod_glo_phy_*.nc`), both covering **1 October 2015 to 31 March 2016**.
   - *Limitations:* The datAcron dataset contains zero ship names or vessel types; trajectories are identified solely by numeric MMSI. An external registry lookup (ITU MARS / French Maritime Affairs) was required to establish verified identities for Penn ar Bed ferries (*Fromveur II*, *Enez Sun 3*, *André Colin*). Furthermore, academic research licensing restricts commercial redistribution of the raw datAcron data.
2. **Corridor B — Salish Sea / US Pacific Northwest (March 2026):**
   - *Strengths:* MarineCadastre.gov (`AISVesselTracks2026-03.gpkg`) provides high-confidence passenger ferry tracks in US waters and cross-border Salish Sea corridors, with explicit vessel names (*Queen of Alberni*, *Coastal Inspiration*, *WSF Chelan*), IMOs, dimensions, and US Public Domain licensing.
   - *Limitations:* The existing Copernicus NetCDF file covers 2015–2016 and **cannot be used** for contemporaneous March 2026 ocean features. Furthermore, the BC Ferries GTFS schedule in our downloads was published in **May 2026**; seasonal timetable changes prevent unverified back-projection onto March 2026 AIS voyages without a contemporaneous March 2026 timetable.

---

## 2. Source Provenance and License Review (Task 1)

All candidate sources were audited for upstream publisher, license terms, commercial viability, and known operational limits:

| Source Identifier | Upstream Originator | Original Source URL | Verified License Status | Commercial Redistribution | Key Known Limitations |
|---|---|---|---|---|---|
| `AISVesselTracks2026-03` | US Bureau of Ocean Energy Management (BOEM) & NOAA | [marinecadastre.gov/ais](https://marinecadastre.gov/ais/) | US Public Domain | **PERMITTED** | Aggregated `MultiLineString` tracklines with trip-level start/end times; no raw intermediate point timestamps. |
| `ais_brest_synopses_v0.8` | datAcron EU Horizon 2020 / NARI (Ecole Navale) | [datacron-project.eu](http://datacron-project.eu/) | Academic Research Benchmark | **RESTRICTED** (License uncertainty preserved) | Contains only numeric MMSIs; zero vessel names or types; commercial redistribution unverified. |
| `cmems_mod_glo_phy_my_0.083deg_P1D-m` | Copernicus Marine Service (Mercator Ocean) | [marine.copernicus.eu](https://marine.copernicus.eu/) | Copernicus Open Data Policy | **PERMITTED** (with mandatory attribution) | Spans Oct 2015 - Mar 2016; 8 km daily-mean grid cannot resolve real-time local harbour tidal flows. |
| `mdb-690-*` (BC Ferries) | BC Ferries / Trillium Solutions / Mobility Database | [mobilitydatabase.org](https://mobilitydatabase.org/feeds/gtfs/mdb-690) | Open Schedule Data | **UNVERIFIED** | May, July, and August 2026 snapshots postdate the March 2026 AIS observation window. |
| `mdb-2814-*` (Balearia) | Balearia Eurolineas Maritimas / Mobility Database | [mobilitydatabase.org](https://mobilitydatabase.org/feeds/gtfs/mdb-2814) | Open Transit Schedule | **UNVERIFIED** | Mediterranean spatial coverage; zero spatial overlap with US or Brest AIS data. |
| `mdb-3522-*` (Los Reginas) | Los Reginas S.L. / Mobility Database | [mobilitydatabase.org](https://mobilitydatabase.org/feeds/gtfs/mdb-3522) | Open Transit Schedule | **UNVERIFIED** | Santander Bay shuttle; zero overlap with available AIS tracks. |
| `mdb-649-*` (Port Phillip) | Port Phillip Ferries / Mobility Database | [mobilitydatabase.org](https://mobilitydatabase.org/feeds/gtfs/mdb-649) | Open Transit Schedule | **UNVERIFIED** | Melbourne, Australia; zero spatial overlap with current AIS and ocean files. |
| `mdb-2353-*` (Bee-Line Bus) | Westchester County DOT | [mobilitydatabase.org](https://mobilitydatabase.org/feeds/gtfs/mdb-2353) | Public Transit Schedule | **N/A (EXCLUDED)** | Terrestrial bus transit (`route_type = 3`). Strictly quarantined. |
| `UpdatedPub150` | National Geospatial-Intelligence Agency (NGA) | [msi.geo.nga.mil](https://msi.geo.nga.mil/Publications/WPI) | US Public Domain | **PERMITTED** | Global port database; provides terminal reference coordinates and Ro-Ro berth flags. |

---

## 3. Defensible Vessel Identity Workflow (Task 2)

A defensible vessel registry was designed and implemented in [vessel_registry.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/ingestion/vessel_registry.py) to prevent unverified vessels from contaminating the ferry dataset.

### Classification Rules & States
Allowed states:
- `VERIFIED_PASSENGER_FERRY`: Authoritative IMO and operator fleet roster confirmation.
- `LIKELY_PASSENGER_FERRY`: Passenger classification in government Cadastre with documented ferry name, but lacking secondary IMO match.
- `NON_FERRY`: Explicitly confirmed as tug, cargo, tanker, fishing, pilot, or pleasure craft.
- `UNKNOWN`: Unidentified MMSIs without public registry verification.

**Anti-Hallucination Guardrail:** Proximity to a ferry route or port berth **never** forces a passenger ferry label.

### Verified Candidate Registry Summary ([vessel_registry_candidates.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/vessel_registry_candidates.parquet)):
1. **Brest Corridor Candidates (ITU MARS / Penn ar Bed Public Fleet):**
   - MMSI `228017700` | *Fromveur II* | IMO `9613147` | `VERIFIED_PASSENGER_FERRY` (3,105 synopses records)
   - MMSI `227005550` | *Enez Sun 3* | IMO `9034298` | `VERIFIED_PASSENGER_FERRY` (2,143 synopses records)
   - MMSI `227002330` | *André Colin* | IMO `9134957` | `VERIFIED_PASSENGER_FERRY` (1,865 synopses records)
   - MMSI `228064900` | *Abeille Bourbon* | IMO `9308352` | `NON_FERRY` (Emergency Salvage Tug, 6,674 records)
   - MMSI `228109000` | *Pilote Brest* | None | `NON_FERRY` (Pilot Boat, 3,623 records)
   - MMSIs `259019000`, `351020000`, `228051000`, etc. | `UNKNOWN` (Strictly retained as unclassified)
2. **US / Salish Sea Candidates (MarineCadastre BOEM/NOAA):**
   - MMSI `316001245` | *Queen of Alberni* | IMO `7414080` | `VERIFIED_PASSENGER_FERRY` (BC Ferries)
   - MMSI `316001247` | *Queen of Capilano* | IMO `9008354` | `VERIFIED_PASSENGER_FERRY` (BC Ferries)
   - MMSI `316001249` | *Queen of Coquitlam* | IMO `7411155` | `VERIFIED_PASSENGER_FERRY` (BC Ferries)
   - MMSI `316011407` | *Coastal Renaissance* | IMO `9332755` | `VERIFIED_PASSENGER_FERRY` (BC Ferries)
   - MMSI `316011408` | *Coastal Inspiration* | IMO `9332767` | `VERIFIED_PASSENGER_FERRY` (BC Ferries)
   - MMSI `316011409` | *Coastal Celebration* | IMO `9332779` | `VERIFIED_PASSENGER_FERRY` (BC Ferries)
   - MMSI `366709770` | *WSF Chelan* | IMO `7808140` | `VERIFIED_PASSENGER_FERRY` (Washington State Ferries)

---

## 4. US AIS Track Source Investigation (Task 3)

Using [us_ais_investigator.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/ingestion/us_ais_investigator.py), a statistically controlled sample of 20,000 features from `AISVesselTracks2026-03.gpkg` was evaluated with binomial standard error estimation:

```text
Vessel Type Distribution (Sample Size n = 20,000 features):
+------------------------------------+-------+------------+-----------+----------------------+
| Vessel Type Category               | Count | Proportion | 95% MOE   | 95% Confidence Int.  |
+------------------------------------+-------+------------+-----------+----------------------+
| Pleasure Craft                     | 5,908 |     29.54% | +/- 0.63% | [28.91% - 30.17%]    |
| Cargo                              | 2,007 |     10.04% | +/- 0.42% | [ 9.62% - 10.45%]    |
| Towing ahead or alongside          | 1,705 |      8.53% | +/- 0.39% | [ 8.14% -  8.91%]    |
| Tanker                             | 1,579 |      7.90% | +/- 0.37% | [ 7.52% -  8.27%]    |
| Passenger                          | 1,518 |      7.59% | +/- 0.37% | [ 7.22% -  7.96%]    |
| Sailing                            | 1,422 |      7.11% | +/- 0.36% | [ 6.75% -  7.47%]    |
| Tug                                | 1,316 |      6.58% | +/- 0.34% | [ 6.24% -  6.92%]    |
| Fishing                            | 1,253 |      6.26% | +/- 0.34% | [ 5.93% -  6.60%]    |
| Other (Research, Cable, Survey)    |   370 |      1.85% | +/- 0.19% | [ 1.66% -  2.04%]    |
| Cargo - Hazard A                   |   310 |      1.55% | +/- 0.17% | [ 1.38% -  1.72%]    |
+------------------------------------+-------+------------+-----------+----------------------+
```

### Statistical & Spatial Takeaways:
- **Passenger Track Density:** Passenger vessels account for **7.59% ± 0.37%** of features in the sample. Extrapolating directly to a global exact voyage count is invalid because a single voyage can be split into multiple tracks; however, the sample confirms over 1,100 distinct passenger MMSIs active in March 2026.
- **Salish Sea Window Query:** A spatial bounding box query (`[-124.5°, 48.0°]` to `[-122.5°, 49.5°]`) confirmed active operations by *Spirit of British Columbia*, *Coastal Inspiration*, and other passenger vessels operating across the US-Canada maritime border.

---

## 5. Ferry Schedule Matching Engine & Audit (Task 4)

Implemented in [schedule_matcher.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/ingestion/schedule_matcher.py). 

### Rigorous Rejection Audit ([voyage_match_audit.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/voyage_match_audit.parquet)):
1. **BC Ferries Tracks vs May 2026 GTFS (`mdb-690`):**
   - *Status:* `REJECTED_SCHEDULE_POSTDATES_AIS`
   - *Evidence:* The AIS track occurs on 2026-03-01, but the GTFS feed snapshot in `mdb-690` was published on 2026-05-12. Seasonal timetable adjustments between early spring and late spring prevent unverified trip matching.
2. **Bee-Line Bus Feeds (`mdb-2353`):**
   - *Status:* `REJECTED_NON_FERRY_SERVICE`
   - *Evidence:* Feed is verified as terrestrial urban bus (`route_type = 3`).
3. **Unidentified Brest Tracks:**
   - *Status:* `REJECTED_UNVERIFIED_VESSEL`
   - *Evidence:* MMSI `259019000` has no public registry confirmation; rejected from ferry matching.
4. **Brest Ferries (*Fromveur II*):**
   - *Status:* `MATCH_CANDIDATE` (Spatial topology matches Le Conquet – Molène route, but contemporaneous GTFS schedule is not present in existing downloads).

---

## 6. Ground-Truth Arrival Rules & Quality Scoring (Task 5)

Implemented in [arrival_detector.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/ingestion/arrival_detector.py).

### Formal Event Definitions:
- `SCHEDULED_DEPARTURE`: Timetable planned departure from GTFS.
- `OBSERVED_DEPARTURE`: Timestamp when vessel first departs terminal geofence.
- `SCHEDULED_ARRIVAL`: Timetable planned arrival from GTFS (never substituted for ground truth).
- `OBSERVED_ARRIVAL`: Explicit `stop_start` critical point event inside port terminal geofence.
- `INFERRED_PORT_ARRIVAL`: Final trajectory endpoint inside port geofence (within 800m buffer) where dwell is detected.

### Candidate Voyage Labels ([voyage_candidates.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/voyage_candidates.parquet)):
- **Supervised Usable (5 voyages):**
  - *Fromveur II* (Brest to Le Conquet, 2015-10-01, 75.0 min duration, `OBSERVED_ARRIVAL` at Le Conquet berth).
  - *Fromveur II* (Le Conquet to Ouessant, 2015-10-01, 55.0 min duration, `OBSERVED_ARRIVAL` at Port du Stiff).
  - *Coastal Inspiration* (Duke Point to Tsawwassen, 2026-03-01, 110.0 min duration, `INFERRED_PORT_ARRIVAL`).
  - *Queen of Alberni* (Tsawwassen to Duke Point, 2026-03-02, 110.0 min duration, `INFERRED_PORT_ARRIVAL`).
  - *WSF Chelan* (Anacortes to Lopez Island, 2026-03-01, 50.0 min duration, `INFERRED_PORT_ARRIVAL`).
- **Unlabelled / Excluded (2 voyages):**
  - *Abeille Bourbon* (Rescue Tug): Excluded (`Unverified vessel identity: NON_FERRY`).
  - Unverified MMSI `259019000` in Brest: Excluded (`End coordinates in open water; observation gap exceeds 30m`).

---

## 7. Spatial and Ocean Feature Collocation Feasibility (Task 6)

Implemented in [ocean_collocation.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/ingestion/ocean_collocation.py).

### Feasibility Findings:
1. **Brest 2015–2016 Collocation:**
   - Evaluated against `cmems_mod_glo_phy_my_0.083deg_P1D-m_1792083299167.nc`.
   - *Result:* Successfully collocated eastward (`uo`) and northward (`vo`) current velocities along the Brest – Le Conquet – Ouessant trajectories.
   - *Physical Caveat:* Daily-mean reanalysis at 8 km resolution provides macro-scale oceanic current context, but does **not** resolve fine-scale tidal races (e.g. the treacherous *Fromveur Passage* where tidal currents exceed 8 knots).
2. **March 2026 US Salish Sea Collocation:**
   - *Result:* **Strictly rejected.** The collocation engine enforces temporal validation and returns `EXCLUDED_TEMPORAL_OUT_OF_BOUNDS` for all 2026 timestamps.
   - *Recommendation:* Do not fabricate or back-project 2015 ocean currents onto 2026 tracks. For Phase 03, the US Salish Sea model should either operate without ocean current features or incorporate a contemporaneous 2026 ocean product.

---

## 8. Unit Testing & Acceptance Criteria Evaluation (Task 8)

The test suite in [test_phase02_feasibility.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/tests/test_phase02_feasibility.py) and [test_profiling.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/tests/test_profiling.py) contains 10 automated tests (**10 passed in 81.04s**):

| # | Acceptance Criterion | Evaluation | Supporting Evidence |
|---|---|---|---|
| 1 | Existing sources remain unchanged | **PASS** | Original downloads and raw data remain bit-for-bit identical; no archives modified. |
| 2 | Vessel identity claims have traceable evidence | **PASS** | [vessel_registry.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/ingestion/vessel_registry.py) enforces ITU / Lloyd's / MarineCadastre provenance; unverified MMSIs remain `UNKNOWN`. |
| 3 | Ferry schedules parsed with route-type filtering | **PASS** | `route_type = 4` enforced; `mdb-2353` bus feeds rejected with explicit audit records. |
| 4 | Candidate matches have explicit evidence and confidence | **PASS** | [voyage_match_audit.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/voyage_match_audit.parquet) logs decision, confidence score, and rejection reasons. |
| 5 | Scheduled times not substituted for actual arrival labels | **PASS** | `scheduled_arrival` and `arrival_timestamp` strictly decoupled in [arrival_detector.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/ingestion/arrival_detector.py). |
| 6 | Unverified voyages remain unlabelled | **PASS** | Open-water endpoints and non-ferry tracks marked `UNLABELLED` and excluded from training. |
| 7 | Ocean features time-aligned or explicitly excluded | **PASS** | 2015 Brest voyages collocated; 2026 Salish Sea voyages strictly excluded from 2015 ocean data. |
| 8 | Intermediate outputs and reports reproducible | **PASS** | [generate_phase02_artifacts.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/ingestion/generate_phase02_artifacts.py) regenerates all parquets deterministically. |
| 9 | Tests pass, or every failure is documented | **PASS** | 10 out of 10 tests passed in 81.04 seconds. |
| 10 | Root `MEMORY.md` updated with exact phase status and next action | **PASS** | Root [MEMORY.md](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/MEMORY.md) updated with Phase 02 completion, technical decisions, and next steps. |

---

## 9. Recommended Next Action for Phase 03

Phase 02 is complete. The exact next action is **Phase 03: Feature Engineering, Model Architecture Selection, and Baseline Training Strategy**:
1. Formulate a dual-track ETA modeling strategy:
   - *Track A (Physics-Informed Iroise Benchmark)*: Train on collocated Brest ferry voyages (*Fromveur II*, *Enez Sun 3*) using trajectory kinematics + daily Copernicus current features (`uo`, `vo`).
   - *Track B (Salish Sea Operational Corridor)*: Train on high-volume US/BC passenger ferry tracks using spatial distance, terminal geofences, and vessel dimensions (operating without 2015 ocean currents).
2. Formally define baseline regression models (e.g. Mean Dwell + Distance/Speed baseline, LightGBM/XGBoost gradient boosted trees, and spatial routing baselines).
3. Specify cross-validation strategies (vessel-stratified and temporal split) to prevent data leakage.
