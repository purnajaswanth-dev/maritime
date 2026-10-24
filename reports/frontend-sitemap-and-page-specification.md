# Frontend Sitemap & Page Specification

**Project:** Where Is My Ferry?  
**Phase:** Complete Professional Frontend Design & Local Implementation  
**Date:** 2026-10-16  
**Document:** Route Hierarchy, Layout Conventions, and Component Specification  

---

## 1. Application Layout Architecture

The application is structured into four distinct layout shells to preserve role boundaries and provide contextual navigation:

1. **`PublicLayout` (Passenger Facing):**
   - Global Deep Ocean header with brand logo, primary navigation (`Search`, `Routes`, `Destinations`, `Ports`, `Live Tracking`), search action CTA, account quick-link/login, and responsive mobile drawer.
   - Persistent Simulated Data notification banner when on tracking or demo e-commerce pages.
   - Comprehensive multi-column footer with destination directory, passenger tools, operator links, legal notices, and simulated environment badge.

2. **`TrackingLayout` (Interactive Map View):**
   - High-density header with simulation mode indicator, clock advancement controls, active vessel counter, and return-to-home link.
   - Full-bleed or split-screen interactive maritime map with responsive drawer/sidebar for vessel details, countdown timers, and lifecycle state badges.

3. **`OperatorLayout` (Maritime Fleet & Port Operations):**
   - Distinct slate/navy sidebar workspace with operator branding.
   - Operational navigation: Overview Dashboard, Fleet Management, Vessels, Route & Schedule Management, Passenger Manifest, Service Disruptions, Reports.
   - Operator status badge and organization selector.

4. **`AdminLayout` (Platform Governance & Diagnostics):**
   - Dark command header with administrative badge and system health status.
   - Admin navigation: Platform Overview, Operator Approvals, Route Registry, Simulation Engine Controls, System Diagnostics, Audit Logs.

---

## 2. Complete Application Sitemap & Route Specifications

### A. Public Passenger Discovery
| Route | Page Name | Key Components & Features |
|---|---|---|
| `/` | **Home** | Hero with prominent multi-mode search panel (Origin, Destination, Swap, Dates, Passengers), Popular Routes carousel, Featured Destinations grid, Fleet highlights, Live Tracking preview widget, Product value propositions, Travel guides entry, Footer. |
| `/search` | **Search Results** | Search query summary bar with "Edit Search" drawer, departure date quick-picker, sort/filter sidebar (Price, Duration, Operator, Departure time), Journey cards with departure/arrival, duration, amenities, fares, real-time availability indicator, empty/error/loading states. |
| `/journeys/:id` | **Journey Details** | Route summary, intermediate passage waypoints, terminal embarkation instructions, vessel profile & amenities (Wi-Fi, cafe, vehicle deck, pet area), fare class selector, availability countdown, "Continue to Passenger Details" CTA. |
| `/destinations` | **Destinations Directory** | Grid of Brittany & Atlantic island ports (Ouessant, Molène, Île de Sein, Le Conquet, Brest, Camaret) with high-quality descriptions, weather summaries, port guides, and direct route shortcuts. |
| `/destinations/:slug` | **Destination Detail** | Editorial guide, connected ports, departure schedules, tourist & boarding regulations, map snippet. |
| `/ports` | **Port Directory** | List of all terminals with coordinates, parking information, check-in cut-off times, accessibility ratings. |
| `/ports/:id` | **Port Detail** | Terminal address, map coordinates, parking/transit connections, live departures & arrivals board. |

### B. Virtual Vessel Tracking (`/track`)
| Route | Page Name | Key Components & Features |
|---|---|---|
| `/track` | **Live Fleet Map** | Interactive Leaflet/OSM maritime map, real-time vessel markers with course arrows, route polylines, terminal markers, vessel filter sidebar, persistent simulation banner, speed multiplier indicator. |
| `/track/vessels/:id` | **Vessel Tracking Detail** | Split map view focusing on active vessel, authoritative countdown timer, dynamic lifecycle state badge (`ESTIMATING`, `STALE_DATA`, `DELAYED_OR_UNCERTAIN`, `ARRIVAL_PENDING_CONFIRMATION`, `ARRIVED`), telemetry freshness, SOG/COG metrics, route progress bar, post-arrival protection indicator. |

