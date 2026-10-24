import { useState, useEffect, useRef, useCallback } from 'react';

export interface VesselLiveTelemetry {
  vesselId: string;
  syntheticMmsi: number;
  name: string;
  operator: string;
  corridor: string;
  originTerminalId: string;
  destinationTerminalId: string;
  lat: number;
  lon: number;
  sogKnots: number;
  cogDegrees: number;
  etaLifecycleState: string;
  positionTimestampUtc?: string;
  predictionTimestampUtc?: string;
  predictedArrivalUtc?: string;
  estimatedRemainingMinutes: number;
  uncertaintyLowerMinutes?: number;
  uncertaintyUpperMinutes?: number;
  distanceRemainingKm?: number;
  distanceRemainingNm?: number;
  telemetryAgeSeconds?: number;
  isStale?: boolean;
  isArrived?: boolean;
  dataProvenance?: string;
  modelWeightsSha256?: string;
}

export interface UseVesselStreamResult {
  vessels: VesselLiveTelemetry[];
  selectedVessel: VesselLiveTelemetry | null;
  selectedVesselId: string | null;
  setSelectedVesselId: (id: string) => void;
  connectionStatus: 'Live' | 'Reconnecting' | 'Stale';
  lastEventTime: Date | null;
  isOffline: boolean;
  error: string | null;
}

function mapRawVessel(raw: any): VesselLiveTelemetry {
  return {
    vesselId: raw.vessel_id || raw.vesselId || '',
    syntheticMmsi: Number(raw.synthetic_mmsi || raw.syntheticMmsi || 0),
    name: raw.name || raw.vessel_name || raw.vesselName || 'Unnamed Vessel',
    operator: raw.operator || 'Penn ar Bed',
    corridor: raw.corridor || '',
    originTerminalId: raw.origin_terminal_id || raw.originTerminalId || '',
    destinationTerminalId: raw.destination_terminal_id || raw.destinationTerminalId || '',
    lat: Number(raw.lat || raw.latitude || 0),
    lon: Number(raw.lon || raw.longitude || 0),
    sogKnots: Number(raw.sog_knots ?? raw.sogKnots ?? raw.speedKnots ?? 0),
    cogDegrees: Number(raw.cog_degrees ?? raw.cogDegrees ?? raw.headingDegrees ?? 0),
    etaLifecycleState: raw.eta_lifecycle_state || raw.lifecycleState || raw.state || 'SCHEDULED',
    positionTimestampUtc: raw.position_timestamp_utc || raw.positionTimestampUtc,
    predictionTimestampUtc: raw.prediction_timestamp_utc || raw.predictionTimestampUtc,
    predictedArrivalUtc: raw.predicted_arrival_utc || raw.predictedArrivalUtc || raw.etaIso,
    estimatedRemainingMinutes: Number(raw.estimated_remaining_minutes ?? raw.estimatedRemainingMinutes ?? 0),
    uncertaintyLowerMinutes: raw.uncertainty_lower_minutes != null ? Number(raw.uncertainty_lower_minutes) : undefined,
    uncertaintyUpperMinutes: raw.uncertainty_upper_minutes != null ? Number(raw.uncertainty_upper_minutes) : undefined,
    distanceRemainingKm: raw.distance_remaining_km != null ? Number(raw.distance_remaining_km) : undefined,
    distanceRemainingNm: raw.distance_remaining_nm != null ? Number(raw.distance_remaining_nm) : undefined,
    telemetryAgeSeconds: raw.telemetry_age_seconds != null ? Number(raw.telemetry_age_seconds) : undefined,
    isStale: Boolean(raw.is_stale || raw.isStale),
    isArrived: Boolean(raw.is_arrived || raw.isArrived),
    dataProvenance: raw.data_provenance || raw.dataProvenance || 'SIMULATED_LOCAL',
    modelWeightsSha256: raw.model_weights_sha256 || raw.modelWeightsSha256 || 'e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9',
  };
}

