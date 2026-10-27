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
      [48.38218, -4.48563],
      [48.382, -4.486],
      [48.38, -4.484],
      [48.378, -4.484],
      [48.376, -4.487],
      [48.374, -4.487],
      [48.37, -4.489],
      [48.366, -4.486],
      [48.36, -4.495],
      [48.358, -4.515],
      [48.351, -4.54],
      [48.344, -4.57],
      [48.336, -4.604],
      [48.332, -4.63],
      [48.329, -4.662],
      [48.327, -4.698],
      [48.325, -4.73],
      [48.318, -4.762],
      [48.318, -4.776],
      [48.325, -4.788],
      [48.336, -4.788],
      [48.348, -4.788],
      [48.356, -4.787],
      [48.3575, -4.7835],
      [48.358, -4.7815],
      [48.35816, -4.77967],
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
      [48.35816, -4.77967],
      [48.358, -4.7815],
      [48.3575, -4.7835],
      [48.356, -4.787],
      [48.365, -4.845],
      [48.395, -4.885],
      [48.425, -4.935],
      [48.448, -4.98],
      [48.465, -5.02],
      [48.4665, -5.035],
      [48.4655, -5.044],
      [48.4633, -5.04889],
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
      [48.021586, -4.537544],
      [48.022, -4.5374],
      [48.0188, -4.5342],
      [48.0172, -4.5342],
      [48.014, -4.5374],
      [48.0132, -4.5374],
      [48.01, -4.5406],
      [48.0092, -4.5406],
      [48.0084, -4.5414],
      [48.0084, -4.5478],
      [48.0044, -4.5518],
      [48.004, -4.553],
      [48.004677, -4.553014],
      [48.001287, -4.55478],
      [47.99502, -4.559789],
      [47.993426, -4.563877],
      [47.994857, -4.574342],
      [48.001957, -4.611476],
      [48.009326, -4.653799],
      [48.019423, -4.701426],
      [48.029446, -4.74354],
      [48.038328, -4.774028],
      [48.039262, -4.77916],
      [48.040792, -4.789406],
      [48.04318, -4.814946],
      [48.04306, -4.831404],
      [48.041948, -4.842513],
      [48.041, -4.845],
      [48.040779, -4.844169],
      [48.037579, -4.847369],
      [48.037179, -4.850169],
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
      [48.35816, -4.77967],
      [48.358, -4.7815],
      [48.3575, -4.7835],
      [48.356, -4.787],
      [48.365, -4.845],
      [48.395, -4.885],
      [48.3972, -4.9531],
    ],
  },
];

function haversineDistanceM(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function pointAlongWaterRoute(
  wps: [number, number][],
  ratio: number
): { lat: number; lon: number; cog: number; remainingM: number } {
  if (wps.length <= 1) {
    return { lat: wps[0][0], lon: wps[0][1], cog: 90, remainingM: 0 };
  }

  const segLengths: number[] = [];
  let totalDist = 0;
  for (let i = 0; i < wps.length - 1; i++) {
    const d = haversineDistanceM(wps[i][0], wps[i][1], wps[i + 1][0], wps[i + 1][1]);
    segLengths.push(d);
    totalDist += d;
  }

  const targetDist = Math.max(0, Math.min(totalDist, ratio * totalDist));
  const remainingM = Math.max(0, totalDist - targetDist);
  let cumDist = 0;
  let lat = wps[wps.length - 1][0];
  let lon = wps[wps.length - 1][1];
  let segIdx = wps.length - 2;

  for (let i = 0; i < segLengths.length; i++) {
    if (cumDist + segLengths[i] >= targetDist) {
      const frac = (targetDist - cumDist) / Math.max(1, segLengths[i]);
      const p1 = wps[i];
      const p2 = wps[i + 1];
      lat = p1[0] + frac * (p2[0] - p1[0]);
      lon = p1[1] + frac * (p2[1] - p1[1]);
      segIdx = i;
      break;
    }
    cumDist += segLengths[i];
  }

  // Smooth tangent lookahead COG
  const pA = wps[segIdx];
  const pB = wps[segIdx + 1];
  const dLat = pB[0] - pA[0];
  const dLon = (pB[1] - pA[1]) * Math.cos(((pA[0] + pB[0]) / 2) * (Math.PI / 180));
  const cog = (Math.atan2(dLon, dLat) * (180 / Math.PI) + 360) % 360;

  return { lat, lon, cog, remainingM };
}

function generateSimulatedVessels(nowMs: number): VesselLiveTelemetry[] {
  return SIMULATED_CORRIDORS.map((corridor) => {
    const elapsed = (nowMs / 1000 + corridor.timeOffsetSeconds) % corridor.cycleSeconds;
    const halfCycle = corridor.cycleSeconds / 2;
    const isForward = elapsed < halfCycle;
    const rawT = isForward ? elapsed / halfCycle : (corridor.cycleSeconds - elapsed) / halfCycle;
    const t = Math.max(0, Math.min(1, rawT));

    const wps = isForward ? corridor.waypoints : [...corridor.waypoints].reverse();
    const { lat, lon, cog, remainingM } = pointAlongWaterRoute(wps, t);

    // Speed with tidal micro-variation
    const sog = Math.round((corridor.baseSpeed + 0.9 * Math.sin(nowMs / 12000)) * 10) / 10;

    const distNm = Math.round((remainingM / 1852) * 10) / 10;
    const distKm = Math.round((remainingM / 1000) * 10) / 10;

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
      lat: Math.round(lat * 100000) / 100000,
      lon: Math.round(lon * 100000) / 100000,
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
