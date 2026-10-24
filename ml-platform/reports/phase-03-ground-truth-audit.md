# Where Is My Ferry? — Phase 03: Ground-Truth Voyage & AIS Granularity Audit Report

**Date:** 2026-10-16  
**Auditor:** Senior ML Engineer & Data Scientist  
**Scope:** Phase 03 Ground-Truth Audit, Data Granularity Verification, and Label Usability Assessment  
**Status:** `AUDIT COMPLETE — 0 CONFIRMED REAL-WORLD SUPERVISED VOYAGES IN CURRENT PARQUET`

---

## 1. Executive Summary

In Phase 02, candidate Parquet artifacts (`voyage_candidates.parquet`, `vessel_registry_candidates.parquet`, `voyage_match_audit.parquet`) were generated to establish schema contracts, arrival detector heuristics, and schedule-matching interfaces. The Phase 02 report indicated five candidate voyages scored as `SUPERVISED_USABLE`.

In this Phase 03 audit, every individual candidate record was cross-referenced against the raw underlying AIS archives:
1. **datAcron Brest AIS Archive (`ais_brest_synopses_v0.8.zip`)**:
   - `ais_brest_positions_raw.csv`: **18,495,677 lines** (18,495,676 deduplicated raw kinematic AIS messages from NARI).
   - `ais_brest_synopses.csv`: **4,637,652 lines** (4,637,651 critical point trajectory synopses).
   - Archive volume: **24.24 GB uncompressed** across 9 members (resolving the prior narrative conflation of 24 GB with 24M observations).
2. **US MarineCadastre GeoPackage (`AISVesselTracks2026-03.gpkg`)**: 1,446,038 aggregated trackline features.

### Critical Audit Finding: A Three-Way Distinction
1. **Zero Verified Voyages in Current Candidate Parquet:** All seven candidate entries in `voyage_candidates.parquet` fail independent reconstruction (the 5 entries previously scored as `SUPERVISED_USABLE` were synthetic demonstration mockups created with nominal timestamps to test schema pipelines).
2. **Existence of Recoverable Real Voyages in Raw Archives:** The raw archives contain hundreds of physically observed real-world ferry transits (e.g. *FROMVEUR II* completed multiple genuine transits on 2015-10-01 in Brest, and *Coastal Inspiration* completed 29 track segments on 2026-03-01 in Salish Sea). Zero verified records in the candidate Parquet does NOT mean the raw archive is empty or unusable.
3. **Number of Verified Real Voyages Actually Extracted:** Currently **zero (0)**. A systematic segmentation pipeline is required to extract them defensibly.

Prior artifacts are preserved unmodified; audited dispositions are versioned in [phase_03_voyage_audit_result.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/phase_03_voyage_audit_result.parquet). All five candidate voyages have been downgraded to `UNVERIFIED` and excluded from supervised training.

---

## 2. Granularity Investigation: Point Observations vs. Aggregated Tracklines

Understanding data granularity is foundational to preventing false claims regarding live ETA prediction feasibility.

### Corridor A — datAcron Brest AIS Granularity
- **Data Unit:** Discrete, timestamped point observations (synopses).
- **Attributes per Ping:** `id` (MMSI), `timestamp` (epoch milliseconds UTC), `longitude`, `latitude`, `speed` (SOG in knots), `course` (COG), `heading`, `turn`.
- **Temporal Resolution:** High-frequency pings (typical interval 1 to 30 seconds while underway).
- **Live Snapshot Feasibility:** **FEASIBLE**. Because raw timestamped positions, speeds, and courses are available, an arbitrary simulation cutoff $t_{\text{pred}}$ can be selected during an in-progress trip, extracting only historical pings $t \le t_{\text{pred}}$ to predict $t_{\text{arr}}$.
- **Limitations:**
  - Academic research license (commercial redistribution prohibited without clearance).
  - External ITU/fleet registry cross-reference required to identify passenger ferries (vessel name not in data stream).
  - Requires automated trajectory segmentation into discrete voyages based on terminal dwell and speed cutoffs.