export function useVesselStream(streamUrl = '/api/v1/stream/vessels'): UseVesselStreamResult {
  const [vessels, setVessels] = useState<VesselLiveTelemetry[]>([]);
  const [selectedVesselId, setSelectedVesselId] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'Live' | 'Reconnecting' | 'Stale'>('Live');
  const [lastEventTime, setLastEventTime] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const watchdogIntervalRef = useRef<any>(null);
  const reconnectDelayRef = useRef<number>(1000);
  const isMountedRef = useRef<boolean>(true);

  const handleMessageArrival = useCallback(() => {
    const now = new Date();
    setLastEventTime(now);
    setConnectionStatus('Live');
  }, []);

  const connect = useCallback(() => {
    if (!isMountedRef.current) return;

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    try {
      const es = new EventSource(streamUrl);
      eventSourceRef.current = es;

      es.addEventListener('open', () => {
        if (!isMountedRef.current) return;
        reconnectDelayRef.current = 1000;
        setError(null);
        setConnectionStatus('Live');
      });

      es.addEventListener('snapshot', (e: MessageEvent) => {
        if (!isMountedRef.current) return;
        handleMessageArrival();
        try {
          const list = JSON.parse(e.data);
          if (Array.isArray(list)) {
            const mapped = list.map(mapRawVessel);
            setVessels(mapped);
            if (!selectedVesselId && mapped.length > 0) {
              setSelectedVesselId(mapped[0].vesselId);
            }
          }
        } catch (err: any) {
          console.error('Failed to parse snapshot SSE event', err);
        }
      });

      es.addEventListener('telemetry_update', (e: MessageEvent) => {
        if (!isMountedRef.current) return;
        handleMessageArrival();
        try {
          const list = JSON.parse(e.data);
          if (Array.isArray(list)) {
            const mapped = list.map(mapRawVessel);
            setVessels(mapped);
          }
        } catch (err: any) {
          console.error('Failed to parse telemetry_update SSE event', err);
        }
      });

      es.addEventListener('eta_transition', (e: MessageEvent) => {
        if (!isMountedRef.current) return;
        handleMessageArrival();
      });

      es.addEventListener('ping', () => {
        if (!isMountedRef.current) return;
        handleMessageArrival();
      });

      es.addEventListener('stale', () => {
        if (!isMountedRef.current) return;
        setConnectionStatus('Stale');
      });

      es.onerror = () => {
        if (!isMountedRef.current) return;
        setConnectionStatus('Reconnecting');
        es.close();
        eventSourceRef.current = null;

        // Exponential backoff up to 15 seconds
        const delay = reconnectDelayRef.current;
        reconnectDelayRef.current = Math.min(15000, Math.round(delay * 1.5));

        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch (err: any) {
      if (!isMountedRef.current) return;
      setError('Unable to initialize EventSource connection');
      setConnectionStatus('Reconnecting');
    }
  }, [streamUrl, selectedVesselId, handleMessageArrival]);

  // Connect on mount
  useEffect(() => {
    isMountedRef.current = true;
    connect();

    // 30-Second Stale Watchdog
    watchdogIntervalRef.current = setInterval(() => {
      setLastEventTime((prevTime) => {
        if (prevTime) {
          const elapsedMs = Date.now() - prevTime.getTime();
          if (elapsedMs > 30000) {
            setConnectionStatus('Stale');
          }
        }
        return prevTime;
      });
    }, 5000);

    return () => {
      isMountedRef.current = false;
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (watchdogIntervalRef.current) {
        clearInterval(watchdogIntervalRef.current);
      }
    };
  }, [connect]);

  const selectedVessel =
    vessels.find((v) => v.vesselId === selectedVesselId) ||
    (vessels.length > 0 ? vessels[0] : null);

  return {
    vessels,
    selectedVessel,
    selectedVesselId,
    setSelectedVesselId,
    connectionStatus,
    lastEventTime,
    isOffline: connectionStatus === 'Reconnecting' && vessels.length === 0,
    error,
  };
}
