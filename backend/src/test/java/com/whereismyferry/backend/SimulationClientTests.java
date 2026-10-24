package com.whereismyferry.backend;

import com.whereismyferry.backend.client.SimulationClient;
import com.whereismyferry.backend.exception.SimulationEngineUnavailableException;
import com.whereismyferry.backend.health.SimulationDaemonHealthIndicator;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.Status;
import org.springframework.boot.test.context.SpringBootTest;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@SpringBootTest
class SimulationClientTests {

    @Autowired
    private SimulationClient simulationClient;

    @Autowired
    private SimulationDaemonHealthIndicator healthIndicator;

    @Test
    @DisplayName("Verify simulation client behavior when daemon is offline")
    void testSimulationOfflineBehavior() {
        // If simulation daemon is not running on port 8000 during isolated backend test:
        boolean available = simulationClient.isAvailable();
        Health health = healthIndicator.health();

        if (!available) {
            assertThat(health.getStatus()).isEqualTo(Status.DOWN);
            assertThat(health.getDetails()).containsKey("message");
            assertThatThrownBy(() -> simulationClient.getLiveDeparture("DEP-NONEXISTENT"))
                    .isInstanceOf(SimulationEngineUnavailableException.class);
        } else {
            assertThat(health.getStatus()).isEqualTo(Status.UP);
        }
    }
}
