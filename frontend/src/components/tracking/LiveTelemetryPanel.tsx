import React from 'react';
import {
  Compass,
  Gauge,
  MapPin,
  Clock,
  Radio,
  Share2,
  AlertTriangle,
  RefreshCw,
  Navigation,
  ShieldCheck,
} from 'lucide-react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { StatusChip } from '../common/StatusChip';
import { Badge } from '../common/Badge';
import { LiveTelemetry } from '../../types/tracking';

export interface LiveTelemetryPanelProps {
  telemetry: LiveTelemetry | null;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  onShare?: () => void;
  className?: string;
}

export const LiveTelemetryPanel: React.FC<LiveTelemetryPanelProps> = ({
  telemetry,
  loading = false,
  error = null,
  onRetry,
  onShare,
  className = '',
}) => {
  if (error) {
    return (
      <Card className={`telemetry-panel error-panel ${className}`.trim()} style={{ borderLeft: '4px solid var(--color-destructive)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginBottom: '1rem' }}>
          <AlertTriangle size={24} style={{ color: 'var(--color-destructive)', flexShrink: 0 }} />
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-navy)', marginBottom: '0.25rem' }}>
              Telemetry Stream Offline (503)
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--color-slate-medium)', lineHeight: 1.5 }}>
              {error}
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {onRetry && (
            <Button variant="primary" size="sm" icon={<RefreshCw size={14} />} onClick={onRetry}>
              Reconnect Stream
            </Button>
          )}
          <span style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
            Replay daemon port: 8000
          </span>
        </div>
      </Card>
    );
  }

  if (loading && !telemetry) {
    return (
      <Card className={`telemetry-panel loading-panel ${className}`.trim()} style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-slate-light)' }}>
          <RefreshCw size={18} className="pulse-icon" />
          <span>Synchronizing vessel telemetry...</span>
        </div>
      </Card>
    );
  }

  if (!telemetry) {
    return (
      <Card className={`telemetry-panel empty-panel ${className}`.trim()} style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
          Select an active departure sailing to view live telemetry.
        </p>
      </Card>
    );
  }

  const {
    vesselName,
    mmsi,
    speedKnots,
    headingDegrees,
    latitude,
    longitude,
    state,
    predictedDelayMinutes,
    ciLowerMinutes,
    ciUpperMinutes,
    etaIso,
    targetPortName,
    departurePortName,
    dataSource,
    modelWeightsSha256,
  } = telemetry;

  const formattedEta = etaIso ? new Date(etaIso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--';
  const delayDisplay = predictedDelayMinutes !== undefined
    ? `${predictedDelayMinutes >= 0 ? '+' : ''}${predictedDelayMinutes.toFixed(1)} min`
    : 'On Time';

  return (
    <Card className={`telemetry-panel ${className}`.trim()} style={{ padding: '1.5rem' }}>
      {/* Header with Vessel & Status */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.25rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-navy)', margin: 0 }}>
              {vesselName}
            </h2>
            <Badge variant="info">MMSI {mmsi}</Badge>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)', margin: 0 }}>
            {departurePortName ? `${departurePortName} → ` : ''}{targetPortName || 'Brittany Crossing'}
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <StatusChip status={state} />
          {onShare && (
            <Button
              variant="secondary"
              size="sm"
              icon={<Share2 size={14} />}
              onClick={onShare}
              aria-label="Share public tracking link"
            >
              Share
            </Button>
          )}
        </div>
      </div>

      {/* Grid of Key Telemetry Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
        {/* Speed */}
        <div style={{ backgroundColor: 'var(--color-bg)', padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--color-slate-light)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
            <Gauge size={14} />
            <span>Speed (SOG)</span>
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-navy)' }}>
            {speedKnots.toFixed(1)} <span style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--color-slate-light)' }}>kts</span>
          </div>
        </div>

        {/* Heading */}
        <div style={{ backgroundColor: 'var(--color-bg)', padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--color-slate-light)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
            <Compass size={14} />
            <span>Heading (COG)</span>
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-navy)' }}>
            {Math.round(headingDegrees)}&deg;
          </div>
        </div>

        {/* Predictive Delay */}
        <div style={{ backgroundColor: 'var(--color-bg)', padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--color-slate-light)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
            <Clock size={14} />
            <span>Predicted Delay</span>
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: (predictedDelayMinutes || 0) > 5 ? 'var(--color-warning)' : 'var(--color-navy)' }}>
            {delayDisplay}
          </div>
          {ciLowerMinutes !== undefined && ciUpperMinutes !== undefined && (
            <div style={{ fontSize: '0.6875rem', color: 'var(--color-slate-light)', marginTop: '2px' }}>
              CI [{ciLowerMinutes.toFixed(1)}, {ciUpperMinutes.toFixed(1)}] min
            </div>
          )}
        </div>

        {/* Predicted ETA */}
        <div style={{ backgroundColor: 'var(--color-bg)', padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--color-slate-light)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
            <Navigation size={14} />
            <span>Estimated Arrival</span>
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-navy)' }}>
            {formattedEta}
          </div>
        </div>
      </div>

      {/* GPS Coordinates */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', fontSize: '0.8125rem', color: 'var(--color-slate-medium)', marginBottom: '1rem', backgroundColor: '#F1F5F9', padding: '0.625rem 0.875rem', borderRadius: 'var(--radius-md)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <MapPin size={14} style={{ color: 'var(--color-primary)' }} />
          <span>Coordinates:</span>
          <strong>{latitude.toFixed(4)}&deg; N, {Math.abs(longitude).toFixed(4)}&deg; W</strong>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--color-slate-light)' }}>
          <Radio size={12} className="pulse-icon" />
          <span>Live 1 Hz telemetry stream</span>
        </div>
      </div>

      {/* Honesty Provenance & Ridge Weights SHA-256 */}
      <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <ShieldCheck size={14} style={{ color: 'var(--color-success)' }} />
          <span>Source: <strong>{dataSource}</strong></span>
        </div>
        {modelWeightsSha256 && (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6875rem' }}>
            Ridge model SHA: {modelWeightsSha256.substring(0, 10)}...
          </div>
        )}
      </div>
    </Card>
  );
};
