import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { Navbar } from '../components/layout/Navbar';

describe('Navbar Component', () => {
  it('renders brand title and primary navigation links', () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );

    expect(screen.getByText('Where Is My Ferry?')).toBeInTheDocument();
    expect(screen.getByText(/penn ar bed/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /live tracking/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /timetable/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /ports/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /fares/i })).toBeInTheDocument();
  });

  it('renders login and register buttons when user is unauthenticated', () => {
    render(
      <MemoryRouter>
        <Navbar user={null} />
      </MemoryRouter>
    );

    const loginButtons = screen.getAllByRole('button', { name: /login/i });
    expect(loginButtons.length).toBeGreaterThan(0);
    const registerButtons = screen.getAllByRole('button', { name: /register/i });
    expect(registerButtons.length).toBeGreaterThan(0);
  });

  it('renders user details and logout button when authenticated', () => {
    const handleLogout = vi.fn();
    render(
      <MemoryRouter>
        <Navbar
          user={{
            email: 'passenger@whereismyferry.bzh',
            firstName: 'Yann',
            roles: ['ROLE_PASSENGER'],
          }}
          onLogout={handleLogout}
        />
      </MemoryRouter>
    );

    expect(screen.getByText('Yann')).toBeInTheDocument();
    expect(screen.getByText('PASSENGER')).toBeInTheDocument();
    const logoutBtn = screen.getByRole('button', { name: /logout/i });
    fireEvent.click(logoutBtn);
    expect(handleLogout).toHaveBeenCalledTimes(1);
  });

  it('toggles mobile menu on hamburger click', () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );

    const menuToggle = screen.getByLabelText('Toggle navigation menu');
    expect(menuToggle).toBeInTheDocument();
    fireEvent.click(menuToggle);
    // Menu opens
    expect(screen.getAllByRole('link', { name: /live tracking/i }).length).toBeGreaterThan(1);
  });
});
