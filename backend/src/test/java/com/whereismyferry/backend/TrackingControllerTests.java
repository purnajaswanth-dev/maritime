package com.whereismyferry.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.whereismyferry.backend.client.SimulationClient;
import com.whereismyferry.backend.dto.SimulationLiveDto;
import com.whereismyferry.backend.entity.Departure;
import com.whereismyferry.backend.exception.SimulationEngineUnavailableException;
import com.whereismyferry.backend.repository.DepartureRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import java.util.List;
import java.util.Map;

import static org.hamcrest.Matchers.*;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class TrackingControllerTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private DepartureRepository departureRepository;

    @Autowired
    private ObjectMapper objectMapper;

    @MockitoBean
    private SimulationClient simulationClient;

    private SimulationLiveDto buildMockLiveDto(String depCode) {
        SimulationLiveDto dto = new SimulationLiveDto();
        dto.setDepartureId(depCode);
        dto.setServiceId("DAILY_YEAR_ROUND");
        dto.setCorridor("BREST_LE_CONQUET");
        dto.setVesselId("V-FROMVEUR-SIM");
        dto.setLifecycleState("UNDERWAY");
        dto.setCurrentPosition(Map.of("latitude", 48.36, "longitude", -4.62, "speed_knots", 17.5));
        dto.setEtaPrediction(Map.of("minutes_to_arrival", 22.4, "predicted_arrival_timestamp_utc", "2026-10-24T18:00:00Z"));
        dto.setTargetBerth(Map.of("terminal_id", "LE_CONQUET", "latitude", 48.3585, "longitude", -4.7788, "radius_km", 0.5));
        dto.setConfidenceScore(0.92);
        dto.setDataSource("HISTORICAL_REPLAY");
        dto.setModelWeightsSha256("e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9");
        return dto;
    }

    @Test
    @DisplayName("GET /api/v1/departures/{id}/live returns live telemetry and ML prediction")
    void testGetLiveTrackingSuccess() throws Exception {
        Departure dep = departureRepository.findAll().stream().findFirst().orElseThrow();
        when(simulationClient.getLiveDeparture(anyString())).thenReturn(buildMockLiveDto(dep.getDepartureCode()));

        mockMvc.perform(get("/api/v1/departures/" + dep.getDepartureCode() + "/live"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.lifecycle_state", is("UNDERWAY")))
                .andExpect(jsonPath("$.data_source", is("HISTORICAL_REPLAY")))
                .andExpect(jsonPath("$.current_position.speed_knots", is(17.5)))
                .andExpect(jsonPath("$.eta_prediction.minutes_to_arrival", is(22.4)))
                .andExpect(jsonPath("$.model_weights_sha256", notNullValue()));
    }

    @Test
    @DisplayName("GET /api/v1/departures/{id}/live returns 503 ProblemDetail when Python simulation daemon is down")
    void testGetLiveTrackingDaemonOffline() throws Exception {
        Departure dep = departureRepository.findAll().stream().findFirst().orElseThrow();
        when(simulationClient.getLiveDeparture(anyString()))
                .thenThrow(new SimulationEngineUnavailableException("Python daemon is offline"));

        mockMvc.perform(get("/api/v1/departures/" + dep.getDepartureCode() + "/live"))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/simulation-unavailable")))
                .andExpect(jsonPath("$.title", is("Simulation Engine Unavailable")))
                .andExpect(jsonPath("$.status", is(503)));
    }

    @Test
    @DisplayName("GET /api/v1/departures/{id}/track returns voyage track polyline coordinates")
    void testGetVoyageTrack() throws Exception {
        Departure dep = departureRepository.findAll().stream().findFirst().orElseThrow();
        when(simulationClient.getDepartureTrack(anyString())).thenReturn(Map.of(
                "departure_id", dep.getDepartureCode(),
                "track_points", List.of(
                        Map.of("latitude", 48.3828, "longitude", -4.4855),
                        Map.of("latitude", 48.3600, "longitude", -4.6200),
                        Map.of("latitude", 48.3585, "longitude", -4.7788)
                )
        ));

        mockMvc.perform(get("/api/v1/departures/" + dep.getDepartureCode() + "/track"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.departure_id", is(dep.getDepartureCode())))
                .andExpect(jsonPath("$.track_points", hasSize(3)));
    }

    @Test
    @DisplayName("POST /api/v1/departures/{id}/share generates public token, and GET /api/v1/track/{token} resolves it")
    void testShareableLinkLifecycle() throws Exception {
        Departure dep = departureRepository.findAll().stream().findFirst().orElseThrow();
        when(simulationClient.getLiveDeparture(anyString())).thenReturn(buildMockLiveDto(dep.getDepartureCode()));

        // 1. Generate share link
        MvcResult shareResult = mockMvc.perform(post("/api/v1/departures/" + dep.getDepartureCode() + "/share?hours=12"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token", notNullValue()))
                .andExpect(jsonPath("$.shareUrl", containsString("/track/")))
                .andExpect(jsonPath("$.departureCode", is(dep.getDepartureCode())))
                .andReturn();

        JsonNode shareJson = objectMapper.readTree(shareResult.getResponse().getContentAsString());
        String token = shareJson.path("token").asText();

        // 2. Resolve public tracking link without any credentials
        mockMvc.perform(get("/api/v1/track/" + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.departureCode", is(dep.getDepartureCode())))
                .andExpect(jsonPath("$.route", notNullValue()))
                .andExpect(jsonPath("$.live.lifecycle_state", is("UNDERWAY")));
    }

    @Test
    @DisplayName("GET /api/v1/track/{invalidToken} returns 404 ProblemDetail")
    void testInvalidShareToken() throws Exception {
        mockMvc.perform(get("/api/v1/track/nonexistent_or_expired_token"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/resource-not-found")));
    }
}
