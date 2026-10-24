# Map Tile Watermark Fix & OpenStreetMap Default Provider Report

**Date:** 2026-10-25  
**Objective:** Eliminate "API KEY REQUIRED" raster tile watermark stamped by CARTO on keyless requests, configure OpenStreetMap as the primary clean default zero-key provider, support optional `VITE_CARTO_KEY` via `.env`, and maintain graceful tiered fallback to local vector GeoJSON.

---

## 1. Root Cause Analysis

CARTO (`basemaps.cartocdn.com`) updated its public policy regarding raster tile endpoints (`/rastertiles/voyager/{z}/{x}/{y}.png`). Unauthenticated / keyless tile requests continue returning HTTP 200 responses, but each tile image is stamped with a baked-in "API KEY REQUIRED" watermark diagonally across the tile graphic.

In `where-is-my-ferry`, the frontend `FerryMap` and `tileProviders.ts` previously designated CARTO Voyager as the primary layer without an API key. Consequently, all maritime map views displayed watermarked tiles across the Brittany coastline and Iroise Sea.

---

## 2. Step 1: Tile Source Inventory (Pre-Edit Audit)

A comprehensive scan across `frontend/` (`src/`, `public/`, `index.html`, `.env*`, `vite.config.ts`) identified all tile sources and key references:

1. **`frontend/src/components/map/FerryMap.tsx`**
   - Line 106: Hardcoded direct CartoDB Voyager raster tile URL:
     `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png`
   - *Impact:* Root cause of the "API KEY REQUIRED" raster watermark.

2. **`frontend/src/map/tileProviders.ts`**
   - Lines 28-29: Default provider pointing to keyless `basemaps.cartocdn.com`.
   - Lines 62-75: Rigid validator banning any `key=` parameters.

3. **`frontend/src/__tests__/TileProviders.test.ts`**
   - Unit tests enforcing strict absence of any `key=` string, preventing valid optional CARTO key support.

4. **`frontend/e2e/phaseA.spec.ts`**
   - E2E assertions for Phase A tile layer behavior.

5. **Environment & Configuration:**
   - No `.env.example` existed in `frontend/`.
   - Root `.gitignore` already properly ignores `.env` and `.env.*`.

---

## 3. Step 2: Implementation & Architectural Fixes

### A. Centralized Tier Provider (`frontend/src/map/tileProviders.ts`)
Refactored `tileProviders.ts` to export an ordered list of tile tiers:
1. **Tier 1 (Optional CARTO Voyager):** Included ONLY if `import.meta.env.VITE_CARTO_KEY` is present and non-empty:
   - URL: `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=<VITE_CARTO_KEY>`
   - Subdomains: `'abcd'`, `maxZoom: 20`, attribution with links to OSM and CARTO.
2. **Tier 2 (OpenStreetMap Default):** Default tier when no key is configured:
   - URL: `https://tile.openstreetmap.org/{z}/{x}/{y}.png`
   - `maxZoom: 19`, attribution: `© OpenStreetMap contributors` linked to `https://www.openstreetmap.org/copyright`.
   - Normal browser referrer preserved (no `referrerPolicy: 'no-referrer'`).
3. **Tier 3 (Offline Vector Tier):** Local `iroiseCoastline.json` GeoJSON drawn on a plain sea-colored canvas (`#071B2B` / `#1E3A52`), displaying a prominent `"Offline map"` badge.

Implemented `TileErrorTracker` sliding-window state machine: advances to the next tier if 6 tile load errors occur within 5 seconds.

### B. Map Component (`frontend/src/components/map/FerryMap.tsx`)
- Standardized on `tileProviders.ts` as the sole source of truth for tile URLs.
- Removed all hardcoded `cartocdn.com` URLs.
- Bound `tileerror` events directly to `TileErrorTracker`.
- React state synchronization for `mapInstance` ensuring vessel marker, heading arrow, live speed label, and voyage track render reliably even under React StrictMode re-mounts.
- Explicit container height and Leaflet default marker asset resolution for Vite bundler.

