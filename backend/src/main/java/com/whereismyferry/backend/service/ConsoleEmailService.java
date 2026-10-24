package com.whereismyferry.backend.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class ConsoleEmailService implements EmailService {

    private static final Logger log = LoggerFactory.getLogger(ConsoleEmailService.class);

    @Override
    public void sendVerificationEmail(String toEmail, String token) {
        log.info("[SIMULATED EMAIL] Verification email to: {}", toEmail);
        log.info("[SIMULATED EMAIL] Verification link: http://localhost:5173/verify-email?token={}", token);
    }

    @Override
    public void sendPasswordResetEmail(String toEmail, String resetToken) {
        log.info("[SIMULATED EMAIL] Password reset email to: {}", toEmail);
        log.info("[SIMULATED EMAIL] Reset link: http://localhost:5173/reset-password?token={}", resetToken);
    }
}
