import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Shield, KeyRound, Ticket, Compass, LogOut, CheckCircle2 } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Alert } from '../components/common/Alert';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';

export const AccountPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Change password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);

  // Bookings state
  const [bookings, setBookings] = useState<any[]>([]);
  const [bookingsLoading, setBookingsLoading] = useState(true);

  useEffect(() => {
    async function fetchBookings() {
      try {
        const data = await apiClient<any[]>('/bookings');
        setBookings(data || []);
      } catch {
        setBookings([]);
      } finally {
        setBookingsLoading(false);
      }
    }
    fetchBookings();
  }, []);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);

    if (newPassword.length < 10) {
      setPasswordError('New password must be at least 10 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match.');
      return;
    }

    setPasswordLoading(true);
    try {
      await apiClient('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({
          currentPassword,
          newPassword,
        }),
      });
      setPasswordSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setPasswordError(err?.message || 'Failed to change password. Please verify your current password.');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="container" style={{ padding: '2.5rem 1rem', maxWidth: '880px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '0.25rem' }}>
            Passenger Account
          </h1>
          <p style={{ color: 'var(--color-slate-light)', fontSize: '0.9375rem' }}>
            Manage your personal profile, credentials, and upcoming Brittany ferry sailings.
          </p>
        </div>
        <Button variant="secondary" onClick={handleLogout}>
          <LogOut size={16} style={{ marginRight: '0.5rem' }} />
          Sign Out
        </Button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Profile Details Card */}
        <Card style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'rgba(20, 184, 166, 0.1)',
                color: 'var(--color-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <User size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--color-navy)' }}>Personal Profile</h2>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)' }}>Verified account details</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Full Name</span>
              <div style={{ fontSize: '0.9375rem', fontWeight: 500, color: 'var(--color-navy)' }}>
                {user?.fullName || `${user?.firstName || ''} ${user?.lastName || ''}`.trim() || 'Passenger'}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Email Address</span>
              <div style={{ fontSize: '0.9375rem', fontWeight: 500, color: 'var(--color-navy)' }}>
                {user?.email}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Phone</span>
              <div style={{ fontSize: '0.9375rem', fontWeight: 500, color: 'var(--color-navy)' }}>
                {user?.phone || 'Not provided'}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Account Role</span>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', backgroundColor: 'rgba(20, 184, 166, 0.1)', color: 'var(--color-primary)', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.8125rem', fontWeight: 600, marginTop: '0.25rem' }}>
                <Shield size={14} />
                {user?.role || 'PASSENGER'}
              </div>
            </div>
          </div>
        </Card>

        {/* Change Password Card */}
        <Card style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'rgba(7, 27, 43, 0.08)',
                color: 'var(--color-navy)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <KeyRound size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--color-navy)' }}>Security Settings</h2>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)' }}>Change your account password</p>
            </div>
          </div>

          {passwordSuccess && (
            <div style={{ marginBottom: '1rem' }}>
              <Alert variant="success" title="Success">
                Password updated successfully.
              </Alert>
            </div>
          )}

          {passwordError && (
            <div style={{ marginBottom: '1rem' }}>
              <Alert variant="danger" title="Error">
                {passwordError}
              </Alert>
            </div>
          )}

          <form onSubmit={handleChangePassword}>
            <Input
              label="Current password"
              id="account-current-password"
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="••••••••••••"
            />

            <Input
              label="New password (min 10 characters)"
              id="account-new-password"
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••••••"
            />

            <Input
              label="Confirm new password"
              id="account-confirm-password"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••••••"
            />

            <Button
              type="submit"
              variant="primary"
              size="sm"
              loading={passwordLoading}
              style={{ width: '100%', marginTop: '0.5rem' }}
            >
              Update Password
            </Button>
          </form>
        </Card>
      </div>

      {/* Booked Trips Section */}
      <Card style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'rgba(20, 184, 166, 0.1)',
                color: 'var(--color-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Ticket size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--color-navy)' }}>Booked Sailings</h2>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)' }}>Your upcoming and completed voyages</p>
            </div>
          </div>

          <Link to="/timetable" style={{ textDecoration: 'none' }}>
            <Button variant="secondary" size="sm">
              Book a Sailing
            </Button>
          </Link>
        </div>

        {bookingsLoading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-slate-light)' }}>
            Loading bookings...
          </div>
        ) : bookings.length === 0 ? (
          <div style={{ padding: '2.5rem 1rem', textAlign: 'center', border: '1px dashed var(--color-slate-border)', borderRadius: '8px' }}>
            <p style={{ color: 'var(--color-slate-light)', marginBottom: '1rem', fontSize: '0.9375rem' }}>
              You do not have any active or past ferry bookings.
            </p>
            <Link to="/timetable" style={{ textDecoration: 'none' }}>
              <Button variant="primary" size="md">
                View Timetable & Book
              </Button>
            </Link>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {bookings.map((booking, idx) => (
              <div
                key={booking.id || idx}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '1rem 1.25rem',
                  border: '1px solid var(--color-slate-border)',
                  borderRadius: '6px',
                  backgroundColor: 'white',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--color-navy)', fontSize: '0.9375rem' }}>
                    {booking.departure?.origin || 'Brest'} → {booking.departure?.destination || 'Le Conquet'}
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)', marginTop: '0.2rem' }}>
                    Ref: <strong>{booking.bookingReference || `WIMF-${1000 + idx}`}</strong> • {booking.passengersCount || 1} passenger(s)
                  </div>
                </div>

                <Link
                  to={`/track/departures/${booking.departureId || booking.departure?.id || 'DEP-BREST-CONQUET-0830'}`}
                  style={{ textDecoration: 'none' }}
                >
                  <Button variant="primary" size="sm">
                    <Compass size={14} style={{ marginRight: '0.375rem' }} />
                    Track my ferry
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};
