import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Input } from '../components/common/Input';

describe('Input Component', () => {
  it('renders input with label and placeholder', () => {
    render(<Input label="Email address" placeholder="test@example.com" />);
    expect(screen.getByLabelText('Email address')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('test@example.com')).toBeInTheDocument();
  });

  it('renders error message and sets aria-invalid', () => {
    render(<Input label="Password" error="Password must be at least 8 characters" />);
    const input = screen.getByLabelText('Password');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByRole('alert')).toHaveTextContent('Password must be at least 8 characters');
  });

  it('renders helper text when no error is present', () => {
    render(<Input label="Username" helperText="Enter your unique callsign" />);
    expect(screen.getByText('Enter your unique callsign')).toBeInTheDocument();
  });

  it('handles value changes', () => {
    const handleChange = vi.fn();
    render(<Input label="Search" onChange={handleChange} />);
    const input = screen.getByLabelText('Search');
    fireEvent.change(input, { target: { value: 'Fromveur' } });
    expect(handleChange).toHaveBeenCalled();
  });
});