### Corridor B — US MarineCadastre 2026-03 AIS Granularity
- **Data Unit:** Pre-aggregated multi-segment tracklines (Layer: `AIS_Tracks_2026_03`).
- **Feature Schema:** `['OBJECTID', 'Shape', 'mmsi', 'vessel_name', 'imo', 'call_sign', 'vessel_type', 'vessel_type_name', 'navigation_status', 'vessel_length', 'width', 'draft', 'cargo', 'transceiver', 'duration_minutes', 'start_time', 'end_time']`.
- **Geometry Type:** 2D `MultiLineString` (EPSG:4326).
- **Temporal Resolution:** Two scalar timestamps per feature: `start_time` and `end_time`, plus integer `duration_minutes`.
- **Per-Vertex Timestamps:** **NONE (0)**. Coordinates are $(X, Y)$ only. No $(Z)$ or $(M)$ measurement dimensions exist.
- **Live Snapshot Feasibility:** **UNSUPPORTED BY THIS SOURCE ALONE**.
  - One cannot determine where the vessel was at an intermediate time $t \in (\text{start\_time}, \text{end\_time})$.
  - Interpolating along the MultiLineString curve to manufacture intermediate observations would be synthetic fabrication of data, which is explicitly prohibited.
- **Supported Use Cases:**
  - Retrospective voyage duration modeling for tracklines whose endpoints directly correspond to verified terminal berths.
- **Aggregation Variance:**
  - Tracklines vary wildly in scope. For *Coastal Inspiration* on 2026-03-01, NOAA segmented movement into 29 discrete track fragments (ranging from 1 minute to 212 minutes).
  - For *WSF Chelan* on 2026-03-01, NOAA created a single 24-hour trackline (`OBJECTID 3667`, duration 1439 minutes) combining all morning, afternoon, and evening runs into one single MultiLineString.
  - **Conclusion:** Track count $\neq$ voyage count. Feature count $\neq$ independent trips.

---

## 3. Detailed Audit of Every Candidate Voyage

The seven candidate records in `data/interim/voyage_candidates.parquet` were audited:

### 1. `VOY-FR-BREST-001`
- **Reported Identity:** MMSI `228017700` (*FROMVEUR II*), IMO 9613147. Confirmed passenger ferry via ITU MARS.
- **Reported Route:** Port de Brest $\rightarrow$ Le Conquet.
- **Reported Timestamps:** `2015-10-01 08:30:00` to `2015-10-01 09:45:00` (75.0 min).
- **Underlying Raw Evidence Audit:**
  - Scanning `ais_brest_synopses.csv` for MMSI `228017700` on 2015-10-01 revealed that *FROMVEUR II* actually slipped its moorings in Brest at **06:20:27 UTC** (speed 0.1 kn $\rightarrow$ 2.6 kn), accelerated to 13.4 kn at 06:27:54, transit the Goulet de Brest at 20.5 kn at 06:41:43, and arrived at the Le Conquet berth at **07:48:37 UTC** (speed dropped to 0.4 kn at 48.3595°N, -4.7844°W). Total actual duration: ~88 minutes.
  - At the reported candidate departure time (`08:30:00 UTC`), *FROMVEUR II* was already west of Le Conquet, cruising past Île de Molène towards Ouessant!
- **Label Disposition:** **UNVERIFIED / EXCLUDED FROM CONFIRMED SUPERVISED DATASET**.
- **Reason:** Nominal test timestamps do not match the physical voyage observed in raw AIS pings.

