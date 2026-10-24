export interface LiveTelemetry {
  departureId: string | number;
  departureCode?: string;
  vesselName: string;
  mmsi: number;
  latitude: number;
  longitude: number;
  speedKnots: number;
  headingDegrees: number;
  state: 'SCHEDULED' | 'BERTH_DWELL' | 'UNDERWAY' | 'APPROACHING' | 'ARRIVED' | 'DELAYED' | 'CANCELLED' | string;
  predictedDelayMinutes?: number;
  etaIso?: string;
  ciLowerMinutes?: number;
  ciUpperMinutes?: number;
  targetPortName?: string;
  departurePortName?: string;
  dataSource: 'HISTORICAL_REPLAY' | 'LIVE_AIS' | string;
  modelWeightsSha256?: string;
  lastUpdateIso?: string;
  distanceRemainingNm?: number;
}

export interface DepartureSummary {
  id: string | number;
  departureCode: string;
  vesselName: string;
  mmsi: number;
  departurePort: {
    code: string;
    name: string;
  };
  arrivalPort: {
    code: string;
    name: string;
  };
  scheduledDepartureTime: string;
  scheduledArrivalTime: string;
  status: string;
}

export interface TrackPoint {
  latitude: number;
  longitude: number;
  timestamp?: string;
  speedKnots?: number;
}

export interface PublicTrackData {
  departureCode: string;
  vesselName: string;
  mmsi: number;
  departurePortName: string;
  arrivalPortName: string;
  scheduledDepartureTime: string;
  scheduledArrivalTime: string;
  status: string;
  live?: LiveTelemetry;
  trackCoordinates: [number, number][];
}
