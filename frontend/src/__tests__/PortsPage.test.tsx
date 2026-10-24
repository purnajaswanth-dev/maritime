import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { PortsPage } from '../pages/PortsPage';

describe('PortsPage Component', () => {
  it('renders ports heading and all 7 Brittany terminals', () => {
    render(
      <MemoryRouter>
        <PortsPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { level: 1, name: /ports & maritime terminals/i })).toBeInTheDocument();
    expect(screen.getByText('Brest Port de Commerce')).toBeInTheDocument();
    expect(screen.getByText('Le Conquet Gare Maritime')).toBeInTheDocument();
    expect(screen.getByText(/île-molène \(quai nord\)/i)).toBeInTheDocument();
    expect(screen.getAllByText(/ouessant \(port du stiff\)/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/audierne \(sainte-évette\)/i)).toBeInTheDocument();
    expect(screen.getByText('Île de Sein')).toBeInTheDocument();
    expect(screen.getByText('Camaret-sur-Mer')).toBeInTheDocument();
  });

  it('filters ports by search input', () => {
    render(
      <MemoryRouter>
        <PortsPage />
      </MemoryRouter>
    );

    const searchInput = screen.getByPlaceholderText(/search port by name/i);
    fireEvent.change(searchInput, { target: { value: 'Ouessant' } });

    expect(screen.getAllByText(/ouessant \(port du stiff\)/i).length).toBeGreaterThan(0);
    expect(screen.queryByText('Brest Port de Commerce')).not.toBeInTheDocument();
  });

  it('filters ports by Island tab', () => {
    render(
      <MemoryRouter>
        <PortsPage />
      </MemoryRouter>
    );

    const islandsTab = screen.getByRole('button', { name: /islands/i });
    fireEvent.click(islandsTab);

    expect(screen.getAllByText(/ouessant \(port du stiff\)/i).length).toBeGreaterThan(0);
    expect(screen.getByText('Île de Sein')).toBeInTheDocument();
    expect(screen.queryByText('Brest Port de Commerce')).not.toBeInTheDocument();
  });
});
