import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, LogOut } from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { useAuth } from '../../context/AuthContext';

export const UnauthorizedPage: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <div className="container" style={{ padding: '4rem 1rem', maxWidth: '520px' }}>
      <Card style={{ padding: '2.5rem', textAlign: 'center' }}>
        <div
          style={{
            width: '56px',
            height: '56px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            color: 'var(--color-danger)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.5rem auto',
          }}
        >
          <ShieldAlert size={28} />
        </div>

        <h1
          style={{
            fontSize: '1.5rem',
            fontWeight: 700,
            color: 'var(--color-navy)',
            marginBottom: '0.5rem',
          }}
        >
          Access Restricted
        </h1>

        <p
          style={{
            color: 'var(--color-slate-light)',
            fontSize: '0.9375rem',
            lineHeight: 1.5,
            marginBottom: '1.5rem',
          }}
        >
          You do not have the required administrative permissions to access this portal.
          {user && (
            <span style={{ display: 'block', marginTop: '0.5rem', fontSize: '0.875rem', color: 'var(--color-slate-medium)' }}>
              Signed in as: <strong>{user.email}</strong> (Role: {user.role})
            </span>
          )}
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <Link to="/" style={{ textDecoration: 'none' }}>
            <Button variant="primary" style={{ width: '100%' }}>
              <ArrowLeft size={16} style={{ marginRight: '0.5rem' }} />
              Return to Public Portal
            </Button>
          </Link>

          {user && (
            <Button
              variant="secondary"
              onClick={async () => {
                await logout();
                window.location.href = '/admin/login';
              }}
              style={{ width: '100%' }}
            >
              <LogOut size={16} style={{ marginRight: '0.5rem' }} />
              Sign in with another account
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
};
