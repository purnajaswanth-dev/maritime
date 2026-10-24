package com.whereismyferry.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.whereismyferry.backend.dto.LoginRequest;
import com.whereismyferry.backend.dto.UpdateProfileRequest;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import org.springframework.transaction.annotation.Transactional;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class SecurityRbacTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    private String getAccessTokenFor(String email, String password) throws Exception {
        LoginRequest loginReq = new LoginRequest(email, password);
        MvcResult result = mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(loginReq)))
                .andExpect(status().isOk())
                .andReturn();

        JsonNode json = objectMapper.readTree(result.getResponse().getContentAsString());
        return json.path("accessToken").asText();
    }

    @Test
    @DisplayName("GET /api/v1/users/me without token returns 401 Unauthorized ProblemDetail")
    void testGetProfileUnauthenticated() throws Exception {
        mockMvc.perform(get("/api/v1/users/me"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/unauthorized")))
                .andExpect(jsonPath("$.status", is(401)));
    }

    @Test
    @DisplayName("GET /api/v1/users/me with invalid token returns 401 Unauthorized ProblemDetail")
    void testGetProfileInvalidToken() throws Exception {
        mockMvc.perform(get("/api/v1/users/me")
                        .header("Authorization", "Bearer invalid.jwt.token"))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/unauthorized")));
    }

    @Test
    @DisplayName("GET /api/v1/users/me with valid token returns user profile")
    void testGetProfileAuthenticated() throws Exception {
        String token = getAccessTokenFor("passenger@whereismyferry.bzh", "PassengerPass123!");

        mockMvc.perform(get("/api/v1/users/me")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email", is("passenger@whereismyferry.bzh")))
                .andExpect(jsonPath("$.firstName", is("Yann")))
                .andExpect(jsonPath("$.roles", hasItem("ROLE_PASSENGER")));
    }

    @Test
    @DisplayName("PUT /api/v1/users/me updates profile details")
    void testUpdateProfile() throws Exception {
        String token = getAccessTokenFor("passenger@whereismyferry.bzh", "PassengerPass123!");

        UpdateProfileRequest updateReq = new UpdateProfileRequest("Yann-Aodren", "Penn-Ar-Bed", "+33612345678");

        mockMvc.perform(put("/api/v1/users/me")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updateReq)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.firstName", is("Yann-Aodren")))
                .andExpect(jsonPath("$.lastName", is("Penn-Ar-Bed")))
                .andExpect(jsonPath("$.phone", is("+33612345678")));
    }

    @Test
    @DisplayName("ROLE_PASSENGER accessing /api/v1/admin/** returns 403 Forbidden ProblemDetail")
    void testPassengerForbiddenOnAdminEndpoint() throws Exception {
        String passengerToken = getAccessTokenFor("passenger@whereismyferry.bzh", "PassengerPass123!");

        mockMvc.perform(post("/api/v1/admin/departures/generate")
                        .header("Authorization", "Bearer " + passengerToken))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/forbidden")))
                .andExpect(jsonPath("$.status", is(403)));
    }

    @Test
    @DisplayName("ROLE_ADMIN accessing /api/v1/admin/** returns 200 OK")
    void testAdminAllowedOnAdminEndpoint() throws Exception {
        String adminToken = getAccessTokenFor("admin@whereismyferry.bzh", "AdminPass123!");

        mockMvc.perform(post("/api/v1/admin/departures/generate?days=5")
                        .header("Authorization", "Bearer " + adminToken))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("SUCCESS")))
                .andExpect(jsonPath("$.departures_created", notNullValue()));
    }

    @Test
    @DisplayName("Public endpoints allow unauthenticated access")
    void testPublicEndpointsAllowUnauthenticated() throws Exception {
        mockMvc.perform(get("/api/v1/ports"))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/v1/routes"))
                .andExpect(status().isOk());

        mockMvc.perform(get("/api/v1/departures"))
                .andExpect(status().isOk());
    }
}
