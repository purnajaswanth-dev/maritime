import React from 'react';

export type BadgeVariant = 'neutral' | 'success' | 'info' | 'warning' | 'danger';

export interface BadgeProps {
  variant?: BadgeVariant;
  size?: 'xs' | 'sm' | 'md' | 'lg' | string;
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  children,
  className = '',
}) => {
  return (
    <span className={`badge badge-${variant} ${className}`.trim()}>
      {children}
    </span>
  );
};
