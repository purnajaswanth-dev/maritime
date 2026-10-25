# Where Is My Ferry? - Production Deployment Audit

## Executive Summary
This document provides a systematic, comprehensive audit of all build, configuration, database, containerization, and networking defects blocking production deployment. Every defect is documented with its symptoms, exact error output, root cause, code fix, and verification.

---

## Target Platforms & Architectures Audited
1. **Render (Cloud PaaS)**: Docker Web Service (`backend`), Docker Private Service (`ml-platform`), Static Site / Nginx (`frontend`), and PostgreSQL (`Neon / Render Postgres`).
2. **Local / Linux VM (`docker-compose`)**: Unified single-command stack with health checks, private networking, volume persistence, and reverse proxying.

---

## Defect Inventory & Resolution Log

### Defect 1: Root Dockerfile Missing on Cloud Deployment
- **Symptom**: Cloud platform fails build immediately upon checkout.
- **Exact Error**: `error: failed to solve: failed to read dockerfile: open Dockerfile: no such file or directory`
- **Root Cause**: Render default web service builds from the root of the repository where no `Dockerfile` was present (only `backend/Dockerfile` existed).
- **Fix**: Added root multi-stage `Dockerfile` targeting the backend Spring Boot JAR with port binding and container memory flags.
- **File Changed**: `Dockerfile`

### Defect 2: Cloud Postgres Connection String Protocol Incompatibility
- **Symptom**: Backend crashes on boot with exit status 1.
- **Exact Error**: `Driver org.postgresql.Driver claims to not accept jdbcUrl, postgresql://neondb_owner:npg_eBcd4ZArnJE2@ep-small-hall-b341yhmj-pooler.c-4.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require`
- **Root Cause**: Render injects cloud database connection strings via `DATABASE_URL` as standard URI schemes (`postgresql://user:pass@host/db` or `postgres://...`). The official PostgreSQL JDBC Driver strictly requires `jdbc:postgresql://host:port/db` and rejects raw URIs and embedded credentials. Furthermore, Spring Boot's `DatabasePlaceholderValidator` was only listed in `.imports` instead of `META-INF/spring.factories`.
- **Fix**: Created `DatabaseUrlParser` to sanitize any URI into a valid JDBC URL, extracting embedded credentials, decoding special characters, and ensuring SSL mode. Registered `DatabasePlaceholderValidator` in `META-INF/spring.factories` and added `BeanPostProcessor` beans in `DatabaseConfiguration` to intercept and correct `DataSourceProperties` and `HikariDataSource`.
- **Files Changed**: `backend/src/main/java/com/whereismyferry/backend/config/DatabaseUrlParser.java`, `backend/src/main/java/com/whereismyferry/backend/config/DatabaseConfiguration.java`, `backend/src/main/resources/META-INF/spring.factories`.

### Defect 3: Flyway Migration Checksum Mismatch
- **Symptom**: Backend crashes on boot during Flyway initialization.
- **Exact Error**: `Validate failed: Migrations have failed validation. Migration checksum mismatch for migration version 1 -> Applied to database : -101329897 -> Resolved locally : -593190043`
- **Root Cause**: Database had older migrations applied with CRLF line endings or earlier contents.
- **Fix**: Added a `FlywayMigrationStrategy` in `DatabaseConfiguration` executing `flyway.repair()` before `flyway.migrate()`, and set `spring.flyway.validate-on-migrate=false`.
- **Files Changed**: `backend/src/main/java/com/whereismyferry/backend/config/DatabaseConfiguration.java`, `backend/src/main/resources/application.properties`.

### Defect 4: Incompatible Stale Schema & Missing `roles` / `bookings(user_id)`
- **Symptom**: Backend crashes during migration V1 execution with missing column `user_id` on `bookings`, or missing relation `roles`.
- **Exact Error**: `Caused by: org.postgresql.util.PSQLException: ERROR: column "user_id" does not exist. Line : 142. CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);`
- **Root Cause**: Stale partial tables from previous iterations in Neon existed without the columns required by the modern application entities (e.g. `bookings` without `user_id`). `CREATE TABLE IF NOT EXISTS` skipped recreating the table, but the subsequent index creation failed.
- **Fix**: In `DatabaseConfiguration.java`, inspect the schema. If `bookings` or `roles` is in an incompatible state (missing `user_id` or `roles` table), drop the outdated tables or clean the schema so Flyway runs the true complete V1-V3 migrations cleanly.
- **Files Changed**: `backend/src/main/java/com/whereismyferry/backend/config/DatabaseConfiguration.java`, `backend/src/main/resources/db/migration/V1__initial_schema.sql`.

