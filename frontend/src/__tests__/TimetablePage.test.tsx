import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { TimetablePage } from '../pages/TimetablePage';

describe('TimetablePage Component', () => {
  it('renders timetable heading, filter inputs, and departure cards', async () => {
    render(
      <MemoryRouter>
        <TimetablePage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { level: 1, name: /daily ferry timetable & sailings/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/travel date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/corridor \/ route/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/search sailings/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getAllByText(/Fromveur II/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/Brest Port de Commerce → Le Conquet Gare Maritime/i)).toBeInTheDocument();
    });
  });

  it('filters departures when search query is entered', async () => {
    render(
      <MemoryRouter>
        <TimetablePage />
      </MemoryRouter>
    );

    const searchInput = screen.getByLabelText(/search sailings/i);
    fireEvent.change(searchInput, { target: { value: 'Audierne' } });

    await waitFor(() => {
      expect(screen.getByText(/Audierne \(Sainte-Évette\) → Île de Sein/i)).toBeInTheDocument();
      expect(screen.queryByText(/Brest Port de Commerce → Le Conquet/i)).not.toBeInTheDocument();
    });
  });

  it('renders live tracking button on each departure card', async () => {
    render(
      <MemoryRouter>
        <TimetablePage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const trackButtons = screen.getAllByRole('button', { name: /track live/i });
      expect(trackButtons.length).toBeGreaterThan(0);
    });
  });
});
