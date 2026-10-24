import React from 'react';
import { Badge, BadgeVariant } from './Badge';

export interface StatusChipProps {
  status: string;
  className?: string;
}

export const StatusChip: React.FC<StatusChipProps> = ({ status, className = '' }) => {
  const normalized = (status || '').toUpperCase().trim();

  let variant: BadgeVariant = 'neutral';
  let label = normalized;

  switch (normalized) {
    case 'UNDERWAY':
      variant = 'info';
      label = 'Underway';
      break;
    case 'APPROACHING':
      variant = 'info';
      label = 'Approaching';
      break;
    case 'ARRIVED':
      variant = 'success';
      label = 'Arrived';
      break;
    case 'DELAYED':
      variant = 'warning';
      label = 'Delayed';
      break;
    case 'CANCELLED':
      variant = 'danger';
      label = 'Cancelled';
      break;
    case 'SCHEDULED':
      variant = 'neutral';
      label = 'Scheduled';
      break;
    default:
      variant = 'neutral';
      label = normalized;
      break;
  }

  return (
    <Badge variant={variant} className={`status-chip ${className}`.trim()}>
      <span
        style={{
          display: 'inline-block',
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: 'currentColor',
          marginRight: '4px',
        }}
        aria-hidden="true"
      />
      {label}
    </Badge>
  );
};
