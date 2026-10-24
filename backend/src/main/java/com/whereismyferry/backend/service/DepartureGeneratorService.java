package com.whereismyferry.backend.service;

import com.whereismyferry.backend.client.SimulationClient;
import com.whereismyferry.backend.entity.*;
import com.whereismyferry.backend.repository.BookingRepository;
import com.whereismyferry.backend.repository.DepartureRepository;
import com.whereismyferry.backend.repository.ScheduleRepository;
import com.whereismyferry.backend.repository.ServiceEntityRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
public class DepartureGeneratorService {

    private static final Logger log = LoggerFactory.getLogger(DepartureGeneratorService.class);
    private static final ZoneId PARIS_ZONE = ZoneId.of("Europe/Paris");
    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("HHmm");

    private final ScheduleRepository scheduleRepository;
    private final ServiceEntityRepository serviceEntityRepository;
    private final DepartureRepository departureRepository;
    private final BookingRepository bookingRepository;
    private final SimulationClient simulationClient;

    public DepartureGeneratorService(
            ScheduleRepository scheduleRepository,
            ServiceEntityRepository serviceEntityRepository,
            DepartureRepository departureRepository,
            BookingRepository bookingRepository,
            SimulationClient simulationClient) {
        this.scheduleRepository = scheduleRepository;
        this.serviceEntityRepository = serviceEntityRepository;
        this.departureRepository = departureRepository;
        this.bookingRepository = bookingRepository;
        this.simulationClient = simulationClient;
    }

    @EventListener(ApplicationReadyEvent.class)
    @Order(10) // Run after DatabaseSeederService
    @Transactional
    public void onStartup() {
        if (departureRepository.count() == 0) {
            log.info("Generating initial departures for the next 60 days...");
            int count = generateDepartures(60);
            log.info("Initial departure generation complete: {} departures created.", count);
        }
        syncTodayDeparturesWithEngine();
    }

    /**
     * Daily scheduled generator to keep departures generated 60 days ahead.
     */
    @Scheduled(cron = "0 0 1 * * ?")
    @Transactional
    public void scheduledDailyGeneration() {
        log.info("Running scheduled departure generator for 60 days ahead...");
        int count = generateDepartures(60);
        log.info("Daily scheduled departure generation generated {} new departures.", count);
        syncTodayDeparturesWithEngine();
    }

    /**
     * Generates departures from today up to daysAhead into the future.
     * Returns count of newly created departures.
     */
    @Transactional
    public int generateDepartures(int daysAhead) {
        LocalDate startDate = LocalDate.now(PARIS_ZONE);
        LocalDate endDate = startDate.plusDays(daysAhead);
        int createdCount = 0;

        List<ServiceEntity> services = serviceEntityRepository.findByActiveTrue();
        if (!services.isEmpty()) {
            for (LocalDate date = startDate; !date.isAfter(endDate); date = date.plusDays(1)) {
                int dowInt = date.getDayOfWeek().getValue(); // 1=Mon, 7=Sun
                String dowStr = String.valueOf(dowInt);

                for (ServiceEntity service : services) {
                    if (service.getDaysOfWeek() != null && !service.getDaysOfWeek().contains(dowStr)) {
                        continue;
                    }
                    if (date.isBefore(service.getValidFrom()) || date.isAfter(service.getValidTo())) {
                        continue;
                    }

                    Route route = service.getRoute();
                    Vessel vessel = service.getVessel();
                    LocalTime depTime = service.getDepartureTime();
                    long durationMins = Math.round(service.getDurationMin() != null ? service.getDurationMin() : 60.0);

                    ZonedDateTime depZdt = ZonedDateTime.of(date, depTime, PARIS_ZONE);
                    ZonedDateTime arrZdt = depZdt.plusMinutes(durationMins);

                    OffsetDateTime depOdt = depZdt.toOffsetDateTime();
                    OffsetDateTime arrOdt = arrZdt.toOffsetDateTime();

                    String origCode = route.getOriginPort().getCode();
                    String destCode = route.getDestinationPort().getCode();
                    String depCode = String.format("DEP-%s-%s-%s-%s",
                            date.format(DATE_FMT),
                            origCode,
                            destCode,
                            depTime.format(TIME_FMT));

                    // Idempotent: check duplicates
                    if (departureRepository.existsByDepartureCode(depCode)) {
                        continue;
                    }
                    if (departureRepository.existsByVesselIdAndScheduledDepartureTime(vessel.getId(), depOdt)) {
                        continue;
                    }

                    Departure departure = new Departure(depCode, route, vessel, depOdt, arrOdt, "SCHEDULED");
                    departure.setServiceId(service.getId());
                    departure.setSeatsAvailable(service.getCapacity() != null ? service.getCapacity() : 250);
                    departureRepository.save(departure);
                    createdCount++;
                }
            }
        } else {
            // Fallback to legacy schedules if services table empty
            List<Schedule> schedules = scheduleRepository.findByActiveTrue();
            for (LocalDate date = startDate; !date.isAfter(endDate); date = date.plusDays(1)) {
                DayOfWeek dow = date.getDayOfWeek();
                for (Schedule schedule : schedules) {
                    if (!isDayValid(schedule, dow)) {
                        continue;
                    }
                    if (date.isBefore(schedule.getValidFrom()) || date.isAfter(schedule.getValidTo())) {
                        continue;
                    }

                    Route route = schedule.getRoute();
                    Vessel vessel = schedule.getVessel();
                    LocalTime depTime = schedule.getDepartureTime();
                    LocalTime arrTime = schedule.getArrivalTime();

                    ZonedDateTime depZdt = ZonedDateTime.of(date, depTime, PARIS_ZONE);
                    LocalDate arrDate = arrTime.isBefore(depTime) ? date.plusDays(1) : date;
                    ZonedDateTime arrZdt = ZonedDateTime.of(arrDate, arrTime, PARIS_ZONE);

                    OffsetDateTime depOdt = depZdt.toOffsetDateTime();
                    OffsetDateTime arrOdt = arrZdt.toOffsetDateTime();

                    String origCode = route.getOriginPort().getCode();
                    String destCode = route.getDestinationPort().getCode();
                    String depCode = String.format("DEP-%s-%s-%s-%s",
                            date.format(DATE_FMT),
                            origCode,
                            destCode,
                            depTime.format(TIME_FMT));

                    if (departureRepository.existsByDepartureCode(depCode)) {
                        continue;
                    }
                    if (departureRepository.existsByVesselIdAndScheduledDepartureTime(vessel.getId(), depOdt)) {
                        continue;
                    }

                    Departure departure = new Departure(depCode, route, vessel, depOdt, arrOdt, "SCHEDULED");
                    departureRepository.save(departure);
                    createdCount++;
                }
            }
        }

        return createdCount;
    }

