import { describe, it, expect, vi } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import {
  getTileTiers,
  OFFLINE_VECTOR_CONFIG,
  TileErrorTracker,
} from '../map/tileProviders';

describe('Map Tile Providers Configuration & Dynamic Tiers', () => {
  it('with no VITE_CARTO_KEY set, the first tier is OpenStreetMap and no tier URL contains "cartocdn", "key=", "apiKey" or "access_token"', () => {
    const tiers = getTileTiers('');
    expect(tiers.length).toBeGreaterThanOrEqual(2);

    // First tier must be OpenStreetMap
    expect(tiers[0].id).toBe('osm');
    expect(tiers[0].name).toBe('OpenStreetMap');
    expect(tiers[0].url).toContain('tile.openstreetmap.org');

    const forbiddenPatterns = [/cartocdn/i, /key=/i, /apiKey/i, /access_token/i];
    tiers.forEach((tier) => {
      if (tier.url) {
        forbiddenPatterns.forEach((pattern) => {
          expect(tier.url).not.toMatch(pattern);
        });
      }
    });
  });

  it('with VITE_CARTO_KEY set to "test123", the first tier is CARTO and its URL ends with ?key=test123 and the second tier is OSM', () => {
    const tiers = getTileTiers('test123');
    expect(tiers[0].id).toBe('cartodb');
    expect(tiers[0].name).toBe('CARTO Voyager');
    expect(tiers[0].url).toBe(
      'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=test123'
    );
    expect(tiers[0].url?.endsWith('?key=test123')).toBe(true);

    // Second tier must be OpenStreetMap
    expect(tiers[1].id).toBe('osm');
    expect(tiers[1].name).toBe('OpenStreetMap');
    expect(tiers[1].url).toBe('https://tile.openstreetmap.org/{z}/{x}/{y}.png');
  });

  it('provides valid local offline GeoJSON vector configuration', () => {
    expect(OFFLINE_VECTOR_CONFIG.id).toBe('offline');
    expect(OFFLINE_VECTOR_CONFIG.isOffline).toBe(true);
    expect(OFFLINE_VECTOR_CONFIG.geoJson).toBeDefined();
    expect((OFFLINE_VECTOR_CONFIG.geoJson as any).type).toBe('FeatureCollection');
    expect((OFFLINE_VECTOR_CONFIG.geoJson as any).features.length).toBeGreaterThan(0);
  });

  it('fallback test: after 6 tile errors within 5 seconds the active tier advances; after the last tile tier it switches to the offline GeoJSON', () => {
    const onTierChange = vi.fn();
    // Test with CARTO key present (3 tiers: cartodb -> osm -> offline)
    const trackerWithKey = new TileErrorTracker(6, 5000, onTierChange, 'test123');
    expect(trackerWithKey.getCurrentTier()).toBe('cartodb');

    // 5 errors: below threshold
    for (let i = 0; i < 5; i++) {
      trackerWithKey.recordError();
    }
    expect(trackerWithKey.getCurrentTier()).toBe('cartodb');

    // 6th error: advances to OSM
    trackerWithKey.recordError();
    expect(trackerWithKey.getCurrentTier()).toBe('osm');

    // 6 more errors: advances to offline
    for (let i = 0; i < 6; i++) {
      trackerWithKey.recordError();
    }
    expect(trackerWithKey.getCurrentTier()).toBe('offline');

    // Test with default (no key, 2 tiers: osm -> offline)
    const trackerNoKey = new TileErrorTracker(6, 5000, undefined, '');
    expect(trackerNoKey.getCurrentTier()).toBe('osm');
    for (let i = 0; i < 6; i++) {
      trackerNoKey.recordError();
    }
    expect(trackerNoKey.getCurrentTier()).toBe('offline');
  });

  it('TileErrorTracker does not degrade if errors are outside the 5-second sliding window', () => {
    const tracker = new TileErrorTracker(6, 5000, undefined, 'test123');

    const t0 = 10000;
    // 5 errors at t0
    for (let i = 0; i < 5; i++) {
      tracker.recordError(t0);
    }
    expect(tracker.getCurrentTier()).toBe('cartodb');

    // 6th error occurs 6 seconds later (window expired)
    tracker.recordError(t0 + 6000);
    expect(tracker.getCurrentTier()).toBe('cartodb');
  });

  it('scan test: fails if any file under frontend/src contains the string "cartocdn.com" outside tileProviders.ts', () => {
    const srcDir = path.resolve(__dirname, '..');
    const violations: string[] = [];
    const targetString = ['carto', 'cdn.com'].join('');

    function scanDir(dir: string) {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          scanDir(fullPath);
        } else if (entry.isFile() && /\.(tsx?|jsx?|html|css|json)$/i.test(entry.name)) {
          const relativePath = path.relative(srcDir, fullPath).replace(/\\/g, '/');
          // Allow only tileProviders.ts and the test file itself
          if (relativePath === 'map/tileProviders.ts' || relativePath.includes('TileProviders.test.ts')) {
            continue;
          }
          const content = fs.readFileSync(fullPath, 'utf-8');
          if (content.includes(targetString)) {
            violations.push(relativePath);
          }
        }
      }
    }

    scanDir(srcDir);
    expect(violations).toEqual([]);
  });
});
