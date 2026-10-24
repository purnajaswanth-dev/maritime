package com.whereismyferry.backend;

import com.whereismyferry.backend.dto.LoginRequest;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import com.whereismyferry.backend.client.SimulationClient;
import org.junit.jupiter.api.BeforeEach;
import org.springframework.test.context.bean.override.mockito.MockitoBean;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class SecurityHardeningTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockitoBean
    private SimulationClient simulationClient;

    @BeforeEach
    void setUp() {
        when(simulationClient.isAvailable()).thenReturn(true);
    }

    @Test
    @DisplayName("Correlation ID: propagates incoming X-Correlation-Id header to response")
    void testCorrelationIdPropagation() throws Exception {
        mockMvc.perform(get("/api/v1/ports")
                        .header("X-Correlation-Id", "TEST-CORR-UUID-9876"))
                .andExpect(status().isOk())
                .andExpect(header().string("X-Correlation-Id", "TEST-CORR-UUID-9876"));
    }

    @Test
    @DisplayName("Correlation ID: generates default WIMF- UUID if incoming header is missing")
    void testCorrelationIdGeneration() throws Exception {
        mockMvc.perform(get("/api/v1/ports"))
                .andExpect(status().isOk())
                .andExpect(header().string("X-Correlation-Id", startsWith("WIMF-")));
    }

    @Test
    @DisplayName("Security Headers: enforces X-Frame-Options DENY and X-Content-Type-Options nosniff")
    void testSecurityHeadersEnforcement() throws Exception {
        mockMvc.perform(get("/api/v1/ports"))
                .andExpect(status().isOk())
                .andExpect(header().string("X-Frame-Options", "DENY"))
                .andExpect(header().string("X-Content-Type-Options", "nosniff"))
                .andExpect(header().string("Referrer-Policy", "strict-origin-when-cross-origin"));
    }

    @Test
    @DisplayName("Token Tampering: modified signature in JWT token is rejected with 401 Unauthorized")
    void testTamperedJwtRejection() throws Exception {
        String tamperedToken = "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJhZG1pbkB3aGVyZWlzbXlmZXJyeS5iemgiLCJyb2xlcyI6WyJST0xFX0FETUlOIl19.TAMPERED_INVALID_SIGNATURE";

        mockMvc.perform(get("/api/v1/admin/overview")
                        .header("Authorization", "Bearer " + tamperedToken))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/unauthorized")));
    }

    @Test
    @DisplayName("OWASP Auth Fuzzing: passenger token forbidden from executing admin mutation (403 Forbidden)")
    void testAuthorizationFuzzing() throws Exception {
        LoginRequest login = new LoginRequest("passenger@whereismyferry.bzh", "PassengerPass123!");
        var res = mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(login)))
                .andExpect(status().isOk())
                .andReturn();

        String token = objectMapper.readTree(res.getResponse().getContentAsString()).path("accessToken").asText();

        mockMvc.perform(post("/api/v1/admin/simulation/control")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"action\":\"reset\"}"))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/forbidden")));
    }

    @Test
    @DisplayName("Actuator Metrics & Health: /actuator/health is accessible and returns UP")
    void testActuatorHealth() throws Exception {
        mockMvc.perform(get("/actuator/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("UP")));
    }
}
