package com.whereismyferry.backend;

import com.whereismyferry.backend.entity.Port;
import com.whereismyferry.backend.entity.Route;
import com.whereismyferry.backend.entity.Vessel;
import com.whereismyferry.backend.repository.*;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
class DatabaseSeederAndCatalogTests {

    @Autowired
    private PortRepository portRepository;

    @Autowired
    private VesselRepository vesselRepository;

    @Autowired
    private RouteRepository routeRepository;

    @Autowired
    private ScheduleRepository scheduleRepository;

    @Autowired
    private FareRuleRepository fareRuleRepository;

    @Autowired
    private RoleRepository roleRepository;

    @Test
    @DisplayName("Verify canonical 7 Brittany ports are seeded")
    void testPortsSeeded() {
        List<Port> ports = portRepository.findAll();
        assertThat(ports).hasSizeGreaterThanOrEqualTo(7);
        assertThat(portRepository.findById("BREST")).isPresent();
        assertThat(portRepository.findById("LE_CONQUET")).isPresent();
        assertThat(portRepository.findById("OUESSANT_STIFF")).isPresent();
        assertThat(portRepository.findById("AUDIERNE")).isPresent();
        assertThat(portRepository.findById("ILE_DE_SEIN")).isPresent();
        assertThat(portRepository.findById("MOLENE")).isPresent();
        assertThat(portRepository.findById("CAMARET")).isPresent();
    }

    @Test
    @DisplayName("Verify 4 fleet vessels are seeded with tracking IDs")
    void testVesselsSeeded() {
        List<Vessel> vessels = vesselRepository.findAll();
        assertThat(vessels).hasSizeGreaterThanOrEqualTo(4);
        assertThat(vesselRepository.findById("V-FROMVEUR-SIM")).isPresent();
        assertThat(vesselRepository.findById("V-AZENOR-SIM")).isPresent();
        assertThat(vesselRepository.findById("V-OUESSANT-SIM")).isPresent();
        assertThat(vesselRepository.findById("V-SEIN-SIM")).isPresent();
    }

    @Test
    @DisplayName("Verify Penn ar Bed routes are seeded with tracking flag")
    void testRoutesSeeded() {
        List<Route> routes = routeRepository.findAll();
        assertThat(routes).isNotEmpty();
        
        // Modelled routes should have tracking_supported = true
        Route breCnq = routeRepository.findById("R_BRE_CNQ").orElse(null);
        if (breCnq != null) {
            assertThat(breCnq.getTrackingSupported()).isTrue();
        }
    }

    @Test
    @DisplayName("Verify recurring timetable schedules and fare rules are seeded")
    void testSchedulesAndFaresSeeded() {
        assertThat(scheduleRepository.count()).isGreaterThanOrEqualTo(20);
        assertThat(fareRuleRepository.count()).isGreaterThan(0);
        assertThat(roleRepository.count()).isGreaterThanOrEqualTo(4);
    }
}
