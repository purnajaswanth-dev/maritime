import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { BookingModal } from '../components/booking/BookingModal';
import { Departure } from '../types/catalog';

const mockDeparture: Departure = {
  id: 1,
  departureCode: 'DEP-20261024-BES-OUES-0830',
  route: {
    id: 'BES-OUES',
    code: 'BES-OUES',
    name: 'Brest → Ouessant (Le Stiff)',
    originPortId: 'BES',
    originPortName: 'Brest Port de Commerce',
    destinationPortId: 'OUES',
    destinationPortName: 'Ouessant (Le Stiff)',
    distanceNm: 25.4,
    crossingDurationMinutes: 75,
  },
  vessel: {
    id: 'ves-1',
    name: 'Fromveur II',
    mmsi: 227005550,
    passengerCapacity: 365,
    serviceSpeedKnots: 15.5,
  },
  scheduledDepartureTime: '2026-10-24T08:30:00Z',
  scheduledArrivalTime: '2026-10-24T09:45:00Z',
  status: 'SCHEDULED',
  liveTrackingAvailable: true,
};

describe('BookingModal Component', () => {
  it('renders step 1 with departure info and passenger inputs', () => {
    render(
      <MemoryRouter>
        <BookingModal
          isOpen={true}
          onClose={vi.fn()}
          departure={mockDeparture}
        />
      </MemoryRouter>
    );

    expect(screen.getByText(/Book Sailing: Brest → Ouessant \(Le Stiff\)/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contact email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/first name/i)).toHaveValue('Yann');
    expect(screen.getByPlaceholderText(/last name/i)).toHaveValue('Kermorgant');
    expect(screen.getByText(/subtotal: €36.00/i)).toBeInTheDocument();
  });

  it('allows adding and removing passengers and recalculates subtotal', async () => {
    render(
      <MemoryRouter>
        <BookingModal
          isOpen={true}
          onClose={vi.fn()}
          departure={mockDeparture}
        />
      </MemoryRouter>
    );

    const addPassengerBtn = screen.getByRole('button', { name: /add passenger/i });
    fireEvent.click(addPassengerBtn);

    expect(screen.getByText(/passengers \(2\)/i)).toBeInTheDocument();
    expect(screen.getByText(/subtotal: €72.00/i)).toBeInTheDocument();

    const removeBtns = screen.getAllByRole('button', { name: /remove passenger/i });
    expect(removeBtns.length).toBe(2);
    fireEvent.click(removeBtns[0]);

    expect(screen.getByText(/passengers \(1\)/i)).toBeInTheDocument();
    expect(screen.getByText(/subtotal: €36.00/i)).toBeInTheDocument();
  });

  it('navigates through step 1, review step 2, and displays confirmation in step 3', async () => {
    const handleSuccess = vi.fn();
    render(
      <MemoryRouter>
        <BookingModal
          isOpen={true}
          onClose={vi.fn()}
          departure={mockDeparture}
          onBookingSuccess={handleSuccess}
        />
      </MemoryRouter>
    );

    // Step 1 -> Step 2
    const continueBtn = screen.getByRole('button', { name: /continue to review/i });
    fireEvent.click(continueBtn);

    expect(screen.getByText(/sailing information/i)).toBeInTheDocument();
    expect(screen.getByText(/passenger list & pricing/i)).toBeInTheDocument();

    // Step 2 -> Step 3 (Confirm)
    const confirmBtn = screen.getByRole('button', { name: /confirm & issue tickets/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getAllByText(/booking confirmed!/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/digital tickets/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /track sailing live/i })).toBeInTheDocument();
    });
  });
});
