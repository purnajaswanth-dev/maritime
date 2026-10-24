package com.whereismyferry.backend.controller;

import com.whereismyferry.backend.entity.AuditLog;
import com.whereismyferry.backend.entity.User;
import com.whereismyferry.backend.repository.UserRepository;
import com.whereismyferry.backend.service.AdminService;
import com.whereismyferry.backend.service.DepartureGeneratorService;
import com.whereismyferry.backend.service.SystemConfigService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/admin")
@Tag(name = "Admin", description = "Administrative and Governance Operations")
@CrossOrigin(origins = "*")
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

    // 1. Overview KPIs & Service Health Tiles
    @GetMapping("/overview")
    @Operation(summary = "Get overview metrics, service health tiles, bookings and user counts")
    public ResponseEntity<Map<String, Object>> getOverview() {
        return ResponseEntity.ok(adminService.getOverview());
    }

    // 2. Simulation Lifecycle Controls
    @GetMapping("/simulation/status")
    @Operation(summary = "Get real-time simulation engine status and clock")
    public ResponseEntity<Map<String, Object>> getSimulationStatus() {
        return ResponseEntity.ok(adminService.getSimulationStatus());
    }

    @PostMapping("/simulation/control")
    @Operation(summary = "Execute simulation control action (start, pause, resume, reset, stop, speed)")
    public ResponseEntity<Map<String, Object>> controlSimulation(
            @RequestBody Map<String, Object> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        String action = (String) payload.get("action");
        Double speed = null;
        if (payload.get("speed_multiplier") instanceof Number num) {
            speed = num.doubleValue();
        }
        User user = getAuthenticatedUser(userDetails);
        Map<String, Object> result = adminService.controlSimulation(action, speed, user);
        return ResponseEntity.ok(result);
    }

    // 3. Scenario Library & Triggering
    @GetMapping("/simulation/scenarios")
    @Operation(summary = "Get scenario library (all 22 operational and adversarial scenarios)")
    public ResponseEntity<List<Map<String, Object>>> getScenarios() {
        return ResponseEntity.ok(adminService.getScenarios());
    }

    @PostMapping("/simulation/scenarios/{scenarioId}")
    @Operation(summary = "Trigger a specific operational or adversarial scenario on the simulation engine")
    public ResponseEntity<Map<String, Object>> triggerScenario(
            @PathVariable String scenarioId,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        Map<String, Object> result = adminService.triggerScenario(scenarioId, user);
        return ResponseEntity.ok(result);
    }

    // 4. ML Model Diagnostics & Residual Error Metrics
    @GetMapping("/diagnostics/ml")
    @Operation(summary = "Get ML model metadata, benchmark metrics (MAE, RMSE, MedAE), drift, and baseline comparisons")
    public ResponseEntity<Map<String, Object>> getMlDiagnostics() {
        return ResponseEntity.ok(adminService.getMlDiagnostics());
    }

    // 5. Audit Log (Append-only)
    @GetMapping("/audit-logs")
    @Operation(summary = "Get immutable system audit logs with optional action filter")
    public ResponseEntity<List<AuditLog>> getAuditLogs(@RequestParam(required = false) String action) {
        return ResponseEntity.ok(adminService.getAuditLogs(action));
    }

    // 6. User Governance
    @GetMapping("/users")
    @Operation(summary = "Get all registered users and assigned roles")
    public ResponseEntity<List<Map<String, Object>>> getUsers() {
        return ResponseEntity.ok(adminService.getUsers());
    }

    @PatchMapping("/users/{id}/role")
    @Operation(summary = "Assign a role to a user")
    public ResponseEntity<Map<String, String>> updateUserRole(
            @PathVariable Long id,
            @RequestBody Map<String, String> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        String role = payload.get("role");
        User user = getAuthenticatedUser(userDetails);
        adminService.updateUserRole(id, role, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "Role assigned"));
    }

    @PostMapping("/users/{id}/suspend")
    @Operation(summary = "Toggle user suspension status")
    public ResponseEntity<Map<String, String>> toggleUserSuspended(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = getAuthenticatedUser(userDetails);
        adminService.toggleUserSuspension(id, user);
        return ResponseEntity.ok(Map.of("status", "SUCCESS", "message", "User status updated"));
    }

    // 7. System Maintenance Mode & Feature Flags
    @GetMapping("/system/config")
    @Operation(summary = "Get current system configuration, maintenance mode state, and feature flags")
    public ResponseEntity<Map<String, Object>> getSystemConfig() {
        return ResponseEntity.ok(Map.of(
                "maintenanceMode", systemConfigService.isMaintenanceMode(),
                "maintenanceReason", systemConfigService.getMaintenanceReason(),
                "maintenanceActivatedAt", systemConfigService.getMaintenanceActivatedAt() != null ? systemConfigService.getMaintenanceActivatedAt().toString() : "",
                "maintenanceActivatedBy", systemConfigService.getMaintenanceActivatedBy(),
                "featureFlags", systemConfigService.getFeatureFlags()
        ));
    }

    @PostMapping("/system/maintenance")
    @Operation(summary = "Enable or disable global system maintenance mode")
    public ResponseEntity<Map<String, Object>> setMaintenanceMode(
            @RequestBody Map<String, Object> payload,
            @AuthenticationPrincipal UserDetails userDetails) {
        boolean enabled = Boolean.TRUE.equals(payload.get("enabled"));
        String reason = (String) payload.getOrDefault("reason", "Scheduled maritime system update");
        User user = getAuthenticatedUser(userDetails);
        systemConfigService.setMaintenanceMode(enabled, user, reason);
        return ResponseEntity.ok(Map.of(
                "status", "SUCCESS",
                "maintenanceMode", enabled,
                "reason", reason
        ));
    }

    // 8. Timetable Batch Departure Generation
    @PostMapping("/departures/generate")
    @Operation(summary = "Generate departures for upcoming days from timetable schedules")
    public ResponseEntity<Map<String, Object>> generateDepartures(
            @RequestParam(defaultValue = "60") int days) {
        int generated = departureGeneratorService.generateDepartures(days);
        return ResponseEntity.ok(Map.of(
                "status", "SUCCESS",
                "days_ahead", days,
                "departures_created", generated
        ));
    }
}
