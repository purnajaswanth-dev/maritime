import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Select } from '../components/common/Select';

describe('Select Component', () => {
  const options = [
    { label: 'Brest Port de Commerce', value: 'BES' },
    { label: 'Le Conquet', value: 'LCQ' },
    { label: 'Ouessant (Stiff)', value: 'OUE' },
  ];

  it('renders select with label and options', () => {
    render(<Select label="Departure Port" options={options} />);
    expect(screen.getByLabelText('Departure Port')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getAllByRole('option')).toHaveLength(3);
  });

  it('handles selection change and shows error', () => {
    const handleChange = vi.fn();
    const { rerender } = render(
      <Select label="Port" options={options} onChange={handleChange} />
    );

    const select = screen.getByLabelText('Port');
    fireEvent.change(select, { target: { value: 'LCQ' } });
    expect(handleChange).toHaveBeenCalled();

    rerender(
      <Select label="Port" options={options} error="Port selection is required" />
    );
    expect(screen.getByRole('alert')).toHaveTextContent('Port selection is required');
  });
});
