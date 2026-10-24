package com.whereismyferry.backend.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.env.EnvironmentPostProcessor;
import org.springframework.core.Ordered;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.Profiles;

public class DatabasePlaceholderValidator implements EnvironmentPostProcessor, Ordered {

    private static final Logger log = LoggerFactory.getLogger(DatabasePlaceholderValidator.class);

    @Override
    public int getOrder() {
        // Run after ConfigDataEnvironmentPostProcessor so application.properties is loaded
        return Ordered.LOWEST_PRECEDENCE;
    }

    @Override
    public void postProcessEnvironment(ConfigurableEnvironment environment, SpringApplication application) {
        // Skip validation during automated tests (test profile or when running H2 datasource)
        if (environment.acceptsProfiles(Profiles.of("test")) ||
                environment.getProperty("spring.datasource.url", "").contains("h2:mem")) {
            return;
        }

        String url = environment.getProperty("spring.datasource.url", "");
        String username = environment.getProperty("spring.datasource.username", "");
        String password = environment.getProperty("spring.datasource.password", "");
        String jwtSecret = environment.getProperty("app.jwt.secret", "");

        if (url.contains("YOUR_DATABASE_NAME")) {
            throw new IllegalStateException("CONFIGURATION ERROR: Please configure 'spring.datasource.url' in backend/src/main/resources/application.properties with your PostgreSQL database name.");
        }
        if ("YOUR_DB_USERNAME".equals(username)) {
            throw new IllegalStateException("CONFIGURATION ERROR: Please configure 'spring.datasource.username' in backend/src/main/resources/application.properties with your PostgreSQL username.");
        }
        if ("YOUR_DB_PASSWORD".equals(password)) {
            throw new IllegalStateException("CONFIGURATION ERROR: Please configure 'spring.datasource.password' in backend/src/main/resources/application.properties with your PostgreSQL password.");
        }
        if (jwtSecret != null && jwtSecret.contains("CHANGE_ME_TO_A_LONG_RANDOM_SECRET")) {
            throw new IllegalStateException("CONFIGURATION ERROR: Please configure 'app.jwt.secret' in backend/src/main/resources/application.properties with a secret at least 32 bytes long.");
        }
    }
}
