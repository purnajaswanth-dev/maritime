import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, Home } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="container" style={{ padding: '4rem 1rem', maxWidth: '520px', textAlign: 'center' }}>
      <Card style={{ padding: '3rem 2rem' }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          backgroundColor: '#F1F5F9',
          color: 'var(--color-slate-light)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 1.5rem auto',
        }}>
          <Compass size={32} />
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '0.5rem' }}>
          404 - Page Not Found
        </h1>
        <p style={{ color: 'var(--color-slate-medium)', fontSize: '0.9375rem', lineHeight: 1.6, marginBottom: '2rem' }}>
          The maritime route or page you are looking for does not exist or has shifted with the tide.
        </p>
        <Link to="/">
          <Button variant="primary" size="md" icon={<Home size={16} />}>
            Return to Port Homepage
          </Button>
        </Link>
      </Card>
    </div>
  );
};