### C. Environment Configuration (`frontend/.env.example`)
Created `frontend/.env.example`:
```bash
# Optional: CARTO Voyager Basemap API Key (free tier available at https://carto.com/basemaps/apikey)
# If left unset or blank, Where Is My Ferry automatically defaults to OpenStreetMap with zero watermark.
VITE_CARTO_KEY=
```

---

## 4. Tests Added & Updated

### Vitest Unit Suite (`frontend/src/__tests__/TileProviders.test.ts`)
- **Keyless Default:** Verified that with no `VITE_CARTO_KEY`, Tier 1 is OpenStreetMap and contains no `cartocdn`, `key=`, `apiKey`, or `access_token`.
- **Optional CARTO Key:** Verified that with `VITE_CARTO_KEY="test123"`, Tier 1 is CARTO with URL ending in `?key=test123`, and Tier 2 is OpenStreetMap.
- **Offline Fallback Config:** Verified local `iroiseCoastline.json` vector layer and attribution.
- **Sliding Window State Machine:** Verified tier progression upon 6 tile errors within 5 seconds, and window expiry reset.
- **Src Code Scan:** Enforced that no file in `frontend/src` contains `"cartocdn.com"` outside `tileProviders.ts`.

### Playwright E2E Suite (`frontend/e2e/phaseA.spec.ts`)
- **Test 1 (Clean Tiles & Live Tracking):**
  - Open `/track` with clean cache.
  - Assert HTTP 200 responses from `tile.openstreetmap.org`.
  - Assert the text `"API KEY REQUIRED"` is absent from page.
  - Captured full-resolution screenshot: `docs/fix/map_clean_tiles.png`.
  - Verified vessel marker renders and telemetry updates over 10 seconds.
- **Test 2 (Offline Fallback on Tile Outage):**
  - Blocked all external tile endpoints (`tile.openstreetmap.org` and `basemaps.cartocdn.com`).
  - Verified 6 tile errors trigger automatic switch to Tier 3 (offline vector map).
  - Asserted visible `"Offline map"` indicator badge and GeoJSON coastline render.
  - Captured screenshot: `docs/fix/map_offline_fallback.png`.

---

## 5. Verification & Test Totals

| Test Suite | Total Files | Passed | Failed | Status |
|---|---|---|---|---|
| **Vitest (Unit & Integration)** | 27 | 98 / 98 | 0 | **PASS** |
| **Playwright E2E (`phaseA.spec.ts`)** | 1 | 2 / 2 | 0 | **PASS** |
| **Playwright E2E (Full Suite)** | 4 | 15 / 15 | 0 | **PASS** |
| **TypeScript & Production Build (`npm run build`)** | - | Exit Code 0 | 0 | **PASS** (5.30s) |

---

## 6. How to Add an Optional CARTO Key

To enable CARTO Voyager as the primary layer:
1. Create a `frontend/.env` file (or append to existing):
   ```bash
   VITE_CARTO_KEY=your_carto_api_key_here
   ```
2. Restart the Vite development server or rebuild the application:
   ```bash
   npm run dev
   # or
   npm run build
   ```
3. When `VITE_CARTO_KEY` is present and non-empty, `getTileTiers()` places CARTO Voyager with `?key=<KEY>` at Tier 1 and OpenStreetMap at Tier 2. When omitted, OpenStreetMap is automatically served with zero configuration.

---

## 7. Artifacts & Screenshots

- Clean OpenStreetMap Tiles: [`docs/fix/map_clean_tiles.png`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/docs/fix/map_clean_tiles.png)
- Offline GeoJSON Vector Fallback: [`docs/fix/map_offline_fallback.png`](file:///c:/Users/sunka/OneDrive/coding/where-is-my-ferry/docs/fix/map_offline_fallback.png)
