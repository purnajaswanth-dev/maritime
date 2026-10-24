import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { TrackingPage } from '../pages/TrackingPage';

describe('TrackingPage Component', () => {
  it('renders page header, honesty badge, and departure selector tabs', async () => {
    render(
      <MemoryRouter>
        <TrackingPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { level: 1, name: /live vessel tracking & telemetry/i })).toBeInTheDocument();
    expect(screen.getAllByText(/historical replay mode \(simulated live\)/i).length).toBeGreaterThan(0);

    const brestTab = screen.getByRole('button', { name: /brest → le conquet/i });
    expect(brestTab).toBeInTheDocument();

    const audierneTab = screen.getByRole('button', { name: /audierne → île de sein/i });
    expect(audierneTab).toBeInTheDocument();
  });

  it('switches departure tab and updates selected vessel', async () => {
    render(
      <MemoryRouter>
        <TrackingPage />
      </MemoryRouter>
    );

    const audierneTab = screen.getByRole('button', { name: /audierne → île de sein/i });
    fireEvent.click(audierneTab);

    await waitFor(() => {
      expect(screen.getByText(/Enez Sun 3/i)).toBeInTheDocument();
    });
  });
});
