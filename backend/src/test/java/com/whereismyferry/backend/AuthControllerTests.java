package com.whereismyferry.backend;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.whereismyferry.backend.dto.*;
import com.whereismyferry.backend.entity.User;
import com.whereismyferry.backend.repository.UserRepository;
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
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class AuthControllerTests {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private UserRepository userRepository;

    @Test
    @DisplayName("Register new passenger account returns 201 with JWT and sets refresh cookie")
    void testRegisterPassenger() throws Exception {
        RegisterRequest request = new RegisterRequest(
                "newpassenger@iroise.bzh",
                "Password1234!",
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
                .andExpect(jsonPath("$.user.role", is("PASSENGER")))
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
                "SomePassword1234!",
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
    @DisplayName("Register with short password (<10 chars) returns 422 Unprocessable Entity")
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
                .andExpect(jsonPath("$.user.role", is("ADMIN")))
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
    @DisplayName("Account lockout after 5 consecutive failed login attempts")
    void testAccountLockoutAfterFiveAttempts() throws Exception {
        String testEmail = "lockout-test@iroise.bzh";
        RegisterRequest regReq = new RegisterRequest(testEmail, "SafePass12345!", "Lock", "Out", null);
        mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(regReq)))
                .andExpect(status().isCreated());

        LoginRequest badReq = new LoginRequest(testEmail, "WrongPassword!");

        // 4 failed attempts -> 401
        for (int i = 0; i < 4; i++) {
            mockMvc.perform(post("/api/v1/auth/login")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(badReq)))
                    .andExpect(status().isUnauthorized());
        }

        // 5th failed attempt -> locks account
        mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(badReq)))
                .andExpect(status().isUnauthorized());

        // 6th attempt -> Account locked (403 or locked error message)
        mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(badReq)))
                .andExpect(status().isUnauthorized());

        User user = userRepository.findByEmailIgnoreCase(testEmail).orElseThrow();
        assertThat(user.isAccountLocked()).isTrue();
    }

    @Test
    @DisplayName("Refresh token rotation and token reuse detection")
    void testRefreshTokenRotationAndReuseDetection() throws Exception {
        // 1. Login to get initial refresh token
        LoginRequest loginReq = new LoginRequest("passenger@whereismyferry.bzh", "PassengerPass123!");
        MvcResult loginResult = mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(loginReq)))
                .andExpect(status().isOk())
                .andReturn();

        JsonNode loginJson = objectMapper.readTree(loginResult.getResponse().getContentAsString());
        String initialRefresh = loginJson.path("refreshToken").asText();

        // 2. Rotate token
        RefreshTokenRequest refreshReq = new RefreshTokenRequest(initialRefresh);
        MvcResult rotateResult = mockMvc.perform(post("/api/v1/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(refreshReq)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken", notNullValue()))
                .andExpect(jsonPath("$.refreshToken", notNullValue()))
                .andReturn();

        JsonNode rotateJson = objectMapper.readTree(rotateResult.getResponse().getContentAsString());
        String newRefresh = rotateJson.path("refreshToken").asText();
        assertThat(newRefresh).isNotEqualTo(initialRefresh);

        // 3. Attempt to reuse old initial refresh token -> triggers reuse detection!
        mockMvc.perform(post("/api/v1/auth/refresh")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(new RefreshTokenRequest(initialRefresh))))
                .andExpect(status().isUnauthorized());
    }

    @Test
    @DisplayName("Logout clears refresh cookie and returns 200 OK")
    void testLogout() throws Exception {
        mockMvc.perform(post("/api/v1/auth/logout"))
                .andExpect(status().isOk())
                .andExpect(cookie().maxAge("refreshToken", 0))
                .andExpect(jsonPath("$.status", is("SUCCESS")));
    }

    @Test
    @DisplayName("Forgot password returns generic 200 success without leaking email existence")
    void testForgotPasswordGenericResponse() throws Exception {
        ForgotPasswordRequest req = new ForgotPasswordRequest("nonexistent@example.com");
        mockMvc.perform(post("/api/v1/auth/forgot-password")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status", is("SUCCESS")))
                .andExpect(jsonPath("$.message", containsString("If an account exists")));
    }

    @Test
    @DisplayName("First admin is seeded with app.admin.seed.email")
    void testFirstAdminSeeded() {
        User admin = userRepository.findByEmailIgnoreCase("admin@example.com").orElse(null);
        assertThat(admin).isNotNull();
        assertThat(admin.getRole().name()).isEqualTo("ADMIN");
        assertThat(admin.getStatus().name()).isEqualTo("ACTIVE");
    }

    @Test
    @DisplayName("GET /api/v1/auth/me returns profile for authenticated user")
    void testGetMeAuthenticated() throws Exception {
        LoginRequest loginReq = new LoginRequest("passenger@whereismyferry.bzh", "PassengerPass123!");
        MvcResult loginResult = mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(loginReq)))
                .andExpect(status().isOk())
                .andReturn();

        String token = objectMapper.readTree(loginResult.getResponse().getContentAsString()).path("accessToken").asText();

        mockMvc.perform(get("/api/v1/auth/me")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.email", is("passenger@whereismyferry.bzh")))
                .andExpect(jsonPath("$.role", is("PASSENGER")));
    }
}