### 2. `VOY-FR-BREST-002`
- **Reported Identity:** MMSI `228017700` (*FROMVEUR II*).
- **Reported Route:** Le Conquet $\rightarrow$ Port du Stiff (Ouessant).
- **Reported Timestamps:** `2015-10-01 10:15:00` to `2015-10-01 11:10:00` (55.0 min).
- **Underlying Raw Evidence Audit:**
  - Raw AIS pings show that *FROMVEUR II* departed Le Conquet at 07:49:36 UTC, called at Molène at 08:38:03 UTC, and docked at Port du Stiff (Ouessant) at 48.4691°N, -5.0545°W before 09:30 UTC.
  - It remained moored with speed = 0.0 kn at Ouessant until 15:21:37 UTC.
  - At the candidate interval (`10:15:00` to `11:10:00`), the vessel was motionless at the pier.
- **Label Disposition:** **UNVERIFIED / EXCLUDED FROM CONFIRMED SUPERVISED DATASET**.
- **Reason:** Fictitious interval during stationary berth dwell.

### 3. `VOY-FR-BREST-003`
- **Reported Identity:** MMSI `228064900` (*ABEILLE BOURBON*), IMO 9308352.
- **Reported Route:** Port de Brest $\rightarrow$ UNKNOWN_DESTINATION.
- **Reported Timestamps:** `2015-10-02 04:00:00` to `2015-10-02 08:30:00` (270.0 min).
- **Underlying Raw Evidence Audit:**
  - Vessel is an emergency towing and salvage tug operated for the French Navy, not a scheduled passenger ferry.
  - Trajectory ended in open waters of the Iroise Sea.
- **Phase 02 Label:** `UNLABELLED`.
- **Phase 03 Disposition:** **REJECTED**.

### 4. `VOY-US-SALISH-001`
- **Reported Identity:** MMSI `316011408` (*COASTAL INSPIRATION*), IMO 9332767. Verified BC Ferries vessel.
- **Reported Route:** Duke Point Ferry Terminal $\rightarrow$ Tsawwassen Ferry Terminal.
- **Reported Timestamps:** `2026-03-01 14:15:00` to `2026-03-01 16:05:00` (110.0 min).
- **Underlying Raw Evidence Audit:**
  - Querying the indexed GeoPackage layer `AIS_Tracks_2026_03` for MMSI `316011408` on 2026-03-01 revealed 29 track features.
  - Feature `1215` started at `2026-03-01T10:49:59.0Z` and ended at `2026-03-01T14:22:58.0Z` (duration 212 min).
  - The next feature (`1216`) did not begin until `2026-03-01T16:00:01.0Z` (duration 150 min).
  - There is no track record in the GeoPackage matching 14:15:00 to 16:05:00. The candidate timestamps were artificially constructed to match a May 2026 GTFS timetable entry.
- **Label Disposition:** **UNVERIFIED / EXCLUDED FROM CONFIRMED SUPERVISED DATASET**.
- **Reason:** No matching feature in source database; derived from unverified schedule back-projection.

### 5. `VOY-US-SALISH-002`
- **Reported Identity:** MMSI `316001245` (*QUEEN OF ALBERNI*), IMO 7414080.
- **Reported Route:** Tsawwassen Ferry Terminal $\rightarrow$ Duke Point Ferry Terminal.
- **Reported Timestamps:** `2026-03-02 08:30:00` to `2026-03-02 10:20:00` (110.0 min).
- **Underlying Raw Evidence Audit:**
  - Querying the GeoPackage for MMSI `316001245` on 2026-03-02 revealed 22 track features.
  - Feature `54502` started at `07:31:46.0Z` and ended at `08:27:29.0Z` (duration 55 min).
  - No track feature corresponds to departure at 08:30:00 or arrival at 10:20:00.
- **Label Disposition:** **UNVERIFIED / EXCLUDED FROM CONFIRMED SUPERVISED DATASET**.
- **Reason:** Feature absent from source database.

### 6. `VOY-FR-BREST-004`
- **Reported Identity:** MMSI `259019000` (Unknown vessel).
- **Reported Route:** Port de Brest $\rightarrow$ UNKNOWN_DESTINATION.
- **Reported Timestamps:** `2015-10-01 02:00:00` to `2015-10-01 05:40:00` (220.0 min).
- **Underlying Raw Evidence Audit:**
  - Vessel identity cannot be verified in ITU MARS or public registers.
  - Contains a 45-minute ping gap (exceeds 30-minute threshold).
  - Endpoint terminates in open water.
