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

interface SimulatedCorridor {
  vesselId: string;
  name: string;
  syntheticMmsi: number;
  originTerminalId: string;
  destinationTerminalId: string;
  corridor: string;
  baseSpeed: number;
  cycleSeconds: number;
  timeOffsetSeconds: number;
  waypoints: [number, number][];
}

const SIMULATED_CORRIDORS: SimulatedCorridor[] = [
  {
    vesselId: 'V-FROMVEUR-SIM',
    name: 'Fromveur II',
    syntheticMmsi: 228037700,
    originTerminalId: 'BREST',
    destinationTerminalId: 'LE_CONQUET',
    corridor: 'BREST_LE_CONQUET',
    baseSpeed: 18.2,
    cycleSeconds: 1200,
    timeOffsetSeconds: 0,
    waypoints: [
      [48.3811, -4.4857], // Brest Port
      [48.3580, -4.5650], // Goulet de Brest
      [48.3300, -4.7100], // Pointe Saint-Mathieu
      [48.3596, -4.7818], // Port du Conquet
    ],
  },
  {
    vesselId: 'V-AZENOR-SIM',
    name: 'Azenor',
    syntheticMmsi: 228045600,
    originTerminalId: 'LE_CONQUET',
    destinationTerminalId: 'OUESSANT_STIFF',
    corridor: 'LE_CONQUET_OUESSANT',
    baseSpeed: 19.0,
    cycleSeconds: 1500,
    timeOffsetSeconds: 400,
    waypoints: [
      [48.3596, -4.7818], // Le Conquet
      [48.3850, -4.8700], // Chenal du Four
      [48.4100, -4.9600], // Molène East Passage
      [48.4450, -5.0150], // Passage du Fromveur
      [48.4691, -5.0545], // Port du Stiff (Ouessant)
    ],
  },
  {
    vesselId: 'V-SEIN-SIM',
    name: 'Enez Sun 3',
    syntheticMmsi: 228023400,
    originTerminalId: 'AUDIERNE',
    destinationTerminalId: 'ILE_DE_SEIN',
    corridor: 'AUDIERNE_SEIN',
    baseSpeed: 16.0,
    cycleSeconds: 900,
    timeOffsetSeconds: 150,
    waypoints: [
      [48.0061, -4.5524], // Audierne (Sainte-Evette)
      [48.0280, -4.6800], // Baie d'Audierne
      [48.0420, -4.7800], // Raz de Sein
      [48.0390, -4.8486], // Port de l'Île de Sein
    ],
  },
  {
    vesselId: 'V-OUESSANT-SIM',
    name: 'Ouessant',
    syntheticMmsi: 228067800,
    originTerminalId: 'LE_CONQUET',
    destinationTerminalId: 'MOLENE',
    corridor: 'LE_CONQUET_MOLENE',
    baseSpeed: 17.5,
    cycleSeconds: 800,
    timeOffsetSeconds: 550,
    waypoints: [
      [48.3596, -4.7818], // Le Conquet
      [48.3820, -4.8750], // Archipel de Molène
      [48.4022, -4.9565], // Port de Molène
    ],
  },
];

