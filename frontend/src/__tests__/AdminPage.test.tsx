import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { AdminPage } from '../pages/AdminPage';

describe('AdminPage Component', () => {
  it('renders admin portal header, health tiles, and overview operational KPIs', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { level: 1, name: /administration & control portal/i })).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/ml & ais engine/i)).toBeInTheDocument();
      expect(screen.getByText(/backend gateway/i)).toBeInTheDocument();
      expect(screen.getByText(/database tier/i)).toBeInTheDocument();
      expect(screen.getByText(/today's sailings/i)).toBeInTheDocument();
      expect(screen.getByText(/ships in transit/i)).toBeInTheDocument();
      expect(screen.getByText(/total bookings/i)).toBeInTheDocument();
      expect(screen.getByText(/confirmed revenue/i)).toBeInTheDocument();
    });
  });

  it('switches to Timetable tab and displays operating services and dated departures', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    const timetableTab = screen.getByRole('button', { name: /^timetable$/i });
    fireEvent.click(timetableTab);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /operating services/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /dated departures/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /add service/i })).toBeInTheDocument();
    });

    // Switch to dated departures
    const departuresSubTab = screen.getByRole('button', { name: /dated departures/i });
    fireEvent.click(departuresSubTab);

    await waitFor(() => {
      expect(screen.getByText(/seats/i)).toBeInTheDocument();
    });
  });

  it('switches to Ports tab and displays port authority management', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    const portsTab = screen.getByRole('button', { name: /ports/i });
    fireEvent.click(portsTab);

    await waitFor(() => {
      expect(screen.getByText(/port code/i)).toBeInTheDocument();
      expect(screen.getByText(/berth radius/i)).toBeInTheDocument();
    });
  });

  it('switches to Ships tab and displays fleet status', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    const shipsTab = screen.getByRole('button', { name: /ships/i });
    fireEvent.click(shipsTab);

    await waitFor(() => {
      expect(screen.getByText(/ship name/i)).toBeInTheDocument();
      expect(screen.getByText(/home port/i)).toBeInTheDocument();
      expect(screen.getByText(/live ais/i)).toBeInTheDocument();
    });
  });

  it('switches to Passengers tab and displays manifest directory and CSV export', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    const paxTab = screen.getByRole('button', { name: /passengers/i });
    fireEvent.click(paxTab);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search passenger by name\/email/i)).toBeInTheDocument();
      expect(screen.getByText(/export all passengers csv/i)).toBeInTheDocument();
    });
  });

  it('switches to Live engine tab and displays simulation controls and ML diagnostics', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    const simTab = screen.getByRole('button', { name: /live engine/i });
    fireEvent.click(simTab);

    await waitFor(() => {
      expect(screen.getByText(/virtual maritime simulation engine controls/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^start$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^pause$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^reset docks$/i })).toBeInTheDocument();
      expect(screen.getByText(/simulation speed multiplier/i)).toBeInTheDocument();
      expect(screen.getByText(/VectorizedRidgeETAModel/i)).toBeInTheDocument();
      expect(screen.getByText(/integrity pass/i)).toBeInTheDocument();
      expect(screen.getByText(/mean absolute error/i)).toBeInTheDocument();
      expect(screen.getByText(/5.2 min/i)).toBeInTheDocument();
      expect(screen.getByText(/3.56 min/i)).toBeInTheDocument();
      expect(screen.getByText(/7.47 min/i)).toBeInTheDocument();
    });

    // Verify scenario library trigger modal
    const triggerButtons = screen.getAllByRole('button', { name: /trigger scenario/i });
    expect(triggerButtons.length).toBeGreaterThan(0);
    fireEvent.click(triggerButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/confirm scenario trigger/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /confirm & inject fault/i })).toBeInTheDocument();
    });
  });

  it('switches to Admins tab and opens maintenance mode lockdown modal', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    const adminsTab = screen.getByRole('button', { name: /admins/i });
    fireEvent.click(adminsTab);

    await waitFor(() => {
      expect(screen.getByText(/system users & operator governance/i)).toBeInTheDocument();
      expect(screen.getByText(/immutable system audit trail/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /create admin/i })).toBeInTheDocument();
    });

    // Test maintenance mode modal opening from header button
    const maintenanceBtn = screen.getByRole('button', { name: /maintenance/i });
    fireEvent.click(maintenanceBtn);

    await waitFor(() => {
      expect(screen.getByText(/enable maintenance lockdown/i)).toBeInTheDocument();
      expect(screen.getByText(/enabling maintenance mode blocks all passenger bookings with http 503/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /confirm lockdown/i })).toBeInTheDocument();
    });
  });
});
