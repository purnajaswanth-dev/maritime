import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { StatusChip } from '../components/common/StatusChip';

describe('StatusChip Component', () => {
  it('renders underway status with info variant', () => {
    render(<StatusChip status="UNDERWAY" />);
    const chip = screen.getByText('Underway');
    expect(chip).toBeInTheDocument();
    expect(chip.closest('.badge')).toHaveClass('badge-info');
  });

  it('renders arrived status with success variant', () => {
    render(<StatusChip status="ARRIVED" />);
    const chip = screen.getByText('Arrived');
    expect(chip).toBeInTheDocument();
    expect(chip.closest('.badge')).toHaveClass('badge-success');
  });

  it('renders delayed and cancelled statuses', () => {
    const { rerender } = render(<StatusChip status="DELAYED" />);
    expect(screen.getByText('Delayed').closest('.badge')).toHaveClass('badge-warning');

    rerender(<StatusChip status="CANCELLED" />);
    expect(screen.getByText('Cancelled').closest('.badge')).toHaveClass('badge-danger');
  });

  it('handles unknown or scheduled status gracefully', () => {
    render(<StatusChip status="SCHEDULED" />);
    expect(screen.getByText('Scheduled').closest('.badge')).toHaveClass('badge-neutral');
  });
});
