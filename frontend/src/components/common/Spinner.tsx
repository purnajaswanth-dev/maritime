import React from 'react';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  color = 'var(--color-primary)',
  className = '',
}) => {
  const sizePx = size === 'sm' ? '16px' : size === 'lg' ? '36px' : '24px';
  const borderWidth = size === 'sm' ? '2px' : size === 'lg' ? '3px' : '2.5px';

  return (
    <div
      role="status"
      aria-label="Loading"
      className={`spinner ${className}`.trim()}
      style={{
        display: 'inline-block',
        width: sizePx,
        height: sizePx,
        border: `${borderWidth} solid rgba(20, 184, 166, 0.2)`,
        borderTopColor: color,
        borderRadius: '50%',
        animation: 'spin 0.6s linear infinite',
      }}
    >
      <span style={{ position: 'absolute', width: '1px', height: '1px', padding: 0, margin: '-1px', overflow: 'hidden', clip: 'rect(0, 0, 0, 0)', border: 0 }}>
        Loading...
      </span>
    </div>
  );
};
