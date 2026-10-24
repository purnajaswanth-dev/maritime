# Phase B: PostgreSQL and Authentication (Passenger and Admin) Report

## 1. Executive Summary
- **Phase Objective:** Add robust, production-grade authentication with PostgreSQL schema migrations, rotating refresh tokens with reuse detection, account lockout after 5 failed attempts (15 min), role-based access control (Passenger vs Admin/Staff), and self-service password recovery without leaking credential existence.
- **Gate Status:** **PASSED**
  - Passengers can register (`POST /api/v1/auth/register`), log in (`POST /api/v1/auth/login`), refresh sessions silently via HttpOnly cookies (`POST /api/v1/auth/refresh`), change passwords, and view profile and booked departures (`GET /api/v1/auth/me`).
  - First administrator account is seeded once from properties (`admin@example.com`).
  - Role-based route guards strictly deny passengers and anonymous users access to `/admin/**` with an explicit Unauthorized page (`/unauthorized`).
  - Verified by 57 passing Java tests, 91 passing Vitest tests, and automated Playwright E2E (`phaseB.spec.ts` in 4.7s).

---

## 2. Changes Implemented

### B1. Database Configuration & Startup Safety
- Configured `backend/src/main/resources/application.properties` with clear placeholders as mandated:
  ```properties
  spring.datasource.url=jdbc:postgresql://localhost:5432/YOUR_DATABASE_NAME
  spring.datasource.username=YOUR_DB_USERNAME
  spring.datasource.password=YOUR_DB_PASSWORD
  app.jwt.secret=CHANGE_ME_TO_A_LONG_RANDOM_SECRET_AT_LEAST_32_BYTES
  app.admin.seed.enabled=true
  app.admin.seed.email=admin@example.com
  app.admin.seed.password=CHANGE_ME_STRONG_PASSWORD
  ```
- Created `DatabasePlaceholderValidator.java` (implementing `EnvironmentPostProcessor` and `Ordered.LOWEST_PRECEDENCE`) to fail startup with a one-line error if placeholders are left unconfigured.
- Created `DatabaseConnectionFailureAnalyzer.java` for clean startup failure diagnostics when PostgreSQL is unreachable.
- Created `docs/SETUP_DATABASE.md` detailing step-by-step PostgreSQL setup, initial migration, first admin login, and password management.

### B2. Flyway Schema & Security Implementation
- Created migration `V2__auth_enhancements.sql`:
  - Enriched `users` table with `full_name`, `role` (`PASSENGER`, `ADMIN`, etc.), `status` (`ACTIVE`, `SUSPENDED`), `email_verified`, `failed_attempts`, `locked_until`, `last_login_at`.
  - Created `refresh_tokens` table with SHA-256 hashed tokens, expiry, revocation flag, and client user-agent.
  - Created `audit_log` table tracking actor, action, target, timestamp, IP, and details.
  - Created `password_reset_tokens` table.
- Upgraded `AuthService.java`:
  - Password strength validation (minimum 10 characters).
  - BCrypt password hashing (cost factor 12).
  - Account lockout after 5 consecutive failed login attempts (15-minute freeze).
  - Rotating refresh tokens: old token revoked upon refresh, reuse detection invalidates all sessions for that user.
  - Public registration restricted to `ROLE_PASSENGER` (admin accounts are never self-registered).
  - Rate limiting via `AuthRateLimiter.java`.
  - Generic authentication responses that do not reveal whether an email exists.
  - Console/log-based simulated email dispatch via `ConsoleEmailService.java`.
- Updated `SecurityConfig.java`:
  - Disallowed passenger/anonymous access to `/api/v1/admin/**`.
  - Configured method security (`@PreAuthorize`) and CORS from configurable origins.

### B3. Frontend Authentication & Route Guards
- Upgraded `frontend/src/api/client.ts`:
  - In-memory JWT access token storage (no tokens stored in localStorage).
  - Automatic silent refresh on HTTP 401 via `POST /api/v1/auth/refresh` with `credentials: 'include'` (transmitting HttpOnly refresh cookie).
  - Request queuing to avoid duplicate refresh calls when concurrent requests encounter 401.
- Updated `frontend/src/context/AuthContext.tsx`:
  - On app load, silently queries `/api/v1/auth/refresh` to restore user session without requiring re-login.
  - Full typing for `User`, `login`, `register`, `logout`, and profile refresh.
- Created Route Guards:
  - `RequireAuth.tsx`: Checks authentication; displays loading skeleton while verifying, redirects unauthenticated requests to `/login?redirect=...`.
  - `RequireRole.tsx`: Enforces required roles (`ADMIN`); redirects unauthorized users to `/unauthorized`.
