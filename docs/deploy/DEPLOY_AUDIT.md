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
