import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { Card } from '../components/common/Card';

describe('Card Component', () => {
  it('renders card content with title and subtitle', () => {
    render(
      <Card title="Port de Commerce" subtitle="Mainland Terminal">
        <p>Departure information goes here.</p>
      </Card>
    );

    expect(screen.getByText('Port de Commerce')).toBeInTheDocument();
    expect(screen.getByText('Mainland Terminal')).toBeInTheDocument();
    expect(screen.getByText('Departure information goes here.')).toBeInTheDocument();
  });

  it('renders action element and custom className', () => {
    render(
      <Card
        title="Fleet Status"
        action={<button>Refresh</button>}
        className="custom-card-class"
      >
        <p>All vessels on time.</p>
      </Card>
    );

    expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
    const cardEl = screen.getByText('All vessels on time.').closest('.card');
    expect(cardEl).toHaveClass('custom-card-class');
  });
});
