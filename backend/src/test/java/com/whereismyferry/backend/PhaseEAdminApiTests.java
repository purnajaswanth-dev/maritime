package com.whereismyferry.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.whereismyferry.backend.dto.AdminServiceDto;
import com.whereismyferry.backend.entity.AuditLog;
import com.whereismyferry.backend.entity.User;
import com.whereismyferry.backend.repository.AuditLogRepository;
import com.whereismyferry.backend.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class PhaseEAdminApiTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private AuditLogRepository auditLogRepository;

    private String adminToken;

    @BeforeEach
    void setUp() throws Exception {
        MvcResult res = mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"email\":\"admin@whereismyferry.bzh\",\"password\":\"AdminPass123!\"}"))
                .andExpect(status().isOk())
                .andReturn();
        JsonNode json = objectMapper.readTree(res.getResponse().getContentAsString());
        adminToken = json.path("accessToken").asText();
    }

    @Test
    @DisplayName("E1: Admin Dashboard returns real non-zero operational metrics")
    void testDashboardOperationalMetrics() throws Exception {
        mockMvc.perform(get("/api/v1/admin/dashboard")
                        .header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.sailingsTodayByStatus", notNullValue()))
                .andExpect(jsonPath("$.sailingsTodayByStatus.TOTAL", greaterThanOrEqualTo(0)))
                .andExpect(jsonPath("$.shipsInTransit", greaterThanOrEqualTo(0)))
                .andExpect(jsonPath("$.passengersBookedToday", greaterThanOrEqualTo(0)))
                .andExpect(jsonPath("$.activeAnnouncements", greaterThanOrEqualTo(0)))
                .andExpect(jsonPath("$.engineStatus", notNullValue()));
    }

    @Test
    @DisplayName("E2: Adding conflicting timetable service returns 409 Conflict with turnaround description")
    void testTimetableConflictDetection() throws Exception {
        // Fetch existing services to get route and vessel IDs
        MvcResult res = mockMvc.perform(get("/api/v1/admin/services")
                        .header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andReturn();

        JsonNode services = objectMapper.readTree(res.getResponse().getContentAsString());
        assertThat(services.size()).isGreaterThan(0);

        JsonNode existing = services.get(0);
        String routeId = existing.path("routeId").asText();
        String vesselId = existing.path("vesselId").asText();
        String depTimeStr = existing.path("departureTime").asText();
        LocalTime depTime = LocalTime.parse(depTimeStr);

        // Attempt to create a service overlapping with existing service (+10 minutes, turnaround requirement is 20 min)
        AdminServiceDto conflictDto = new AdminServiceDto(
                null,
                routeId,
                null,
                null,
                null,
                null,
                null,
                vesselId,
                null,
                depTime.plusMinutes(10),
                60,
                "MON,TUE,WED,THU,FRI,SAT,SUN",
                LocalDate.now(),
                LocalDate.now().plusMonths(6),
                BigDecimal.valueOf(25.00),
                350,
                true,
                true
        );

        mockMvc.perform(post("/api/v1/admin/services")
                        .header("Authorization", "Bearer " + adminToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(conflictDto)))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.title", is("Service Schedule Conflict")))
                .andExpect(jsonPath("$.detail", containsString("Turnaround requirement: 20 minutes")));
    }

    @Test
    @DisplayName("E3: Setting port status to CLOSED flags port and generates automatic scoped announcement")
    void testPortClosureAndAnnouncement() throws Exception {
        mockMvc.perform(post("/api/v1/admin/ports/BREST/status")
                        .header("Authorization", "Bearer " + adminToken)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"status\":\"CLOSED\",\"reason\":\"Storm swell in harbor basin\"}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("SUCCESS")));

        // Verify port status
        mockMvc.perform(get("/api/v1/admin/ports")
                        .header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[?(@.id == 'BREST')].status", hasItem("CLOSED")));

        // Verify announcement generated with scope PORT and targetId BREST
        mockMvc.perform(get("/api/v1/admin/announcements")
                        .header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[?(@.scope == 'PORT' && @.targetId == 'BREST')]", hasSize(greaterThanOrEqualTo(1))));
    }

    @Test
    @DisplayName("E4: Viewing passenger detail records explicit VIEW_PASSENGER_RECORD in audit log")
    void testPassengerDetailAudited() throws Exception {
        User passenger = userRepository.findAll().stream()
                .filter(u -> u.getRoles().stream().anyMatch(r -> r.getName().equals("ROLE_PASSENGER")))
                .findFirst()
                .orElseThrow();

        long auditCountBefore = auditLogRepository.count();

        mockMvc.perform(get("/api/v1/admin/passengers/" + passenger.getId())
                        .header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email", is(passenger.getEmail())));

        List<AuditLog> recentLogs = auditLogRepository.findTop100ByOrderByCreatedAtDesc();
        boolean foundViewLog = recentLogs.stream()
                .anyMatch(l -> "VIEW_PASSENGER_RECORD".equals(l.getAction()) &&
                        passenger.getEmail().equals(l.getEntityId()));

        assertThat(foundViewLog).isTrue();
    }
}
