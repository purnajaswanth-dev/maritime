package com.whereismyferry.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.whereismyferry.backend.client.SimulationClient;
import com.whereismyferry.backend.dto.CreateBookingRequestDto;
import com.whereismyferry.backend.dto.LoginRequest;
import com.whereismyferry.backend.dto.PassengerItemDto;
import com.whereismyferry.backend.entity.Departure;
import com.whereismyferry.backend.entity.EtaAccuracyRecord;
import com.whereismyferry.backend.repository.AuditLogRepository;
import com.whereismyferry.backend.repository.DepartureRepository;
import com.whereismyferry.backend.repository.EtaAccuracyRecordRepository;
import com.whereismyferry.backend.service.AuditService;
import com.whereismyferry.backend.service.DepartureGeneratorService;
import com.whereismyferry.backend.service.SystemConfigService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.hamcrest.Matchers.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class AdminControllerTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private AuditLogRepository auditLogRepository;

    @Autowired
    private AuditService auditService;

    @Autowired
    private SystemConfigService systemConfigService;

    @Autowired
    private EtaAccuracyRecordRepository etaAccuracyRecordRepository;

    @Autowired
    private DepartureRepository departureRepository;

    @Autowired
    private DepartureGeneratorService departureGeneratorService;

    @MockitoBean
    private SimulationClient simulationClient;

    @BeforeEach
    void setUp() {
        if (departureRepository.count() == 0) {
            departureGeneratorService.generateDepartures(7);
        }
        systemConfigService.setMaintenanceMode(false, null, "Normal operations");
    }

    private String getToken(String email, String password) throws Exception {
        LoginRequest login = new LoginRequest(email, password);
        MvcResult res = mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(login)))
                .andExpect(status().isOk())
                .andReturn();

        JsonNode json = objectMapper.readTree(res.getResponse().getContentAsString());
        return json.path("accessToken").asText();
    }

    @Test
    @DisplayName("Role RBAC: Auditor is read-only on admin endpoints, cannot execute mutations (403 Forbidden)")
    void testAuditorReadOnlyRbac() throws Exception {
        String auditorToken = getToken("auditor@whereismyferry.bzh", "AuditorPass123!");

        // 1. Auditor can read overview
        mockMvc.perform(get("/api/v1/admin/overview")
                        .header("Authorization", "Bearer " + auditorToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.health", notNullValue()));

        // 2. Auditor can read ML diagnostics
        mockMvc.perform(get("/api/v1/admin/diagnostics/ml")
                        .header("Authorization", "Bearer " + auditorToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.modelMetadata.name", is("VectorizedRidgeETAModel")));

        // 3. Auditor CANNOT execute simulation control mutation -> 403 Forbidden
        mockMvc.perform(post("/api/v1/admin/simulation/control")
                        .header("Authorization", "Bearer " + auditorToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"action\":\"pause\"}"))
                .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("Role RBAC: Support cannot access simulation controls or user governance (403 Forbidden)")
    void testSupportRoleBoundaries() throws Exception {
        String supportToken = getToken("support@whereismyferry.bzh", "SupportPass123!");

        // Support cannot touch simulation controls
        mockMvc.perform(post("/api/v1/admin/simulation/control")
                        .header("Authorization", "Bearer " + supportToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"action\":\"start\"}"))
                .andExpect(status().isForbidden());

        // Support cannot read user governance
        mockMvc.perform(get("/api/v1/admin/users")
                        .header("Authorization", "Bearer " + supportToken))
                .andExpect(status().isForbidden());
    }

    @Test
    @DisplayName("Simulation control: valid action reaches engine, invalid action returns 422 Unprocessable Entity")
    void testSimulationControlValidation() throws Exception {
        String adminToken = getToken("admin@whereismyferry.bzh", "AdminPass123!");

        when(simulationClient.controlSimulation(anyString(), any())).thenReturn(Map.of(
                "status", "SUCCESS",
                "current_action", "pause",
                "is_running", true,
                "is_paused", true
        ));

        // 1. Valid action succeeds
        mockMvc.perform(post("/api/v1/admin/simulation/control")
                        .header("Authorization", "Bearer " + adminToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"action\":\"pause\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("SUCCESS")))
                .andExpect(jsonPath("$.is_paused", is(true)));

        // 2. Invalid action returns 422 Unprocessable Entity
        mockMvc.perform(post("/api/v1/admin/simulation/control")
                        .header("Authorization", "Bearer " + adminToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"action\":\"teleport\"}"))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/unprocessable-entity")))
                .andExpect(jsonPath("$.status", is(422)));

        // 3. Invalid speed multiplier returns 422 Unprocessable Entity
        mockMvc.perform(post("/api/v1/admin/simulation/control")
                        .header("Authorization", "Bearer " + adminToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"action\":\"speed\",\"speed_multiplier\":-5.0}"))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.status", is(422)));
    }

    @Test
    @DisplayName("Diagnostics numbers computed from fixture accuracy records match expected statistics")
    void testDiagnosticsStatisticsComputation() throws Exception {
        String adminToken = getToken("admin@whereismyferry.bzh", "AdminPass123!");

        Departure dep = departureRepository.findAll().stream().findFirst().orElseThrow();

        // Seed 3 fixture records with known errors: 2.0, 4.0, 6.0
        // Expected MAE = (2.0 + 4.0 + 6.0) / 3 = 4.0
        // Expected MedAE = 4.0
        // Expected RMSE = sqrt((4 + 16 + 36) / 3) = sqrt(56 / 3) = 4.32049...
        etaAccuracyRecordRepository.deleteAll();

        EtaAccuracyRecord r1 = new EtaAccuracyRecord();
        r1.setDeparture(dep);
        r1.setTimestampUtc(OffsetDateTime.now());
        r1.setErrorMinutes(2.0);
        r1.setPredictedMinutesToArrival(20.0);
        r1.setActualRemainingMinutes(18.0);
        etaAccuracyRecordRepository.save(r1);

        EtaAccuracyRecord r2 = new EtaAccuracyRecord();
        r2.setDeparture(dep);
        r2.setTimestampUtc(OffsetDateTime.now());
        r2.setErrorMinutes(-4.0);
        r2.setPredictedMinutesToArrival(15.0);
        r2.setActualRemainingMinutes(19.0);
        etaAccuracyRecordRepository.save(r2);

        EtaAccuracyRecord r3 = new EtaAccuracyRecord();
        r3.setDeparture(dep);
        r3.setTimestampUtc(OffsetDateTime.now());
        r3.setErrorMinutes(6.0);
        r3.setPredictedMinutesToArrival(10.0);
        r3.setActualRemainingMinutes(4.0);
        etaAccuracyRecordRepository.save(r3);

        mockMvc.perform(get("/api/v1/admin/diagnostics/ml")
                        .header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.testMetrics.mae", is(4.0)))
                .andExpect(jsonPath("$.testMetrics.medAe", is(4.0)))
                .andExpect(jsonPath("$.testMetrics.rmse", is(4.32)))
                .andExpect(jsonPath("$.testMetrics.recordCount", is(3)));
    }

    @Test
    @DisplayName("Audit log is append-only: writes entry on privileged action, rejects modifications/deletions")
    void testAuditLogAppendOnlyGuarantee() throws Exception {
        String adminToken = getToken("admin@whereismyferry.bzh", "AdminPass123!");

        long beforeCount = auditLogRepository.count();

        // 1. Privileged action triggers audit log entry
        when(simulationClient.controlSimulation(anyString(), any())).thenReturn(Map.of("status", "SUCCESS"));

        mockMvc.perform(post("/api/v1/admin/simulation/control")
                        .header("Authorization", "Bearer " + adminToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"action\":\"reset\"}"))
                .andExpect(status().isOk());

        assertThat(auditLogRepository.count()).isGreaterThan(beforeCount);

        // 2. Direct modification/deletion on AuditService throws UnsupportedOperationException
        assertThatThrownBy(() -> auditService.deleteAuditLog(1L))
                .isInstanceOf(UnsupportedOperationException.class)
                .hasMessageContaining("Audit logs are append-only");

        assertThatThrownBy(() -> auditService.updateAuditLog(1L, null))
                .isInstanceOf(UnsupportedOperationException.class)
                .hasMessageContaining("Audit logs are append-only");
    }

    @Test
    @DisplayName("Maintenance mode blocks passenger booking (503 Service Unavailable) and keeps admin access (200 OK)")
    void testMaintenanceModeEnforcement() throws Exception {
        String adminToken = getToken("admin@whereismyferry.bzh", "AdminPass123!");
        String passengerToken = getToken("passenger@whereismyferry.bzh", "PassengerPass123!");

        Departure dep = departureRepository.findAll().stream().findFirst().orElseThrow();

        // 1. Enable maintenance mode via Admin API
        mockMvc.perform(post("/api/v1/admin/system/maintenance")
                        .header("Authorization", "Bearer " + adminToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"enabled\":true,\"reason\":\"Quarterly harbor network update\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.maintenanceMode", is(true)));

        // 2. Admin access remains intact (200 OK)
        mockMvc.perform(get("/api/v1/admin/overview")
                        .header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.maintenanceMode", is(true)));

        // 3. Passenger booking is blocked with 503 Service Unavailable ProblemDetail
        CreateBookingRequestDto request = new CreateBookingRequestDto();
        request.setDepartureId(dep.getId());
        request.setContactEmail("passenger@whereismyferry.bzh");
        request.setPassengers(List.of(new PassengerItemDto("Gaël", "Le Bihan", "ADULT")));

        mockMvc.perform(post("/api/v1/bookings")
                        .header("Authorization", "Bearer " + passengerToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/maintenance-mode")))
                .andExpect(jsonPath("$.title", is("Service Unavailable - Maintenance Mode")));
    }
}
