package com.whereismyferry.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.whereismyferry.backend.dto.LoginRequest;
import com.whereismyferry.backend.dto.CreateBookingRequestDto;
import com.whereismyferry.backend.dto.PassengerItemDto;
import com.whereismyferry.backend.entity.Departure;
import com.whereismyferry.backend.repository.DepartureRepository;
import com.whereismyferry.backend.service.DepartureGeneratorService;
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

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class BookingControllerTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private DepartureRepository departureRepository;

    @Autowired
    private DepartureGeneratorService departureGeneratorService;

    @BeforeEach
    void setUp() {
        if (departureRepository.count() == 0) {
            departureGeneratorService.generateDepartures(7);
        }
    }

    private String getPassengerToken() throws Exception {
        LoginRequest login = new LoginRequest("passenger@whereismyferry.bzh", "PassengerPass123!");
        MvcResult res = mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(login)))
                .andExpect(status().isOk())
                .andReturn();

        JsonNode json = objectMapper.readTree(res.getResponse().getContentAsString());
        return json.path("accessToken").asText();
    }

    @Test
    @DisplayName("Create booking without auth token returns 401 Unauthorized ProblemDetail")
    void testCreateBookingUnauthenticated() throws Exception {
        CreateBookingRequestDto request = new CreateBookingRequestDto();
        request.setDepartureId(1L);
        request.setContactEmail("anon@whereismyferry.bzh");
        request.setPassengers(List.of(new PassengerItemDto("Gaël", "Le Bihan", "ADULT")));

        mockMvc.perform(post("/api/v1/bookings")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/unauthorized")));
    }

    @Test
    @DisplayName("Create booking with valid token creates booking, tickets with QR code, and returns 201 Created")
    void testCreateBookingSuccess() throws Exception {
        String token = getPassengerToken();

        Departure dep = departureRepository.findAll().stream().findFirst()
                .orElseThrow(() -> new IllegalStateException("No departures found in test db"));

        CreateBookingRequestDto request = new CreateBookingRequestDto();
        request.setDepartureId(dep.getId());
        request.setContactEmail("passenger@whereismyferry.bzh");
        request.setContactPhone("+33612345678");
        request.setPassengers(List.of(
                new PassengerItemDto("Yann", "Kermorgant", "ADULT"),
                new PassengerItemDto("Soizic", "Kermorgant", "RESIDENT")
        ));

        MvcResult result = mockMvc.perform(post("/api/v1/bookings")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.bookingReference", startsWith("WIMF-")))
                .andExpect(jsonPath("$.status", is("CONFIRMED")))
                .andExpect(jsonPath("$.paymentStatus", is("PAID")))
                .andExpect(jsonPath("$.totalAmountEur", is(50.50))) // 36.00 + 14.50 = 50.50
                .andExpect(jsonPath("$.passengers", hasSize(2)))
                .andExpect(jsonPath("$.tickets", hasSize(2)))
                .andExpect(jsonPath("$.tickets[0].qrCodeData", containsString("WIMF-")))
                .andExpect(jsonPath("$.tickets[0].ticketNumber", startsWith("TKT-WIMF-")))
                .andReturn();

        JsonNode json = objectMapper.readTree(result.getResponse().getContentAsString());
        String bookingRef = json.path("bookingReference").asText();
        assertThat(bookingRef).isNotEmpty();
    }

    @Test
    @DisplayName("Get user bookings returns list of confirmed bookings for authenticated user")
    void testGetUserBookings() throws Exception {
        String token = getPassengerToken();

        Departure dep = departureRepository.findAll().stream().findFirst().orElseThrow();

        CreateBookingRequestDto req = new CreateBookingRequestDto();
        req.setDepartureId(dep.getId());
        req.setContactEmail("passenger@whereismyferry.bzh");
        req.setPassengers(List.of(new PassengerItemDto("Yann", "Kermorgant", "ADULT")));

        mockMvc.perform(post("/api/v1/bookings")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isCreated());

        mockMvc.perform(get("/api/v1/bookings")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(greaterThanOrEqualTo(1))))
                .andExpect(jsonPath("$[0].bookingReference", startsWith("WIMF-")));
    }

    @Test
    @DisplayName("Cancel booking updates status to CANCELLED and marks tickets as CANCELLED")
    void testCancelBooking() throws Exception {
        String token = getPassengerToken();

        Departure dep = departureRepository.findAll().stream()
                .filter(d -> d.getScheduledDepartureTime().isAfter(java.time.OffsetDateTime.now().plusHours(48)))
                .findFirst()
                .orElseThrow();

        CreateBookingRequestDto req = new CreateBookingRequestDto();
        req.setDepartureId(dep.getId());
        req.setContactEmail("passenger@whereismyferry.bzh");
        req.setPassengers(List.of(new PassengerItemDto("Yann", "Kermorgant", "ADULT")));

        MvcResult createRes = mockMvc.perform(post("/api/v1/bookings")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isCreated())
                .andReturn();

        String ref = objectMapper.readTree(createRes.getResponse().getContentAsString()).path("bookingReference").asText();

        mockMvc.perform(delete("/api/v1/bookings/" + ref)
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("CANCELLED")))
                .andExpect(jsonPath("$.tickets[0].status", is("CANCELLED")));
    }
}
