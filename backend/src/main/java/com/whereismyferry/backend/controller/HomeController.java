package com.whereismyferry.backend.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.OffsetDateTime;
import java.util.Map;

@RestController
public class HomeController {

    @GetMapping("/")
    public ResponseEntity<Map<String, Object>> root() {
        return ResponseEntity.ok(Map.of(
                "application", "Where Is My Ferry? API",
                "status", "UP",
                "version", "1.0.0",
                "timestamp", OffsetDateTime.now().toString(),
                "documentation", "/swagger-ui.html",
                "health", "/actuator/health",
                "endpoints", Map.of(
                        "ports", "/api/v1/ports",
                        "routes", "/api/v1/routes",
                        "departures", "/api/v1/departures",
                        "timetable", "/api/v1/timetable",
                        "fares", "/api/v1/fares",
                        "announcements", "/api/v1/announcements",
                        "auth", "/api/v1/auth"
                )
        ));
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "UP"));
    }
}
