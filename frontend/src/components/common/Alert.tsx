import React from 'react';
import { AlertCircle, CheckCircle, Info, TriangleAlert, X } from 'lucide-react';

export type AlertVariant = 'info' | 'success' | 'warning' | 'error' | 'danger';

export interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  children: React.ReactNode;
  onClose?: () => void;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  children,
  onClose,
  className = '',
}) => {
  const getStyles = () => {
    switch (variant) {
      case 'success':
        return {
          bg: 'var(--color-success-light)',
          border: '#A7F3D0',
          text: '#065F46',
          icon: <CheckCircle size={20} aria-hidden="true" color="#059669" />,
        };
      case 'warning':
        return {
          bg: 'var(--color-warning-light)',
          border: '#FDE68A',
          text: '#92400E',
          icon: <TriangleAlert size={20} aria-hidden="true" color="#D97706" />,
        };
      case 'danger':
      case 'error':
        return {
          bg: '#FEF2F2',
          border: '#FECACA',
          text: '#991B1B',
          icon: <AlertCircle size={20} aria-hidden="true" color="#DC2626" />,
        };
      case 'info':
      default:
        return {
          bg: 'var(--color-info-light)',
          border: '#BAE6FD',
          text: '#0369A1',
          icon: <Info size={20} aria-hidden="true" color="#0284C7" />,
        };
    }
  };

  const style = getStyles();

  return (
    <div
      role="alert"
      className={`alert ${className}`.trim()}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem',
        padding: '1rem',
        borderRadius: 'var(--radius-md)',
        backgroundColor: style.bg,
        border: `1px solid ${style.border}`,
        color: style.text,
        marginBottom: '1rem',
      }}
    >
      <div style={{ flexShrink: 0, marginTop: '2px' }}>{style.icon}</div>
      <div style={{ flex: 1 }}>
        {title && <h3 style={{ fontWeight: 600, fontSize: '0.9375rem', marginBottom: '0.25rem' }}>{title}</h3>}
        <div style={{ fontSize: '0.875rem' }}>{children}</div>
      </div>
      {onClose && (
        <button
          onClick={onClose}
          aria-label="Dismiss alert"
          style={{
            background: 'none',
            border: 'none',
            color: 'inherit',
            cursor: 'pointer',
            padding: '2px',
          }}
        >
          <X size={16} aria-hidden="true" />
        </button>
      )}
    </div>
  );
};
