package com.whereismyferry.backend.health;

import com.whereismyferry.backend.client.SimulationClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;

@Component
public class SimulationDaemonHealthIndicator implements HealthIndicator {

    private final SimulationClient simulationClient;
    private final String daemonUrl;

    public SimulationDaemonHealthIndicator(
            SimulationClient simulationClient,
            @Value("${ferry.simulation.daemon-url:http://127.0.0.1:8000}") String daemonUrl) {
        this.simulationClient = simulationClient;
        this.daemonUrl = daemonUrl;
    }

    @Override
    public Health health() {
        if (simulationClient.isAvailable()) {
            return Health.up()
                    .withDetail("daemonUrl", daemonUrl)
                    .withDetail("status", "AVAILABLE")
                    .build();
        } else {
            return Health.down()
                    .withDetail("daemonUrl", daemonUrl)
                    .withDetail("status", "UNAVAILABLE")
                    .withDetail("message", "Python simulation daemon is unreachable")
                    .build();
        }
    }
}
