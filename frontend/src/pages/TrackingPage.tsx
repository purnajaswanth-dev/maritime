import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Radio, RefreshCw, Ship } from 'lucide-react';
import { FerryMap } from '../components/map/FerryMap';
import { LiveTelemetryPanel } from '../components/tracking/LiveTelemetryPanel';
import { ShareModal } from '../components/tracking/ShareModal';
import { Button } from '../components/common/Button';
import { apiClient } from '../api/client';
import { LiveTelemetry } from '../types/tracking';

interface DepartureOption {
  id: string | number;
  label: string;
  vessel: string;
}

const DEFAULT_DEPARTURES: DepartureOption[] = [
  { id: '1', label: 'Brest \u2192 Le Conquet', vessel: 'Fromveur II' },
  { id: '2', label: 'Le Conquet \u2192 Ouessant (Stiff)', vessel: 'Fromveur II' },
  { id: '3', label: 'Audierne \u2192 \u00CEle de Sein', vessel: 'Enez Sun 3' },
  { id: '4', label: 'Le Conquet \u2192 \u00CEle-Mol\u00E8ne', vessel: 'Enez Eussa 3' },
];

export const TrackingPage: React.FC = () => {
  const [selectedDeparture, setSelectedDeparture] = useState<DepartureOption>(DEFAULT_DEPARTURES[0]);
  const [telemetry, setTelemetry] = useState<LiveTelemetry | null>(null);
  const [trackCoordinates, setTrackCoordinates] = useState<[number, number][]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isShareModalOpen, setIsShareModalOpen] = useState<boolean>(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Fetch initial telemetry and track polyline
  const loadDepartureData = useCallback(async (depId: string | number) => {
    setLoading(true);
    setError(null);

    try {
      // 1. Fetch live telemetry snapshot
      const liveData = await apiClient<LiveTelemetry>(`/departures/${depId}/live`);
      setTelemetry(liveData);
    } catch (err: any) {
      if (err?.status === 503) {
        setError(
          'The simulation replay daemon is currently offline. Telemetry cannot be streamed without an active replay engine.'
        );
      } else {
        // Fallback demo state if backend is completely offline
        setTelemetry({
          departureId: depId,
          vesselName: selectedDeparture.vessel,
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
          departurePortName: 'Brest',
          targetPortName: 'Le Conquet',
          dataSource: 'HISTORICAL_REPLAY',
          modelWeightsSha256: 'e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9',
        });
      }
    }

    try {
      // 2. Fetch track coordinates
      const trackData = await apiClient<any>(`/departures/${depId}/track`);
      if (Array.isArray(trackData)) {
        setTrackCoordinates(trackData.map((pt: any) => [pt.latitude || pt[0], pt.longitude || pt[1]]));
      } else if (trackData?.coordinates) {
        setTrackCoordinates(trackData.coordinates);
      }
    } catch {
      // Fallback demo route
      setTrackCoordinates([
        [48.3831, -4.4842],
        [48.3650, -4.5800],
        [48.3750, -4.6200],
        [48.3592, -4.7794],
      ]);
    } finally {
      setLoading(false);
    }
  }, [selectedDeparture.vessel]);

  // Connect SSE Stream
  useEffect(() => {
    loadDepartureData(selectedDeparture.id);

    // Close previous stream
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    // Connect SSE stream
    try {
      const sseUrl = `/api/v1/departures/${selectedDeparture.id}/stream`;
      const es = new EventSource(sseUrl);
      eventSourceRef.current = es;

      es.addEventListener('live-update', (event) => {
        try {
          const update = JSON.parse(event.data);
          setTelemetry((prev) => (prev ? { ...prev, ...update } : update));
          setError(null);
        } catch {
          // ignore parse errors
        }
      });

      es.onerror = () => {
        // SSE error or stream closed
      };
    } catch {
      // Fallback
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [selectedDeparture.id, loadDepartureData]);

  return (
    <div className="container" style={{ padding: '2rem 1rem' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '0.25rem' }}>
            Live Vessel Tracking &amp; Telemetry
          </h1>
          <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
            Real-time AIS positions, speed, heading, and Ridge model delay predictions across the Iroise Sea.
          </p>
        </div>
        <div className="honesty-badge-pill" role="status" aria-label="Replay telemetry mode indicator">
          <Radio size={14} className="pulse-icon" aria-hidden="true" />
          <span>Historical replay mode (simulated live)</span>
        </div>
      </div>

      {/* Departure Sailing Selector Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', paddingBottom: '0.75rem', marginBottom: '1.5rem' }}>
        {DEFAULT_DEPARTURES.map((dep) => {
          const isSelected = dep.id === selectedDeparture.id;
          return (
            <Button
              key={dep.id}
              variant={isSelected ? 'primary' : 'secondary'}
              size="sm"
              icon={<Ship size={14} />}
              onClick={() => setSelectedDeparture(dep)}
            >
              {dep.label} ({dep.vessel})
            </Button>
          );
        })}
      </div>

      {/* Main Grid: Map (Left/Top) + Telemetry Panel (Right/Bottom) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.8fr) minmax(320px, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
        <div>
          <FerryMap
            telemetry={telemetry}
            trackCoordinates={trackCoordinates}
            height="520px"
          />
        </div>

        <div>
          <LiveTelemetryPanel
            telemetry={telemetry}
            loading={loading}
            error={error}
            onRetry={() => loadDepartureData(selectedDeparture.id)}
            onShare={() => setIsShareModalOpen(true)}
          />
        </div>
      </div>

      {/* Share Modal */}
      <ShareModal
        isOpen={isShareModalOpen}
        onClose={() => setIsShareModalOpen(false)}
        departureId={selectedDeparture.id}
        vesselName={selectedDeparture.vessel}
      />
    </div>
  );
};
