import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { FaresPage } from '../pages/FaresPage';

describe('FaresPage Component', () => {
  it('renders fare estimator with route selection and default total', () => {
    render(<FaresPage />);

    expect(screen.getByRole('heading', { level: 1, name: /fares & pricing calculator/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/selected crossing route/i)).toBeInTheDocument();
    expect(screen.getByText(/adult standard/i)).toBeInTheDocument();
    expect(screen.getByText(/island resident/i)).toBeInTheDocument();
    // Default 1 adult on Le Conquet -> Ouessant is €36.00
    expect(screen.getByText('€36.00')).toBeInTheDocument();
  });

  it('updates total when increasing passenger quantities', () => {
    render(<FaresPage />);

    const increaseAdultBtn = screen.getByRole('button', { name: /increase adult count/i });
    fireEvent.click(increaseAdultBtn);

    // 2 adults = €72.00
    expect(screen.getByText('€72.00')).toBeInTheDocument();

    const increaseBikeBtn = screen.getByRole('button', { name: /increase bike count/i });
    fireEvent.click(increaseBikeBtn);

    // 2 adults (€72) + 1 bike (€8.50) = €80.50
    expect(screen.getByText('€80.50')).toBeInTheDocument();
  });

  it('recalculates total when changing routes', () => {
    render(<FaresPage />);

    const routeSelect = screen.getByLabelText(/selected crossing route/i);
    // Switch to Brest -> Ouessant (adult is €42.00)
    fireEvent.change(routeSelect, { target: { value: 'BES-OUE' } });

    expect(screen.getByText('€42.00')).toBeInTheDocument();
  });
});
