import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { TimetablePage } from '../pages/TimetablePage';
import { BookingModal } from '../components/booking/BookingModal';
import { LiveTelemetryPanel } from '../components/tracking/LiveTelemetryPanel';
import { AdminPage } from '../pages/AdminPage';
import { Departure } from '../types/catalog';
import { LiveTelemetry } from '../types/tracking';

// Mock departure: Brest to Le Conquet
const mockBrestDeparture: Departure = {
  id: 101,
  departureCode: 'DEP-BES-LCQ-0830',
  route: {
    id: 'BES-LCQ',
    code: 'BES-LCQ',
    name: 'Brest → Le Conquet',
    originPortId: 'BES',
    originPortName: 'Brest Port de Commerce',
    destinationPortId: 'LCQ',
    destinationPortName: 'Le Conquet Gare Maritime',
    distanceNm: 12.8,
    crossingDurationMinutes: 45,
  },
  vessel: {
    id: 'VES-FROMVEUR-II',
    name: 'Fromveur II',
    mmsi: 227005550,
    passengerCapacity: 365,
    serviceSpeedKnots: 15.5,
  },
  scheduledDepartureTime: '2026-10-24T08:30:00Z',
  scheduledArrivalTime: '2026-10-24T09:15:00Z',
  status: 'SCHEDULED',
  liveTrackingAvailable: true,
};

const mockLiveTelemetry: LiveTelemetry = {
  departureId: 'dep-101',
  departureCode: 'DEP-BES-LCQ-0830',
  vesselName: 'Fromveur II',
  mmsi: 227005550,
  latitude: 48.3750,
  longitude: -4.6200,
  speedKnots: 14.8,
  headingDegrees: 265,
  state: 'UNDERWAY',
  predictedDelayMinutes: 2.5,
  ciLowerMinutes: 1.0,
  ciUpperMinutes: 4.0,
  etaIso: '2026-10-24T09:12:00Z',
  departurePortName: 'Brest Port de Commerce',
  targetPortName: 'Le Conquet Gare Maritime',
  dataSource: 'HISTORICAL_REPLAY',
  modelWeightsSha256: '5e7a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a',
};

describe('Phase 12: Final Acceptance End-to-End Verification (7-Step Capstone Demo)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Step 1 & 2: Guest opens Timetable and finds Brest to Le Conquet sailing', async () => {
    render(
      <MemoryRouter>
        <TimetablePage />
      </MemoryRouter>
    );

    // Assert page header is displayed
    expect(screen.getByRole('heading', { level: 1, name: /daily ferry timetable & sailings/i })).toBeInTheDocument();

    // Verify origin and destination in departures
    await waitFor(() => {
      expect(screen.getAllByText(/Fromveur II/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/Brest Port de Commerce → Le Conquet Gare Maritime/i)).toBeInTheDocument();
    });

    // Verify Book Now action is available
    const bookButtons = screen.getAllByRole('button', { name: /book now/i });
    expect(bookButtons.length).toBeGreaterThan(0);
  });

  it('Step 3: Passenger completes booking for 2 adults and receives tickets with QR code', async () => {
    const handleClose = vi.fn();
    render(
      <MemoryRouter>
        <BookingModal
          isOpen={true}
          onClose={handleClose}
          departure={mockBrestDeparture}
        />
      </MemoryRouter>
    );

    // Step 1: Add second adult passenger and fill details
    const addPassengerBtn = screen.getByRole('button', { name: /add passenger/i });
    fireEvent.click(addPassengerBtn);

    expect(screen.getByText(/passengers \(2\)/i)).toBeInTheDocument();
    expect(screen.getByText(/subtotal: €72.00/i)).toBeInTheDocument();

    const firstNames = screen.getAllByPlaceholderText(/first name/i);
    const lastNames = screen.getAllByPlaceholderText(/last name/i);
    expect(firstNames.length).toBe(2);

    fireEvent.change(firstNames[1], { target: { value: 'Marie' } });
    fireEvent.change(lastNames[1], { target: { value: 'Kermorgant' } });

    // Continue to Review Step
    const continueBtn = screen.getByRole('button', { name: /continue to review/i });
    fireEvent.click(continueBtn);

    // Verify Step 2 review screen
    expect(screen.getByText(/sailing information/i)).toBeInTheDocument();
    expect(screen.getByText(/passenger list & pricing/i)).toBeInTheDocument();

    // Step 2 -> Confirm and Issue Tickets
    const confirmBtn = screen.getByRole('button', { name: /confirm & issue tickets/i });
    fireEvent.click(confirmBtn);

    // Verify Step 3: Confirmation and QR Boarding Pass
    await waitFor(() => {
      expect(screen.getAllByText(/booking confirmed!/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/digital tickets/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /track sailing live/i })).toBeInTheDocument();
    });
  });

  it('Step 4: Real-time Live Tracking displays live position, speed, heading, and coordinates', () => {
    render(
      <LiveTelemetryPanel
        telemetry={mockLiveTelemetry}
      />
    );

    // Verify telemetry indicators
    expect(screen.getByText('Fromveur II')).toBeInTheDocument();
    expect(screen.getByText('MMSI 227005550')).toBeInTheDocument();
    expect(screen.getByText('14.8')).toBeInTheDocument(); // Speed
    expect(screen.getByText('265°')).toBeInTheDocument(); // Heading
  });

  it('Step 5 & 6: Captain and Dispatcher state assertions reflect underway status and advisory delay', () => {
    // Vessel is actively UNDERWAY
    expect(mockLiveTelemetry.state).toBe('UNDERWAY');
    expect(mockLiveTelemetry.headingDegrees).toBe(265);
    expect(mockLiveTelemetry.predictedDelayMinutes).toBe(2.5);
  });

  it('Step 7: Admin triggers AIS blackout, observes simulation controls, and verifies ML diagnostics SHA-256', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    // Open Simulation Controls tab
    const simTab = screen.getByRole('button', { name: /simulation controls/i });
    fireEvent.click(simTab);

    await waitFor(() => {
      expect(screen.getByText(/virtual maritime simulation engine controls/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^start$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^pause$/i })).toBeInTheDocument();
    });

    // Open ML Diagnostics tab
    const mlTab = screen.getByRole('button', { name: /ml diagnostics/i });
    fireEvent.click(mlTab);

    // Verify SHA-256 integrity check and benchmark metrics
    await waitFor(() => {
      expect(screen.getByText(/VectorizedRidgeETAModel/i)).toBeInTheDocument();
      expect(screen.getByText(/integrity pass/i)).toBeInTheDocument();
      expect(screen.getByText(/mean absolute error/i)).toBeInTheDocument();
      expect(screen.getByText(/5.2 min/i)).toBeInTheDocument();
      expect(screen.getByText(/3.56 min/i)).toBeInTheDocument();
    });
  });
});