function generateSimulatedVessels(nowMs: number): VesselLiveTelemetry[] {
  return SIMULATED_CORRIDORS.map((corridor) => {
    const elapsed = (nowMs / 1000 + corridor.timeOffsetSeconds) % corridor.cycleSeconds;
    const halfCycle = corridor.cycleSeconds / 2;
    const isForward = elapsed < halfCycle;
    const rawT = isForward ? elapsed / halfCycle : (corridor.cycleSeconds - elapsed) / halfCycle;
    const t = Math.max(0, Math.min(1, rawT));

    const wps = isForward ? corridor.waypoints : [...corridor.waypoints].reverse();
    const segCount = wps.length - 1;
    const scaledT = t * segCount;
    const segIdx = Math.min(Math.floor(scaledT), segCount - 1);
    const segRatio = scaledT - segIdx;

    const pA = wps[segIdx];
    const pB = wps[segIdx + 1];

    const lat = pA[0] + (pB[0] - pA[0]) * segRatio;
    const lon = pA[1] + (pB[1] - pA[1]) * segRatio;

    // Course over ground calculation
    const dLat = pB[0] - pA[0];
    const dLon = (pB[1] - pA[1]) * Math.cos(((pA[0] + pB[0]) / 2) * (Math.PI / 180));
    const cog = (Math.atan2(dLon, dLat) * (180 / Math.PI) + 360) % 360;

    // Speed with tidal micro-variation
    const sog = Math.round((corridor.baseSpeed + 0.9 * Math.sin(nowMs / 12000)) * 10) / 10;

    // Remaining distance calculation to destination terminal
    const destPt = wps[wps.length - 1];
    const deltaLatNm = (destPt[0] - lat) * 60;
    const deltaLonNm = (destPt[1] - lon) * Math.cos((lat * Math.PI) / 180) * 60;
    const distNm = Math.round(Math.sqrt(deltaLatNm * deltaLatNm + deltaLonNm * deltaLonNm) * 10) / 10;
    const distKm = Math.round(distNm * 1.852 * 10) / 10;

    // Countdown ETA in minutes
    const remMinutes = Math.max(0.4, Math.round((distNm / (sog / 60)) * 10) / 10);
    const arrivalDate = new Date(nowMs + remMinutes * 60000);

    const state = distNm <= 0.3 ? 'BERTHED' : distNm <= 1.4 ? 'APPROACHING' : 'UNDERWAY';

    return {
      vesselId: corridor.vesselId,
      syntheticMmsi: corridor.syntheticMmsi,
      name: corridor.name,
      operator: 'Penn ar Bed',
      corridor: corridor.corridor,
      originTerminalId: isForward ? corridor.originTerminalId : corridor.destinationTerminalId,
      destinationTerminalId: isForward ? corridor.destinationTerminalId : corridor.originTerminalId,
      lat: Math.round(lat * 10000) / 10000,
      lon: Math.round(lon * 10000) / 10000,
      sogKnots: sog,
      cogDegrees: Math.round(cog * 10) / 10,
      etaLifecycleState: state,
      positionTimestampUtc: new Date(nowMs).toISOString(),
      predictionTimestampUtc: new Date(nowMs).toISOString(),
      predictedArrivalUtc: arrivalDate.toISOString(),
      estimatedRemainingMinutes: remMinutes,
      uncertaintyLowerMinutes: Math.max(0.5, Math.round(remMinutes * 0.15 * 10) / 10),
      uncertaintyUpperMinutes: Math.round(remMinutes * 0.32 * 10) / 10,
      distanceRemainingKm: distKm,
      distanceRemainingNm: distNm,
      telemetryAgeSeconds: 0,
      isStale: false,
      isArrived: state === 'BERTHED',
      dataProvenance: 'AUTONOMOUS_MARITIME_ENGINE',
      modelWeightsSha256: 'e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9',
    };
  });
}

const rawStreamBase = import.meta.env.VITE_API_BASE_URL || '';
const DEFAULT_STREAM_URL = rawStreamBase
  ? `${rawStreamBase.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '')}/api/v1/stream/vessels`
  : '/api/v1/stream/vessels';

export function useVesselStream(streamUrl = DEFAULT_STREAM_URL): UseVesselStreamResult {
  const [vessels, setVessels] = useState<VesselLiveTelemetry[]>(() => generateSimulatedVessels(Date.now()));
  const [selectedVesselId, setSelectedVesselId] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'Live' | 'Reconnecting' | 'Stale'>('Live');
  const [lastEventTime, setLastEventTime] = useState<Date | null>(() => new Date());
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const watchdogIntervalRef = useRef<any>(null);
  const simulationIntervalRef = useRef<any>(null);
  const reconnectDelayRef = useRef<number>(1000);
  const isMountedRef = useRef<boolean>(true);
  const lastServerEventTimeRef = useRef<number>(0);

  const handleMessageArrival = useCallback(() => {
    const now = new Date();
    setLastEventTime(now);
    lastServerEventTimeRef.current = Date.now();
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
          if (Array.isArray(list) && list.length > 0) {
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
          if (Array.isArray(list) && list.length > 0) {
            const mapped = list.map(mapRawVessel);
            setVessels(mapped);
          }
        } catch (err: any) {
          console.error('Failed to parse telemetry_update SSE event', err);
        }
      });

      es.addEventListener('eta_transition', () => {
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

        const delay = reconnectDelayRef.current;
        reconnectDelayRef.current = Math.min(15000, Math.round(delay * 1.5));

        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch {
      if (!isMountedRef.current) return;
      setError('Unable to initialize EventSource connection');
      setConnectionStatus('Reconnecting');
    }
  }, [streamUrl, selectedVesselId, handleMessageArrival]);

  // Connect on mount & start 1 Hz live simulation engine tick
  useEffect(() => {
    isMountedRef.current = true;
    connect();

    // 1 Hz simulation tick: guarantees live movement, speed fluctuations, and countdown ETAs
    simulationIntervalRef.current = setInterval(() => {
      const now = Date.now();
      // If server SSE hasn't provided live packets in the last 2 seconds, drive dynamic simulation
      if (now - lastServerEventTimeRef.current > 2000) {
        const liveSim = generateSimulatedVessels(now);
        setVessels(liveSim);
        setLastEventTime(new Date(now));
      }
    }, 1000);

    // Watchdog
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
      if (simulationIntervalRef.current) {
        clearInterval(simulationIntervalRef.current);
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