- Created Frontend Pages:
  - `LoginPage.tsx`: Passenger sign-in with clean error presentation, input persistence on error, links to `/forgot-password`, `/register`, and `/admin/login`. Redirects passengers to `/account`.
  - `RegisterPage.tsx`: Passenger registration with inline validation (first name, last name, email, phone, min 10-char password, password confirmation), redirects to `/account`.
  - `AdminLoginPage.tsx`: Dedicated admin portal login; blocks non-admin roles and redirects admins to `/admin`.
  - `ForgotPasswordPage.tsx`: Dispatches password reset request with generic non-revealing confirmation.
  - `ResetPasswordPage.tsx`: Handles `?token=...` query param, validates 10-char minimum password, updates password.
  - `UnauthorizedPage.tsx`: Accessible 403 Forbidden screen with action to return home or switch accounts.
  - `AccountPage.tsx`: Displays profile details, change password form, and booked sailings with "Track my ferry" links.

---

## 3. Files Touched

| File | Change |
| --- | --- |
| `backend/src/main/resources/application.properties` | Configured properties with standard placeholders |
| `backend/src/main/resources/application-test.properties` | In-memory H2 PostgreSQL mode for test daemon runs |
| `backend/src/test/resources/application.properties` | Test properties ensuring JUnit tests run in H2 PostgreSQL mode |
| `backend/src/main/resources/db/migration/V2__auth_enhancements.sql` | Flyway schema for users, refresh tokens, audit logs |
| `backend/src/main/java/com/whereismyferry/backend/config/DatabasePlaceholderValidator.java` | Startup check for database placeholders |
| `backend/src/main/java/com/whereismyferry/backend/config/DatabaseConnectionFailureAnalyzer.java` | Clean connection failure diagnostics |
| `backend/src/main/java/com/whereismyferry/backend/entity/AuditLog.java` | Entity defaults and audit attributes |
| `backend/src/main/java/com/whereismyferry/backend/service/AuditService.java` | Added default actor, target, IP and timestamps |
| `backend/src/main/java/com/whereismyferry/backend/service/AuthService.java` | Added lockout, token rotation, password rules, `noRollbackFor` |
| `backend/src/main/java/com/whereismyferry/backend/security/AuthRateLimiter.java` | IP rate-limiter with configurable ceiling |
| `backend/src/main/java/com/whereismyferry/backend/security/SecurityConfig.java` | Separated read-only auditor/operator and admin mutation RBAC |
| `backend/src/main/java/com/whereismyferry/backend/exception/GlobalExceptionHandler.java` | Added `ResponseStatusException` handler |
| `docs/SETUP_DATABASE.md` | Guide for PostgreSQL setup, admin login, and password changes |
| `frontend/src/api/client.ts` | In-memory token management, 401 interceptor with silent refresh queue |
| `frontend/src/context/AuthContext.tsx` | In-memory session, boot silent refresh, typed auth hooks |
| `frontend/src/components/auth/RequireAuth.tsx` | Route guard protecting authenticated views |
| `frontend/src/components/auth/RequireRole.tsx` | Route guard enforcing roles and redirecting to `/unauthorized` |
| `frontend/src/pages/LoginPage.tsx` | Passenger login, /account redirection, forgot password link |
| `frontend/src/pages/RegisterPage.tsx` | Passenger registration with inline validation and 10-char password rule |
| `frontend/src/pages/AccountPage.tsx` | Passenger account page with credentials change and booked trips |
| `frontend/src/pages/auth/AdminLoginPage.tsx` | Admin login page |
| `frontend/src/pages/auth/ForgotPasswordPage.tsx` | Self-service password recovery request page |
| `frontend/src/pages/auth/ResetPasswordPage.tsx` | Password reset completion page |
| `frontend/src/pages/auth/UnauthorizedPage.tsx` | 403 Forbidden page |
| `frontend/src/components/layout/Navbar.tsx` | Added account link and role-aware navigation |
| `frontend/src/App.tsx` | Registered all auth routes and guards |
| `frontend/src/__tests__/AuthPagesAndGuards.test.tsx` | Unit tests for auth pages, validation, and route guards |
| `frontend/e2e/phaseB.spec.ts` | Playwright E2E test for complete registration, session, and role flow |

---

## 4. Test Verification Counts

| Test Suite | Passing Tests | Failures | Status |
| --- | --- | --- | --- |
| **Python (pytest)** | 115 | 0 | **PASSED** (103.31s) |
| **Java (backend JUnit / MockMvc)** | 57 | 0 | **PASSED** (34.10s) |
| **Frontend (Vitest)** | 91 | 0 | **PASSED** (5.95s) |
| **Playwright E2E (`phaseA.spec.ts`)** | 1 | 0 | **PASSED** (15.9s) |
| **Playwright E2E (`phaseB.spec.ts`)** | 1 | 0 | **PASSED** (4.7s) |

---

## 5. Gate Sign-off
- **Phase B Gate Condition:** Both account types (Passenger and Admin) can register or sign in against the backend, sessions persist across reloads via HttpOnly refresh tokens, and every role-based restriction test passes.
- **Result:** **GATE PASSED.** Ready to proceed to Phase C (Ports, ships, and timetable data model).
