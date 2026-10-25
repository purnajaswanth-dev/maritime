package com.whereismyferry.backend.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.env.EnvironmentPostProcessor;
import org.springframework.core.Ordered;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.MapPropertySource;
import org.springframework.core.env.Profiles;

import java.util.HashMap;
import java.util.Map;

public class DatabasePlaceholderValidator implements EnvironmentPostProcessor, Ordered {

    private static final Logger log = LoggerFactory.getLogger(DatabasePlaceholderValidator.class);

    @Override
    public int getOrder() {
        // Run after ConfigDataEnvironmentPostProcessor so application.properties is loaded
        return Ordered.LOWEST_PRECEDENCE;
    }

    @Override
    public void postProcessEnvironment(ConfigurableEnvironment environment, SpringApplication application) {
        // 1. Check DATABASE_URL (standard for Render, Heroku, Railway, Fly.io)
        String databaseUrl = environment.getProperty("DATABASE_URL");
        if (databaseUrl != null && !databaseUrl.isBlank()) {
            parseAndApplyUrl(databaseUrl, environment, "render-database-url");
        }

        // 2. Check spring.datasource.url if provided as a raw postgresql:// URI
        String currentUrl = environment.getProperty("spring.datasource.url", "");
        if (currentUrl.contains("@") || (currentUrl.startsWith("postgresql://") && !currentUrl.startsWith("jdbc:postgresql://")) || currentUrl.startsWith("postgres://")) {
            parseAndApplyUrl(currentUrl, environment, "spring-datasource-url-fix");
        }

        // 3. Automatically adapt Render PORT environment variable
        String portEnv = environment.getProperty("PORT");
        if (portEnv != null && !portEnv.isBlank()) {
            Map<String, Object> portProps = new HashMap<>();
            portProps.put("server.port", portEnv);
            environment.getPropertySources().addFirst(new MapPropertySource("render-port", portProps));
        }

        // 4. Skip validation during automated tests (test profile or when running H2 datasource)
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

    private void parseAndApplyUrl(String rawUrl, ConfigurableEnvironment environment, String sourceName) {
        try {
            DatabaseUrlParser.ParsedDbConfig parsed = DatabaseUrlParser.parse(rawUrl);
            if (parsed == null || parsed.jdbcUrl() == null) {
                return;
            }

            Map<String, Object> props = new HashMap<>();
            props.put("spring.datasource.url", parsed.jdbcUrl());
            if (parsed.username() != null && !parsed.username().isBlank()) {
                props.put("spring.datasource.username", parsed.username());
            }
            if (parsed.password() != null && !parsed.password().isBlank()) {
                props.put("spring.datasource.password", parsed.password());
            }
            props.put("spring.datasource.driver-class-name", "org.postgresql.Driver");

            environment.getPropertySources().addFirst(new MapPropertySource(sourceName, props));
            log.info("DatabasePlaceholderValidator: Successfully configured datasource from {}: {}",
                    sourceName, parsed.jdbcUrl().replaceAll(":[^/@]+@", ":***@"));
        } catch (Exception e) {
            log.warn("Failed to parse datasource URL: {}", e.getMessage());
        }
    }
}
