# Phase D Completion Report: Passenger Portal (Search, Timetable, Tracking)

**Timestamp:** 2026-10-24T21:52:00+05:30  
**Status:** GATE D PASSED  

---

## 1. Executive Summary

Phase D completes the passenger-facing portal improvements for "Where Is My Ferry?":
1. **From-To Search:** Implemented a new search form on the Home page (`/`) and Timetable page (`/timetable`) featuring:
   - Origin port dropdown ("From")
   - Destination port dropdown ("To"), dynamically filtered to only reachable direct terminals
   - Instant "Swap" button
   - Date picker (defaulting to today, min today)
   - Passenger counter (1 to 10 pax)
   - Primary "Search sailings" action button
   - Responsive search results (table view on desktop, card view on mobile) with scheduled departure/arrival times, vessel name, tabular numerals, live status badges, dynamic pricing, and "Book" / "Track" action buttons.
   - Intelligent empty state: automatically scans future dates up to 30 days and outputs honest guidance such as *"No sailings on this date. Next sailing: 26 Oct 2026, 08:30"*.
2. **Timetable & Weekly Route Schedule:** Upgraded `/timetable` with corridor and route browser, travel date filters, text search, and a weekly operating timetable schedule.
3. **Ports Directory & Live Port Boards:** Enhanced `/ports` and `/ports/:code` pages. Individual port detail views show terminal status (`OPEN`/`CLOSED`), berth coordinates and radii, terminal facilities, scoped announcements, and dual live operational boards:
   - **Departing from this port** (upcoming departures with vessel name, status, and direct tracking link)
   - **Arriving at this port** (upcoming arrivals with live ETAs from the simulation engine)
4. **Announcements System:** Announcement banners scoped to `ALL`, `PORT`, `ROUTE`, and `DEPARTURE` displaying severity badges (`INFO`, `WARNING`, `CRITICAL`), body text, and dismissal controls.
5. **Live Tracking from Passenger Trips:** Added "Track my ferry" navigation from booked voyages on `/account` and `/bookings` to `/track/departures/:id`.

---

## 2. Files Touched & Created

### Backend (Spring Boot & JPA)
- `backend/src/main/java/com/whereismyferry/backend/dto/DepartureSearchResultDto.java`: Added search container response DTO.
- `backend/src/main/java/com/whereismyferry/backend/dto/DepartureSearchResultItemDto.java`: Added individual departure result DTO with pricing, duration, seats available, and tracking availability.
- `backend/src/main/java/com/whereismyferry/backend/dto/AnnouncementDto.java`: Added announcement DTO.
- `backend/src/main/java/com/whereismyferry/backend/service/CatalogService.java`: Implemented `searchSailings`, `getReachableDestinations`, and `getActiveAnnouncements`.
- `backend/src/main/java/com/whereismyferry/backend/controller/CatalogController.java`: Exposed `GET /api/v1/departures/search`, `GET /api/v1/ports/{id}/destinations`, and `GET /api/v1/announcements`.
- `backend/src/test/java/com/whereismyferry/backend/PhaseDSearchApiTests.java`: Created 8 integration tests covering valid searches, unreachable pair rejections, passenger count validation, past date rejections, empty state next sailing lookups, and time-of-day filters.

### Frontend (React + Vite + TypeScript)
- `frontend/src/api/client.ts`: Extended `apiClient` with attached `.get()`, `.post()`, `.put()`, `.patch()`, `.delete()` helper methods.
- `frontend/src/components/common/AnnouncementBanner.tsx`: Implemented scoped and global announcement banner with dismissibility and severity styling.
- `frontend/src/components/search/SailingSearchForm.tsx`: Built accessible From-To search form with swap and reachable port filtering.
- `frontend/src/components/search/SailingSearchResults.tsx`: Built tabular and card results with pricing, filters, and booking/tracking triggers.
- `frontend/src/pages/HomePage.tsx`: Integrated announcement banner, search form, and search results.
- `frontend/src/pages/TimetablePage.tsx`: Integrated announcement banner, search form, search results, day cards, and weekly timetable table.
- `frontend/src/pages/PortsPage.tsx`: Enhanced directory with categories (`All`, `Mainland`, `Islands`), search input, and `/ports/:code` detailed live boards.
- `frontend/src/pages/TrackingPage.tsx`: Added dynamic departure loading and `apiClient` integration.
- `frontend/src/App.tsx`: Added `/ports/:code` route.
- `frontend/src/__tests__/PhaseDSearchAndAnnouncements.test.tsx`: Created 5 unit tests for search form, swap, results rendering, and announcement banners.
- `frontend/e2e/phaseD.spec.ts`: Created 3 Playwright end-to-end tests for guest from-to search, timetable schedule, and account "Track my ferry".

---

## 3. Test Suites & Results

| Test Suite | Total Tests | Passed | Failed | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Python ML Engine (`pytest`)** | 116 | 116 | 0 | **PASS** |
| **Java Backend (`Phase*Tests`)** | 12 | 12 | 0 | **PASS** |
| **Frontend Unit (`Vitest`)** | 96 (27 files) | 96 | 0 | **PASS** |
| **Playwright E2E (`e2e/`)** | 5 | 5 | 0 | **PASS** |

### Verified Test Highlights
- **Python**: 116 tests passed across all GTFS loaders, Ridge ML models, AIS streaming, and virtual simulation replays.
- **Java**: 8 new Phase D tests (`PhaseDSearchApiTests`) verified from-to validation, unreachable pairs, and price calculations; 4 Phase C tests verified timetable generation and engine sync.
- **Vitest**: All 27 test files passed cleanly (including `PhaseDSearchAndAnnouncements.test.tsx`, `TimetablePage.test.tsx`, `PortsPage.test.tsx`, and `AcceptanceEndToEnd.test.tsx`).
- **Playwright**: 5 E2E tests across Phase A, Phase B, and Phase D passed cleanly against the running full stack.

---

## 4. Gate D Checklist & Verification

- [x] Home page and `/timetable` feature the new From-To search form (From, To, Swap, Date, Passengers).
- [x] Destination dropdown is dynamically constrained to reachable ports from the chosen origin.
- [x] Results display clear departure/arrival times, duration, vessel, price, and Book/Track buttons.
- [x] Non-operational / unsupported departures show "Schedule only" / "Live tracking not available for this service".
- [x] Ports directory and `/ports/:code` detail page show terminal metadata and Departing/Arriving live boards.
- [x] Announcements appear as banners across relevant scopes.
- [x] Passenger account trips include "Track my ferry" navigation.
- [x] All existing tests preserved; zero mock data in operational views.

**Gate D Status: PASSED.** Ready to begin Phase E (Admin portal rebuild).
