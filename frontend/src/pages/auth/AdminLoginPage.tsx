import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { Input } from '../../components/common/Input';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { Alert } from '../../components/common/Alert';
import { useAuth } from '../../context/AuthContext';

export const AdminLoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login, logout } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const user = await login(email, password);
      const role = (user.role || '').toUpperCase();
      const isAdminOrStaff = role === 'ADMIN' || role === 'ROLE_ADMIN' || role === 'OPERATOR' || role === 'AUDITOR';

      if (!isAdminOrStaff) {
        await logout();
        setError('This account does not have administrative privileges. Please use the passenger portal.');
        return;
      }

      navigate('/admin');
    } catch (err: any) {
      setError(err?.message || 'Invalid administrative credentials. Please verify your email and password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ padding: '3.5rem 1rem', maxWidth: '440px' }}>
      <Card style={{ padding: '2rem' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'rgba(7, 27, 43, 0.08)',
              color: 'var(--color-navy)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem auto',
            }}
          >
            <ShieldCheck size={26} />
          </div>

          <h1
            style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: 'var(--color-navy)',
              marginBottom: '0.25rem',
            }}
          >
            Admin Sign In
          </h1>

          <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
            Operations & Timetable Management Console.
          </p>
        </div>

        {error && (
          <div style={{ marginBottom: '1.25rem' }}>
            <Alert variant="danger" title="Authentication Error">
              {error}
            </Alert>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <Input
            label="Staff email address"
            id="admin-email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@example.com"
          />

          <Input
            label="Password"
            id="admin-password"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
          />

          <Button
            type="submit"
            variant="primary"
            size="md"
            loading={loading}
            style={{ width: '100%', marginTop: '0.5rem' }}
          >
            Access Admin Portal
          </Button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem', color: 'var(--color-slate-medium)' }}>
          Are you a passenger?{' '}
          <Link to="/login" style={{ color: 'var(--color-primary)', textDecoration: 'none', fontWeight: 500 }}>
            Passenger sign in
          </Link>
        </div>
      </Card>
    </div>
  );
};
