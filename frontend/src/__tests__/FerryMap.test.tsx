import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { FerryMap } from '../components/map/FerryMap';

describe('FerryMap Component', () => {
  it('renders map container with accessible label and honesty badge', () => {
    render(
      <FerryMap
        telemetry={{
          departureId: 'dep-101',
          vesselName: 'Fromveur II',
          mmsi: 228037700,
          latitude: 48.375,
          longitude: -4.62,
          speedKnots: 15.0,
          headingDegrees: 270,
          state: 'UNDERWAY',
          dataSource: 'HISTORICAL_REPLAY',
        }}
      />
    );

    const mapContainer = screen.getByTestId('ferry-map-container');
    expect(mapContainer).toBeInTheDocument();
    expect(screen.getByText(/historical replay mode \(simulated live\)/i)).toBeInTheDocument();
  });
});
