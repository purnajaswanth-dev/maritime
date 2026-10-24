package com.whereismyferry.backend;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.whereismyferry.backend.client.SimulationClient;
import com.whereismyferry.backend.dto.VesselLiveDto;
import com.whereismyferry.backend.entity.Departure;
import com.whereismyferry.backend.exception.SimulationEngineUnavailableException;
import com.whereismyferry.backend.repository.DepartureRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.is;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class VesselContractTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private DepartureRepository departureRepository;

    @MockitoBean
    private SimulationClient simulationClient;

    private static final String ENGINE_SNAPSHOT_FIXTURE = """
        [
          {
            "vessel_id": "V-FROMVEUR-SIM",
            "synthetic_mmsi": 228037700,
            "name": "Fromveur II",
            "operator": "Penn ar Bed",
            "corridor": "BREST_LE_CONQUET",
            "origin_terminal_id": "BREST",
            "destination_terminal_id": "LE_CONQUET",
            "lat": 48.3751,
            "lon": -4.6202,
            "sog_knots": 15.6,
            "cog_degrees": 265.4,
            "eta_lifecycle_state": "UNDERWAY",
            "position_timestamp_utc": "2026-10-24T18:00:00Z",
            "prediction_timestamp_utc": "2026-10-24T18:00:00Z",
            "predicted_arrival_utc": "2026-10-24T18:35:00Z",
            "estimated_remaining_minutes": 22.4,
            "uncertainty_lower_minutes": 1.5,
            "uncertainty_upper_minutes": 4.8,
            "distance_remaining_km": 10.2,
            "distance_remaining_nm": 5.5,
            "telemetry_age_seconds": 1.2,
            "is_stale": false,
            "is_arrived": false,
            "data_provenance": "HISTORICAL_REPLAY",
            "model_weights_sha256": "e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9"
          }
        ]
        """;

    @Test
    @DisplayName("Contract test: Engine JSON fleet snapshot maps completely to Java VesselLiveDto")
    void testEngineJsonContractMapping() throws Exception {
        VesselLiveDto[] vessels = objectMapper.readValue(ENGINE_SNAPSHOT_FIXTURE, VesselLiveDto[].class);

        assertThat(vessels).hasSize(1);
        VesselLiveDto v = vessels[0];

        assertThat(v.getVesselId()).isEqualTo("V-FROMVEUR-SIM");
        assertThat(v.getSyntheticMmsi()).isEqualTo(228037700L);
        assertThat(v.getName()).isEqualTo("Fromveur II");
        assertThat(v.getOperator()).isEqualTo("Penn ar Bed");
        assertThat(v.getCorridor()).isEqualTo("BREST_LE_CONQUET");
        assertThat(v.getOriginTerminalId()).isEqualTo("BREST");
        assertThat(v.getDestinationTerminalId()).isEqualTo("LE_CONQUET");
        assertThat(v.getLat()).isEqualTo(48.3751);
        assertThat(v.getLon()).isEqualTo(-4.6202);
        assertThat(v.getSogKnots()).isEqualTo(15.6);
        assertThat(v.getCogDegrees()).isEqualTo(265.4);
        assertThat(v.getEtaLifecycleState()).isEqualTo("UNDERWAY");
        assertThat(v.getPositionTimestampUtc()).isEqualTo("2026-10-24T18:00:00Z");
        assertThat(v.getPredictionTimestampUtc()).isEqualTo("2026-10-24T18:00:00Z");
        assertThat(v.getPredictedArrivalUtc()).isEqualTo("2026-10-24T18:35:00Z");
        assertThat(v.getEstimatedRemainingMinutes()).isEqualTo(22.4);
        assertThat(v.getUncertaintyLowerMinutes()).isEqualTo(1.5);
        assertThat(v.getUncertaintyUpperMinutes()).isEqualTo(4.8);
        assertThat(v.getDistanceRemainingKm()).isEqualTo(10.2);
        assertThat(v.getDistanceRemainingNm()).isEqualTo(5.5);
        assertThat(v.getTelemetryAgeSeconds()).isEqualTo(1.2);
        assertThat(v.getIsStale()).isFalse();
        assertThat(v.getIsArrived()).isFalse();
        assertThat(v.getDataProvenance()).isEqualTo("HISTORICAL_REPLAY");
        assertThat(v.getModelWeightsSha256()).isEqualTo("e4da4af5cf8a5e7b31337ca9ae9e37740a9062ccdc584b8c3aad69deb0f6d9e9");
    }

    @Test
    @DisplayName("GET /api/v1/stream/vessels returns 200 text/event-stream")
    void testFleetVesselStreamEndpoint() throws Exception {
        VesselLiveDto[] vessels = objectMapper.readValue(ENGINE_SNAPSHOT_FIXTURE, VesselLiveDto[].class);
        when(simulationClient.isAvailable()).thenReturn(true);
        when(simulationClient.getFleetVessels()).thenReturn(List.of(vessels));

        mockMvc.perform(get("/api/v1/stream/vessels"))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("When simulation daemon is offline, getFleetVessels and departures return 503 ProblemDetail")
    void testDaemonOfflineReturns503() throws Exception {
        when(simulationClient.isAvailable()).thenReturn(false);
        when(simulationClient.getLiveDeparture(anyString()))
                .thenThrow(new SimulationEngineUnavailableException("Python daemon is offline"));

        mockMvc.perform(get("/api/v1/departures/DEP-20241024-BES-LCQ-0830/live"))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.status", is(503)))
                .andExpect(jsonPath("$.title", is("Simulation Engine Unavailable")));

        mockMvc.perform(get("/api/v1/stream/vessels"))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.status", is(503)))
                .andExpect(jsonPath("$.title", is("Simulation Engine Unavailable")));
    }
}
