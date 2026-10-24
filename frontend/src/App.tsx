import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { MainLayout } from './components/layout/MainLayout';
import { HomePage } from './pages/HomePage';
import { TrackingPage } from './pages/TrackingPage';
import { TimetablePage } from './pages/TimetablePage';
import { PortsPage } from './pages/PortsPage';
import { FaresPage } from './pages/FaresPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';
import { AdminLoginPage } from './pages/auth/AdminLoginPage';
import { UnauthorizedPage } from './pages/auth/UnauthorizedPage';
import { AccountPage } from './pages/AccountPage';
import { PublicTrackPage } from './pages/PublicTrackPage';
import { BookingsPage } from './pages/BookingsPage';
import { AdminPage } from './pages/AdminPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { RequireAuth } from './components/auth/RequireAuth';
import { RequireRole } from './components/auth/RequireRole';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        {/* Public Routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/tracking" element={<TrackingPage />} />
        <Route path="/track" element={<TrackingPage />} />
        <Route path="/track/departures/:id" element={<TrackingPage />} />
        <Route path="/track/:token" element={<PublicTrackPage />} />
        <Route path="/timetable" element={<TimetablePage />} />
        <Route path="/ports" element={<PortsPage />} />
        <Route path="/ports/:code" element={<PortsPage />} />
        <Route path="/fares" element={<FaresPage />} />

        {/* Authentication Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />

        {/* Protected Passenger Routes */}
        <Route
          path="/account"
          element={
            <RequireAuth>
              <AccountPage />
            </RequireAuth>
          }
        />
        <Route
          path="/bookings"
          element={
            <RequireAuth>
              <BookingsPage />
            </RequireAuth>
          }
        />

        {/* Protected Admin Routes */}
        <Route
          path="/admin/*"
          element={
            <RequireAuth>
              <RequireRole roles={['ADMIN', 'OPERATOR', 'AUDITOR']}>
                <AdminPage />
              </RequireRole>
            </RequireAuth>
          }
        />
        <Route
          path="/admin"
          element={
            <RequireAuth>
              <RequireRole roles={['ADMIN', 'OPERATOR', 'AUDITOR']}>
                <AdminPage />
              </RequireRole>
            </RequireAuth>
          }
        />

        {/* 404 Not Found */}
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
