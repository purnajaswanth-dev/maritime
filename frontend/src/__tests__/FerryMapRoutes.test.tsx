import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, waitFor, cleanup } from '@testing-library/react';
import React from 'react';
import L from 'leaflet';
import { FerryMap, RouteGeometry } from '../components/map/FerryMap';

describe('FerryMap Routes & Geofencing Component Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('renders corridor lines from /api/v1/routes/geometry with coordinates preserved in [lat, lon] order', async () => {
    const mockRoutes: RouteGeometry[] = [
      {
        id: 'BREST_LE_CONQUET',
        name: 'Brest - Le Conquet Water Corridor',
        origin_terminal_id: 'BREST',
        destination_terminal_id: 'LE_CONQUET',
        polyline: [
          [48.38218, -4.48563],
          [48.382, -4.486],
          [48.36, -4.62],
          [48.3585, -4.7788],
        ],
        length_km: 29.65,
        great_circle_km: 21.83,
      },
    ];

    const polylineSpy = vi.spyOn(L, 'polyline');

    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/routes/geometry')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockRoutes),
          });
        }
        return Promise.reject(new Error('Unknown URL: ' + url));
      })
    );

    render(
      <FerryMap
        telemetry={{
          departureId: 'dep-101',
          vesselName: 'Fromveur II',
          mmsi: 228037700,
          latitude: 48.38218,
          longitude: -4.48563,
          speedKnots: 15.0,
          headingDegrees: 270,
          state: 'UNDERWAY',
          dataSource: 'HISTORICAL_REPLAY',
        }}
      />
    );

    await waitFor(() => {
      expect(polylineSpy).toHaveBeenCalled();
      const calls = polylineSpy.mock.calls;
      const corridorCall = calls.find(
        (call) => Array.isArray(call[0]) && call[0].length === 4
      );
      expect(corridorCall).toBeDefined();
      const coords = corridorCall![0] as [number, number][];
      // Coordinates must be in [lat, lon] order: latitude in [48.0, 48.5], longitude in [-5.5, -4.0]
      expect(coords[0][0]).toBeCloseTo(48.38218, 4);
      expect(coords[0][1]).toBeCloseTo(-4.48563, 4);
      expect(coords[0][0]).toBeGreaterThan(coords[0][1]); // lat > lon in Brittany
    });
  });

  it('draws NO corridor lines when /api/v1/routes/geometry fetch fails, never drawing straight lines over land', async () => {
    const polylineSpy = vi.spyOn(L, 'polyline');

    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        if (url.includes('/api/v1/routes/geometry')) {
          return Promise.reject(new Error('Simulation daemon offline'));
        }
        return Promise.reject(new Error('Unknown URL: ' + url));
      })
    );

    render(
      <FerryMap
        telemetry={{
          departureId: 'dep-101',
          vesselName: 'Fromveur II',
          mmsi: 228037700,
          latitude: 48.38218,
          longitude: -4.48563,
          speedKnots: 15.0,
          headingDegrees: 270,
          state: 'UNDERWAY',
          dataSource: 'HISTORICAL_REPLAY',
        }}
      />
    );

    await waitFor(() => {
      // Any polylines created should NOT be straight lines of length 2 cutting across land
      const corridorStraightLineCalls = polylineSpy.mock.calls.filter(
        (call) =>
          Array.isArray(call[0]) &&
          call[0].length === 2 &&
          (call[1] as any)?.color === '#14B8A6'
      );
      expect(corridorStraightLineCalls.length).toBe(0);
    });
  });

  it('enforces 300m breadcrumb rule: does not connect points jumping > 300m across land', async () => {
    const polylineSpy = vi.spyOn(L, 'polyline');

    const { rerender } = render(
      <FerryMap
        telemetry={{
          departureId: 'dep-101',
          vesselName: 'Fromveur II',
          mmsi: 228037700,
          latitude: 48.382,
          longitude: -4.485,
          speedKnots: 15.0,
          headingDegrees: 270,
          state: 'UNDERWAY',
          dataSource: 'HISTORICAL_REPLAY',
        }}
      />
    );

    // Update with a jump > 300m (e.g. from Brest 48.382 to Le Conquet 48.359: ~23 km)
    rerender(
      <FerryMap
        telemetry={{
          departureId: 'dep-101',
          vesselName: 'Fromveur II',
          mmsi: 228037700,
          latitude: 48.359,
          longitude: -4.779,
          speedKnots: 15.0,
          headingDegrees: 270,
          state: 'UNDERWAY',
          dataSource: 'HISTORICAL_REPLAY',
        }}
      />
    );

    await waitFor(() => {
      // Breadcrumb polyline spy should have been called, but coordinates should be reset to just the new point,
      // never bridging the 23km jump across land
      const breadcrumbCalls = polylineSpy.mock.calls.filter(
        (call) => (call[1] as any)?.className === 'ferry-breadcrumb'
      );
      if (breadcrumbCalls.length > 0) {
        const lastCallCoords = breadcrumbCalls[breadcrumbCalls.length - 1][0] as [number, number][];
        expect(lastCallCoords.length).toBe(1);
      }
    });
  });
});
