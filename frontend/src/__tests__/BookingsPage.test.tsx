import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { BookingsPage } from '../pages/BookingsPage';

describe('BookingsPage Component', () => {
  it('renders page header, search input, and booking cards', async () => {
    render(
      <MemoryRouter>
        <BookingsPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { level: 1, name: /my ferry bookings/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search by booking reference/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/WIMF-20261024-BRE9/i)).toBeInTheDocument();
      expect(screen.getByText(/CONFIRMED/i)).toBeInTheDocument();
      expect(screen.getByText(/€50.50/i)).toBeInTheDocument();
      expect(screen.getByText(/Yann Kermorgant/i)).toBeInTheDocument();
      expect(screen.getByText(/Soizic Kermorgant/i)).toBeInTheDocument();
    });
  });

  it('opens digital QR boarding passes modal on clicking View Boarding Passes', async () => {
    render(
      <MemoryRouter>
        <BookingsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/WIMF-20261024-BRE9/i)).toBeInTheDocument();
    });

    const viewPassesBtn = screen.getByRole('button', { name: /view boarding passes/i });
    fireEvent.click(viewPassesBtn);

    await waitFor(() => {
      expect(screen.getByText(/Boarding Passes: WIMF-20261024-BRE9/i)).toBeInTheDocument();
      expect(screen.getByText(/Present these digital QR boarding passes/i)).toBeInTheDocument();
      expect(screen.getByText(/TKT-WIMF-20261024-BRE9-01/i)).toBeInTheDocument();
    });
  });

  it('opens cancel confirmation modal and updates status to CANCELLED', async () => {
    render(
      <MemoryRouter>
        <BookingsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /cancel booking/i })).toBeInTheDocument();
    });

    const cancelBtn = screen.getByRole('button', { name: /cancel booking/i });
    fireEvent.click(cancelBtn);

    await waitFor(() => {
      expect(screen.getByText(/confirm booking cancellation/i)).toBeInTheDocument();
      expect(screen.getByText(/full refunds are issued for cancellations completed at least 24 hours/i)).toBeInTheDocument();
    });

    const confirmCancelBtn = screen.getByRole('button', { name: /yes, cancel reservation/i });
    fireEvent.click(confirmCancelBtn);

    await waitFor(() => {
      expect(screen.getAllByText(/CANCELLED/i).length).toBeGreaterThan(0);
    });
  });

  it('filters bookings by reference in search input', async () => {
    render(
      <MemoryRouter>
        <BookingsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/WIMF-20261024-BRE9/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search by booking reference/i);
    fireEvent.change(searchInput, { target: { value: 'NONEXISTENT' } });

    await waitFor(() => {
      expect(screen.getByText(/no matching bookings found/i)).toBeInTheDocument();
    });

    fireEvent.change(searchInput, { target: { value: 'BRE9' } });
    await waitFor(() => {
      expect(screen.getByText(/WIMF-20261024-BRE9/i)).toBeInTheDocument();
    });
  });
});
