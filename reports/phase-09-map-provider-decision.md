# Map Provider Architecture & No-User-Key Decision Document

**Project:** Where Is My Ferry?  
**Phase:** 09 — Map Reliability & Integration Planning (Corrective Architecture Review)  
**Auditor:** Geospatial Systems Engineer & Senior Frontend Architect  
**Date:** 2026-10-16  
**Status:** Approved Architectural Baseline (Corrected)  

---

## 1. Executive Mandate: Critical Requirement A

> **"The finished application must not ask the user to obtain, purchase, or manually enter a map API key merely to view the vessel-tracking map."**

This document establishes the tile provider strategy, usage compliance, fallback hierarchy, technical browser error handling, and deterministic verification test suite to guarantee that the tracking map operates seamlessly out of the box on any fresh clone without requiring map accounts, credit cards, `.env` private keys, or third-party signups.

---

## 2. Audit of Existing Map Implementation

### A. Current Configuration in `frontend/src/components/tracking/FleetMap.tsx`
- **Library:** Leaflet 1.9.4 (`leaflet@^1.9.4`)
- **Active Tile URL:** `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png`
- **Subdomains:** `['a', 'b', 'c', 'd']`
- **Zoom Range:** Default zoom `10`, min zoom `8`, max zoom `18`
- **Map View Center:** `[48.34, -4.75]` (Iroise Sea, Brittany)
- **Attribution Text:** `&copy; <a href="https://openstreetmap.org" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> | CartoDB`
- **API Key Status:** **None required.** The endpoint directly serves 256x256 raster PNG tiles over standard HTTPS.
- **Vessel Marker / Overlay Layer:** Decoupled from tile layer using independent Leaflet `Marker`, `Polyline`, and `Popup` instances.

### B. Provider Capabilities, Policies, and Limitation Analysis

| Provider / Source | URL Template | Key Required? | Commercial Cost | Usage Constraints & Rate Limits | Visual Suitability |
|---|---|---|---|---|---|
| **CartoDB Voyager** *(Primary Online)* | `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png` | **NO** | Free for non-commercial web demo & evaluation | Carto Basemaps TOS: Free tier permitted for open web demonstration. Must not be scraped; browser caching respected. | **Superior:** High contrast ocean blues (`#A0C8D7`), subdued land, clear route contrast. |
| **OpenStreetMap Standard** *(Secondary Online)* | `https://tile.openstreetmap.org/{z}/{x}/{y}.png` | **NO** | Free open-source | Strict OSM Foundation Tile Usage Policy: Valid User-Agent required, strict rate limiting, no bulk scraping, max 2 concurrent download threads. | **High:** Universally accessible fallback; slightly crowded land topography. |
| **Local GeoJSON Coastline** *(Tier 3 Offline Vector)* | Bundled `frontend/src/data/iroiseCoastline.json` | **NO** | Zero | 100% offline, zero network dependencies, zero rate limits, instantaneous load. | **Essential Fallback:** Clean polygon landmass with vessel overlay visibility. |
| **Mapbox GL / Raster** | `https://api.mapbox.com/...` | **YES** | Paid / Tiered free quota | Requires mandatory `pk.eyJ...` public access token; breaks fresh clones without user setup. | **Rejected:** Violates Critical Requirement A. |
| **Stadia Maps** | `https://tiles.stadiamaps.com/...` | **YES** | Paid / Auth required | Requires API key or domain whitelist registration. | **Rejected:** Violates Critical Requirement A. |

---

## 3. Technical Assessment of Browser-Level Automatic Tile Fallback

### A. Reliability of `tileerror` in Leaflet
In Leaflet, the standard `TileLayer` fires a `tileerror` event whenever an individual tile image fails to load (e.g. HTTP 404, 429, 503, or network timeout/DNS failure). However, relying naively on individual `tileerror` events introduces significant operational risks:
1. **Isolated Missing Tiles vs. Provider Outage:** A single missing tile (e.g., zoom level edge) should NOT immediately trigger a full provider switch.
2. **Infinite Fallback Loops:** If a secondary provider also encounters an error, alternating between providers can cause render thrashing and CPU spikes.
3. **CORS / Mixed Content Constraints:** All tile sources must strictly use HTTPS.

### B. Resilient Provider-Switching State Machine
To guarantee browser-level technical reliability, the fallback logic is managed via a deterministic state machine:

