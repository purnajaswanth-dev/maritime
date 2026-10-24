export interface ServiceHealthTile {
  name: string;
  status: 'HEALTHY' | 'DEGRADED' | 'DOWN' | string;
  port?: number;
  url?: string;
  version?: string;
  activeConnections?: number;
}

export interface AdminOverview {
  usersCount: number;
  usersByRole: Record<string, number>;
  bookings: {
    total: number;
    confirmed: number;
    cancelled: number;
    revenueEur: number;
  };
  activeDeparturesCount: number;
  activeSseConnections: number;
  health: {
    engine: ServiceHealthTile;
    backend: ServiceHealthTile;
    database: ServiceHealthTile;
  };
  maintenanceMode: boolean;
}

export interface SimulationStatus {
  simulation_available: boolean;
  run_id?: string;
  is_running: boolean;
  is_paused: boolean;
  sim_time_utc?: string;
  speed_multiplier: number;
  total_events_processed?: number;
  active_vessels_count?: number;
  active_scenario_id?: string;
  mode?: string;
}

export interface SimulationScenario {
  id: string;
  name: string;
  description: string;
  vessel_id?: string;
  duration_steps?: number;
  step_interval_s?: number;
  fault_type?: string;
  expected_state?: string;
}

export interface MlDiagnostics {
  modelMetadata: {
    name: string;
    schemaVersion: string;
    alpha: number;
    weightsSha256: string;
    integrityStatus: string;
    tamperAlert: boolean;
  };
  testMetrics: {
    mae: number;
    medAe: number;
    rmse: number;
    recordCount?: number;
  };
  baselineComparison: Array<{
    model: string;
    mae: number;
    rmse: number;
    p95LatencyMs: number;
  }>;
  driftMonitor: {
    status: string;
    klDivergence: number;
    ksPValue: number;
    telemetryFreshnessSeconds: number;
  };
  errorHistogram: Record<string, number>;
}

export interface AuditLogEntry {
  id: number;
  action: string;
  entityType?: string;
  entityId?: string;
  details?: string;
  ipAddress?: string;
  createdAt: string;
  user?: {
    id: number;
    email: string;
    firstName?: string;
    lastName?: string;
  };
}

export interface AdminUser {
  id: number;
  email: string;
  firstName?: string;
  lastName?: string;
  roles: string[];
  enabled: boolean;
}

export interface SystemConfig {
  maintenanceMode: boolean;
  maintenanceReason?: string;
  maintenanceActivatedAt?: string;
  maintenanceActivatedBy?: string;
  featureFlags?: Record<string, boolean>;
}

export interface AdminDashboard {
  sailingsTodayByStatus: Record<string, number>;
  shipsInTransit: number;
  passengersBookedToday: number;
  activeAnnouncements: number;
  engineStatus: string;
  delayedOrCancelledSailings: any[];
}

export interface AdminServiceItem {
  id?: number;
  routeId: string;
  routeName?: string;
  originPortId?: string;
  originPortName?: string;
  destinationPortId?: string;
  destinationPortName?: string;
  vesselId: string;
  vesselName?: string;
  departureTime: string;
  durationMinutes: number;
  daysOfWeek: string;
  validFrom: string;
  validTo: string;
  baseFareEur: number;
  capacity: number;
  active: boolean;
  trackingSupported?: boolean;
}

export interface AdminShipItem {
  id: string;
  name: string;
  capacity: number;
  homePortId: string;
  homePortName?: string;
  status: string;
  engineVesselId?: string;
  sailingsTodayCount: number;
  liveTrackingAvailable: boolean;
  latitude?: number;
  longitude?: number;
  speedKnots?: number;
  cogDegrees?: number;
  etaLifecycleState?: string;
}

export interface AdminPortItem {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  status: string;
  berthRadiusMeters: number;
  closedReason?: string;
}

export interface AdminPassengerItem {
  id: number;
  fullName: string;
  email: string;
  phone?: string;
  status: string;
  bookingsCount: number;
  lastLoginAt?: string;
  createdAt: string;
  hasUpcomingTrips: boolean;
  bookings?: any[];
}

export interface AdminAnnouncementItem {
  id?: number;
  title: string;
  body: string;
  severity: string;
  scope: string;
  targetId?: string;
  startsAt?: string;
  endsAt?: string;
  createdBy?: string;
  createdAt?: string;
}
