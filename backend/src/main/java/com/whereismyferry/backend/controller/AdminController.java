package com.whereismyferry.backend.controller;

import com.whereismyferry.backend.dto.*;
import com.whereismyferry.backend.entity.AuditLog;
import com.whereismyferry.backend.entity.User;
import com.whereismyferry.backend.repository.UserRepository;
import com.whereismyferry.backend.service.AdminService;
import com.whereismyferry.backend.service.DepartureGeneratorService;
import com.whereismyferry.backend.service.SystemConfigService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/admin")
@Tag(name = "Admin", description = "Administration & Control Portal APIs")
@CrossOrigin(origins = "*")
@PreAuthorize("hasAnyRole('ADMIN', 'AUDITOR', 'OPERATOR')")
public class AdminController {

    private final AdminService adminService;
    private final DepartureGeneratorService departureGeneratorService;
    private final SystemConfigService systemConfigService;
    private final UserRepository userRepository;

    public AdminController(
            AdminService adminService,
            DepartureGeneratorService departureGeneratorService,
            SystemConfigService systemConfigService,
            UserRepository userRepository) {
        this.adminService = adminService;
        this.departureGeneratorService = departureGeneratorService;
        this.systemConfigService = systemConfigService;
        this.userRepository = userRepository;
    }

    private User getAuthenticatedUser(UserDetails userDetails) {
        if (userDetails == null) return null;
        return userRepository.findByEmail(userDetails.getUsername()).orElse(null);
    }

    // =========================================================================
    // 1. DASHBOARD
    // =========================================================================
    @GetMapping("/dashboard")
    @Operation(summary = "Get real-time operational dashboard metrics")
    public ResponseEntity<AdminDashboardDto> getDashboard() {
        return ResponseEntity.ok(adminService.getDashboard());
    }

    @GetMapping("/overview")
    @Operation(summary = "Get overview metrics (compatibility endpoint)")
    public ResponseEntity<Map<String, Object>> getOverview() {
        return ResponseEntity.ok(adminService.getOverview());
    }

    @GetMapping("/users")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Get all registered users")
    public ResponseEntity<List<Map<String, Object>>> getUsers() {
        return ResponseEntity.ok(adminService.getUsers());
    }

    // =========================================================================
    // 2. TIMETABLE: SERVICES & DEPARTURES
    // =========================================================================
    @GetMapping("/services")
    @Operation(summary = "List operating timetable services")
    public ResponseEntity<List<AdminServiceDto>> getServices(
            @RequestParam(required = false) String routeId,
            @RequestParam(required = false) String vesselId,
            @RequestParam(required = false) Boolean active) {
        return ResponseEntity.ok(adminService.getServices(routeId, vesselId, active));
    }

    @PostMapping("/services")
    @Operation(summary = "Add a new timetable service with conflict detection and departure generation")
    public ResponseEntity<AdminServiceDto> createService(
            @Valid @RequestBody AdminServiceDto dto,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        return ResponseEntity.ok(adminService.createService(dto, user));
    }

    @PutMapping("/services/{id}")
    @Operation(summary = "Update an existing timetable service")
    public ResponseEntity<AdminServiceDto> updateService(
            @PathVariable Long id,
            @RequestBody AdminServiceDto dto,
            @RequestParam(defaultValue = "false") boolean applyToFutureWithoutBookings,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        return ResponseEntity.ok(adminService.updateService(id, dto, applyToFutureWithoutBookings, user));
    }

