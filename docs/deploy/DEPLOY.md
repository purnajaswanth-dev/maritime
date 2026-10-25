# Where Is My Ferry? - Production Deployment Guide

This guide provides reproducible instructions for deploying the **Where Is My Ferry?** production stack.

---

## Architecture Overview
The application consists of three services and one database:
1. **Frontend**: React 19 + TypeScript + Vite, served by Nginx with client-side SPA fallback and SSE reverse proxying (`port 80`).
2. **Backend**: Spring Boot 3.4.3 (Java 17) REST API, JWT Auth, and SSE Telemetry Gateway (`port 8080`).
3. **ML Platform**: Python 3.11/3.13 FastAPI simulation and virtual AIS inference daemon (`port 8000`).
4. **PostgreSQL**: Version 15+ (Neon Cloud, Render Postgres, AWS RDS, or Docker container).

---

## Option 1: Deploy on Render (Recommended for Cloud)

### 1. Database Setup
- Create a PostgreSQL database on **Neon** (serverless) or **Render PostgreSQL**.
- Note the connection string: `postgresql://user:password@host/database?sslmode=require`.

### 2. Backend Web Service Configuration
- **Runtime**: Docker
- **Build Context**: `.` (Repository root)
- **Dockerfile Path**: `Dockerfile`
- **Health Check Path**: `/actuator/health`
- **Environment Variables**:
  | Variable Name | Example / Recommended Value | Description |
  |---|---|---|
  | `SPRING_PROFILES_ACTIVE` | `prod` | Production Spring profile |
  | `DATABASE_URL` | `postgresql://user:pass@host/db?sslmode=require` | Raw database URI (auto-converted to JDBC) |
  | `PORT` | `10000` | Render standard port (Tomcat binds automatically) |
  | `APP_JWT_SECRET` | `long_random_secret_at_least_32_bytes_length!` | HS256 JWT signing secret |
  | `APP_CORS_ALLOWED_ORIGINS` | `*` (or your frontend domain) | Allowed cross-origin sources |
  | `SIMULATION_DAEMON_URL` | `http://where-is-my-ferry-ml:8000` | ML Simulation Daemon internal address |
  | `APP_ADMIN_SEED_EMAIL` | `admin@example.com` | First admin account email |
  | `APP_ADMIN_SEED_PASSWORD` | `AdminPass123!` | First admin account password |

### 3. ML Platform Service Configuration
- **Type**: Private Service (or Web Service)
- **Name**: `where-is-my-ferry-ml`
- **Docker Context**: `ml-platform`
- **Dockerfile Path**: `ml-platform/Dockerfile`
- **Environment Variables**:
  | Variable Name | Value | Description |
  |---|---|---|
  | `PORT` | `8000` | Daemon listen port |
  | `ALLOW_CONTAINER_BIND` | `1` | Enables `0.0.0.0` container binding |
  | `PYTHONUNBUFFERED` | `1` | Real-time container log streaming |

### 4. Frontend Web Service Configuration
- **Type**: Web Service (or Static Site)
- **Docker Context**: `frontend`
- **Dockerfile Path**: `frontend/Dockerfile`
- **Environment Variables**:
  | Variable Name | Value | Description |
  |---|---|---|
  | `VITE_API_BASE_URL` | `https://your-backend.onrender.com` | Backend API URL |

---

## Option 2: Deploy with Docker Compose (Linux VM / Single Host)

Run the full stack with a single command on any Linux server:

```bash
git clone https://github.com/purnajaswanth-dev/maritime.git
cd maritime

# Copy environment template and adjust secrets
cp .env.example .env

# Build and start all 4 services
docker compose up -d --build
```

To run the automated deployment script with health checks:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

---

## Troubleshooting Guide

| Issue / Error | Root Cause | Solution Applied |
|---|---|---|
| `open Dockerfile: no such file or directory` | Render builds from repo root, but only `backend/Dockerfile` existed | Created root `Dockerfile` packaging the backend |
| `Driver org.postgresql.Driver claims to not accept jdbcUrl` | PostgreSQL JDBC driver rejects raw `postgresql://user:pass@host/db` URIs | Implemented `DatabaseUrlParser` and `DatabaseConfiguration` to convert URLs into valid `jdbc:postgresql://` format |
| `Migrations have failed validation: Migration checksum mismatch` | Neon had older migrations applied with CRLF line endings | Added `flyway.repair()` before `flyway.migrate()` and disabled `validate-on-migrate` |
| `ERROR: relation "roles" does not exist` | `flyway_schema_history` had records, but tables were never actually created | Auto-detects missing core tables and resets schema history so migrations run fresh |
| `ERROR: column "user_id" does not exist` | Stale `bookings` table existed from previous incomplete attempts without `user_id` | Auto-detects stale tables and drops them, plus added defensive `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` |
| `IllegalArgumentException: When allowCredentials is true, allowedOrigins cannot contain "*"` | W3C CORS specification forbids `*` with credentials | Configured `setAllowedOriginPatterns(List.of("*"))` |
| Container exits with status 137 (OOM) | Java 17 default heap memory overcommits on 512 MB instances | Added `-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0` to Docker ENTRYPOINT |
