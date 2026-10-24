# Frontend Data Contract Audit — Where Is My Ferry?

**Date:** 2026-10-16  
**Auditor:** Senior Frontend Architect & Maritime Data Specialist  
**Reference Contracts:** Phase 07 Streaming Contract, Phase 08 Simulation Contract, `frontend/src/types/ferry.ts`  

---

## 1. Data Contract Inventory & Verification

The frontend data contracts are defined in `frontend/src/types/ferry.ts` and populated by local fixtures in `frontend/src/data/mockData.ts`.

### A. Virtual Vessel Telemetry Contract
```typescript
export interface VirtualVessel {
  virtualVesselId?: string;
  id?: string;
  name: string;
  operator: string;
  type?: string;
  syntheticMmsi?: number;
  mmsi?: number;
  routeId?: string;
  originTerminal?: string;
  originTerminalId?: string;
  destTerminal?: string;
  destinationTerminalId?: string;
  nominalSpeedKnots?: number;
  capacityPassengers?: number;
  capacityVehicles?: number;
  amenities?: string[];
  lat?: number;
  currentLat?: number;
  lon?: number;
  currentLon?: number;
  sogKnots?: number;
  speedKnots?: number;
  cogDegrees?: number;
  headingDeg?: number;
  lifecycleState?: ETALifecycleState;
  etaState?: ETALifecycleState;
  estimatedRemainingMinutes?: number;
  predictedArrivalTimestampUtc?: string;
  predictedArrivalUtc?: string;
  latestObservationTimestampUtc?: string;
  dataFreshnessSeconds?: number;
  isStale?: boolean;
  isArrived?: boolean;
  routeProgressPercent?: number;
  reasonCode?: string;
  dataProvenance?: 'OBSERVED_AIS' | 'SIMULATED_SYNTHETIC';
  uncertaintyMinutes?: number;
}
```

#### Field Verification & Quality Assessment:
1. **Identifier Consistency:** All virtual vessels use IDs prefixed with `V-` (e.g., `V-FROMVEUR-SIM`, `V-AZENOR-SIM`, `V-OUESSANT-SIM`) and synthetic MMSIs in the range `999000001–999000004`. No collisions with real operational MMSIs.
2. **Geographical Coordinates:** Latitude ranges between `48.34°N` and `48.47°N`; longitude ranges between `-5.06°W` and `-4.48°W`. All points reside strictly within the physical Iroise Sea fairway corridor between Brest and Ushant.
3. **Speed & Heading:** Speed is expressed in knots (`13.9–15.0 kts` cruising; `0.8 kts` moored); heading is expressed in degrees (`0°–360°`).
4. **Timestamp Format:** All timestamps use ISO 8601 UTC representation (e.g. `2026-10-16T12:45:00.000Z`).
5. **Data Provenance:** Field `dataProvenance` is strictly set to `'SIMULATED_SYNTHETIC'`, preventing accidental representation as live telemetry.

---

### B. ETA Lifecycle State Machine Contract
The lifecycle states mirror the Phase 07 and Phase 08 streaming contracts:
- `SCHEDULED`: Voyage planned, vessel at berth.
- `DEPARTING`: Vessel maneuvering from berth into channel.
- `IN_TRANSIT`: Underway cruising along route corridor.
- `SLOWING`: Decelerating upon approach to terminal fairway.
- `HOLDING`: Vessel maintaining position outside harbor due to traffic/tides.
- `APPROACHING`: Final approach corridor within 0.5 NM of berth.
- `ARRIVED`: Vessel confirmed moored; countdown clamps to 00m 00s.
- `STALE`: Telemetry gap exceeding freshness threshold (>60s).
- `UNCERTAIN`: High variance prediction or anomalous weather.
- `ERROR`: Sensor fault or out-of-corridor trajectory.

---

### C. Fares and Commercial Data Contract
```typescript
export interface Journey {
  id: string; // e.g. 'J-BRE-OUE-01'
  originTerminal: Terminal;
  destTerminal: Terminal;
  vessel: VirtualVessel;
  departureTimeUtc: string;
  arrivalTimeUtc: string;
  durationMinutes: number;
  fares: {
    standardAdult: number; // e.g. 24.50
    standardChild: number; // e.g. 14.00
    flexiAdultUpgrade: number; // e.g. 6.00
    bicycleFee: number; // e.g. 8.00
    petFee: number; // e.g. 4.50
  };
  availableSeats: number;
  amenities: string[];
}
```
All prices are specified in EUR (`€`) and computed deterministically without rounding errors or negative balances.

---

## 2. API Contract Gaps & Future Backend Integration Requirements

| Endpoint / Resource | Existing Status | Future Backend Contract Requirement |
|---|---|---|
| `GET /api/v1/vessels` | Mocked (`mockData.ts`) | Streaming SSE or WebSocket emitting Phase 07 `VesselStateEvent` |
| `GET /api/v1/journeys` | Mocked (`mockData.ts`) | Spring Boot REST endpoint querying Postgres schedules |
| `POST /api/v1/bookings` | Simulated client-side | Spring Boot payment authorization & ticket persistence |
| `GET /api/v1/operator/manifest` | Mocked client-side | Role-protected backend query returning checked-in manifest |
| `POST /api/v1/admin/simulation/scenario` | Client-side mock | Phase 08 Python simulation controller or Kafka scenario injector |

*Note: As mandated by Project Scope Rule #1, no backend code or mock endpoints were created during this audit.*
