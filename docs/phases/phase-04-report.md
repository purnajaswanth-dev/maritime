# Phase 4 Report: Authentication & RBAC

**Date:** 2026-10-24  
**Author:** Antigravity Full-Stack Agent  
**Status:** GATE PASSED  

---

## 1. Executive Summary

Phase 4 established the complete security, authentication, and role-based access control (RBAC) infrastructure for Where Is My Ferry. The system implements stateless JWT authentication with short-lived access tokens (15 minutes), rotating long-lived refresh tokens (7 days) via secure HttpOnly cookies, BCrypt password hashing (strength 12), and role-based path protections with RFC 7807 problem details for 401, 403, 409, and 422 error states.

All 14 new Java authentication and RBAC tests pass, and all 15 Phase 3 tests + 115 Python tests continue to pass with zero regressions (144 total tests passing across both tiers).

---

## 2. Deliverables Built

### A. Security Configuration & Infrastructure (`com.whereismyferry.backend.security`)
- **`SecurityConfig.java`**:
  - Stateless session management (`SessionCreationPolicy.STATELESS`).
  - CSRF disabled for stateless REST endpoints; CORS configured for web clients.
  - BCrypt password encoder with work factor 12.
  - Route authorization rules:
    - **Public**: `/api/v1/auth/**`, `/api/v1/ports/**`, `/api/v1/routes/**`, `/api/v1/departures/**`, `/api/v1/timetable/**`, `/api/v1/fares/**`, `/api/v1/vessels/**`, `/swagger-ui/**`, `/v3/api-docs/**`, `/actuator/**`.
    - **Authenticated Passenger**: `/api/v1/users/me`, `/api/v1/bookings/**`.
    - **Admin**: `/api/v1/admin/**` (`hasRole('ADMIN')`).
    - **Operator**: `/api/v1/operator/**`, `/api/v1/disruptions/**` (`hasAnyRole('ADMIN', 'OPERATOR')`).
    - **Crew**: `/api/v1/crew/**` (`hasAnyRole('ADMIN', 'OPERATOR', 'CREW')`).
- **`JwtService.java`**:
  - HMAC-SHA256 signature verification with configurable secret (`jwt.secret`).
  - Access token validity: 900 seconds (15 minutes), containing subject, user ID, and granted roles.
  - Refresh token validity: 604,800 seconds (7 days).
- **`JwtAuthenticationFilter.java`**:
  - Intercepts requests, parses `Authorization: Bearer <token>`, validates claims against `CustomUserDetailsService`, and populates `SecurityContextHolder`.
- **`DelegatedAuthenticationEntryPoint.java` & `DelegatedAccessDeniedHandler.java`**:
  - Converts unauthenticated requests (401) and insufficient permission requests (403) into RFC 7807 `application/problem+json` ProblemDetails (`https://whereismyferry.bzh/problems/unauthorized`, `https://whereismyferry.bzh/problems/forbidden`).

### B. Seed Accounts & Roles (`DatabaseSeederService.java`)
- Automated startup seeding of 4 canonical system accounts with BCrypt-hashed credentials:
  1. **Admin**: `admin@whereismyferry.bzh` / `AdminPass123!` (Roles: `ROLE_ADMIN`, `ROLE_OPERATOR`, `ROLE_PASSENGER`)
  2. **Operator**: `operator@whereismyferry.bzh` / `OperatorPass123!` (Roles: `ROLE_OPERATOR`, `ROLE_PASSENGER`)
  3. **Crew**: `crew@whereismyferry.bzh` / `CrewPass123!` (Roles: `ROLE_CREW`, `ROLE_PASSENGER`)
  4. **Passenger**: `passenger@whereismyferry.bzh` / `PassengerPass123!` (Roles: `ROLE_PASSENGER`)

### C. Authentication & Profile Endpoints (`AuthController.java`, `UserController.java`)
- **`POST /api/v1/auth/register`**: Registers new passenger with duplicate email rejection (409 Conflict), input validation (422), returns access token, user summary, and sets HttpOnly `refreshToken` cookie.
- **`POST /api/v1/auth/login`**: Authenticates credentials, returns JWT tokens and sets HttpOnly `refreshToken` cookie.
- **`POST /api/v1/auth/refresh`**: Accepts refresh token via JSON body or HttpOnly cookie, performs token rotation, and issues fresh access and refresh tokens.
- **`POST /api/v1/auth/logout`**: Clears the refresh token cookie and terminates the session.
- **`GET /api/v1/users/me`**: Returns profile for authenticated user.
- **`PUT /api/v1/users/me`**: Updates first name, last name, and phone number for authenticated user.

### D. OpenAPI Security Integration (`OpenApiConfig.java`)
- Documented Bearer HTTP authentication scheme in OpenAPI 3.0 specification for Swagger UI testing.

---

## 3. Test Suites & Verification

### Test Counts
| Suite | Passed | Failed | Skipped | Time |
| :--- | :---: | :---: | :---: | :---: |
| **Python ML Platform (`pytest`)** | 115 | 0 | 0 | ~140s |
| **Java Spring Boot Backend (`mvn test`)** | 29 | 0 | 0 | ~28s |
| **Total Test Count** | **144** | **0** | **0** | **~168s** |

### Verified Test Cases
- `AuthControllerTests`:
  - `testRegisterPassenger`: 201 Created with JWT tokens and HttpOnly cookie.
  - `testRegisterDuplicateEmail`: 409 Conflict ProblemDetail.
  - `testRegisterValidationFailure`: 422 Unprocessable Entity ProblemDetail for short password.
  - `testLoginSuccess`: 200 OK with correct role grants for seed user.
  - `testLoginBadPassword`: 401 Unauthorized ProblemDetail for invalid password.
  - `testRefreshTokenRotation`: Rotating tokens via body or cookie.
  - `testLogout`: Cookie invalidation.
- `SecurityRbacTests`:
  - `testGetProfileUnauthenticated`: 401 Unauthorized ProblemDetail when token missing.
  - `testGetProfileInvalidToken`: 401 Unauthorized ProblemDetail when token invalid.
  - `testGetProfileAuthenticated`: 200 OK returning user profile.
  - `testUpdateProfile`: 200 OK updating user attributes.
  - `testPassengerForbiddenOnAdminEndpoint`: 403 Forbidden ProblemDetail for unauthorized role.
  - `testAdminAllowedOnAdminEndpoint`: 200 OK for authorized admin role.
  - `testPublicEndpointsAllowUnauthenticated`: Public catalog routes accessible without credentials.

---

## 4. Deviations & Observations

- None. Implementation adhered strictly to the master build prompt specifications.

---

## 5. Gate Checklist

- [x] Spring Security configured with stateless JWT authentication filter
- [x] BCrypt (strength 12) password hashing implemented
- [x] Access tokens (15m) and refresh tokens (7d) with HttpOnly cookie support
- [x] 4 system roles (`ROLE_PASSENGER`, `ROLE_ADMIN`, `ROLE_OPERATOR`, `ROLE_CREW`) configured
- [x] 4 seed accounts created on startup
- [x] Register, login, refresh, logout, and profile endpoints operational
- [x] RFC 7807 ProblemDetails returned for 401, 403, 409, and 422 errors
- [x] 29 Java tests passing (14 new + 15 existing)
- [x] 115 Python tests passing with zero regressions
- [x] `docs/phases/phase-04-report.md` written
