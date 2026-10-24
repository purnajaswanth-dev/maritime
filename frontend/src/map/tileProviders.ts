/**
 * tileProviders.ts
 * Configures map tile tiers for Where Is My Ferry?
 * 
 * Hierarchy:
 * 1. CARTO Voyager (ONLY if VITE_CARTO_KEY is non-empty)
 * 2. OpenStreetMap Standard (Default when no key is provided - Clean & watermark-free)
 * 3. Offline GeoJSON Vector Coastline (Local Brittany coastline fallback)
 */

import iroiseCoastlineGeoJson from './iroiseCoastline.json';

export type MapTier = 'cartodb' | 'osm' | 'offline';

export interface TileTierConfig {
  id: MapTier;
  name: string;
  url?: string;
  subdomains?: string | string[];
  maxZoom?: number;
  attribution: string;
  isOffline: boolean;
}

export function getTileTiers(cartoKey?: string): TileTierConfig[] {
  const envKey = typeof cartoKey !== 'undefined'
    ? cartoKey
    : (typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env.VITE_CARTO_KEY : '');

  const cleanKey = typeof envKey === 'string' ? envKey.trim() : '';
  const tiers: TileTierConfig[] = [];

  // Tier 1: CARTO Voyager (ONLY if key is provided and non-empty)
  if (cleanKey) {
    tiers.push({
      id: 'cartodb',
      name: 'CARTO Voyager',
      url: `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=${cleanKey}`,
      subdomains: 'abcd',
      maxZoom: 20,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>, &copy; <a href="https://carto.com/" target="_blank" rel="noopener noreferrer">CARTO</a>',
      isOffline: false,
    });
  }

  // Tier 2 (or Default Tier 1 when no key): OpenStreetMap Standard
  tiers.push({
    id: 'osm',
    name: 'OpenStreetMap',
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    subdomains: 'abc',
    maxZoom: 19,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>',
    isOffline: false,
  });

  // Tier 3: Local Offline GeoJSON Vector Coastline
  tiers.push({
    id: 'offline',
    name: 'Offline Coastline Vector',
    maxZoom: 18,
    attribution: 'Natural Earth 10m Coastline (Offline Maritime Replay)',
    isOffline: true,
  });

  return tiers;
}

export const TILE_TIERS: TileTierConfig[] = getTileTiers();

export const OFFLINE_VECTOR_CONFIG = {
  id: 'offline' as const,
  name: 'Local Offline Vector Coastline',
  geoJson: iroiseCoastlineGeoJson,
  backgroundColor: '#071B2B', // Plain sea-coloured background
  landFillColor: '#1E3A52',
  landStrokeColor: '#2A4D6C',
  attribution: 'Natural Earth 10m Coastline (Offline Maritime Replay)',
  isOffline: true,
};

/**
 * Tile error tracker state machine.
 * Advances to next tier after 6 tile errors within a 5-second (5000ms) sliding window.
 */
export class TileErrorTracker {
  private errorTimestamps: number[] = [];
  private currentTierIndex = 0;
  private readonly tiers: TileTierConfig[];
  private readonly thresholdCount: number;
  private readonly windowMs: number;
  private onTierChange?: (newTier: TileTierConfig) => void;

  constructor(
    thresholdCount = 6,
    windowMs = 5000,
    onTierChange?: (newTier: TileTierConfig) => void,
    cartoKey?: string
  ) {
    this.thresholdCount = thresholdCount;
    this.windowMs = windowMs;
    this.onTierChange = onTierChange;
    this.tiers = getTileTiers(cartoKey);
  }

  public recordError(now = Date.now()): TileTierConfig {
    this.errorTimestamps = this.errorTimestamps.filter(
      (ts) => now - ts < this.windowMs
    );
    this.errorTimestamps.push(now);

    if (this.errorTimestamps.length >= this.thresholdCount) {
      this.errorTimestamps = [];
      if (this.currentTierIndex < this.tiers.length - 1) {
        this.currentTierIndex++;
        const newTier = this.tiers[this.currentTierIndex];
        this.onTierChange?.(newTier);
      }
    }

    return this.getCurrentTierConfig();
  }

  public getCurrentTier(): MapTier {
    return this.tiers[this.currentTierIndex].id;
  }

  public getCurrentTierConfig(): TileTierConfig {
    return this.tiers[this.currentTierIndex];
  }

  public reset(): void {
    this.errorTimestamps = [];
    this.currentTierIndex = 0;
  }
}
