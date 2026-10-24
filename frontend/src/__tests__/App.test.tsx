import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from '../App';
import { AuthProvider } from '../context/AuthContext';

const renderWithRouter = (initialRoute = '/') => {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[initialRoute]}>
        <AppRoutes />
      </MemoryRouter>
    </AuthProvider>
  );
};

describe('App Routing', () => {
  it('renders home page on root route', () => {
    renderWithRouter('/');
    expect(screen.getByRole('heading', { level: 1, name: /real-time brittany & iroise sea ferry tracking/i })).toBeInTheDocument();
  });

  it('renders tracking page on /tracking route', async () => {
    renderWithRouter('/tracking');
    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: /live vessel tracking/i })).toBeInTheDocument();
    });
  });

  it('renders timetable page on /timetable route', async () => {
    renderWithRouter('/timetable');
    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: /daily ferry timetable/i })).toBeInTheDocument();
    });
  });

  it('renders ports page on /ports route', () => {
    renderWithRouter('/ports');
    expect(screen.getByRole('heading', { level: 1, name: /ports & (terminals|maritime)/i })).toBeInTheDocument();
  });

  it('renders fares page on /fares route', () => {
    renderWithRouter('/fares');
    expect(screen.getByRole('heading', { level: 1, name: /fares & (tariffs|pricing)/i })).toBeInTheDocument();
  });

  it('renders login page on /login route', () => {
    renderWithRouter('/login');
    expect(screen.getByRole('heading', { level: 1, name: /account sign in/i })).toBeInTheDocument();
  });

  it('renders 404 page for unknown routes', () => {
    renderWithRouter('/unknown-corridor-route');
    expect(screen.getByRole('heading', { level: 1, name: /404 - page not found/i })).toBeInTheDocument();
  });
});
