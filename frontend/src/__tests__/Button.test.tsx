import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Button } from '../components/common/Button';

describe('Button Component', () => {
  it('renders primary button with text', () => {
    render(<Button variant="primary">Click Me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('btn-primary');
    expect(button).toHaveClass('btn-md');
  });

  it('renders secondary button with custom size', () => {
    render(<Button variant="secondary" size="lg">Secondary Large</Button>);
    const button = screen.getByRole('button', { name: /secondary large/i });
    expect(button).toHaveClass('btn-secondary');
    expect(button).toHaveClass('btn-lg');
  });

  it('renders text and destructive button variants', () => {
    const { rerender } = render(<Button variant="text">Text Link</Button>);
    expect(screen.getByRole('button', { name: /text link/i })).toHaveClass('btn-text');

    rerender(<Button variant="destructive">Delete Item</Button>);
    expect(screen.getByRole('button', { name: /delete item/i })).toHaveClass('btn-destructive');
  });

  it('handles click events when enabled', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Submit</Button>);
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('prevents click when disabled', () => {
    const handleClick = vi.fn();
    render(<Button disabled onClick={handleClick}>Disabled</Button>);
    const button = screen.getByRole('button', { name: /disabled/i });
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('renders loading spinner and disables button when loading', () => {
    render(<Button loading>Processing</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