### C. Booking & E-Commerce Flow
| Route | Page Name | Key Components & Features |
|---|---|---|
| `/booking/passenger-info` | **Step 1: Passenger Info** | Lead passenger form, additional travelers, vehicle details (car/motorcycle/bicycle), pet registration, accessibility accommodations. |
| `/booking/addons` | **Step 2: Amenities & Add-ons** | Cabin selection, priority boarding, baggage allowance, onboard dining vouchers, carbon offset. |
| `/booking/review` | **Step 3: Review & Summary** | Journey recap, itemized price breakdown (base fare, port taxes, add-ons, promo code field), traveler details verification. |
| `/booking/checkout` | **Step 4: Demo Checkout** | Clearly labeled **SIMULATED DEMO PAYMENT**, mock card form with preset test cards, instant validation, terms agreement checkbox. |
| `/booking/confirmation` | **Step 5: Confirmation** | Booking reference number (`WMF-XXXXXX`), downloadable/printable PDF ticket view, QR code presentation, calendar export, "Track Your Ferry" link. |

### D. Customer Account Portal
| Route | Page Name | Key Components & Features |
|---|---|---|
| `/login` | **Sign In** | Email/password form, demo user quick-fill buttons (Passenger, Operator, Admin), password reset link. |
| `/register` | **Create Account** | Registration form, newsletter toggle, terms acceptance. |
| `/account` | **Account Overview** | Customer dashboard, upcoming journey card, quick actions, frequent passenger status. |
| `/account/trips` | **Booking History** | Filterable list of upcoming and past voyages, ticket downloads, rescheduling/cancellation demo request. |
| `/account/bookings/:id` | **Trip Detail & Digital Ticket** | Full itinerary, boarding pass QR code, baggage receipts, refund status timeline. |
| `/account/profile` | **Profile & Preferences** | Contact information, preferred routes, travel companions, saved vehicles, notification settings. |

### E. Operator Portal (`/operator`)
| Route | Page Name | Key Components & Features |
|---|---|---|
| `/operator` | **Dashboard** | Fleet status metrics (vessels at sea, docked, delayed), today's departures count, passenger volume gauge, active alerts. |
| `/operator/fleet` | **Fleet Management** | List of operator vessels, technical specs, maintenance status, active assignment. |
| `/operator/vessels/:id` | **Vessel Profile** | Capacity breakdown, engine status, AIS transponder info, crew allocation. |
| `/operator/schedules` | **Schedule Management** | Calendar grid of scheduled crossings, timetable editor, seasonal adjustments. |
| `/operator/manifest` | **Passenger Manifest** | Passenger count per crossing, checked-in vs boarded, vehicle loading balance, export to CSV. |
| `/operator/disruptions` | **Service Disruptions** | Issue incident notices (weather, mechanical, tidal), broadcast passenger SMS/email alerts, delay adjustment. |

### F. Admin Portal (`/admin`)
| Route | Page Name | Key Components & Features |
|---|---|---|
| `/admin` | **System Overview** | Platform KPI metrics, active simulations, server status, database health, recent error logs. |
| `/admin/operators` | **Operator Governance** | List of registered ferry lines, license verification, compliance status. |
| `/admin/routes` | **Port & Route Registry** | Master geospatial corridor definitions, terminal geofences, waypoint coordinator. |
| `/admin/simulation` | **Virtual Simulation Controls** | Trigger any of the 22 Phase 08 scenarios, adjust simulation speed (1x to 50x), inject network drops, force dock dwell, inspect live diagnostics. |
| `/admin/diagnostics` | **ML & Engine Diagnostics** | Inspect Ridge ETA predictions vs baselines, jump frequency monitors, telemetry freshness graphs, raw log viewer. |

### G. Shared Support & Error Pages
| Route | Page Name | Key Components & Features |
|---|---|---|
| `/help` | **Help Centre** | Searchable knowledge base, FAQs (booking, baggage, pet travel, refund policy), contact support form. |
| `/terms` | **Terms & Conditions** | Clear demonstration disclaimer and passenger travel conditions placeholder. |
| `/privacy` | **Privacy Policy** | Data protection disclosures. |
| `/404` | **Page Not Found** | Maritime-themed error page with quick links to return home or search. |
| `/unauthorized` | **Access Denied** | Role-based restriction notice for operator or admin paths. |
