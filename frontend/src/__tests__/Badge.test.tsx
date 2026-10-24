import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { Badge } from '../components/common/Badge';

describe('Badge Component', () => {
  it('renders default neutral badge', () => {
    render(<Badge>Default</Badge>);
    const badge = screen.getByText('Default');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge');
    expect(badge).toHaveClass('badge-neutral');
  });

  it('renders various variants correctly', () => {
    const { rerender } = render(<Badge variant="success">Active</Badge>);
    expect(screen.getByText('Active')).toHaveClass('badge-success');

    rerender(<Badge variant="danger">Cancelled</Badge>);
    expect(screen.getByText('Cancelled')).toHaveClass('badge-danger');

    rerender(<Badge variant="warning">Delayed</Badge>);
    expect(screen.getByText('Delayed')).toHaveClass('badge-warning');

    rerender(<Badge variant="info">Penn ar Bed</Badge>);
    expect(screen.getByText('Penn ar Bed')).toHaveClass('badge-info');
  });

  it('applies custom className', () => {
    render(<Badge className="custom-badge">Tag</Badge>);
    expect(screen.getByText('Tag')).toHaveClass('custom-badge');
  });
});