    /**
     * Pushes today's scheduled departures from PostgreSQL to the Python simulation engine
     * for historical replay synchronization.
     */
    @Transactional(readOnly = true)
    public Map<String, Object> syncTodayDeparturesWithEngine() {
        try {
            LocalDate today = LocalDate.now(PARIS_ZONE);
            ZonedDateTime startOfDay = today.atStartOfDay(PARIS_ZONE);
            ZonedDateTime endOfDay = today.plusDays(1).atStartOfDay(PARIS_ZONE).minusNanos(1);

            List<Departure> todayDeps = departureRepository.findByScheduledDepartureTimeBetweenOrderByScheduledDepartureTimeAsc(
                    startOfDay.toOffsetDateTime(), endOfDay.toOffsetDateTime());

            List<Map<String, Object>> payloadList = new ArrayList<>();
            for (Departure dep : todayDeps) {
                Map<String, Object> depMap = new HashMap<>();
                depMap.put("departure_id", dep.getDepartureCode());
                depMap.put("id", dep.getId());
                depMap.put("departureCode", dep.getDepartureCode());
                depMap.put("corridor", dep.getRoute().getEngineCorridorId() != null
                        ? dep.getRoute().getEngineCorridorId()
                        : (dep.getRoute().getCode().contains("BRE") ? "BREST_LE_CONQUET" : "CONQUET_OUESSANT"));
                depMap.put("origin_terminal_id", dep.getRoute().getOriginPort().getCode());
                depMap.put("dest_terminal_id", dep.getRoute().getDestinationPort().getCode());
                depMap.put("vessel_id", dep.getVessel().getEngineVesselId() != null
                        ? dep.getVessel().getEngineVesselId()
                        : dep.getVessel().getId());
                depMap.put("vessel_name", dep.getVessel().getName());
                depMap.put("scheduled_departure_utc", dep.getScheduledDepartureTime().toString());
                depMap.put("scheduled_arrival_utc", dep.getScheduledArrivalTime().toString());
                depMap.put("tracking_supported", Boolean.TRUE.equals(dep.getRoute().getTrackingSupported()));
                depMap.put("duration_minutes", dep.getRoute().getTypicalDurationMin() != null
                        ? dep.getRoute().getTypicalDurationMin()
                        : dep.getRoute().getCrossingDurationMinutes());

                payloadList.add(depMap);
            }

            log.info("Syncing {} today departures with Python simulation engine...", payloadList.size());
            Map<String, Object> res = simulationClient.syncTimetable(payloadList);
            log.info("Simulation engine sync response: {}", res);
            return res;
        } catch (Exception e) {
            log.warn("Could not sync today departures with simulation engine: {}", e.getMessage());
            return Map.of("status", "FAILED", "error", e.getMessage());
        }
    }

    private boolean isDayValid(Schedule schedule, DayOfWeek dow) {
        return switch (dow) {
            case MONDAY -> Boolean.TRUE.equals(schedule.getMonday());
            case TUESDAY -> Boolean.TRUE.equals(schedule.getTuesday());
            case WEDNESDAY -> Boolean.TRUE.equals(schedule.getWednesday());
            case THURSDAY -> Boolean.TRUE.equals(schedule.getThursday());
            case FRIDAY -> Boolean.TRUE.equals(schedule.getFriday());
            case SATURDAY -> Boolean.TRUE.equals(schedule.getSaturday());
            case SUNDAY -> Boolean.TRUE.equals(schedule.getSunday());
        };
    }
}
