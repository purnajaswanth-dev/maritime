package com.whereismyferry.backend.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.whereismyferry.backend.entity.*;
import com.whereismyferry.backend.repository.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
public class DatabaseSeederService {

    private static final Logger log = LoggerFactory.getLogger(DatabaseSeederService.class);

    private final PortRepository portRepository;
    private final VesselRepository vesselRepository;
    private final RouteRepository routeRepository;
    private final ScheduleRepository scheduleRepository;
    private final ServiceEntityRepository serviceEntityRepository;
    private final FareRuleRepository fareRuleRepository;
    private final RoleRepository roleRepository;
    private final UserRepository userRepository;
    private final org.springframework.security.crypto.password.PasswordEncoder passwordEncoder;
    private final ObjectMapper objectMapper;

    public DatabaseSeederService(
            PortRepository portRepository,
            VesselRepository vesselRepository,
            RouteRepository routeRepository,
            ScheduleRepository scheduleRepository,
            ServiceEntityRepository serviceEntityRepository,
            FareRuleRepository fareRuleRepository,
            RoleRepository roleRepository,
            UserRepository userRepository,
            org.springframework.security.crypto.password.PasswordEncoder passwordEncoder,
            ObjectMapper objectMapper) {
        this.portRepository = portRepository;
        this.vesselRepository = vesselRepository;
        this.routeRepository = routeRepository;
        this.scheduleRepository = scheduleRepository;
        this.serviceEntityRepository = serviceEntityRepository;
        this.fareRuleRepository = fareRuleRepository;
        this.roleRepository = roleRepository;
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.objectMapper = objectMapper;
    }

    @EventListener(ApplicationReadyEvent.class)
    @org.springframework.core.annotation.Order(1)
    public void seedInitialData() {
        try {
            log.info("Starting Where Is My Ferry catalog database seeding...");
            seedRoles();
            seedDefaultUsers();
            seedPorts();
            seedVessels();
            seedRoutesAndSchedules();
            seedFareRules();
            log.info("Database seeding successfully completed.");
        } catch (Exception e) {
            log.error("Database seeding encountered a non-fatal error during startup: {}", e.getMessage(), e);
        }
    }

    private void seedRoles() {
        List<String> roles = List.of("ROLE_PASSENGER", "ROLE_ADMIN", "ROLE_OPERATOR", "ROLE_CREW", "ROLE_AUDITOR", "ROLE_SUPPORT");
        for (String roleName : roles) {
            if (roleRepository.findByName(roleName).isEmpty()) {
                roleRepository.save(new Role(roleName));
            }
        }
    }

    @org.springframework.beans.factory.annotation.Value("${app.admin.seed.enabled:true}")
    private boolean adminSeedEnabled;

    @org.springframework.beans.factory.annotation.Value("${app.admin.seed.email:admin@example.com}")
    private String adminSeedEmail;

    @org.springframework.beans.factory.annotation.Value("${app.admin.seed.password:AdminPass123!}")
    private String adminSeedPassword;

