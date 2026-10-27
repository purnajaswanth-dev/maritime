# Geographic Datasets for Where Is My Ferry? (Iroise Sea & Finistère)

This directory contains localized, high-resolution geographic data files used for vessel land-avoidance, water corridor path generation, and real-time geofence enforcement.

## Files

1. `iroise_land.geojson` (~0.71 MB)
   - **Coverage:** Bounding box Latitude [47.8° N, 48.7° N], Longitude [-5.5° W, -4.1° W].
   - **Contents:** MultiPolygon representing all landmasses in the Iroise Sea and western Brittany, including mainland Finistère (Brest, Goulet de Brest, Pointe Saint-Mathieu, Camaret, Cap Sizun, Audierne estuary) and islands (Ouessant, Molène archipelago, Île de Sein).
   - **Source:** OpenStreetMap contributors (via Overpass API coastline data).
   - **License:** Open Database License (ODbL) 1.0 (https://opendatacommons.org/licenses/odbl/).
   - **Attribution:** "© OpenStreetMap contributors".
   - **Processing:** Coastlines extracted from OpenStreetMap, closed against bounding box edges, polygonized, topology-verified using Shapely 2.x, and lightly simplified (tolerance 0.00005° ≈ 5 m) to optimize memory and runtime performance while retaining navigation-grade coastal fidelity.

2. `routes.json` (< 200 KB)
   - **Contents:** Water-verified navigation polylines and geofence safety corridors for active simulation corridors:
     - `BREST_LE_CONQUET` (V-FROMVEUR-SIM)
     - `LE_CONQUET_BREST` (V-AZENOR-SIM)
     - `BREST_OUESSANT_STIFF` (V-OUESSANT-SIM)
     - `AUDIERNE_ILE_DE_SEIN` (V-SEIN-SIM)
   - **Manifest & Checksum:** SHA-256 integrity validation manifest and corridor geofence buffers (400 m near ports, 800 m in open water).
   - **Source:** Historical AIS voyage tracks (`data/replay/voyages.json`) and water path visibility optimization, anchored to official terminal berth coordinates and validated against `iroise_land.geojson`.
   - **License:** Project internal dataset derived from anonymized maritime navigation and OpenStreetMap data.
