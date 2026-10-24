package com.whereismyferry.backend.service;

import com.whereismyferry.backend.entity.Departure;
import com.whereismyferry.backend.entity.Route;
import com.whereismyferry.backend.entity.Schedule;
import com.whereismyferry.backend.entity.Vessel;
import com.whereismyferry.backend.repository.DepartureRepository;
import com.whereismyferry.backend.repository.ScheduleRepository;
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
import java.util.List;

@Service
public class DepartureGeneratorService {

    private static final Logger log = LoggerFactory.getLogger(DepartureGeneratorService.class);
    private static final ZoneId PARIS_ZONE = ZoneId.of("Europe/Paris");
    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final DateTimeFormatter TIME_FMT = DateTimeFormatter.ofPattern("HHmm");

    private final ScheduleRepository scheduleRepository;
    private final DepartureRepository departureRepository;

    public DepartureGeneratorService(ScheduleRepository scheduleRepository, DepartureRepository departureRepository) {
        this.scheduleRepository = scheduleRepository;
        this.departureRepository = departureRepository;
    }

    @EventListener(ApplicationReadyEvent.class)
    @Order(10) // Run after DatabaseSeederService
    @Transactional
    public void onStartup() {
        if (departureRepository.count() == 0) {
            log.info("Generating initial departures for the next 30 days...");
            int count = generateDepartures(30);
            log.info("Initial departure generation complete: {} departures created.", count);
        }
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
    }

    /**
     * Generates departures from today up to daysAhead into the future.
     * Returns count of newly created departures.
     */
    @Transactional
    public int generateDepartures(int daysAhead) {
        LocalDate startDate = LocalDate.now(PARIS_ZONE);
        LocalDate endDate = startDate.plusDays(daysAhead);

        List<Schedule> schedules = scheduleRepository.findByActiveTrue();
        int createdCount = 0;

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

                // Check duplicates
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

        return createdCount;
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
