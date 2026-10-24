import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { KeyRound, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { Input } from '../../components/common/Input';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { Alert } from '../../components/common/Alert';
import { apiClient } from '../../api/client';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !email.includes('@')) {
      setError('Please provide a valid email address.');
      return;
    }

    setLoading(true);
    try {
      await apiClient('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email: email.trim() }),
      });
      setSubmitted(true);
    } catch (err: any) {
      // Prompt requirement: generic error messages that do not reveal whether an email exists
      setSubmitted(true);
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
            <KeyRound size={24} />
          </div>

          <h1
            style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: 'var(--color-navy)',
              marginBottom: '0.25rem',
            }}
          >
            Forgot Password
          </h1>

          <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
            Enter your email to receive a secure password reset link.
          </p>
        </div>

        {submitted ? (
          <div>
            <div
              style={{
                backgroundColor: 'rgba(20, 184, 166, 0.08)',
                border: '1px solid rgba(20, 184, 166, 0.25)',
                borderRadius: '8px',
                padding: '1.25rem',
                marginBottom: '1.5rem',
                display: 'flex',
                gap: '0.75rem',
              }}
            >
              <CheckCircle2 size={20} color="var(--color-primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div style={{ fontSize: '0.875rem', color: 'var(--color-navy)', lineHeight: 1.5 }}>
                If that email address exists in our database, a password reset link has been dispatched.
                In development, check the backend console output for the simulated email link.
              </div>
            </div>

            <Link to="/login" style={{ textDecoration: 'none' }}>
              <Button variant="primary" style={{ width: '100%' }}>
                <ArrowLeft size={16} style={{ marginRight: '0.5rem' }} />
                Back to Sign In
              </Button>
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            {error && (
              <div style={{ marginBottom: '1.25rem' }}>
                <Alert variant="danger" title="Validation Error">
                  {error}
                </Alert>
              </div>
            )}

            <Input
              label="Email address"
              id="forgot-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="passenger@whereismyferry.bzh"
            />

            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={loading}
              style={{ width: '100%', marginTop: '0.75rem' }}
            >
              Send Reset Instructions
            </Button>

            <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.875rem' }}>
              <Link to="/login" style={{ color: 'var(--color-primary)', textDecoration: 'none', fontWeight: 500 }}>
                Return to Sign In
              </Link>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
};
