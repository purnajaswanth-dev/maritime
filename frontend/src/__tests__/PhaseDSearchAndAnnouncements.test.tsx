import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { SailingSearchForm } from '../components/search/SailingSearchForm';
import { SailingSearchResults, SearchResultData } from '../components/search/SailingSearchResults';
import { AnnouncementBanner } from '../components/common/AnnouncementBanner';
import { apiClient } from '../api/client';

// Mock apiClient
vi.mock('../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Phase D: Sailing Search & Announcements', () => {
  const mockPorts = [
    { id: 'BREST', code: 'BREST', name: 'Port de Commerce de Brest', latitude: 48.38, longitude: -4.48, status: 'OPEN' },
    { id: 'LE_CONQUET', code: 'LE_CONQUET', name: 'Port du Conquet', latitude: 48.35, longitude: -4.78, status: 'OPEN' },
    { id: 'OUESSANT_STIFF', code: 'OUESSANT_STIFF', name: 'Port du Stiff (Ouessant)', latitude: 48.46, longitude: -5.05, status: 'OPEN' },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url === '/api/v1/ports') {
        return Promise.resolve(mockPorts);
      }
      if (url.includes('/destinations')) {
        return Promise.resolve([mockPorts[1], mockPorts[2]]);
      }
      if (url.includes('/announcements')) {
        return Promise.resolve([
          {
            id: 101,
            title: 'Gale Warning Passage du Fromveur',
            body: 'Southwesterly force 7 gusts expected this afternoon.',
            severity: 'WARNING',
            scope: 'ALL',
            startsAt: new Date().toISOString(),
          },
        ]);
      }
      return Promise.resolve([]);
    });
  });

  it('renders search form with From, To, Date, Passengers, Swap button and primary action', async () => {
    const onSearch = vi.fn();
    render(<SailingSearchForm onSearch={onSearch} />);

    await waitFor(() => {
      expect(screen.getByLabelText(/From/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/To/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Date/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Passengers/i)).toBeInTheDocument();
      expect(screen.getByText(/Swap/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Search sailings/i })).toBeInTheDocument();
    });
  });

  it('swaps origin and destination when Swap button is clicked', async () => {
    const onSearch = vi.fn();
    render(<SailingSearchForm initialFrom="BREST" initialTo="LE_CONQUET" onSearch={onSearch} />);

    await waitFor(() => {
      const fromSelect = screen.getByLabelText(/From/i) as HTMLSelectElement;
      expect(fromSelect.value).toBe('BREST');
    });

    const swapBtn = screen.getByText(/Swap/i);
    fireEvent.click(swapBtn);

    await waitFor(() => {
      const fromSelect = screen.getByLabelText(/From/i) as HTMLSelectElement;
      expect(fromSelect.value).toBe('LE_CONQUET');
    });
  });

  it('displays search results table with Departure, Arrival, Ship, Status, Price, and Book/Track buttons', () => {
    const mockData: SearchResultData = {
      originPortId: 'BREST',
      originPortName: 'Port de Commerce de Brest',
      destinationPortId: 'LE_CONQUET',
      destinationPortName: 'Port du Conquet',
      searchDate: '2026-10-24',
      passengers: 2,
      totalResults: 1,
      departures: [
        {
          id: 1,
          departureCode: 'DEP-20261024-BREST-LE_CONQUET-0830',
          routeId: 'R_BRE_CNQ',
          routeName: 'Brest - Le Conquet',
          originPortId: 'BREST',
          originPortName: 'Port de Commerce de Brest',
          destinationPortId: 'LE_CONQUET',
          destinationPortName: 'Port du Conquet',
          scheduledDepartureTime: '2026-10-24T08:30:00Z',
          scheduledArrivalTime: '2026-10-24T09:40:00Z',
          durationMinutes: 70,
          vesselId: 'V-FROMVEUR-SIM',
          vesselName: 'FROMVEUR II',
          status: 'SCHEDULED',
          statusLabel: 'On time',
          delayMinutes: 0,
          seatsAvailable: 340,
          fromPriceEur: 50.00,
          liveTrackingAvailable: true,
        },
      ],
    };

    render(
      <BrowserRouter>
        <SailingSearchResults data={mockData} loading={false} />
      </BrowserRouter>
    );

    expect(screen.getByText(/Port de Commerce de Brest → Port du Conquet/i)).toBeInTheDocument();
    expect(screen.getByText('FROMVEUR II')).toBeInTheDocument();
    expect(screen.getAllByText('On time').length).toBeGreaterThan(0);
    expect(screen.getByText(/50.00 €/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Book/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Track/i })).toBeInTheDocument();
  });

  it('renders honest empty state message when no departures match on the requested date', () => {
    const emptyData: SearchResultData = {
      originPortId: 'BREST',
      originPortName: 'Port de Commerce de Brest',
      destinationPortId: 'LE_CONQUET',
      destinationPortName: 'Port du Conquet',
      searchDate: '2026-10-24',
      passengers: 1,
      totalResults: 0,
      departures: [],
      emptyStateMessage: 'No sailings on this date. Next sailing: 26 Oct 2026, 08:30',
    };

    render(
      <BrowserRouter>
        <SailingSearchResults data={emptyData} loading={false} />
      </BrowserRouter>
    );

    expect(screen.getByText('No sailings on this date. Next sailing: 26 Oct 2026, 08:30')).toBeInTheDocument();
  });

  it('renders active announcement banner and dismisses when closed', async () => {
    render(<AnnouncementBanner scope="ALL" />);

    await waitFor(() => {
      expect(screen.getByText('Gale Warning Passage du Fromveur')).toBeInTheDocument();
      expect(screen.getByText(/Southwesterly force 7 gusts/i)).toBeInTheDocument();
    });

    const dismissBtn = screen.getByRole('button', { name: /Dismiss announcement/i });
    fireEvent.click(dismissBtn);

    await waitFor(() => {
      expect(screen.queryByText('Gale Warning Passage du Fromveur')).not.toBeInTheDocument();
    });
  });
});
