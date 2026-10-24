import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export interface RequireAuthProps {
  children?: React.ReactNode;
}

export const RequireAuth: React.FC<RequireAuthProps> = ({ children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="container" style={{ padding: '4rem 1rem', textAlign: 'center' }}>
        <div style={{
          display: 'inline-block',
          width: '40px',
          height: '40px',
          border: '3px solid var(--color-slate-border)',
          borderTopColor: 'var(--color-primary)',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
        <p style={{ marginTop: '1rem', color: 'var(--color-slate-light)' }}>Verifying credentials...</p>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    const isUnderAdmin = location.pathname.startsWith('/admin');
    const loginTarget = isUnderAdmin ? '/admin/login' : '/login';
    return <Navigate to={`${loginTarget}?redirect=${encodeURIComponent(location.pathname + location.search)}`} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};
