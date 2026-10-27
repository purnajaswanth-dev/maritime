package com.whereismyferry.backend;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.whereismyferry.backend.client.SimulationClient;
import com.whereismyferry.backend.dto.RouteGeometryDto;
import com.whereismyferry.backend.exception.SimulationEngineUnavailableException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class RouteGeometryContractTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private com.whereismyferry.backend.service.TrackingService trackingService;

    @MockitoBean
    private SimulationClient simulationClient;

    @org.junit.jupiter.api.BeforeEach
    void setUp() {
        trackingService.clearRouteGeometriesCache();
    }

    private static final String ENGINE_ROUTES_FIXTURE = """
        [
          {
            "id": "BREST_LE_CONQUET",
            "name": "Brest - Le Conquet Water Corridor",
            "origin_terminal_id": "BREST",
            "destination_terminal_id": "LE_CONQUET",
            "polyline": [
              [48.38218, -4.48563],
              [48.382, -4.486],
              [48.3585, -4.7788]
            ],
            "length_km": 29.65,
            "great_circle_km": 21.83
          }
        ]
        """;

    @Test
    @DisplayName("Contract test: Engine JSON routes payload maps completely to Java RouteGeometryDto")
    void testEngineJsonContractMapping() throws Exception {
        RouteGeometryDto[] routes = objectMapper.readValue(ENGINE_ROUTES_FIXTURE, RouteGeometryDto[].class);

        assertThat(routes).hasSize(1);
        RouteGeometryDto r = routes[0];

        assertThat(r.getId()).isEqualTo("BREST_LE_CONQUET");
        assertThat(r.getName()).isEqualTo("Brest - Le Conquet Water Corridor");
        assertThat(r.getOriginTerminalId()).isEqualTo("BREST");
        assertThat(r.getDestinationTerminalId()).isEqualTo("LE_CONQUET");
        assertThat(r.getPolyline()).hasSize(3);
        assertThat(r.getPolyline().get(0)).containsExactly(48.38218, -4.48563);
        assertThat(r.getLengthKm()).isEqualTo(29.65);
        assertThat(r.getGreatCircleKm()).isEqualTo(21.83);
    }

    @Test
    @DisplayName("GET /api/v1/routes/geometry returns route geometries list")
    void testGetRouteGeometriesSuccess() throws Exception {
        RouteGeometryDto dto = new RouteGeometryDto(
                "BREST_LE_CONQUET",
                "Brest - Le Conquet Water Corridor",
                "BREST",
                "LE_CONQUET",
                List.of(
                        List.of(48.38218, -4.48563),
                        List.of(48.382, -4.486),
                        List.of(48.3585, -4.7788)
                ),
                29.65,
                21.83
        );
        when(simulationClient.getRouteGeometries()).thenReturn(List.of(dto));

        mockMvc.perform(get("/api/v1/routes/geometry"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].id", is("BREST_LE_CONQUET")))
                .andExpect(jsonPath("$[0].name", is("Brest - Le Conquet Water Corridor")))
                .andExpect(jsonPath("$[0].origin_terminal_id", is("BREST")))
                .andExpect(jsonPath("$[0].destination_terminal_id", is("LE_CONQUET")))
                .andExpect(jsonPath("$[0].polyline", hasSize(3)))
                .andExpect(jsonPath("$[0].polyline[0][0]", is(48.38218)))
                .andExpect(jsonPath("$[0].polyline[0][1]", is(-4.48563)))
                .andExpect(jsonPath("$[0].length_km", is(29.65)))
                .andExpect(jsonPath("$[0].great_circle_km", is(21.83)));
    }

    @Test
    @DisplayName("GET /api/v1/routes/geometry returns 503 ProblemDetail when Python daemon is offline")
    void testGetRouteGeometriesDaemonOffline() throws Exception {
        when(simulationClient.getRouteGeometries())
                .thenThrow(new SimulationEngineUnavailableException("Simulation engine unavailable"));

        mockMvc.perform(get("/api/v1/routes/geometry"))
                .andExpect(status().isServiceUnavailable())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/simulation-unavailable")))
                .andExpect(jsonPath("$.title", is("Simulation Engine Unavailable")))
                .andExpect(jsonPath("$.status", is(503)));
    }
}
