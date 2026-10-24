import React, { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { Ship, Menu, X, LogIn, UserPlus, LogOut, User as UserIcon } from 'lucide-react';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { useAuth } from '../../context/AuthContext';

export interface NavbarProps {
  user?: {
    email: string;
    firstName?: string;
    lastName?: string;
    roles?: string[];
  } | null;
  onLogout?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user: propUser, onLogout: propLogout }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  let authContext: ReturnType<typeof useAuth> | undefined;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    authContext = useAuth();
  } catch {
    // AuthProvider not in tree (e.g. in isolated component tests)
  }

  const user = propUser !== undefined ? propUser : (authContext?.user ? {
    email: authContext.user.email,
    firstName: authContext.user.firstName,
    lastName: authContext.user.lastName,
    roles: [authContext.user.role],
  } : null);

  const handleLogout = propLogout || (authContext ? () => {
    authContext?.logout();
    navigate('/');
  } : undefined);


  const isAdmin = user?.roles?.includes('ROLE_ADMIN');
  const isAuditor = user?.roles?.includes('ROLE_AUDITOR');
  const isOperator = user?.roles?.includes('ROLE_OPERATOR');

  const navLinks = [
    { label: 'Live Tracking', path: '/tracking' },
    { label: 'Timetable', path: '/timetable' },
    { label: 'Ports', path: '/ports' },
    { label: 'Fares', path: '/fares' },
    ...(user ? [{ label: 'My Bookings', path: '/bookings' }] : []),
    ...(isAdmin || isAuditor ? [{ label: 'Admin Portal', path: '/admin' }] : []),
  ];

  return (
    <header
      style={{
        backgroundColor: '#FFFFFF',
        borderBottom: '1px solid var(--color-border)',
        position: 'sticky',
        top: 0,
        zIndex: 40,
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div
        style={{
          maxWidth: '1280px',
          margin: '0 auto',
          padding: '0.75rem 1rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Brand */}
        <Link
          to="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem',
            textDecoration: 'none',
            color: 'var(--color-navy)',
          }}
        >
          <div
            style={{
              backgroundColor: 'var(--color-primary)',
              color: '#FFFFFF',
              padding: '0.4rem',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Ship size={22} aria-hidden="true" />
          </div>
          <div>
            <span style={{ fontWeight: 700, fontSize: '1.125rem', letterSpacing: '-0.025em' }}>
              Where Is My Ferry?
            </span>
            <span
              style={{
                display: 'block',
                fontSize: '0.6875rem',
                color: 'var(--color-slate-light)',
                fontWeight: 500,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Penn ar Bed &bull; Brittany
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="desktop-nav">
          {navLinks.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              style={({ isActive }) => ({
                fontSize: '0.875rem',
                fontWeight: 500,
                color: isActive ? 'var(--color-primary)' : 'var(--color-slate-medium)',
                textDecoration: 'none',
                borderBottom: isActive ? '2px solid var(--color-primary)' : '2px solid transparent',
                paddingBottom: '0.25rem',
              })}
            >
              {link.label}
            </NavLink>
          ))}

          {isAdmin && (
            <NavLink
              to="/admin"
              style={({ isActive }) => ({
                fontSize: '0.875rem',
                fontWeight: 600,
                color: isActive ? 'var(--color-primary)' : '#7C3AED',
                textDecoration: 'none',
              })}
            >
              Admin
            </NavLink>
          )}

          {isOperator && (
            <NavLink
              to="/operator"
              style={({ isActive }) => ({
                fontSize: '0.875rem',
                fontWeight: 600,
                color: isActive ? 'var(--color-primary)' : '#D97706',
                textDecoration: 'none',
              })}
            >
              Disruptions
            </NavLink>
          )}
        </nav>

        {/* User Auth Buttons */}
        <div className="desktop-auth">
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 600, display: 'block' }}>
                  {user.firstName || user.email.split('@')[0]}
                </span>
                <Badge variant={isAdmin ? 'danger' : isOperator ? 'warning' : 'info'}>
                  {user.roles?.[0]?.replace('ROLE_', '') || 'USER'}
                </Badge>
              </div>
              <Button
                variant="secondary"
                size="sm"
                icon={<LogOut size={16} />}
                onClick={handleLogout}
              >
                Logout
              </Button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Button
                variant="secondary"
                size="sm"
                icon={<LogIn size={16} />}
                onClick={() => navigate('/login')}
              >
                Login
              </Button>
              <Button
                variant="primary"
                size="sm"
                icon={<UserPlus size={16} />}
                onClick={() => navigate('/register')}
              >
                Register
              </Button>
            </div>
          )}
        </div>

        {/* Mobile Hamburger Button */}
        <div className="mobile-toggle">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation menu"
            style={{ padding: '0.35rem' }}
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </Button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div
          style={{
            borderTop: '1px solid var(--color-border)',
            backgroundColor: '#FFFFFF',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={() => setMobileMenuOpen(false)}
              style={{
                fontSize: '0.9375rem',
                fontWeight: 500,
                color: 'var(--color-navy)',
                textDecoration: 'none',
                padding: '0.5rem 0',
              }}
            >
              {link.label}
            </Link>
          ))}
          <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '0.75rem', marginTop: '0.25rem' }}>
            {user ? (
              <Button
                variant="secondary"
                size="sm"
                icon={<LogOut size={16} />}
                onClick={() => {
                  setMobileMenuOpen(false);
                  handleLogout?.();
                }}
                style={{ width: '100%' }}
              >
                Logout ({user.email})
              </Button>
            ) : (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    navigate('/login');
                  }}
                  style={{ flex: 1 }}
                >
                  Login
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    navigate('/register');
                  }}
                  style={{ flex: 1 }}
                >
                  Register
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
        @media (min-width: 768px) {
          .desktop-nav { display: flex !important; }
          .desktop-auth { display: flex !important; }
          .mobile-toggle { display: none !important; }
        }
      `}</style>
    </header>
  );
};