- **Phase 02 Label:** `UNLABELLED`.
- **Phase 03 Disposition:** **REJECTED**.

### 7. `VOY-US-SALISH-003`
- **Reported Identity:** MMSI `366709770` (*WSF CHELAN*), IMO 7808140. Verified WSF passenger ferry.
- **Reported Route:** Anacortes Ferry Terminal $\rightarrow$ Lopez Island Terminal.
- **Reported Timestamps:** `2026-03-01 09:05:00` to `2026-03-01 09:55:00` (50.0 min).
- **Underlying Raw Evidence Audit:**
  - In the indexed US GeoPackage, MMSI `366709770` on 2026-03-01 contains **exactly one feature**: `OBJECTID 3667`, with `start_time = '2026-03-01T00:00:01.0Z'`, `end_time = '2026-03-01T23:59:50.0Z'`, and `duration_minutes = 1439`.
  - NOAA aggregated the vessel's entire 24-hour service into a single MultiLineString. No discrete 50-minute voyage exists as an independent feature.
- **Label Disposition:** **UNVERIFIED / EXCLUDED FROM CONFIRMED SUPERVISED DATASET**.
- **Reason:** Multi-trip 24-hour aggregation in source; individual voyage not extractable without raw NMEA pings.

---

## 4. Summary Audit Matrix

| Voyage ID | Vessel Name | MMSI | Phase 02 Label | Phase 03 Disposition | Independent Verification Status | Supervised Usable |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `VOY-FR-BREST-001` | *FROMVEUR II* | 228017700 | `SUPERVISED_USABLE` | **UNVERIFIED** | Failed (real trip: 06:20 to 07:48 UTC) | **NO** |
| `VOY-FR-BREST-002` | *FROMVEUR II* | 228017700 | `SUPERVISED_USABLE` | **UNVERIFIED** | Failed (docked at Ouessant until 15:21) | **NO** |
| `VOY-FR-BREST-003` | *ABEILLE BOURBON* | 228064900 | `UNLABELLED` | **REJECTED** | Non-ferry salvage tug; open water | **NO** |
| `VOY-US-SALISH-001` | *COASTAL INSPIRATION* | 316011408 | `SUPERVISED_USABLE` | **UNVERIFIED** | Failed (no feature matching interval) | **NO** |
| `VOY-US-SALISH-002` | *QUEEN OF ALBERNI* | 316001245 | `SUPERVISED_USABLE` | **UNVERIFIED** | Failed (no feature matching interval) | **NO** |
| `VOY-FR-BREST-004` | *(Unknown)* | 259019000 | `UNLABELLED` | **REJECTED** | Unknown MMSI; 45m gap; open water | **NO** |
| `VOY-US-SALISH-003` | *WSF CHELAN* | 366709770 | `SUPERVISED_USABLE` | **UNVERIFIED** | Failed (source is single 24hr line) | **NO** |

**Total Confirmed Ground-Truth Voyages in Current Parquet:** **0**  
**Total Confirmed Independent Vessels with Extracted Ground Truth:** **0**

---

## 5. Artifact Provenance & Versioning

- Original artifact [voyage_candidates.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/voyage_candidates.parquet) preserved unmodified to maintain lineage integrity.
- Audited results written to versioned parquet:  
  [phase_03_voyage_audit_result.parquet](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/data/interim/phase_03_voyage_audit_result.parquet).
- Feature contract configured: [eta_feature_contract.yaml](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/configs/eta_feature_contract.yaml).
- Evaluation policy configured: [evaluation_policy.yaml](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/configs/evaluation_policy.yaml).
- Baseline implementation validated: [baselines.py](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/ml-platform/src/models/baselines.py) with 8 passing unit tests.
