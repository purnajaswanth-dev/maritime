export interface Port {
  id: string;
  code: string;
  name: string;
  latitude: number;
  longitude: number;
  timezone?: string;
  amenities?: string;
  berthCount?: number;
}

export interface Route {
  id: string;
  code: string;
  name: string;
  originPortId: string;
  originPortName: string;
  destinationPortId: string;
  destinationPortName: string;
  distanceNm: number;
  crossingDurationMinutes: number;
  trackingSupported?: boolean;
}

export interface Vessel {
  id: string;
  name: string;
  mmsi: number;
  callsign?: string;
  passengerCapacity: number;
  vehicleCapacity?: number;
  serviceSpeedKnots: number;
}

export interface Departure {
  id: number | string;
  departureCode: string;
  route: Route;
  vessel: Vessel;
  scheduledDepartureTime: string;
  scheduledArrivalTime: string;
  actualDepartureTime?: string;
  actualArrivalTime?: string;
  status: string;
  delayMinutes?: number;
  liveTrackingAvailable?: boolean;
  liveTrackingUrl?: string;
  isHistoricalReplay?: boolean;
}

export interface FareRule {
  id: number;
  routeId: string;
  passengerType: string;
  vehicleType?: string;
  basePriceEur: number;
  currency: string;
  validFrom?: string;
  validTo?: string;
}

export interface TimetableEntry {
  tripId?: string | number;
  routeId?: string;
  routeName?: string;
  originPortName?: string;
  destinationPortName?: string;
  departureTime?: string;
  arrivalTime?: string;
  trackingSupported?: boolean;
  status?: string;
  baseFareEur?: number;
  vesselName?: string;
  [key: string]: any;
}

