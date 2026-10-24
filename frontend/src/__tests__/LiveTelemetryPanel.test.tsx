import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { LiveTelemetryPanel } from '../components/tracking/LiveTelemetryPanel';
import { LiveTelemetry } from '../types/tracking';

const mockTelemetry: LiveTelemetry = {
  departureId: 'dep-101',
  departureCode: 'DEP-20241024-BES-LCQ-0830',
  vesselName: 'Fromveur II',
  mmsi: 228037700,
  latitude: 48.3751,
  longitude: -4.6202,
  speedKnots: 15.6,
  headingDegrees: 265.4,
  state: 'UNDERWAY',
  predictedDelayMinutes: 3.2,
  ciLowerMinutes: 1.5,
  ciUpperMinutes: 4.8,
  etaIso: '2026-10-24T09:48:00Z',
  departurePortName: 'Brest Port de Commerce',
  targetPortName: 'Le Conquet Gare Maritime',
  dataSource: 'HISTORICAL_REPLAY',
  modelWeightsSha256: 'e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9',
};

describe('LiveTelemetryPanel Component', () => {
  it('renders vessel name, speed in knots, heading, and GPS coordinates', () => {
    render(<LiveTelemetryPanel telemetry={mockTelemetry} />);

    expect(screen.getByText('Fromveur II')).toBeInTheDocument();
    expect(screen.getByText('MMSI 228037700')).toBeInTheDocument();
    expect(screen.getByText('15.6')).toBeInTheDocument();
    expect(screen.getByText('265°')).toBeInTheDocument();
    expect(screen.getByText(/48.3751° N, 4.6202° W/i)).toBeInTheDocument();
  });

  it('renders predicted delay, confidence interval, and honest provenance', () => {
    render(<LiveTelemetryPanel telemetry={mockTelemetry} />);

    expect(screen.getByText('+3.2 min')).toBeInTheDocument();
    expect(screen.getByText(/CI \[1.5, 4.8\] min/i)).toBeInTheDocument();
    expect(screen.getByText('HISTORICAL_REPLAY')).toBeInTheDocument();
    expect(screen.getByText(/Ridge model SHA: e4da4af5cf/i)).toBeInTheDocument();
  });

  it('renders error state with retry action', () => {
    const handleRetry = vi.fn();
    render(
      <LiveTelemetryPanel
        telemetry={null}
        error="Simulation replay engine disconnected."
        onRetry={handleRetry}
      />
    );

    expect(screen.getByText(/Telemetry Stream Offline \(503\)/i)).toBeInTheDocument();
    expect(screen.getByText('Simulation replay engine disconnected.')).toBeInTheDocument();
    const retryBtn = screen.getByRole('button', { name: /reconnect stream/i });
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('calls onShare callback when share button is clicked', () => {
    const handleShare = vi.fn();
    render(<LiveTelemetryPanel telemetry={mockTelemetry} onShare={handleShare} />);

    const shareBtn = screen.getByRole('button', { name: /share public tracking link/i });
    fireEvent.click(shareBtn);
    expect(handleShare).toHaveBeenCalledTimes(1);
  });
});