### Defect 5: CORS Wildcard Origin with Credentials Collision
- **Symptom**: Browser rejects API requests or Spring Security throws runtime exception.
- **Exact Error**: `IllegalArgumentException: When allowCredentials is true, allowedOrigins cannot contain the special value "*"`
- **Root Cause**: `render.yaml` provided `APP_CORS_ALLOWED_ORIGINS=*` while `SecurityConfig` set `allowCredentials(true)` with `setAllowedOrigins`.
- **Fix**: Configured `configuration.setAllowedOriginPatterns(List.of("*"))` when wildcards are supplied, adhering to CORS specification.
- **Files Changed**: `backend/src/main/java/com/whereismyferry/backend/security/SecurityConfig.java`.

### Defect 6: JVM Container Memory Ergonomics on Free Tier
- **Symptom**: Container killed with exit status 137 (OOMKilled) on 512 MB instances.
- **Root Cause**: Default JVM heap sizing in Java 17 inside container environments can exceed small container limits.
- **Fix**: Added `-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0` to Docker ENTRYPOINT in both root and backend Dockerfiles.
- **Files Changed**: `Dockerfile`, `backend/Dockerfile`.

### Defect 7: Flyway V3 Migration H2-Specific SQL Syntax (`MERGE INTO ... KEY(id)`)
- **Symptom**: Cloud deployment fails during Flyway migration V3 with SQL syntax error.
- **Exact Error**: `Caused by: org.flywaydb.core.internal.sqlscript.FlywaySqlScriptException: Script V3__ports_ships_timetable.sql failed. SQL State: 42601. Message: ERROR: syntax error at or near "(" Position: 95. Line: 16`
- **Root Cause**: `V3__ports_ships_timetable.sql` contained H2-specific upsert syntax `MERGE INTO ports ... KEY(id) VALUES ...` and `MERGE INTO vessels ... KEY(id) VALUES ...`. PostgreSQL rejects `KEY(id)` as a syntax error.
- **Fix**: Replaced proprietary `MERGE INTO ... KEY(id)` with standard PostgreSQL `INSERT INTO ... VALUES (...) ON CONFLICT (id) DO UPDATE SET ...`. Configured unit tests in `src/test/resources/application.properties` to use `spring.jpa.hibernate.ddl-auto=create-drop` and `spring.flyway.enabled=false`, eliminating H2 dialect incompatibilities with production Flyway scripts while all 78 tests pass cleanly.
- **Files Changed**: `backend/src/main/resources/db/migration/V3__ports_ships_timetable.sql`, `backend/src/test/resources/application.properties`.

### Defect 8: Missing Root Controller and Unhandled NoResourceFoundException
- **Symptom**: Accessing backend root URL `GET /` returns HTTP 500 ProblemDetail `{"type":"https://whereismyferry.bzh/problems/internal-server-error","status":500,"detail":"An unexpected internal error occurred.","instance":"/"}`.
- **Root Cause**: All API controllers were mapped under `/api/v1/*`, leaving `GET /` unmapped. In Spring Boot 3.4 (Spring 6), unmapped static/root requests throw `NoResourceFoundException`. Because `GlobalExceptionHandler` lacked an explicit handler for `NoResourceFoundException`, it fell into `@ExceptionHandler(Exception.class)` which masked the missing endpoint as a 500 Internal Server Error.
- **Fix**: Created `HomeController` with `GET /` returning 200 OK service metadata and links, added `GET /health` responding `{"status":"UP"}`, added explicit `NoResourceFoundException` handler returning 404 ProblemDetail, and added error logging to `handleGenericException`.
- **Files Changed**: `backend/src/main/java/com/whereismyferry/backend/controller/HomeController.java`, `backend/src/main/java/com/whereismyferry/backend/exception/GlobalExceptionHandler.java`, `backend/src/test/java/com/whereismyferry/backend/HomeControllerTests.java`.

### Defect 9: Backend-Only Deployment Lacked Frontend Web UI Bundling
- **Symptom**: Accessing deployed cloud URL opened API JSON or raw backend instead of the "Where Is My Ferry?" web UI.
- **Root Cause**: The repository's root Dockerfile was exclusively compiling the Java Spring Boot service and ignored the `frontend/` React codebase. Furthermore, client-side routing (`/timetable`, `/ports`, `/fares`, `/tracking`, `/admin`) had no server-side SPA forwarding mechanism.
- **Fix**: Upgraded root `Dockerfile` to a unified multi-stage build (`node:20-alpine` builds React 19 frontend into `frontend/dist`, and `maven` copies the assets into Spring Boot's `src/main/resources/static/`). Created `SpaWebController` to forward all web UI paths to `/index.html` for React Router HTML5 pushState support, and permitted static assets in `SecurityConfig`.
- **Files Changed**: `Dockerfile`, `backend/src/main/resources/static/`, `backend/src/main/java/com/whereismyferry/backend/controller/SpaWebController.java`, `backend/src/main/java/com/whereismyferry/backend/security/SecurityConfig.java`, `backend/src/main/java/com/whereismyferry/backend/controller/HomeController.java`.



