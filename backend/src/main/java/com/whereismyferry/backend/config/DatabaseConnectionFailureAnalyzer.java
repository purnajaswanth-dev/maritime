package com.whereismyferry.backend.config;

import java.sql.SQLException;
import org.springframework.boot.diagnostics.AbstractFailureAnalyzer;
import org.springframework.boot.diagnostics.FailureAnalysis;

public class DatabaseConnectionFailureAnalyzer extends AbstractFailureAnalyzer<SQLException> {

    @Override
    protected FailureAnalysis analyze(Throwable rootFailure, SQLException cause) {
        String description = "Cannot connect to database: " + cause.getMessage();
        String action = "Please ensure PostgreSQL is running and update 'spring.datasource.*' in backend/src/main/resources/application.properties. Refer to docs/SETUP_DATABASE.md for step-by-step instructions.";
        return new FailureAnalysis(description, action, cause);
    }
}
