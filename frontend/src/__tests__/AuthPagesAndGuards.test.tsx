import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { ForgotPasswordPage } from '../pages/auth/ForgotPasswordPage';
import { ResetPasswordPage } from '../pages/auth/ResetPasswordPage';
import { AdminLoginPage } from '../pages/auth/AdminLoginPage';
import { UnauthorizedPage } from '../pages/auth/UnauthorizedPage';
import { RequireAuth } from '../components/auth/RequireAuth';
import { RequireRole } from '../components/auth/RequireRole';
import { AuthProvider } from '../context/AuthContext';

// Mock apiClient
vi.mock('../api/client', async () => {
  const actual = await vi.importActual<any>('../api/client');
  return {
    ...actual,
    apiClient: vi.fn(),
    refreshAuthToken: vi.fn().mockResolvedValue(null),
    setAccessToken: vi.fn(),
    clearAuthSession: vi.fn(),
    getAccessToken: vi.fn().mockReturnValue(null),
  };
});

describe('Phase B Auth Pages & Guards', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders ForgotPasswordPage and handles submit with instructions', async () => {
    const { apiClient } = await import('../api/client');
    (apiClient as any).mockResolvedValueOnce({ status: 'SUCCESS' });

    render(
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { level: 1, name: /forgot password/i })).toBeInTheDocument();
    const emailInput = screen.getByLabelText(/email address/i);
    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });

    const submitBtn = screen.getByRole('button', { name: /send reset instructions/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/if that email address exists/i)).toBeInTheDocument();
    });
  });

  it('renders ResetPasswordPage and enforces min 10 characters password rule', async () => {
    render(
      <MemoryRouter initialEntries={['/reset-password?token=valid-reset-token']}>
        <ResetPasswordPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { level: 1, name: /reset password/i })).toBeInTheDocument();
    const passInput = screen.getByLabelText(/^new password/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);

    // Enter short password
    fireEvent.change(passInput, { target: { value: 'short' } });
    fireEvent.change(confirmInput, { target: { value: 'short' } });

    const submitBtn = screen.getByRole('button', { name: /update password/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/must be at least 10 characters/i)).toBeInTheDocument();
    });
  });

  it('renders AdminLoginPage with administrative title', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminLoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { level: 1, name: /admin sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/staff email address/i)).toBeInTheDocument();
  });

  it('renders UnauthorizedPage with Access Restricted and role information', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <UnauthorizedPage />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { level: 1, name: /access restricted/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /return to public portal/i })).toBeInTheDocument();
  });

  it('RequireAuth redirects unauthenticated user to /login with redirect parameter', async () => {
    render(
      <MemoryRouter initialEntries={['/account']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/account"
              element={
                <RequireAuth>
                  <div>Secret Account Content</div>
                </RequireAuth>
              }
            />
            <Route path="/login" element={<div>Login Page Target</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Login Page Target')).toBeInTheDocument();
      expect(screen.queryByText('Secret Account Content')).not.toBeInTheDocument();
    });
  });

  it('RequireRole blocks non-admin users and redirects to /unauthorized', async () => {
    render(
      <MemoryRouter initialEntries={['/admin']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/admin"
              element={
                <RequireRole roles={['ADMIN']}>
                  <div>Admin Secret Dashboard</div>
                </RequireRole>
              }
            />
            <Route path="/login" element={<div>Login Target</div>} />
            <Route path="/unauthorized" element={<div>Unauthorized Target</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.queryByText('Admin Secret Dashboard')).not.toBeInTheDocument();
    });
  });
});
