import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { Footer } from '../components/layout/Footer';

describe('Footer Component', () => {
  it('renders honesty disclosure pill and Penn ar Bed corridors', () => {
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>
    );

    expect(screen.getByText(/historical replay mode \(simulated live\)/i)).toBeInTheDocument();
    expect(screen.getByText('Brest Port de Commerce')).toBeInTheDocument();
    expect(screen.getByText('Le Conquet Gare Maritime')).toBeInTheDocument();
    expect(screen.getByText(/ouessant port du stiff/i)).toBeInTheDocument();
    expect(screen.getByText(/île de sein/i)).toBeInTheDocument();
  });

  it('renders vessel names and WCAG AA compliance note', () => {
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>
    );

    expect(screen.getByText(/fromveur ii/i)).toBeInTheDocument();
    expect(screen.getByText(/enez sun 3/i)).toBeInTheDocument();
    expect(screen.getByText(/enez eussa 3/i)).toBeInTheDocument();
    expect(screen.getByText(/wcag 2.1 aa compliant/i)).toBeInTheDocument();
  });
});
