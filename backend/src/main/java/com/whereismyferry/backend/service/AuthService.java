package com.whereismyferry.backend.service;

import com.whereismyferry.backend.dto.*;
import com.whereismyferry.backend.entity.*;
import com.whereismyferry.backend.exception.ResourceNotFoundException;
import com.whereismyferry.backend.exception.UserAlreadyExistsException;
import com.whereismyferry.backend.repository.*;
import com.whereismyferry.backend.security.CustomUserDetails;
import com.whereismyferry.backend.security.JwtService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.OffsetDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class AuthService {

    private static final Logger log = LoggerFactory.getLogger(AuthService.class);
    private static final int MAX_FAILED_ATTEMPTS = 5;
    private static final int LOCKOUT_MINUTES = 15;

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordResetTokenRepository passwordResetTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final AuditLogService auditLogService;
    private final EmailService emailService;

    public AuthService(
            UserRepository userRepository,
            RoleRepository roleRepository,
            RefreshTokenRepository refreshTokenRepository,
            PasswordResetTokenRepository passwordResetTokenRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService,
            AuditLogService auditLogService,
            EmailService emailService) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordResetTokenRepository = passwordResetTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.auditLogService = auditLogService;
        this.emailService = emailService;
    }

    private String hashToken(String token) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(token.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 algorithm not available", e);
        }
    }

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        String normalizedEmail = request.getEmail().trim().toLowerCase();
        if (userRepository.existsByEmailIgnoreCase(normalizedEmail)) {
            throw new UserAlreadyExistsException("A user with this email already exists.");
        }

        if (request.getPassword() == null || request.getPassword().length() < 10) {
            throw new IllegalArgumentException("Password must be at least 10 characters long.");
        }

        Role passengerRole = roleRepository.findByName("ROLE_PASSENGER")
                .orElseGet(() -> roleRepository.save(new Role("ROLE_PASSENGER")));

        User user = new User();
        user.setEmail(normalizedEmail);
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));
        user.setFullName(request.getFullName());
        user.setFirstName(request.getFirstName());
        user.setLastName(request.getLastName());
        user.setPhone(request.getPhone() != null ? request.getPhone().trim() : null);
        user.setRole(UserRole.PASSENGER);
        user.setStatus(UserStatus.ACTIVE);
        user.setEnabled(true);
        user.setEmailVerified(true);
        user.setFailedAttempts(0);
        user.setRoles(Set.of(passengerRole));

        user = userRepository.save(user);

        auditLogService.record(normalizedEmail, "USER_REGISTERED", "User:" + user.getId(), "127.0.0.1", "Registered as passenger");

        CustomUserDetails userDetails = new CustomUserDetails(user);
        String accessToken = jwtService.generateAccessToken(userDetails, user.getId());
        String rawRefreshToken = UUID.randomUUID().toString() + "." + UUID.randomUUID().toString();

        RefreshToken refreshTokenEntity = new RefreshToken();
        refreshTokenEntity.setUser(user);
        refreshTokenEntity.setTokenHash(hashToken(rawRefreshToken));
        refreshTokenEntity.setExpiry(OffsetDateTime.now().plusDays(7));
        refreshTokenEntity.setRevoked(false);
        refreshTokenRepository.save(refreshTokenEntity);

        UserSummaryDto userSummary = mapToUserSummary(user);
        return new AuthResponse(accessToken, rawRefreshToken, jwtService.getAccessTokenExpirationSeconds(), userSummary);
    }

    @Transactional(noRollbackFor = {BadCredentialsException.class})
    public AuthResponse login(LoginRequest request, String clientIp, String userAgent) {
        String normalizedEmail = request.getEmail().trim().toLowerCase();
        Optional<User> userOpt = userRepository.findByEmailIgnoreCase(normalizedEmail);

        if (userOpt.isEmpty()) {
            auditLogService.record(normalizedEmail, "LOGIN_FAILED", "UnknownUser", clientIp, "User not found");
            throw new BadCredentialsException("Invalid email or password.");
        }

        User user = userOpt.get();

        if (user.getStatus() == UserStatus.SUSPENDED) {
            auditLogService.record(normalizedEmail, "LOGIN_FAILED", "User:" + user.getId(), clientIp, "Account suspended");
            throw new LockedException("Your account has been suspended. Please contact customer support.");
        }

        if (user.isAccountLocked()) {
            auditLogService.record(normalizedEmail, "LOGIN_FAILED", "User:" + user.getId(), clientIp, "Account locked out");
            throw new LockedException("Account is temporarily locked due to 5 failed login attempts. Please try again after 15 minutes.");
        }

        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            int attempts = user.getFailedAttempts() + 1;
            user.setFailedAttempts(attempts);
            if (attempts >= MAX_FAILED_ATTEMPTS) {
                user.setLockedUntil(OffsetDateTime.now().plusMinutes(LOCKOUT_MINUTES));
                auditLogService.record(normalizedEmail, "ACCOUNT_LOCKED", "User:" + user.getId(), clientIp, "Locked after 5 failed attempts");
            } else {
                auditLogService.record(normalizedEmail, "LOGIN_FAILED", "User:" + user.getId(), clientIp, "Attempt " + attempts + " failed");
            }
            userRepository.save(user);
            throw new BadCredentialsException("Invalid email or password.");
        }

        // Login successful: reset failed attempts and update last_login_at
        user.setFailedAttempts(0);
        user.setLockedUntil(null);
        user.setLastLoginAt(OffsetDateTime.now());
        userRepository.save(user);

        auditLogService.record(normalizedEmail, "LOGIN_SUCCESS", "User:" + user.getId(), clientIp, "Successful login");

        CustomUserDetails userDetails = new CustomUserDetails(user);
        String accessToken = jwtService.generateAccessToken(userDetails, user.getId());
        String rawRefreshToken = UUID.randomUUID().toString() + "." + UUID.randomUUID().toString();

        RefreshToken refreshTokenEntity = new RefreshToken();
        refreshTokenEntity.setUser(user);
        refreshTokenEntity.setTokenHash(hashToken(rawRefreshToken));
        refreshTokenEntity.setExpiry(OffsetDateTime.now().plusDays(7));
        refreshTokenEntity.setRevoked(false);
        refreshTokenEntity.setUserAgent(userAgent);
        refreshTokenRepository.save(refreshTokenEntity);

        UserSummaryDto userSummary = mapToUserSummary(user);
        return new AuthResponse(accessToken, rawRefreshToken, jwtService.getAccessTokenExpirationSeconds(), userSummary);
    }

    @Transactional
    public AuthResponse refreshToken(String rawRefreshToken, String userAgent, String clientIp) {
        if (rawRefreshToken == null || rawRefreshToken.isBlank()) {
            throw new IllegalArgumentException("Refresh token is required.");
        }

        String tokenHash = hashToken(rawRefreshToken);
        Optional<RefreshToken> tokenOpt = refreshTokenRepository.findByTokenHash(tokenHash);

        if (tokenOpt.isEmpty()) {
            throw new BadCredentialsException("Invalid refresh token.");
        }

        RefreshToken token = tokenOpt.get();
        User user = token.getUser();

        // Token Reuse Detection: If an already-revoked token is presented, suspect token theft!
        if (Boolean.TRUE.equals(token.getRevoked())) {
            refreshTokenRepository.revokeAllForUser(user);
            auditLogService.record(user.getEmail(), "TOKEN_REUSE_DETECTED", "User:" + user.getId(), clientIp, "Compromised refresh token reused. All tokens revoked.");
            throw new BadCredentialsException("Refresh token has been revoked due to potential security compromise.");
        }

        if (token.isExpired()) {
            token.setRevoked(true);
            refreshTokenRepository.save(token);
            throw new BadCredentialsException("Refresh token has expired. Please sign in again.");
        }

        // Rotate: revoke the used token
        token.setRevoked(true);
        refreshTokenRepository.save(token);

        // Issue new refresh token & new access token
        String newRawRefreshToken = UUID.randomUUID().toString() + "." + UUID.randomUUID().toString();
        RefreshToken newTokenEntity = new RefreshToken();
        newTokenEntity.setUser(user);
        newTokenEntity.setTokenHash(hashToken(newRawRefreshToken));
        newTokenEntity.setExpiry(OffsetDateTime.now().plusDays(7));
        newTokenEntity.setRevoked(false);
        newTokenEntity.setUserAgent(userAgent);
        refreshTokenRepository.save(newTokenEntity);

        CustomUserDetails userDetails = new CustomUserDetails(user);
        String newAccessToken = jwtService.generateAccessToken(userDetails, user.getId());

        UserSummaryDto userSummary = mapToUserSummary(user);
        return new AuthResponse(newAccessToken, newRawRefreshToken, jwtService.getAccessTokenExpirationSeconds(), userSummary);
    }

    @Transactional
    public void logout(String rawRefreshToken, String clientIp) {
        if (rawRefreshToken != null && !rawRefreshToken.isBlank()) {
            String tokenHash = hashToken(rawRefreshToken);
            refreshTokenRepository.findByTokenHash(tokenHash).ifPresent(token -> {
                token.setRevoked(true);
                refreshTokenRepository.save(token);
                auditLogService.record(token.getUser().getEmail(), "LOGOUT", "User:" + token.getUser().getId(), clientIp, "Session terminated");
            });
        }
    }

    @Transactional
    public void forgotPassword(ForgotPasswordRequest request, String clientIp) {
        String normalizedEmail = request.getEmail().trim().toLowerCase();
        Optional<User> userOpt = userRepository.findByEmailIgnoreCase(normalizedEmail);

        if (userOpt.isPresent()) {
            User user = userOpt.get();
            // Invalidate any existing tokens
            passwordResetTokenRepository.invalidateAllForUser(user);

            String rawResetToken = UUID.randomUUID().toString().replace("-", "") + UUID.randomUUID().toString().replace("-", "");
            PasswordResetToken resetTokenEntity = new PasswordResetToken();
            resetTokenEntity.setUser(user);
            resetTokenEntity.setTokenHash(hashToken(rawResetToken));
            resetTokenEntity.setExpiry(OffsetDateTime.now().plusHours(1));
            resetTokenEntity.setUsed(false);
            passwordResetTokenRepository.save(resetTokenEntity);

            emailService.sendPasswordResetEmail(user.getEmail(), rawResetToken);
            auditLogService.record(normalizedEmail, "PASSWORD_RESET_REQUESTED", "User:" + user.getId(), clientIp, "Password reset link generated");
        } else {
            // Log attempt without revealing email non-existence to caller
            auditLogService.record(normalizedEmail, "PASSWORD_RESET_IGNORED", "UnknownUser", clientIp, "Email does not exist");
        }
    }

    @Transactional
    public void resetPassword(ResetPasswordRequest request, String clientIp) {
        if (request.getNewPassword() == null || request.getNewPassword().length() < 10) {
            throw new IllegalArgumentException("New password must be at least 10 characters long.");
        }

        String tokenHash = hashToken(request.getToken());
        PasswordResetToken resetToken = passwordResetTokenRepository.findByTokenHash(tokenHash)
                .orElseThrow(() -> new IllegalArgumentException("Invalid or expired password reset token."));

        if (Boolean.TRUE.equals(resetToken.getUsed()) || resetToken.isExpired()) {
            throw new IllegalArgumentException("This password reset token has expired or has already been used.");
        }

        User user = resetToken.getUser();
        user.setPasswordHash(passwordEncoder.encode(request.getNewPassword()));
        user.setFailedAttempts(0);
        user.setLockedUntil(null);
        userRepository.save(user);

        resetToken.setUsed(true);
        passwordResetTokenRepository.save(resetToken);

        // Invalidate all active sessions for this user
        refreshTokenRepository.revokeAllForUser(user);

        auditLogService.record(user.getEmail(), "PASSWORD_RESET_COMPLETED", "User:" + user.getId(), clientIp, "Password reset successfully completed");
    }

    @Transactional(readOnly = true)
    public UserProfileDto getProfile(String email) {
        User user = userRepository.findByEmailIgnoreCase(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));
        return mapToUserProfile(user);
    }

    @Transactional
    public UserProfileDto updateProfile(String email, UpdateProfileRequest request, String clientIp) {
        User user = userRepository.findByEmailIgnoreCase(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));

        if (request.getFirstName() != null && !request.getFirstName().isBlank()) {
            user.setFirstName(request.getFirstName().trim());
        }
        if (request.getLastName() != null && !request.getLastName().isBlank()) {
            user.setLastName(request.getLastName().trim());
        }
        if (request.getFirstName() != null || request.getLastName() != null) {
            user.setFullName((user.getFirstName() + " " + user.getLastName()).trim());
        }
        if (request.getPhone() != null) {
            user.setPhone(request.getPhone().trim());
        }

        user = userRepository.save(user);
        auditLogService.record(email, "PROFILE_UPDATED", "User:" + user.getId(), clientIp, "User profile updated");
        return mapToUserProfile(user);
    }

    @Transactional
    public void changePassword(String email, ChangePasswordRequest request, String clientIp) {
        User user = userRepository.findByEmailIgnoreCase(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + email));

        if (!passwordEncoder.matches(request.getCurrentPassword(), user.getPasswordHash())) {
            throw new BadCredentialsException("Current password does not match.");
        }

        if (request.getNewPassword() == null || request.getNewPassword().length() < 10) {
            throw new IllegalArgumentException("New password must be at least 10 characters long.");
        }

        user.setPasswordHash(passwordEncoder.encode(request.getNewPassword()));
        userRepository.save(user);

        // Revoke all existing refresh tokens
        refreshTokenRepository.revokeAllForUser(user);

        auditLogService.record(email, "PASSWORD_CHANGED", "User:" + user.getId(), clientIp, "Password successfully changed");
    }

    private UserSummaryDto mapToUserSummary(User user) {
        List<String> roleNames = user.getRoles().stream()
                .map(Role::getName)
                .collect(Collectors.toList());
        if (roleNames.isEmpty() && user.getRole() != null) {
            roleNames = List.of("ROLE_" + user.getRole().name());
        }
        return new UserSummaryDto(
                user.getId(),
                user.getEmail(),
                user.getFullName(),
                user.getFirstName(),
                user.getLastName(),
                user.getRole() != null ? user.getRole().name() : "PASSENGER",
                roleNames
        );
    }

    private UserProfileDto mapToUserProfile(User user) {
        List<String> roleNames = user.getRoles().stream()
                .map(Role::getName)
                .collect(Collectors.toList());
        if (roleNames.isEmpty() && user.getRole() != null) {
            roleNames = List.of("ROLE_" + user.getRole().name());
        }
        return new UserProfileDto(
                user.getId(),
                user.getEmail(),
                user.getFullName(),
                user.getFirstName(),
                user.getLastName(),
                user.getPhone(),
                user.getRole() != null ? user.getRole().name() : "PASSENGER",
                user.getStatus() != null ? user.getStatus().name() : "ACTIVE",
                user.getEmailVerified(),
                roleNames,
                user.getCreatedAt(),
                user.getLastLoginAt()
        );
    }
}
