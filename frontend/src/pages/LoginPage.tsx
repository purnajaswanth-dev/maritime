import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { LogIn, Ship } from 'lucide-react';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Alert } from '../components/common/Alert';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const redirectParam = searchParams.get('redirect');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const user = await login(email, password);
      const role = (user.role || '').toUpperCase();
      if (role === 'ADMIN' || role === 'ROLE_ADMIN') {
        navigate(redirectParam || '/admin');
      } else {
        navigate(redirectParam || '/account');
      }
    } catch (err: any) {
      setError(err?.message || 'Invalid email or password. Please try again.');
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
              backgroundColor: 'rgba(20, 184, 166, 0.1)',
              color: 'var(--color-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1rem auto',
            }}
          >
            <Ship size={24} />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '0.25rem' }}>
            Account Sign In
          </h1>
          <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
            Access your bookings and live voyage tracking.
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
            label="Email address"
            id="login-email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="passenger@whereismyferry.bzh"
          />

          <div style={{ position: 'relative' }}>
            <Input
              label="Password"
              id="login-password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
            />
            <div style={{ textAlign: 'right', marginTop: '-0.25rem', marginBottom: '1rem' }}>
              <Link
                to="/forgot-password"
                style={{ fontSize: '0.8125rem', color: 'var(--color-primary)', textDecoration: 'none' }}
              >
                Forgot password?
              </Link>
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="md"
            loading={loading}
            style={{ width: '100%', marginTop: '0.25rem' }}
          >
            <LogIn size={16} style={{ marginRight: '0.5rem' }} />
            Sign In
          </Button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem', color: 'var(--color-slate-medium)' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--color-primary)', textDecoration: 'none', fontWeight: 500 }}>
            Create one
          </Link>
        </div>

        <div style={{ textAlign: 'center', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--color-slate-border)', fontSize: '0.8125rem' }}>
          <Link to="/admin/login" style={{ color: 'var(--color-slate-light)', textDecoration: 'none' }}>
            Ferry operator or staff? Admin sign in →
          </Link>
        </div>
      </Card>
    </div>
  );
};
