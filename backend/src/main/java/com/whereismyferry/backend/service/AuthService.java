package com.whereismyferry.backend.service;

import com.whereismyferry.backend.dto.*;
import com.whereismyferry.backend.entity.Role;
import com.whereismyferry.backend.entity.User;
import com.whereismyferry.backend.exception.ResourceNotFoundException;
import com.whereismyferry.backend.exception.UserAlreadyExistsException;
import com.whereismyferry.backend.repository.RoleRepository;
import com.whereismyferry.backend.repository.UserRepository;
import com.whereismyferry.backend.security.CustomUserDetails;
import com.whereismyferry.backend.security.JwtService;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final AuthenticationManager authenticationManager;

    public AuthService(
            UserRepository userRepository,
            RoleRepository roleRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService,
            AuthenticationManager authenticationManager) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.authenticationManager = authenticationManager;
    }

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        String normalizedEmail = request.getEmail().trim().toLowerCase();
        if (userRepository.existsByEmailIgnoreCase(normalizedEmail)) {
            throw new UserAlreadyExistsException("A user with email " + normalizedEmail + " already exists.");
        }

        Role passengerRole = roleRepository.findByName("ROLE_PASSENGER")
                .orElseGet(() -> roleRepository.save(new Role("ROLE_PASSENGER")));

        User user = new User();
        user.setEmail(normalizedEmail);
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));
        user.setFirstName(request.getFirstName().trim());
        user.setLastName(request.getLastName().trim());
        user.setPhone(request.getPhone() != null ? request.getPhone().trim() : null);
        user.setEnabled(true);
        user.setRoles(Set.of(passengerRole));

        user = userRepository.save(user);

        CustomUserDetails userDetails = new CustomUserDetails(user);
        String accessToken = jwtService.generateAccessToken(userDetails, user.getId());
        String refreshToken = jwtService.generateRefreshToken(userDetails);

        UserSummaryDto userSummary = mapToUserSummary(user);
        return new AuthResponse(accessToken, refreshToken, jwtService.getAccessTokenExpirationSeconds(), userSummary);
    }

    @Transactional(readOnly = true)
    public AuthResponse login(LoginRequest request) {
        String normalizedEmail = request.getEmail().trim().toLowerCase();
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(normalizedEmail, request.getPassword())
        );

        User user = userRepository.findByEmailIgnoreCase(normalizedEmail)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + normalizedEmail));

        CustomUserDetails userDetails = new CustomUserDetails(user);
        String accessToken = jwtService.generateAccessToken(userDetails, user.getId());
        String refreshToken = jwtService.generateRefreshToken(userDetails);

        UserSummaryDto userSummary = mapToUserSummary(user);
        return new AuthResponse(accessToken, refreshToken, jwtService.getAccessTokenExpirationSeconds(), userSummary);
    }

    @Transactional(readOnly = true)
    public AuthResponse refreshToken(String refreshToken) {
        if (refreshToken == null || refreshToken.isBlank()) {
            throw new IllegalArgumentException("Refresh token must not be empty.");
        }

        try {
            if (jwtService.isTokenExpired(refreshToken)) {
                throw new IllegalArgumentException("Refresh token has expired.");
            }
            String email = jwtService.extractUsername(refreshToken);
            User user = userRepository.findByEmailIgnoreCase(email)
                    .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));

            CustomUserDetails userDetails = new CustomUserDetails(user);
            String newAccessToken = jwtService.generateAccessToken(userDetails, user.getId());
            String newRefreshToken = jwtService.generateRefreshToken(userDetails);

            UserSummaryDto userSummary = mapToUserSummary(user);
            return new AuthResponse(newAccessToken, newRefreshToken, jwtService.getAccessTokenExpirationSeconds(), userSummary);
        } catch (Exception e) {
            throw new IllegalArgumentException("Invalid refresh token: " + e.getMessage(), e);
        }
    }

    public UserSummaryDto mapToUserSummary(User user) {
        List<String> roles = user.getRoles().stream()
                .map(Role::getName)
                .sorted()
                .collect(Collectors.toList());
        return new UserSummaryDto(user.getId(), user.getEmail(), user.getFirstName(), user.getLastName(), roles);
    }
}
