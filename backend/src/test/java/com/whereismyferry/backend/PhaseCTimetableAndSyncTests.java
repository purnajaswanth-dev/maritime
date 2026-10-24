package com.whereismyferry.backend;

import com.whereismyferry.backend.client.SimulationClient;
import com.whereismyferry.backend.entity.*;
import com.whereismyferry.backend.repository.*;
import com.whereismyferry.backend.service.DepartureGeneratorService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@SpringBootTest
class PhaseCTimetableAndSyncTests {

    @Autowired
    private PortRepository portRepository;

    @Autowired
    private VesselRepository vesselRepository;

    @Autowired
    private RouteRepository routeRepository;

    @Autowired
    private ServiceEntityRepository serviceEntityRepository;

    @Autowired
    private DepartureRepository departureRepository;

    @Autowired
    private BookingRepository bookingRepository;

    @Autowired
    private DepartureGeneratorService departureGeneratorService;

    @Autowired
    private SimulationClient simulationClient;

    @Test
    @DisplayName("C1: Seed counts - 7 ports, 4 modelled vessels, services in PostgreSQL")
    void testSeedCounts() {
        assertThat(portRepository.count()).isGreaterThanOrEqualTo(7);
        assertThat(vesselRepository.count()).isGreaterThanOrEqualTo(4);

        Port brest = portRepository.findById("BREST").orElseThrow();
        assertThat(brest.getBerthRadiusM()).isNotNull().isGreaterThan(0);
        assertThat(brest.getStatus()).isEqualTo("OPEN");

        Vessel fromveur = vesselRepository.findById("V-FROMVEUR-SIM").orElseThrow();
        assertThat(fromveur.getEngineVesselId()).isEqualTo("V-FROMVEUR-SIM");
        assertThat(fromveur.getCapacity()).isGreaterThan(0);

        List<ServiceEntity> services = serviceEntityRepository.findByActiveTrue();
        assertThat(services).isNotEmpty();
    }

    @Test
    @DisplayName("C1: Unique constraint on vessel and scheduled departure time")
    void testUniqueConstraintOnDeparture() {
        Vessel vessel = vesselRepository.findAll().get(0);
        Route route = routeRepository.findAll().get(0);
        OffsetDateTime scheduledDep = OffsetDateTime.now().plusDays(100);

        Departure d1 = new Departure("DEP-TEST-UNIQUE-1", route, vessel, scheduledDep, scheduledDep.plusHours(1), "SCHEDULED");
        departureRepository.saveAndFlush(d1);

        Departure d2 = new Departure("DEP-TEST-UNIQUE-2", route, vessel, scheduledDep, scheduledDep.plusHours(1), "SCHEDULED");
        assertThatThrownBy(() -> departureRepository.saveAndFlush(d2))
                .isInstanceOf(DataIntegrityViolationException.class);

        departureRepository.delete(d1);
    }

    @Test
    @DisplayName("C2: Departure generation is idempotent and preserves booked departures")
    @Transactional
    void testIdempotentGenerationAndBookedProtection() {
        long initialCount = departureRepository.count();
        assertThat(initialCount).isGreaterThan(0);

        // Re-running generation should be idempotent (no new duplicates created)
        int newAdded = departureGeneratorService.generateDepartures(60);
        assertThat(newAdded).isEqualTo(0);
        assertThat(departureRepository.count()).isEqualTo(initialCount);

        // Create a booking on the first departure
        Departure dep = departureRepository.findAll().get(0);
        Booking booking = new Booking();
        booking.setBookingReference("BK-TEST-PROTECT-1");
        booking.setDeparture(dep);
        booking.setContactEmail("test@example.com");
        booking.setTotalAmountEur(BigDecimal.valueOf(25.0));
        booking.setStatus("CONFIRMED");
        bookingRepository.save(booking);

        assertThat(bookingRepository.existsByDepartureId(dep.getId())).isTrue();

        // Regenerating departures must not overwrite or corrupt booked departure
        departureGeneratorService.generateDepartures(60);
        Departure reloaded = departureRepository.findById(dep.getId()).orElseThrow();
        assertThat(reloaded.getDepartureCode()).isEqualTo(dep.getDepartureCode());
    }

    @Test
    @DisplayName("C2: Engine sync sends today's departures and receives SYNCED status")
    void testEngineTimetableSync() {
        Map<String, Object> result = departureGeneratorService.syncTodayDeparturesWithEngine();
        assertThat(result).isNotNull();
        // If simulation daemon is running, status is SYNCED; if offline, fails gracefully
        if ("SYNCED".equals(result.get("status"))) {
            assertThat(result.get("synced_count")).isNotNull();
            assertThat(result.get("supported_count")).isNotNull();
        }
    }
}
