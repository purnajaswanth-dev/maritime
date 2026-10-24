package com.whereismyferry.backend;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class CatalogControllerTests {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("GET /api/v1/ports returns all ports with 200 OK")
    void testGetPorts() throws Exception {
        mockMvc.perform(get("/api/v1/ports"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(7))))
                .andExpect(jsonPath("$[0].name", notNullValue()));
    }

    @Test
    @DisplayName("GET /api/v1/ports/{id} returns port details and upcoming departure/arrival boards")
    void testGetPortDetail() throws Exception {
        mockMvc.perform(get("/api/v1/ports/BREST"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id", is("BREST")))
                .andExpect(jsonPath("$.upcomingDepartures", notNullValue()))
                .andExpect(jsonPath("$.upcomingArrivals", notNullValue()));
    }

    @Test
    @DisplayName("GET /api/v1/ports/{nonexistent} returns 404 RFC 7807 ProblemDetail")
    void testGetPortNotFound() throws Exception {
        mockMvc.perform(get("/api/v1/ports/UNKNOWN_PORT"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/resource-not-found")))
                .andExpect(jsonPath("$.title", is("Resource Not Found")))
                .andExpect(jsonPath("$.status", is(404)));
    }

    @Test
    @DisplayName("GET /api/v1/routes returns all network routes")
    void testGetRoutes() throws Exception {
        mockMvc.perform(get("/api/v1/routes"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThan(0))))
                .andExpect(jsonPath("$[0].originPortId", notNullValue()))
                .andExpect(jsonPath("$[0].destinationPortId", notNullValue()));
    }

    @Test
    @DisplayName("GET /api/v1/departures returns departures with liveTrackingAvailable flag")
    void testGetDepartures() throws Exception {
        mockMvc.perform(get("/api/v1/departures"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThan(0))))
                .andExpect(jsonPath("$[0].departureCode", startsWith("DEP-")))
                .andExpect(jsonPath("$[0].liveTrackingAvailable", notNullValue()));
    }

    @Test
    @DisplayName("GET /api/v1/timetable returns timetable schedule entries")
    void testGetTimetable() throws Exception {
        mockMvc.perform(get("/api/v1/timetable"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThan(0))))
                .andExpect(jsonPath("$[0].tripId", notNullValue()))
                .andExpect(jsonPath("$[0].departureTime", notNullValue()));
    }

    @Test
    @DisplayName("GET /api/v1/fares returns fare pricing rules")
    void testGetFares() throws Exception {
        mockMvc.perform(get("/api/v1/fares"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThan(0))))
                .andExpect(jsonPath("$[0].basePriceEur", notNullValue()))
                .andExpect(jsonPath("$[0].currency", is("EUR")));
    }

    @Test
    @DisplayName("GET /api/v1/vessels returns fleet vessels")
    void testGetVessels() throws Exception {
        mockMvc.perform(get("/api/v1/vessels"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(4))))
                .andExpect(jsonPath("$[0].name", notNullValue()));
    }
}