```
[ Tier 1: CartoDB Active ]
       │
       │ (tileerror event fires)
       ▼
[ Increment consecutive_error_count ]
       │
       ├─► (consecutive_error_count < 6) ──► Log warning, maintain Tier 1 (allow transient retry)
       │
       └─► (consecutive_error_count >= 6 within 5.0s window)
                 │
                 ▼
         [ Fallback to Tier 2: OSM Standard ]
                 │
                 │ (OSM tileerror event fires)
                 ▼
         [ Increment osm_consecutive_error_count ]
                 │
                 ├─► (osm_consecutive_error_count < 6) ──► Allow transient retry
                 │
                 └─► (osm_consecutive_error_count >= 6 within 5.0s window)
                           │
                           ▼
                   [ Fallback to Tier 3: Local GeoJSON Vector Basemap ]
                   - Unmount raster TileLayer
                   - Render local vector coastline polygon (`#E2E8F0` land, `#071B2B` sea)
                   - Retain all vessel markers, heading vectors, route polylines, and popups
                   - Display degraded basemap toast notification
```

### C. Independence of Basemap Failures and Telemetry Failures
A basemap tile failure is **purely a presentation layer issue**. It must never:
- Invalidate or discard live vessel telemetry.
- Freeze ETA countdowns.
- Mark the simulation as disconnected.
- Hide vessel markers or route polylines.

Conversely, a telemetry/backend failure (Python or Spring Boot offline) must never disrupt map pan, zoom, or tile rendering.

---

## 4. Map Safety, Disclaimers, and Non-Operational Boundaries

1. **Non-Navigation Disclaimer:** A permanently visible badge in the map corner states:
   `"SIMULATED FLEET VISUALIZATION — NOT FOR OFFICIAL NAUTICAL NAVIGATION"`.
2. **Attribution Integrity:**
   - When Tier 1 is active: `© OpenStreetMap contributors | CartoDB`.
   - When Tier 2 is active: `© OpenStreetMap contributors`.
   - When Tier 3 is active: `Local Coastline Vector Data | OpenStreetMap Contributors`.
   Attribution must remain permanently clickable and visible on desktop and mobile viewports.
3. **Graceful Degraded Status Toast:**
   If switching to Tier 3 offline vector fallback, the UI displays:
   `"External map tiles unavailable. Displaying local vector coastline fallback. Vessel tracking remains active."`

---

## 5. Deterministic Verification & Test Specification

The implementation must pass the following deterministic test suite:

### Test Case MAP-DET-01: Normal Primary Provider Operation
- **Precondition:** Standard network connectivity, clean browser cache.
- **Action:** Navigate to `/track`.
- **Expected Outcome:** CartoDB Voyager tiles load (HTTP 200); Leaflet tile container contains valid `.png` images from `cartocdn.com`; attribution shows `OpenStreetMap | CartoDB`; zero console errors.

### Test Case MAP-DET-02: Primary Provider Failure Fallback
- **Precondition:** Block requests to `*.basemaps.cartocdn.com` via DevTools network blocking or proxy.
- **Action:** Pan or zoom the map.
- **Expected Outcome:** Consecutive tile errors reach threshold 6; map seamlessly hot-swaps tile URL to `tile.openstreetmap.org`; map continues displaying tiles; vessel markers do not flicker or unmount.

### Test Case MAP-DET-03: Complete Online Provider Outage (Tier 3 Vector Fallback)
- **Precondition:** Block requests to both `*.cartocdn.com` and `tile.openstreetmap.org`.
- **Action:** Navigate to `/track` or trigger viewport change.
- **Expected Outcome:** Raster layer is unmounted; local GeoJSON vector coastline renders (Finistère, Ouessant, Molène, Sein); background canvas is dark navy `#071B2B`; landmass is slate `#E2E8F0`; vessel markers, route paths, and ETA countdowns remain fully interactive; non-blocking degraded basemap banner is displayed.

### Test Case MAP-DET-04: Fully Offline / Airplane Mode Operation
- **Precondition:** Host machine set to Airplane Mode (zero internet access). Backend and Python running locally on `localhost`.
- **Action:** Launch browser, load `http://localhost:5173/track`.
- **Expected Outcome:** Application loads from Vite local bundle; local GeoJSON vector basemap renders immediately without network hang; live virtual vessels move across the vector bay; zero crash.

### Test Case MAP-DET-05: Attribution Visibility & Legal Compliance
- **Precondition:** Responsive viewports tested (1920x1080 desktop, 768x1024 tablet, 375x812 mobile).
- **Action:** Inspect Leaflet attribution control.
- **Expected Outcome:** Attribution text is never truncated, hidden, or covered by UI panels (`VesselDetailPanel`, simulation drawer); links open safely in external tabs (`rel="noopener noreferrer"`).

### Test Case MAP-DET-06: Map Resize & Marker Interaction During Fallback
- **Precondition:** Map running under Tier 3 offline vector fallback.
- **Action:** Toggle vessel details drawer, resize browser window, click vessel marker, click route line.
- **Expected Outcome:** `map.invalidateSize()` executes cleanly; marker click opens popup/drawer; selection state syncs with query parameter (`?vesselId=...`); zero layout shift or crash.
