import React from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'text' | 'destructive' | 'outline' | 'danger' | 'warning';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  isLoading?: boolean;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  isLoading,
  icon,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const isSpinnerActive = Boolean(loading || isLoading);
  const variantClass = `btn-${variant}`;
  const sizeClass = `btn-${size}`;

  return (
    <button
      className={`btn ${variantClass} ${sizeClass} ${className}`.trim()}
      disabled={disabled || isSpinnerActive}
      {...props}
    >
      {isSpinnerActive ? (
        <span
          className="btn-spinner"
          role="status"
          aria-label="Loading"
          style={{
            display: 'inline-block',
            width: '1em',
            height: '1em',
            border: '2px solid currentColor',
            borderRightColor: 'transparent',
            borderRadius: '50%',
            animation: 'spin 0.6s linear infinite',
          }}
        />
      ) : icon ? (
        <span className="btn-icon" aria-hidden="true" style={{ display: 'inline-flex' }}>
          {icon}
        </span>
      ) : null}
      {children}
    </button>
  );
};