    private void seedDefaultUsers() {
        Role rolePassenger = roleRepository.findByName("ROLE_PASSENGER").orElseThrow();
        Role roleAdmin = roleRepository.findByName("ROLE_ADMIN").orElseThrow();
        Role roleOperator = roleRepository.findByName("ROLE_OPERATOR").orElseThrow();
        Role roleCrew = roleRepository.findByName("ROLE_CREW").orElseThrow();
        Role roleAuditor = roleRepository.findByName("ROLE_AUDITOR").orElseThrow();
        Role roleSupport = roleRepository.findByName("ROLE_SUPPORT").orElseThrow();

        // 1. First Administrator (created once at first start, unlocked and synchronized on start)
        if (adminSeedEnabled) {
            String seedEmail = adminSeedEmail.trim().toLowerCase();
            Optional<User> existing = userRepository.findByEmailIgnoreCase(seedEmail);
            if (existing.isEmpty()) {
                User admin = new User();
                admin.setEmail(seedEmail);
                admin.setPasswordHash(passwordEncoder.encode(adminSeedPassword));
                admin.setFullName("System Administrator");
                admin.setFirstName("System");
                admin.setLastName("Administrator");
                admin.setRole(com.whereismyferry.backend.entity.UserRole.ADMIN);
                admin.setStatus(com.whereismyferry.backend.entity.UserStatus.ACTIVE);
                admin.setRoles(Set.of(roleAdmin, roleOperator, rolePassenger));
                admin.setEnabled(true);
                admin.setEmailVerified(true);
                admin.setFailedAttempts(0);
                admin.setLockedUntil(null);
                userRepository.save(admin);
                log.info("First administrator account successfully seeded: {}", seedEmail);
            } else {
                User admin = existing.get();
                admin.setFailedAttempts(0);
                admin.setLockedUntil(null);
                admin.setStatus(com.whereismyferry.backend.entity.UserStatus.ACTIVE);
                admin.setEnabled(true);
                if (adminSeedPassword != null && !adminSeedPassword.isBlank()) {
                    admin.setPasswordHash(passwordEncoder.encode(adminSeedPassword));
                }
                userRepository.save(admin);
                log.info("Administrator account unlocked and synchronized: {}", seedEmail);
            }
        }

        // 2. Legacy admin account for backwards compatibility with tests
        String legacyAdminEmail = "admin@whereismyferry.bzh";
        Optional<User> existingLegacy = userRepository.findByEmailIgnoreCase(legacyAdminEmail);
        if (existingLegacy.isEmpty()) {
            User admin = new User();
            admin.setEmail(legacyAdminEmail);
            admin.setPasswordHash(passwordEncoder.encode("AdminPass123!"));
            admin.setFullName("Admin Ferry");
            admin.setFirstName("Admin");
            admin.setLastName("Ferry");
            admin.setRole(com.whereismyferry.backend.entity.UserRole.ADMIN);
            admin.setStatus(com.whereismyferry.backend.entity.UserStatus.ACTIVE);
            admin.setRoles(Set.of(roleAdmin, roleOperator, rolePassenger));
            admin.setEnabled(true);
            admin.setEmailVerified(true);
            admin.setFailedAttempts(0);
            admin.setLockedUntil(null);
            userRepository.save(admin);
        } else {
            User admin = existingLegacy.get();
            admin.setFailedAttempts(0);
            admin.setLockedUntil(null);
            admin.setStatus(com.whereismyferry.backend.entity.UserStatus.ACTIVE);
            admin.setEnabled(true);
            admin.setPasswordHash(passwordEncoder.encode("AdminPass123!"));
            userRepository.save(admin);
        }

        // 3. Operator
        if (userRepository.findByEmailIgnoreCase("operator@whereismyferry.bzh").isEmpty()) {
            User operator = new User();
            operator.setEmail("operator@whereismyferry.bzh");
            operator.setPasswordHash(passwordEncoder.encode("OperatorPass123!"));
            operator.setFullName("Operator Port");
            operator.setFirstName("Operator");
            operator.setLastName("Port");
            operator.setRole(com.whereismyferry.backend.entity.UserRole.OPERATOR);
            operator.setStatus(com.whereismyferry.backend.entity.UserStatus.ACTIVE);
            operator.setRoles(Set.of(roleOperator, rolePassenger));
            operator.setEnabled(true);
            operator.setEmailVerified(true);
            userRepository.save(operator);
        }

        // 4. Crew
        if (userRepository.findByEmailIgnoreCase("crew@whereismyferry.bzh").isEmpty()) {
            User crew = new User();
            crew.setEmail("crew@whereismyferry.bzh");
            crew.setPasswordHash(passwordEncoder.encode("CrewPass123!"));
            crew.setFullName("Captain Fromveur");
            crew.setFirstName("Captain");
            crew.setLastName("Fromveur");
            crew.setRole(com.whereismyferry.backend.entity.UserRole.CREW);
            crew.setStatus(com.whereismyferry.backend.entity.UserStatus.ACTIVE);
            crew.setRoles(Set.of(roleCrew, rolePassenger));
            crew.setEnabled(true);
            crew.setEmailVerified(true);
            userRepository.save(crew);
        }

        // 5. Passenger
        if (userRepository.findByEmailIgnoreCase("passenger@whereismyferry.bzh").isEmpty()) {
            User passenger = new User();
            passenger.setEmail("passenger@whereismyferry.bzh");
            passenger.setPasswordHash(passwordEncoder.encode("PassengerPass123!"));
            passenger.setFullName("Yann Penn");
            passenger.setFirstName("Yann");
            passenger.setLastName("Penn");
            passenger.setRole(com.whereismyferry.backend.entity.UserRole.PASSENGER);
            passenger.setStatus(com.whereismyferry.backend.entity.UserStatus.ACTIVE);
            passenger.setRoles(Set.of(rolePassenger));
            passenger.setEnabled(true);
            passenger.setEmailVerified(true);
            userRepository.save(passenger);
        }

        // 5. Auditor (Read-only privileged inspector)
        if (userRepository.findByEmailIgnoreCase("auditor@whereismyferry.bzh").isEmpty()) {
            User auditor = new User();
            auditor.setEmail("auditor@whereismyferry.bzh");
            auditor.setPasswordHash(passwordEncoder.encode("AuditorPass123!"));
            auditor.setFirstName("Auditor");
            auditor.setLastName("Maritime");
            auditor.setRoles(Set.of(roleAuditor));
            auditor.setEnabled(true);
            userRepository.save(auditor);
        }

        // 6. Support (Customer finance and assistance agent)
        if (userRepository.findByEmailIgnoreCase("support@whereismyferry.bzh").isEmpty()) {
            User support = new User();
            support.setEmail("support@whereismyferry.bzh");
            support.setPasswordHash(passwordEncoder.encode("SupportPass123!"));
            support.setFirstName("Support");
            support.setLastName("Agent");
            support.setRoles(Set.of(roleSupport));
            support.setEnabled(true);
            userRepository.save(support);
        }
        log.info("Default seed users verified: admin, operator, crew, passenger, auditor, support");
    }