    @DeleteMapping("/services/{id}")
    @Operation(summary = "Delete an operating service (blocked if bookings exist)")
    public ResponseEntity<Map<String, String>> deleteService(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        adminService.deleteService(id, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Service deleted"));
    }

    @GetMapping("/departures")
    @Operation(summary = "List dated departures for administration")
    public ResponseEntity<List<DepartureSearchResultItemDto>> getDepartures(
            @RequestParam(required = false) LocalDate date,
            @RequestParam(required = false) String routeId,
            @RequestParam(required = false) String status) {
        return ResponseEntity.ok(adminService.getDepartures(date, routeId, status));
    }

    @PostMapping("/departures/{id}/delay")
    @Operation(summary = "Delay a departure by N minutes with reason and automated passenger announcement")
    public ResponseEntity<Map<String, String>> delayDeparture(
            @PathVariable Long id,
            @RequestBody Map<String, Object> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        int delay = payload.get("delayMinutes") instanceof Number n ? n.intValue() : 15;
        String reason = (String) payload.getOrDefault("reason", "Operational turnaround delay");
        User user = getAuthenticatedUser(userDetails);
        adminService.delayDeparture(id, delay, reason, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Departure delayed"));
    }

    @PostMapping("/departures/{id}/cancel")
    @Operation(summary = "Cancel a departure with reason and automated passenger announcement")
    public ResponseEntity<Map<String, String>> cancelDeparture(
            @PathVariable Long id,
            @RequestBody Map<String, Object> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        String reason = (String) payload.getOrDefault("reason", "Adverse sea state and gale warning");
        User user = getAuthenticatedUser(userDetails);
        adminService.cancelDeparture(id, reason, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Departure cancelled"));
    }

    @PostMapping("/departures/{id}/change-vessel")
    @Operation(summary = "Assign another vessel to an existing departure")
    public ResponseEntity<Map<String, String>> changeDepartureVessel(
            @PathVariable Long id,
            @RequestBody Map<String, String> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        String vesselId = payload.get("vesselId");
        User user = getAuthenticatedUser(userDetails);
        adminService.changeDepartureVessel(id, vesselId, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Vessel assigned"));
    }

    @PostMapping("/departures/generate")
    @Operation(summary = "Generate departures ahead for 60 days")
    public ResponseEntity<Map<String, Object>> generateDepartures(
            @RequestParam(defaultValue = "60") int days) {
        int count = departureGeneratorService.generateDepartures(days);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "days", days, "departures_generated", count, "departures_created", count));
    }

    // =========================================================================
    // 3. PORTS & PORT-WISE CONTROL
    // =========================================================================
    @GetMapping("/ports")
    @Operation(summary = "List all ports with status, based ships, and sailings count")
    public ResponseEntity<List<Map<String, Object>>> getPorts() {
        return ResponseEntity.ok(adminService.getPorts());
    }

    @PutMapping("/ports/{id}")
    @Operation(summary = "Update port attributes")
    public ResponseEntity<Map<String, String>> updatePort(
            @PathVariable String id,
            @RequestBody Map<String, Object> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        adminService.updatePort(id, payload, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Port updated"));
    }

    @PostMapping("/ports/{id}/status")
    @Operation(summary = "Set port status Open or Closed with reason")
    public ResponseEntity<Map<String, String>> setPortStatus(
            @PathVariable String id,
            @RequestBody Map<String, String> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        String status = payload.get("status");
        String reason = payload.get("reason");
        User user = getAuthenticatedUser(userDetails);
        adminService.setPortStatus(id, status, reason, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Port status updated"));
    }

    @GetMapping("/ports/{id}/ships")
    @Operation(summary = "Get ships based at this port and arriving/departing ships")
    public ResponseEntity<Map<String, Object>> getPortShips(@PathVariable String id) {
        return ResponseEntity.ok(adminService.getPortShips(id));
    }

    @PostMapping("/ports/{id}/ships/{shipId}/home-port")
    @Operation(summary = "Assign ship home port")
    public ResponseEntity<Map<String, String>> setShipHomePort(
            @PathVariable String id,
            @PathVariable String shipId,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        adminService.setShipHomePort(shipId, id, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Home port assigned"));
    }

    @GetMapping("/ports/{id}/departures")
    @Operation(summary = "Get today's and upcoming departures leaving this port")
    public ResponseEntity<List<Map<String, Object>>> getPortDepartures(
            @PathVariable String id,
            @RequestParam(required = false) LocalDate date) {
        return ResponseEntity.ok(adminService.getPortDepartures(id, date));
    }

    @GetMapping("/ports/{id}/arrivals")
    @Operation(summary = "Get arrivals approaching this port with live ETAs")
    public ResponseEntity<List<Map<String, Object>>> getPortArrivals(
            @PathVariable String id,
            @RequestParam(required = false) LocalDate date) {
        return ResponseEntity.ok(adminService.getPortArrivals(id, date));
    }

    @GetMapping("/ports/{id}/passengers")
    @Operation(summary = "Get all passengers booked on departures from or to this port")
    public ResponseEntity<List<Map<String, Object>>> getPortPassengers(
            @PathVariable String id,
            @RequestParam(required = false) LocalDate date) {
        return ResponseEntity.ok(adminService.getPortPassengers(id, date));
    }

    @GetMapping(value = "/ports/{id}/passengers/export-csv", produces = "text/csv")
    @Operation(summary = "Export booked passengers for a port as CSV")
    public ResponseEntity<String> exportPortPassengersCsv(
            @PathVariable String id,
            @RequestParam(required = false) LocalDate date) {
        String csv = adminService.exportPortPassengersCsv(id, date);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"port_" + id + "_passengers.csv\"")
                .contentType(MediaType.parseMediaType("text/csv"))
                .body(csv);
    }

    // =========================================================================
    // 4. SHIPS
    // =========================================================================
    @GetMapping("/ships")
    @Operation(summary = "List all ships with capacity, home port, status, and telemetry")
    public ResponseEntity<List<AdminShipDto>> getShips() {
        return ResponseEntity.ok(adminService.getShips());
    }

    @PostMapping("/ships")
    @Operation(summary = "Add a new vessel")
    public ResponseEntity<AdminShipDto> createShip(
            @RequestBody Map<String, Object> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        return ResponseEntity.ok(adminService.createShip(payload, user));
    }

    @PutMapping("/ships/{id}")
    @Operation(summary = "Update vessel details")
    public ResponseEntity<AdminShipDto> updateShip(
            @PathVariable String id,
            @RequestBody Map<String, Object> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        return ResponseEntity.ok(adminService.updateShip(id, payload, user));
    }

    @PostMapping("/ships/{id}/retire")
    @Operation(summary = "Retire a vessel")
    public ResponseEntity<Map<String, String>> retireShip(
            @PathVariable String id,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        adminService.retireShip(id, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Ship retired"));
    }

    // =========================================================================
    // 5. PASSENGERS
    // =========================================================================
    @GetMapping("/passengers")
    @Operation(summary = "Get paginated passenger directory")
    public ResponseEntity<Page<AdminPassengerDto>> getPassengers(
            @RequestParam(required = false) String search,
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(adminService.getPassengers(search, status, page, size));
    }

    @GetMapping("/passengers/{id}")
    @Operation(summary = "Get passenger details and booking history (writes audit log)")
    public ResponseEntity<AdminPassengerDto> getPassengerDetail(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        return ResponseEntity.ok(adminService.getPassengerDetail(id, user));
    }

    @PostMapping("/passengers/{id}/suspend")
    @Operation(summary = "Suspend passenger account")
    public ResponseEntity<Map<String, String>> suspendPassenger(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        adminService.togglePassengerStatus(id, "SUSPENDED", user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Passenger suspended"));
    }

    @PostMapping("/passengers/{id}/reactivate")
    @Operation(summary = "Reactivate passenger account")
    public ResponseEntity<Map<String, String>> reactivatePassenger(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        adminService.togglePassengerStatus(id, "ACTIVE", user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Passenger reactivated"));
    }

    @GetMapping(value = "/passengers/export-csv", produces = "text/csv")
    @Operation(summary = "Export all passengers as CSV")
    public ResponseEntity<String> exportPassengersCsv() {
        String csv = adminService.exportPassengersCsv();
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"passengers.csv\"")
                .contentType(MediaType.parseMediaType("text/csv"))
                .body(csv);
    }

    // =========================================================================
    // 6. ANNOUNCEMENTS
    // =========================================================================
    @GetMapping("/announcements")
    @Operation(summary = "List all administrative announcements")
    public ResponseEntity<List<AnnouncementDto>> getAnnouncements() {
        return ResponseEntity.ok(adminService.getAnnouncements());
    }

    @PostMapping("/announcements")
    @Operation(summary = "Publish an announcement")
    public ResponseEntity<AnnouncementDto> createAnnouncement(
            @Valid @RequestBody AnnouncementDto dto,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        return ResponseEntity.ok(adminService.createAnnouncement(dto, user));
    }

    @PutMapping("/announcements/{id}")
    @Operation(summary = "Edit an existing announcement")
    public ResponseEntity<AnnouncementDto> updateAnnouncement(
            @PathVariable Long id,
            @Valid @RequestBody AnnouncementDto dto,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        return ResponseEntity.ok(adminService.updateAnnouncement(id, dto, user));
    }

    @PostMapping("/announcements/{id}/end-early")
    @Operation(summary = "End announcement early")
    public ResponseEntity<Map<String, String>> endAnnouncementEarly(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        adminService.endAnnouncementEarly(id, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Announcement ended"));
    }

    @DeleteMapping("/announcements/{id}")
    @Operation(summary = "Delete an announcement")
    public ResponseEntity<Map<String, String>> deleteAnnouncement(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        adminService.deleteAnnouncement(id, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Announcement deleted"));
    }

    // =========================================================================
    // 7. LIVE ENGINE & DIAGNOSTICS
    // =========================================================================
    @GetMapping("/simulation/status")
    @Operation(summary = "Get simulation engine status and clock")
    public ResponseEntity<Map<String, Object>> getSimulationStatus() {
        return ResponseEntity.ok(adminService.getSimulationStatus());
    }

    @PostMapping("/simulation/control")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Execute simulation control action (start, pause, resume, reset, speed)")
    public ResponseEntity<Map<String, Object>> controlSimulation(
            @RequestBody Map<String, Object> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        String action = (String) payload.get("action");
        Double speed = null;
        if (payload.get("speed_multiplier") instanceof Number num) {
            speed = num.doubleValue();
        }
        User user = getAuthenticatedUser(userDetails);
        return ResponseEntity.ok(adminService.controlSimulation(action, speed, user));
    }

    @GetMapping("/simulation/scenarios")
    @Operation(summary = "Get scenario library")
    public ResponseEntity<List<Map<String, Object>>> getScenarios() {
        return ResponseEntity.ok(adminService.getScenarios());
    }

    @PostMapping("/simulation/scenarios/{scenarioId}")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Trigger a simulation scenario")
    public ResponseEntity<Map<String, Object>> triggerScenario(
            @PathVariable String scenarioId,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        return ResponseEntity.ok(adminService.triggerScenario(scenarioId, user));
    }

    @GetMapping("/diagnostics/ml")
    @Operation(summary = "Get ML model metadata and error metrics")
    public ResponseEntity<Map<String, Object>> getMlDiagnostics() {
        return ResponseEntity.ok(adminService.getMlDiagnostics());
    }

    // =========================================================================
    // 8. ADMINS & SECURITY
    // =========================================================================
    @GetMapping("/staff")
    @Operation(summary = "List all administrator accounts")
    public ResponseEntity<List<Map<String, Object>>> getStaffAdmins() {
        return ResponseEntity.ok(adminService.getStaffAdmins());
    }

    @PostMapping("/staff")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Create a new administrator account")
    public ResponseEntity<Map<String, Object>> createAdmin(
            @Valid @RequestBody CreateAdminDto dto,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        return ResponseEntity.ok(adminService.createAdmin(dto, user));
    }

    @GetMapping("/audit-logs")
    @Operation(summary = "Get immutable system audit trail")
    public ResponseEntity<List<AuditLog>> getAuditLogs(@RequestParam(required = false) String action) {
        return ResponseEntity.ok(adminService.getAuditLogs(action));
    }

    @GetMapping("/system/config")
    @Operation(summary = "Get maintenance mode state")
    public ResponseEntity<Map<String, Object>> getSystemConfig() {
        return ResponseEntity.ok(Map.of(
                "maintenanceMode", systemConfigService.isMaintenanceMode(),
                "maintenanceReason", systemConfigService.getMaintenanceReason(),
                "maintenanceActivatedAt", systemConfigService.getMaintenanceActivatedAt() != null ? systemConfigService.getMaintenanceActivatedAt().toString() : "",
                "maintenanceActivatedBy", systemConfigService.getMaintenanceActivatedBy()
        ));
    }

    @PostMapping("/system/maintenance")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Toggle system maintenance mode")
    public ResponseEntity<Map<String, Object>> setMaintenanceMode(
            @RequestBody Map<String, Object> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        boolean enabled = Boolean.TRUE.equals(payload.get("enabled"));
        String reason = (String) payload.getOrDefault("reason", "Scheduled maritime system update");
        User user = getAuthenticatedUser(userDetails);
        systemConfigService.setMaintenanceMode(enabled, user, reason);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "maintenanceMode", enabled, "reason", reason));
    }
}
