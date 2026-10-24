# Database Setup & Configuration Guide

**Platform:** Where Is My Ferry?  
**Target Environment:** Local Development & Production Deployment  
**Supported Engines:** PostgreSQL 15+ (Production/Dev), H2 In-Memory (Automated Testing)

---

## 1. PostgreSQL Architecture & Flyway Migrations

The platform employs **Flyway** for version-controlled, automated, and idempotent database schema migrations. Schema evolution is managed under `backend/src/main/resources/db/migration/`:

### Migration History
| Migration Version | Description | Key Tables Created / Modified |
|---|---|---|
| **`V1__initial_schema.sql`** | Core relational schema | `users`, `user_roles`, `ports`, `routes`, `vessels`, `departures`, `bookings`, `tickets`, `passengers`, `audit_log` |
| **`V2__auth_enhancements.sql`** | Authentication & Security hardening | `failed_login_attempts`, `locked_until`, `refresh_tokens` (rotating token family with reuse detection) |
| **`V3__ports_ships_timetable.sql`** | Database-first timetable & fleet governance | `schedules`, `services`, `fare_rules`, `announcements`, `system_config`, canonical Camaret-sur-Mer seed |

---

## 2. Quickstart with Docker Compose

To run PostgreSQL locally via Docker:

```bash
docker run --name ferry-postgres \
  -e POSTGRES_DB=ferrydb \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d postgres:16-alpine
```

---

## 3. Configuration & Credentials

### 3.1 Environment Variables
Set the following environment variables before starting the backend in PostgreSQL mode:

```bash
export SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/ferrydb
export SPRING_DATASOURCE_USERNAME=postgres
export SPRING_DATASOURCE_PASSWORD=postgres
export SPRING_FLYWAY_ENABLED=true
export SPRING_JPA_HIBERNATE_DDL_AUTO=validate
```

### 3.2 Dual Profile Support (`application.yml`)
- **`default` (PostgreSQL):** Connects to `jdbc:postgresql://localhost:5432/ferrydb` with `org.postgresql.Driver`.
- **`test` (H2 In-Memory):** Automatically used during CI/CD and integration tests via `jdbc:h2:mem:ferrydb_test;DB_CLOSE_DELAY=-1;MODE=PostgreSQL`.

---

## 4. Default Seeded Accounts

Upon initialization, `DatabaseSeederService` validates and seeds standard staff and passenger accounts:

| Role | Email Address | Default Password | Permissions |
|---|---|---|---|
| **Administrator** | `admin@example.com` | `AdminPass123!` | Full fleet control, timetable mutation, port closures, user governance |
| **Administrator** | `admin@whereismyferry.bzh` | `AdminPass123!` | Fleet management & scenario triggers |
| **Operator** | `operator@whereismyferry.bzh` | `OperatorPass123!` | Port management, schedule adjustments, delay broadcasts |
| **Auditor** | `auditor@whereismyferry.bzh` | `AuditorPass123!` | Read-only inspection of manifests, timetables, and immutable audit log |
| **Crew / Captain**| `crew@whereismyferry.bzh` | `CrewPass123!` | Telemetry inspection & vessel status |
| **Passenger** | `passenger@whereismyferry.bzh` | `PassengerPass123!` | Booking management, ticket QR download, real-time tracking |

---

## 5. Canonical Maritime Seed Data

### 5.1 The 7 Canonical Ports (Brittany & Iroise Sea)
1. **Brest Port de Commerce (`BREST`)**: Main mainland hub.
2. **Le Conquet Gare Maritime (`LE_CONQUET`)**: High-frequency western terminal.
3. **Port du Stiff, Ouessant (`STIFF`)**: Deepwater northern island dock.
4. **Île-Molène (`MOLENE`)**: Archipelago port with tidal draft limits.
5. **Audierne Sainte-Évette (`AUDIERNE`)**: Southern mainland gateway.
6. **Île de Sein (`SEIN`)**: Low-lying granite island port.
7. **Port de Camaret-sur-Mer (`CAMARET`)**: Crozon peninsula corridor port.

### 5.2 Modeled Fleet Vessels
- **Fromveur II (`V-FROMVEUR-SIM`)**: MMSI `228037700`, 350 pax, 15.5 kts service speed.
- **Enez Sun 3 (`V-ENEZ-SIM`)**: MMSI `227318000`, 250 pax, 14.0 kts service speed.
- **Guerveur / Enez Eussa 3 (`V-BROAD-SIM`)**: MMSI `228198900`, 180 pax, 14.5 kts service speed.
- **Camaret Express (`V-CAMARET-EXP`)**: 220 pax, 18.0 kts high-speed catamaran.

---

## 6. Database Verification & Health Checking

To verify that the database is healthy and migrations have applied:

```bash
# 1. Check Spring Boot health endpoint
curl -s http://localhost:8080/actuator/health | jq .components.db

# 2. Query seeded ports via API
curl -s http://localhost:8080/api/v1/ports | jq '.[].name'

# 3. Check migration history directly in PostgreSQL
psql -U postgres -d ferrydb -c "SELECT version, description, success FROM flyway_schema_history;"
```

---

## 7. Troubleshooting & Recovery

### Issue: Flyway Migration Checksum Mismatch
**Cause:** Modifying an existing migration file after it has already run.  
**Resolution:** Run `mvn flyway:repair` or drop and recreate the development database:
```sql
DROP DATABASE ferrydb;
CREATE DATABASE ferrydb;
```

### Issue: Account Lockout after Failed Logins
**Cause:** Account lockout triggered after 5 consecutive failed attempts (15-minute lock window).  
**Resolution:**
```sql
UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE email = 'user@example.com';
```