    private void seedPorts() {
        if (portRepository.count() > 0) {
            return;
        }

        try {
            ClassPathResource resource = new ClassPathResource("catalog/stops.txt");
            if (!resource.exists()) {
                log.warn("catalog/stops.txt not found, using default port definitions");
                seedDefaultPorts();
                return;
            }

            try (BufferedReader reader = new BufferedReader(new InputStreamReader(resource.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                boolean header = true;
                while ((line = reader.readLine()) != null) {
                    line = line.trim();
                    if (line.isEmpty()) continue;
                    if (header) {
                        header = false;
                        continue;
                    }
                    String[] parts = line.split(",");
                    if (parts.length >= 4) {
                        String id = parts[0].trim();
                        String name = parts[1].trim();
                        double lat = Double.parseDouble(parts[2].trim());
                        double lon = Double.parseDouble(parts[3].trim());
                        Port port = new Port(id, id, name, lat, lon, "Europe/Paris", "Waiting room, Restrooms, Ticket desk, Wi-Fi", 2);
                        portRepository.save(port);
                    }
                }
            }
            log.info("Loaded {} ports from stops.txt", portRepository.count());
        } catch (Exception e) {
            log.error("Failed to load stops.txt, loading fallback ports: {}", e.getMessage());
            seedDefaultPorts();
        }
    }

    private void seedDefaultPorts() {
        Map<String, double[]> coords = Map.of(
            "BREST", new double[]{48.3828, -4.4855},
            "LE_CONQUET", new double[]{48.3585, -4.7788},
            "MOLENE", new double[]{48.3970, -4.9965},
            "OUESSANT_STIFF", new double[]{48.4632, -5.0492},
            "AUDIERNE", new double[]{48.0195, -4.5385},
            "ILE_DE_SEIN", new double[]{48.0375, -4.8505},
            "CAMARET", new double[]{48.2780, -4.5940}
        );

        coords.forEach((code, latlon) -> {
            if (portRepository.findById(code).isEmpty()) {
                Port port = new Port(code, code, "Port of " + code, latlon[0], latlon[1], "Europe/Paris", "Ticket counter, Parking", 2);
                portRepository.save(port);
            }
        });
    }

    private void seedVessels() {
        if (vesselRepository.count() > 0) {
            return;
        }

        List<Vessel> vessels = List.of(
            new Vessel("V-FROMVEUR-SIM", "FROMVEUR_II", "SIM_FROMVEUR_EXPRESS", "227005551", "9553751", 365, 0, 20.0, "V-FROMVEUR-SIM", "ACTIVE"),
            new Vessel("V-AZENOR-SIM", "ANDRE_COLIN", "SIM_AZENOR_VOYAGER", "227005552", "9136058", 250, 0, 18.0, "V-AZENOR-SIM", "ACTIVE"),
            new Vessel("V-OUESSANT-SIM", "ENEZ_EUSSA_3", "SIM_IROISE_STAR", "227005553", "9037446", 320, 0, 19.0, "V-OUESSANT-SIM", "ACTIVE"),
            new Vessel("V-SEIN-SIM", "ENEZ_SUN_3", "SIM_SEIN_SHUTTLE", "227005554", "8917821", 200, 0, 16.0, "V-SEIN-SIM", "ACTIVE")
        );

        vesselRepository.saveAll(vessels);
        log.info("Loaded {} fleet vessels", vessels.size());
    }

    private void seedRoutesAndSchedules() {
        if (scheduleRepository.count() > 0) {
            return;
        }

        try {
            ClassPathResource resource = new ClassPathResource("catalog/services.json");
            if (!resource.exists()) {
                log.warn("catalog/services.json not found");
                return;
            }

            try (InputStream is = resource.getInputStream()) {
                JsonNode root = objectMapper.readTree(is);
                if (root.isArray()) {
                    for (JsonNode node : root) {
                        String routeId = node.path("route_id").asText();
                        String routeName = node.path("route_name").asText();
                        String origId = node.path("origin_terminal_id").asText();
                        String destId = node.path("dest_terminal_id").asText();
                        double duration = node.path("duration_minutes").asDouble(60.0);
                        boolean trackingSupported = node.path("tracking_supported").asBoolean(false);

                        Port origPort = portRepository.findById(origId).orElse(null);
                        Port destPort = portRepository.findById(destId).orElse(null);
                        if (origPort == null || destPort == null) {
                            continue;
                        }

                        final String corridor = node.path("corridor").asText(null);
                        Route route = routeRepository.findById(routeId).orElseGet(() -> {
                            Route r = new Route(routeId, routeId, origPort, destPort, routeName, 15.0, duration, trackingSupported);
                            r.setEngineCorridorId(corridor);
                            r.setTypicalDurationMin(duration);
                            r.setDistanceKm(15.0 * 1.852);
                            return routeRepository.save(r);
                        });
                        if (route.getEngineCorridorId() == null && corridor != null) {
                            route.setEngineCorridorId(corridor);
                            route.setTypicalDurationMin(duration);
                            route.setDistanceKm(15.0 * 1.852);
                            routeRepository.save(route);
                        }

                        String tripId = node.path("trip_id").asText();
                        String serviceId = node.path("service_id").asText("DAILY_YEAR_ROUND");
                        String vesselId = node.path("vessel_id").asText();
                        Vessel vessel = vesselRepository.findById(vesselId).orElse(null);
                        if (vessel == null) {
                            vessel = vesselRepository.findAll().stream().findFirst().orElse(null);
                        }

                        String depTimeStr = node.path("departure_time").asText();
                        String arrTimeStr = node.path("arrival_time").asText();
                        LocalTime depTime = LocalTime.parse(depTimeStr.length() == 8 ? depTimeStr : depTimeStr + ":00");
                        LocalTime arrTime = LocalTime.parse(arrTimeStr.length() == 8 ? arrTimeStr : arrTimeStr + ":00");

                        JsonNode days = node.path("days_of_week");
                        boolean mon = days.path("monday").asBoolean(true);
                        boolean tue = days.path("tuesday").asBoolean(true);
                        boolean wed = days.path("wednesday").asBoolean(true);
                        boolean thu = days.path("thursday").asBoolean(true);
                        boolean fri = days.path("friday").asBoolean(true);
                        boolean sat = days.path("saturday").asBoolean(true);
                        boolean sun = days.path("sunday").asBoolean(true);

                        List<String> dows = new ArrayList<>();
                        if (mon) dows.add("1");
                        if (tue) dows.add("2");
                        if (wed) dows.add("3");
                        if (thu) dows.add("4");
                        if (fri) dows.add("5");
                        if (sat) dows.add("6");
                        if (sun) dows.add("7");
                        String daysOfWeekStr = String.join(",", dows);

                        JsonNode season = node.path("season_validity");
                        DateTimeFormatter ymd = DateTimeFormatter.ofPattern("yyyyMMdd");
                        LocalDate validFrom = LocalDate.parse(season.path("start_date").asText("20260101"), ymd);
                        LocalDate validTo = LocalDate.parse(season.path("end_date").asText("20261231"), ymd);

                        Schedule schedule = new Schedule();
                        schedule.setServiceId(serviceId);
                        schedule.setTripId(tripId);
                        schedule.setRoute(route);
                        schedule.setVessel(vessel);
                        schedule.setDepartureTime(depTime);
                        schedule.setArrivalTime(arrTime);
                        schedule.setMonday(mon);
                        schedule.setTuesday(tue);
                        schedule.setWednesday(wed);
                        schedule.setThursday(thu);
                        schedule.setFriday(fri);
                        schedule.setSaturday(sat);
                        schedule.setSunday(sun);
                        schedule.setValidFrom(validFrom);
                        schedule.setValidTo(validTo);
                        schedule.setActive(true);

                        scheduleRepository.save(schedule);

                        // Seed ServiceEntity for the new services table
                        ServiceEntity serviceEntity = new ServiceEntity(
                                route,
                                vessel,
                                depTime,
                                duration,
                                daysOfWeekStr,
                                validFrom,
                                validTo,
                                BigDecimal.valueOf(25.00),
                                vessel != null && vessel.getCapacity() != null ? vessel.getCapacity() : 300,
                                true
                        );
                        serviceEntityRepository.save(serviceEntity);
                    }
                }
            }
            log.info("Loaded {} routes, {} schedules, and {} service entities from services.json",
                    routeRepository.count(), scheduleRepository.count(), serviceEntityRepository.count());
        } catch (Exception e) {
            log.error("Failed to seed services.json: {}", e.getMessage(), e);
        }
    }

    private void seedFareRules() {
        if (fareRuleRepository.count() > 0) {
            return;
        }

        List<Route> routes = routeRepository.findAll();
        List<FareRule> rules = new ArrayList<>();

        for (Route route : routes) {
            BigDecimal base = BigDecimal.valueOf(25.00);
            if (route.getName().contains("Ouessant")) {
                base = BigDecimal.valueOf(32.50);
            } else if (route.getName().contains("Molène") || route.getName().contains("Molene")) {
                base = BigDecimal.valueOf(28.00);
            } else if (route.getName().contains("Sein")) {
                base = BigDecimal.valueOf(24.00);
            }

            rules.add(new FareRule(route, "ADULT", "NONE", base, "EUR"));
            rules.add(new FareRule(route, "CHILD", "NONE", base.multiply(BigDecimal.valueOf(0.60)), "EUR"));
            rules.add(new FareRule(route, "SENIOR", "NONE", base.multiply(BigDecimal.valueOf(0.85)), "EUR"));
            rules.add(new FareRule(route, "RESIDENT", "NONE", base.multiply(BigDecimal.valueOf(0.50)), "EUR"));
            rules.add(new FareRule(route, "ADULT", "BICYCLE", base.add(BigDecimal.valueOf(10.00)), "EUR"));
        }

        fareRuleRepository.saveAll(rules);
        log.info("Loaded {} standard fare rules", rules.size());
    }
}
