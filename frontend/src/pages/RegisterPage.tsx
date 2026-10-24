import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus, Ship } from 'lucide-react';
import { Input } from '../components/common/Input';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Alert } from '../components/common/Alert';
import { useAuth } from '../context/AuthContext';

export const RegisterPage: React.FC = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    phone: '',
  });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (fieldErrors[name]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[name];
        return next;
      });
    }
  };

  const validate = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.firstName.trim()) {
      errors.firstName = 'First name is required.';
    }
    if (!formData.lastName.trim()) {
      errors.lastName = 'Last name is required.';
    }
    if (!formData.email.trim() || !formData.email.includes('@')) {
      errors.email = 'Please provide a valid email address.';
    }
    if (!formData.password || formData.password.length < 10) {
      errors.password = 'Password must be at least 10 characters long.';
    }
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match.';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validate()) {
      return;
    }

    setLoading(true);

    try {
      await register({
        email: formData.email.trim(),
        password: formData.password,
        firstName: formData.firstName.trim(),
        lastName: formData.lastName.trim(),
        fullName: `${formData.firstName.trim()} ${formData.lastName.trim()}`,
        phone: formData.phone.trim() || undefined,
      });
      navigate('/account');
    } catch (err: any) {
      setError(err?.message || 'Registration failed. Please check your information.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ padding: '3.5rem 1rem', maxWidth: '480px' }}>
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
            Passenger Registration
          </h1>
          <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
            Create an account to book Brittany ferry departures and track voyages.
          </p>
        </div>

        {error && (
          <div style={{ marginBottom: '1.25rem' }}>
            <Alert variant="danger" title="Registration Error">
              {error}
            </Alert>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div>
              <Input
                label="First name"
                id="register-first-name"
                name="firstName"
                required
                value={formData.firstName}
                onChange={handleChange}
                placeholder="Malo"
              />
              {fieldErrors.firstName && (
                <div style={{ color: 'var(--color-danger)', fontSize: '0.75rem', marginTop: '-0.75rem', marginBottom: '0.75rem' }}>
                  {fieldErrors.firstName}
                </div>
              )}
            </div>
            <div>
              <Input
                label="Last name"
                id="register-last-name"
                name="lastName"
                required
                value={formData.lastName}
                onChange={handleChange}
                placeholder="Kerjean"
              />
              {fieldErrors.lastName && (
                <div style={{ color: 'var(--color-danger)', fontSize: '0.75rem', marginTop: '-0.75rem', marginBottom: '0.75rem' }}>
                  {fieldErrors.lastName}
                </div>
              )}
            </div>
          </div>

          <Input
            label="Email address"
            id="register-email"
            name="email"
            type="email"
            required
            autoComplete="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="passenger@whereismyferry.bzh"
          />
          {fieldErrors.email && (
            <div style={{ color: 'var(--color-danger)', fontSize: '0.75rem', marginTop: '-0.75rem', marginBottom: '0.75rem' }}>
              {fieldErrors.email}
            </div>
          )}

          <Input
            label="Phone number (optional)"
            id="register-phone"
            name="phone"
            type="tel"
            autoComplete="tel"
            value={formData.phone}
            onChange={handleChange}
            placeholder="+33 2 98 00 00 00"
          />

          <Input
            label="Password (min 10 characters)"
            id="register-password"
            name="password"
            type="password"
            required
            autoComplete="new-password"
            value={formData.password}
            onChange={handleChange}
            placeholder="••••••••••••"
          />
          {fieldErrors.password && (
            <div style={{ color: 'var(--color-danger)', fontSize: '0.75rem', marginTop: '-0.75rem', marginBottom: '0.75rem' }}>
              {fieldErrors.password}
            </div>
          )}

          <Input
            label="Confirm password"
            id="register-confirm-password"
            name="confirmPassword"
            type="password"
            required
            autoComplete="new-password"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="••••••••••••"
          />
          {fieldErrors.confirmPassword && (
            <div style={{ color: 'var(--color-danger)', fontSize: '0.75rem', marginTop: '-0.75rem', marginBottom: '0.75rem' }}>
              {fieldErrors.confirmPassword}
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            size="md"
            loading={loading}
            style={{ width: '100%', marginTop: '0.5rem' }}
          >
            <UserPlus size={16} style={{ marginRight: '0.5rem' }} />
            Create Passenger Account
          </Button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem', color: 'var(--color-slate-medium)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--color-primary)', textDecoration: 'none', fontWeight: 500 }}>
            Sign in
          </Link>
        </div>
      </Card>
    </div>
  );
};
