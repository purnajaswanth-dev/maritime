import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { AdminPage } from '../pages/AdminPage';

describe('AdminPage Component', () => {
  it('renders admin portal header, health tiles, and overview KPIs', async () => {
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
      expect(screen.getByText(/total bookings/i)).toBeInTheDocument();
      expect(screen.getByText(/confirmed revenue/i)).toBeInTheDocument();
    });
  });

  it('switches to Simulation Controls tab and displays control buttons and scenario library', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    const simTab = screen.getByRole('button', { name: /simulation controls/i });
    fireEvent.click(simTab);

    await waitFor(() => {
      expect(screen.getByText(/virtual maritime simulation engine controls/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^start$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^pause$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^reset docks$/i })).toBeInTheDocument();
      expect(screen.getByText(/simulation speed multiplier/i)).toBeInTheDocument();
    });

    // Verify scenario library item and trigger modal
    const triggerButtons = screen.getAllByRole('button', { name: /trigger scenario/i });
    expect(triggerButtons.length).toBeGreaterThan(0);
    fireEvent.click(triggerButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/confirm scenario trigger/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /confirm & inject fault/i })).toBeInTheDocument();
    });
  });

  it('switches to ML Diagnostics tab and displays model integrity and test benchmark metrics', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    const mlTab = screen.getByRole('button', { name: /ml diagnostics/i });
    fireEvent.click(mlTab);

    await waitFor(() => {
      expect(screen.getByText(/VectorizedRidgeETAModel/i)).toBeInTheDocument();
      expect(screen.getByText(/integrity pass/i)).toBeInTheDocument();
      expect(screen.getByText(/mean absolute error/i)).toBeInTheDocument();
      expect(screen.getByText(/5.2 min/i)).toBeInTheDocument();
      expect(screen.getByText(/3.56 min/i)).toBeInTheDocument();
      expect(screen.getByText(/7.47 min/i)).toBeInTheDocument();
      expect(screen.getByText(/physical kinematic sog/i)).toBeInTheDocument();
    });
  });

  it('switches to Users & Operators tab and renders governance table', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    const usersTab = screen.getByRole('button', { name: /users & operators/i });
    fireEvent.click(usersTab);

    await waitFor(() => {
      expect(screen.getByText(/system users & operator governance/i)).toBeInTheDocument();
      expect(screen.getByText(/admin@whereismyferry.bzh/i)).toBeInTheDocument();
      expect(screen.getByText(/auditor@whereismyferry.bzh/i)).toBeInTheDocument();
    });
  });

  it('switches to Audit Trail tab and opens maintenance mode lockdown modal', async () => {
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>
    );

    const auditTab = screen.getByRole('button', { name: /audit trail & security/i });
    fireEvent.click(auditTab);

    await waitFor(() => {
      expect(screen.getByText(/immutable system audit log/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/filter by action/i)).toBeInTheDocument();
    });

    // Test maintenance mode modal opening
    const maintenanceBtn = screen.getByRole('button', { name: /enable maintenance/i });
    fireEvent.click(maintenanceBtn);

    await waitFor(() => {
      expect(screen.getByText(/activate maintenance mode/i)).toBeInTheDocument();
      expect(screen.getByText(/enabling maintenance mode blocks all passenger booking requests/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /confirm maintenance lockdown/i })).toBeInTheDocument();
    });
  });
});
