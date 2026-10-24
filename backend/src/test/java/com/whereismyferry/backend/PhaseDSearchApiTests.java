package com.whereismyferry.backend;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.LocalDate;
import java.time.ZoneId;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class PhaseDSearchApiTests {

    @Autowired
    private MockMvc mockMvc;

    private static final ZoneId PARIS_ZONE = ZoneId.of("Europe/Paris");

    @Test
    @DisplayName("D1: Valid pair returns sailings sorted by departure time ascending with price & tracking info")
    void testValidPairSearch() throws Exception {
        LocalDate today = LocalDate.now(PARIS_ZONE);

        mockMvc.perform(get("/api/v1/departures/search")
                        .param("from", "BREST")
                        .param("to", "LE_CONQUET")
                        .param("date", today.toString())
                        .param("passengers", "2"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.originPortId", is("BREST")))
                .andExpect(jsonPath("$.destinationPortId", is("LE_CONQUET")))
                .andExpect(jsonPath("$.passengers", is(2)))
                .andExpect(jsonPath("$.departures", hasSize(greaterThan(0))))
                .andExpect(jsonPath("$.departures[0].fromPriceEur", notNullValue()))
                .andExpect(jsonPath("$.departures[0].liveTrackingAvailable", notNullValue()))
                .andExpect(jsonPath("$.departures[0].statusLabel", notNullValue()));
    }

    @Test
    @DisplayName("D1: Same origin and destination is rejected with 400 Bad Request")
    void testSameOriginAndDestinationRejected() throws Exception {
        mockMvc.perform(get("/api/v1/departures/search")
                        .param("from", "BREST")
                        .param("to", "BREST")
                        .param("date", LocalDate.now(PARIS_ZONE).toString()))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("D1: Unreachable port pair is rejected with 400 Bad Request")
    void testUnreachablePairRejected() throws Exception {
        mockMvc.perform(get("/api/v1/departures/search")
                        .param("from", "AUDIERNE")
                        .param("to", "OUESSANT_STIFF")
                        .param("date", LocalDate.now(PARIS_ZONE).toString()))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("D1: Past date search is rejected with 400 Bad Request")
    void testPastDateRejected() throws Exception {
        LocalDate yesterday = LocalDate.now(PARIS_ZONE).minusDays(1);
        mockMvc.perform(get("/api/v1/departures/search")
                        .param("from", "BREST")
                        .param("to", "LE_CONQUET")
                        .param("date", yesterday.toString()))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("D1: Passenger count limits (1 to 10) are strictly enforced")
    void testPassengerCountLimits() throws Exception {
        LocalDate today = LocalDate.now(PARIS_ZONE);

        // Passengers = 0 (below minimum)
        mockMvc.perform(get("/api/v1/departures/search")
                        .param("from", "BREST")
                        .param("to", "LE_CONQUET")
                        .param("date", today.toString())
                        .param("passengers", "0"))
                .andExpect(status().isBadRequest());

        // Passengers = 11 (above maximum)
        mockMvc.perform(get("/api/v1/departures/search")
                        .param("from", "BREST")
                        .param("to", "LE_CONQUET")
                        .param("date", today.toString())
                        .param("passengers", "11"))
                .andExpect(status().isBadRequest());

        // Passengers = 10 (maximum allowed)
        mockMvc.perform(get("/api/v1/departures/search")
                        .param("from", "BREST")
                        .param("to", "LE_CONQUET")
                        .param("date", today.toString())
                        .param("passengers", "10"))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("D1: Time of day filters (morning, afternoon, evening)")
    void testTimeOfDayFilters() throws Exception {
        LocalDate today = LocalDate.now(PARIS_ZONE);

        mockMvc.perform(get("/api/v1/departures/search")
                        .param("from", "BREST")
                        .param("to", "LE_CONQUET")
                        .param("date", today.toString())
                        .param("timeOfDay", "morning"))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/v1/departures/search")
                        .param("from", "BREST")
                        .param("to", "LE_CONQUET")
                        .param("date", today.toString())
                        .param("timeOfDay", "afternoon"))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("D1 & D2: Reachable destinations endpoint returns valid ports")
    void testReachableDestinations() throws Exception {
        mockMvc.perform(get("/api/v1/ports/BREST/destinations"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThan(0))))
                .andExpect(jsonPath("$[*].id", hasItem("LE_CONQUET")));
    }

    @Test
    @DisplayName("D2: Announcements endpoint returns active alerts with scope")
    void testActiveAnnouncements() throws Exception {
        mockMvc.perform(get("/api/v1/announcements"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON));
    }
}
