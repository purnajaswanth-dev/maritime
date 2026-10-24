package com.whereismyferry.backend;

import com.whereismyferry.backend.entity.Departure;
import com.whereismyferry.backend.repository.DepartureRepository;
import com.whereismyferry.backend.service.DepartureGeneratorService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class DepartureGeneratorTests {

    @Autowired
    private DepartureGeneratorService departureGeneratorService;

    @Autowired
    private DepartureRepository departureRepository;

    @Test
    @DisplayName("Verify departure generator creates dated departures and is idempotent")
    void testDepartureGenerationIdempotency() {
        long countBefore = departureRepository.count();
        assertThat(countBefore).isGreaterThan(0);

        // Generating again should not duplicate existing departures
        int generatedSecondTime = departureGeneratorService.generateDepartures(7);
        assertThat(generatedSecondTime).isEqualTo(0);

        List<Departure> allDepartures = departureRepository.findAll();
        for (Departure dep : allDepartures) {
            assertThat(dep.getDepartureCode()).startsWith("DEP-");
            assertThat(dep.getScheduledDepartureTime()).isNotNull();
            assertThat(dep.getScheduledArrivalTime()).isNotNull();
            assertThat(dep.getScheduledArrivalTime()).isAfter(dep.getScheduledDepartureTime());
            assertThat(dep.getStatus()).isEqualTo("SCHEDULED");
        }
    }
}
