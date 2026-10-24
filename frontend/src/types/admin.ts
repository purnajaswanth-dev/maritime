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
  featureFlags: Record<string, boolean>;
}
