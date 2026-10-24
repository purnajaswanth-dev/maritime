package com.whereismyferry.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.whereismyferry.backend.dto.LoginRequest;
import com.whereismyferry.backend.dto.RefreshTokenRequest;
import com.whereismyferry.backend.dto.RegisterRequest;
import jakarta.servlet.http.Cookie;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class AuthControllerTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("Register new passenger account returns 201 with JWT and sets refresh cookie")
    void testRegisterPassenger() throws Exception {
        RegisterRequest request = new RegisterRequest(
                "newpassenger@iroise.bzh",
                "Password123!",
                "Malo",
                "Kerjean",
                "+33298000000"
        );

        MvcResult result = mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.accessToken", notNullValue()))
                .andExpect(jsonPath("$.refreshToken", notNullValue()))
                .andExpect(jsonPath("$.tokenType", is("Bearer")))
                .andExpect(jsonPath("$.user.email", is("newpassenger@iroise.bzh")))
                .andExpect(jsonPath("$.user.roles", hasItem("ROLE_PASSENGER")))
                .andExpect(cookie().exists("refreshToken"))
                .andExpect(cookie().httpOnly("refreshToken", true))
                .andReturn();

        JsonNode json = objectMapper.readTree(result.getResponse().getContentAsString());
        assertThat(json.path("accessToken").asText()).isNotEmpty();
    }

    @Test
    @DisplayName("Duplicate registration with existing email returns 409 Conflict")
    void testRegisterDuplicateEmail() throws Exception {
        RegisterRequest request = new RegisterRequest(
                "passenger@whereismyferry.bzh",
                "SomePassword123!",
                "Existing",
                "User",
                null
        );

        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/conflict")))
                .andExpect(jsonPath("$.title", is("Conflict")));
    }

    @Test
    @DisplayName("Register with short password (<8 chars) returns 422 Unprocessable Entity")
    void testRegisterValidationFailure() throws Exception {
        RegisterRequest request = new RegisterRequest(
                "shortpass@iroise.bzh",
                "short",
                "Test",
                "User",
                null
        );

        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/validation-error")))
                .andExpect(jsonPath("$.errors", notNullValue()));
    }

    @Test
    @DisplayName("Login with valid seed user credentials returns 200 and JWT")
    void testLoginSuccess() throws Exception {
        LoginRequest request = new LoginRequest(
                "admin@whereismyferry.bzh",
                "AdminPass123!"
        );

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken", notNullValue()))
                .andExpect(jsonPath("$.refreshToken", notNullValue()))
                .andExpect(jsonPath("$.user.roles", hasItems("ROLE_ADMIN", "ROLE_OPERATOR", "ROLE_PASSENGER")))
                .andExpect(cookie().exists("refreshToken"));
    }

    @Test
    @DisplayName("Login with incorrect password returns 401 Unauthorized ProblemDetail")
    void testLoginBadPassword() throws Exception {
        LoginRequest request = new LoginRequest(
                "admin@whereismyferry.bzh",
                "WrongPassword123!"
        );

        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.type", is("https://whereismyferry.bzh/problems/bad-credentials")))
                .andExpect(jsonPath("$.title", is("Bad Credentials")));
    }

    @Test
    @DisplayName("Refresh token rotation returns new access and refresh tokens")
    void testRefreshTokenRotation() throws Exception {
        // First login to get refresh token
        LoginRequest loginReq = new LoginRequest("passenger@whereismyferry.bzh", "PassengerPass123!");
        MvcResult loginResult = mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(loginReq)))
                .andExpect(status().isOk())
                .andReturn();

        JsonNode loginJson = objectMapper.readTree(loginResult.getResponse().getContentAsString());
        String initialRefresh = loginJson.path("refreshToken").asText();

        // Refresh via body
        RefreshTokenRequest refreshReq = new RefreshTokenRequest(initialRefresh);
        mockMvc.perform(post("/api/v1/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(refreshReq)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken", notNullValue()))
                .andExpect(jsonPath("$.refreshToken", notNullValue()));

        // Also test refresh via cookie
        Cookie cookie = new Cookie("refreshToken", initialRefresh);
        mockMvc.perform(post("/api/v1/auth/refresh")
                        .cookie(cookie))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken", notNullValue()));
    }

    @Test
    @DisplayName("Logout clears refresh cookie and returns 200 OK")
    void testLogout() throws Exception {
        mockMvc.perform(post("/api/v1/auth/logout"))
                .andExpect(status().isOk())
                .andExpect(cookie().maxAge("refreshToken", 0))
                .andExpect(jsonPath("$.status", is("SUCCESS")));
    }
}
