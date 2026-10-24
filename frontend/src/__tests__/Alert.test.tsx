import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Alert } from '../components/common/Alert';

describe('Alert Component', () => {
  it('renders alert with title and message', () => {
    render(
      <Alert variant="info" title="Tidal Notice">
        High currents expected in Passage du Fromveur.
      </Alert>
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Tidal Notice')).toBeInTheDocument();
    expect(screen.getByText('High currents expected in Passage du Fromveur.')).toBeInTheDocument();
  });

  it('renders different alert variants correctly', () => {
    const { rerender } = render(<Alert variant="success">Booking confirmed!</Alert>);
    expect(screen.getByText('Booking confirmed!')).toBeInTheDocument();

    rerender(<Alert variant="warning">Departure delayed by 15 mins.</Alert>);
    expect(screen.getByText('Departure delayed by 15 mins.')).toBeInTheDocument();

    rerender(<Alert variant="error">Service cancelled due to gale force 9.</Alert>);
    expect(screen.getByText('Service cancelled due to gale force 9.')).toBeInTheDocument();
  });

  it('calls onClose when dismiss button is clicked', () => {
    const handleClose = vi.fn();
    render(
      <Alert variant="info" onClose={handleClose}>
        Dismissible notification
      </Alert>
    );

    const dismissBtn = screen.getByRole('button', { name: /dismiss alert/i });
    expect(dismissBtn).toBeInTheDocument();
    fireEvent.click(dismissBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
