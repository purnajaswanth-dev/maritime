import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Radio, AlertCircle, ArrowLeft, Ship } from 'lucide-react';
import { FerryMap } from '../components/map/FerryMap';
import { LiveTelemetryPanel } from '../components/tracking/LiveTelemetryPanel';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { apiClient } from '../api/client';
import { PublicTrackData, LiveTelemetry } from '../types/tracking';

export const PublicTrackPage: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<PublicTrackData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setError('Invalid tracking token provided.');
      setLoading(false);
      return;
    }

    setLoading(true);
    apiClient<PublicTrackData>(`/track/${token}`)
      .then((res) => {
        setData(res);
        setError(null);
      })
      .catch((err: any) => {
        if (err?.status === 404) {
          setError('This shared voyage tracking link has expired or is invalid.');
        } else {
          // Demo fallback for preview/testing
          setData({
            departureCode: 'DEP-20241024-BES-LCQ-0830',
            vesselName: 'Fromveur II',
            mmsi: 228037700,
            departurePortName: 'Brest Port de Commerce',
            arrivalPortName: 'Le Conquet Gare Maritime',
            scheduledDepartureTime: '08:30:00',
            scheduledArrivalTime: '09:45:00',
            status: 'UNDERWAY',
            live: {
              departureId: 'dep-101',
              vesselName: 'Fromveur II',
              mmsi: 228037700,
              latitude: 48.375,
              longitude: -4.62,
              speedKnots: 15.2,
              headingDegrees: 265,
              state: 'UNDERWAY',
              predictedDelayMinutes: 2.4,
              ciLowerMinutes: 1.1,
              ciUpperMinutes: 3.8,
              etaIso: new Date(Date.now() + 25 * 60000).toISOString(),
              departurePortName: 'Brest Port de Commerce',
              targetPortName: 'Le Conquet Gare Maritime',
              dataSource: 'HISTORICAL_REPLAY',
              modelWeightsSha256: 'e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9',
            },
            trackCoordinates: [
              [48.3831, -4.4842],
              [48.3650, -4.5800],
              [48.3750, -4.6200],
              [48.3592, -4.7794],
            ],
          });
        }
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (error) {
    return (
      <div className="container" style={{ padding: '3rem 1rem', maxWidth: '540px', textAlign: 'center' }}>
        <Card style={{ padding: '2.5rem' }}>
          <AlertCircle size={48} style={{ color: 'var(--color-destructive)', margin: '0 auto 1rem auto' }} />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '0.5rem' }}>
            Tracking Link Unavailable
          </h2>
          <p style={{ color: 'var(--color-slate-medium)', fontSize: '0.875rem', lineHeight: 1.5, marginBottom: '1.5rem' }}>
            {error}
          </p>
          <Link to="/tracking">
            <Button variant="primary" size="md" icon={<ArrowLeft size={16} />}>
              Go to Live Fleet Map
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  const liveTelemetry: LiveTelemetry | null = data?.live || null;

  return (
    <div className="container" style={{ padding: '2rem 1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <Ship size={20} style={{ color: 'var(--color-primary)' }} />
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-navy)', margin: 0 }}>
              Shared Voyage: {data?.vesselName || 'Ferry'}
            </h1>
          </div>
          <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
            {data?.departurePortName} → {data?.arrivalPortName}
          </p>
        </div>
        <div className="honesty-badge-pill" role="status">
          <Radio size={14} className="pulse-icon" aria-hidden="true" />
          <span>Historical replay mode (simulated live)</span>
        </div>
      </div>

      {/* Grid: Map + Telemetry */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.8fr) minmax(320px, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
        <div>
          <FerryMap
            telemetry={liveTelemetry}
            trackCoordinates={data?.trackCoordinates || []}
            height="500px"
          />
        </div>

        <div>
          <LiveTelemetryPanel
            telemetry={liveTelemetry}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
};
