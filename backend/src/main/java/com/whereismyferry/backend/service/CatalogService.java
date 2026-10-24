package com.whereismyferry.backend.service;

import com.whereismyferry.backend.dto.*;
import com.whereismyferry.backend.entity.*;
import com.whereismyferry.backend.exception.ResourceNotFoundException;
import com.whereismyferry.backend.repository.*;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.math.BigDecimal;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Service
@Transactional(readOnly = true)
public class CatalogService {

    private static final ZoneId PARIS_ZONE = ZoneId.of("Europe/Paris");

    private final PortRepository portRepository;
    private final RouteRepository routeRepository;
    private final VesselRepository vesselRepository;
    private final ScheduleRepository scheduleRepository;
    private final DepartureRepository departureRepository;
    private final FareRuleRepository fareRuleRepository;
    private final AnnouncementRepository announcementRepository;

    public CatalogService(
            PortRepository portRepository,
            RouteRepository routeRepository,
            VesselRepository vesselRepository,
            ScheduleRepository scheduleRepository,
            DepartureRepository departureRepository,
            FareRuleRepository fareRuleRepository,
            AnnouncementRepository announcementRepository) {
        this.portRepository = portRepository;
        this.routeRepository = routeRepository;
        this.vesselRepository = vesselRepository;
        this.scheduleRepository = scheduleRepository;
        this.departureRepository = departureRepository;
        this.fareRuleRepository = fareRuleRepository;
        this.announcementRepository = announcementRepository;
    }

    public List<PortDto> getAllPorts() {
        return portRepository.findAll().stream()
                .map(this::mapPortToDto)
                .sorted(Comparator.comparing(PortDto::getName))
                .collect(Collectors.toList());
    }

    public List<PortDto> getReachableDestinations(String originPortId) {
        if (originPortId == null || originPortId.isBlank()) {
            return Collections.emptyList();
        }
        List<Route> routes = routeRepository.findByOriginPortId(originPortId);
        return routes.stream()
                .map(Route::getDestinationPort)
                .distinct()
                .map(this::mapPortToDto)
                .sorted(Comparator.comparing(PortDto::getName))
                .collect(Collectors.toList());
    }

    public PortDetailDto getPortDetail(String portId) {
        Port port = portRepository.findById(portId)
                .or(() -> portRepository.findByCodeIgnoreCase(portId))
                .orElseThrow(() -> new ResourceNotFoundException("Port not found: " + portId));

        PortDetailDto detail = new PortDetailDto();
        detail.setId(port.getId());
        detail.setCode(port.getCode());
        detail.setName(port.getName());
        detail.setLatitude(port.getLatitude());
        detail.setLongitude(port.getLongitude());
        detail.setTimezone(port.getTimezone());
        detail.setAmenities(port.getAmenities());
        detail.setBerthCount(port.getBerthCount());
        detail.setBerthRadiusM(port.getBerthRadiusM());
        detail.setStatus(port.getStatus());
        detail.setAddress(port.getAddress());
        detail.setPhone(port.getPhone());
        detail.setEmail(port.getEmail());
        detail.setFacilities(port.getFacilities());
        detail.setNotes(port.getNotes());

        OffsetDateTime now = OffsetDateTime.now(PARIS_ZONE);
        OffsetDateTime windowEnd = now.plusHours(24);

        List<DepartureDto> upcomingDeps = departureRepository.findDeparturesFromPort(port.getId(), now.minusHours(1), windowEnd)
                .stream().map(this::mapDepartureToDto).collect(Collectors.toList());
        List<DepartureDto> upcomingArrs = departureRepository.findArrivalsToPort(port.getId(), now.minusHours(1), windowEnd)
                .stream().map(this::mapDepartureToDto).collect(Collectors.toList());

        detail.setUpcomingDepartures(upcomingDeps);
        detail.setUpcomingArrivals(upcomingArrs);

        return detail;
    }

    public List<RouteDto> getAllRoutes() {
        return routeRepository.findAll().stream()
                .map(this::mapRouteToDto)
                .sorted(Comparator.comparing(RouteDto::getName))
                .collect(Collectors.toList());
    }

    public RouteDto getRouteById(String routeId) {
        Route route = routeRepository.findById(routeId)
                .or(() -> routeRepository.findByCodeIgnoreCase(routeId))
                .orElseThrow(() -> new ResourceNotFoundException("Route not found: " + routeId));
        return mapRouteToDto(route);
    }

    public List<DepartureDto> searchDepartures(String fromPortId, String toPortId, LocalDate date, Integer passengerCount) {
        LocalDate queryDate = date != null ? date : LocalDate.now(PARIS_ZONE);
        ZonedDateTime startZdt = queryDate.atStartOfDay(PARIS_ZONE);
        ZonedDateTime endZdt = queryDate.atTime(23, 59, 59).atZone(PARIS_ZONE);

        List<Departure> departures = departureRepository.findDepartures(
                fromPortId,
                toPortId,
                startZdt.toOffsetDateTime(),
                endZdt.toOffsetDateTime());

        return departures.stream()
                .filter(d -> passengerCount == null || d.getVessel().getCapacityPassengers() >= passengerCount)
                .map(this::mapDepartureToDto)
                .collect(Collectors.toList());
    }

    /**
     * Phase D1: Full From-To Search with strict validation, filters, pricing, and next sailing empty state.
     */
    public DepartureSearchResultDto searchSailings(String fromPortId, String toPortId, LocalDate date,
                                                   Integer passengers, String timeOfDay, String status) {
        // 1. Validation
        if (fromPortId == null || fromPortId.isBlank() || toPortId == null || toPortId.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Both origin and destination ports are required");
        }
        if (fromPortId.equalsIgnoreCase(toPortId)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Origin and destination cannot be the same");
        }

        Port originPort = portRepository.findById(fromPortId)
                .or(() -> portRepository.findByCodeIgnoreCase(fromPortId))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unknown origin port: " + fromPortId));

        Port destPort = portRepository.findById(toPortId)
                .or(() -> portRepository.findByCodeIgnoreCase(toPortId))
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unknown destination port: " + toPortId));

        List<Route> routes = routeRepository.findByOriginPortIdAndDestinationPortId(originPort.getId(), destPort.getId());
        if (routes.isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "No direct ferry service connects " + originPort.getName() + " to " + destPort.getName());
        }

        LocalDate today = LocalDate.now(PARIS_ZONE);
        LocalDate queryDate = date != null ? date : today;
        if (queryDate.isBefore(today)) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Cannot search departures in the past");
        }

        int pax = passengers != null ? passengers : 1;
        if (pax < 1 || pax > 10) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Passenger count must be between 1 and 10");
        }

        // 2. Query departures for the requested date
        ZonedDateTime startZdt = queryDate.atStartOfDay(PARIS_ZONE);
        ZonedDateTime endZdt = queryDate.atTime(23, 59, 59).atZone(PARIS_ZONE);

        List<Departure> rawDepartures = departureRepository.findDepartures(
                originPort.getId(),
                destPort.getId(),
                startZdt.toOffsetDateTime(),
                endZdt.toOffsetDateTime());

        // 3. Apply filters: seats available, time of day, status
        List<DepartureSearchResultItemDto> items = rawDepartures.stream()
                .filter(d -> d.getSeatsAvailable() == null || d.getSeatsAvailable() >= pax)
                .filter(d -> {
                    if (timeOfDay == null || timeOfDay.isBlank() || "all".equalsIgnoreCase(timeOfDay)) {
                        return true;
                    }
                    int hour = d.getScheduledDepartureTime().atZoneSameInstant(PARIS_ZONE).getHour();
                    return switch (timeOfDay.toLowerCase()) {
                        case "morning" -> hour >= 5 && hour < 12;
                        case "afternoon" -> hour >= 12 && hour < 18;
                        case "evening" -> hour >= 18;
                        default -> true;
                    };
                })
                .filter(d -> {
                    if (status == null || status.isBlank() || "all".equalsIgnoreCase(status)) {
                        return true;
                    }
                    return d.getStatus().equalsIgnoreCase(status);
                })
                .sorted(Comparator.comparing(Departure::getScheduledDepartureTime))
                .map(d -> mapToSearchResultItem(d, pax))
                .collect(Collectors.toList());

        DepartureSearchResultDto result = new DepartureSearchResultDto();
        result.setOriginPortId(originPort.getId());
        result.setOriginPortName(originPort.getName());
        result.setDestinationPortId(destPort.getId());
        result.setDestinationPortName(destPort.getName());
        result.setSearchDate(queryDate);
        result.setPassengers(pax);
        result.setTotalResults(items.size());
        result.setDepartures(items);

        // 4. Empty state handling: find next available sailing
        if (items.isEmpty()) {
            ZonedDateTime futureSearchEnd = endZdt.plusDays(30);
            List<Departure> futureDeps = departureRepository.findDepartures(
                    originPort.getId(),
                    destPort.getId(),
                    endZdt.plusSeconds(1).toOffsetDateTime(),
                    futureSearchEnd.toOffsetDateTime());

            Optional<Departure> nextOpt = futureDeps.stream()
                    .filter(d -> d.getSeatsAvailable() == null || d.getSeatsAvailable() >= pax)
                    .min(Comparator.comparing(Departure::getScheduledDepartureTime));

            if (nextOpt.isPresent()) {
                Departure next = nextOpt.get();
                DepartureSearchResultItemDto nextDto = mapToSearchResultItem(next, pax);
                result.setNextAvailableSailing(nextDto);

                ZonedDateTime nextZdt = next.getScheduledDepartureTime().atZoneSameInstant(PARIS_ZONE);
                DateTimeFormatter dFmt = DateTimeFormatter.ofPattern("d MMM yyyy", Locale.ENGLISH);
                DateTimeFormatter tFmt = DateTimeFormatter.ofPattern("HH:mm");
                result.setEmptyStateMessage(String.format("No sailings on this date. Next sailing: %s, %s",
                        nextZdt.format(dFmt), nextZdt.format(tFmt)));
            } else {
                result.setEmptyStateMessage("No sailings available on this route for the requested date.");
            }
        }

        return result;
    }

    private DepartureSearchResultItemDto mapToSearchResultItem(Departure dep, int passengers) {
        DepartureSearchResultItemDto item = new DepartureSearchResultItemDto();
        item.setId(dep.getId());
        item.setDepartureCode(dep.getDepartureCode());
        item.setRouteId(dep.getRoute().getId());
        item.setRouteName(dep.getRoute().getName());
        item.setOriginPortId(dep.getRoute().getOriginPort().getId());
        item.setOriginPortName(dep.getRoute().getOriginPort().getName());
        item.setDestinationPortId(dep.getRoute().getDestinationPort().getId());
        item.setDestinationPortName(dep.getRoute().getDestinationPort().getName());
        item.setScheduledDepartureTime(dep.getScheduledDepartureTime());
        item.setScheduledArrivalTime(dep.getScheduledArrivalTime());

        double duration = dep.getRoute().getTypicalDurationMin() != null ?
                dep.getRoute().getTypicalDurationMin() : dep.getRoute().getCrossingDurationMinutes();
        item.setDurationMinutes(duration);

        item.setVesselId(dep.getVessel().getId());
        item.setVesselName(dep.getVessel().getName());
        item.setStatus(dep.getStatus());
        item.setDelayMinutes(dep.getDelayMinutes() != null ? dep.getDelayMinutes() : 0);

        // Status text label
        if ("CANCELLED".equalsIgnoreCase(dep.getStatus())) {
            item.setStatusLabel("Cancelled");
        } else if ("ARRIVED".equalsIgnoreCase(dep.getStatus())) {
            item.setStatusLabel("Arrived");
        } else if (dep.getDelayMinutes() != null && dep.getDelayMinutes() > 0) {
            item.setStatusLabel("Delayed +" + dep.getDelayMinutes() + " min");
        } else {
            item.setStatusLabel("On time");
        }

        item.setSeatsAvailable(dep.getSeatsAvailable() != null ? dep.getSeatsAvailable() : dep.getVessel().getCapacityPassengers());

        // Base price calculation
        BigDecimal base = BigDecimal.valueOf(25.00);
        List<FareRule> rules = fareRuleRepository.findByRouteId(dep.getRoute().getId());
        for (FareRule r : rules) {
            if ("ADULT".equalsIgnoreCase(r.getPassengerType()) && ("NONE".equalsIgnoreCase(r.getVehicleType()) || r.getVehicleType() == null)) {
                base = r.getBasePriceEur();
                break;
            }
        }
        item.setFromPriceEur(base.multiply(BigDecimal.valueOf(passengers)));

        // Live tracking only for modelled corridor/vessel
        boolean trackingSupported = Boolean.TRUE.equals(dep.getRoute().getTrackingSupported())
                && dep.getVessel().getEngineVesselId() != null;
        item.setLiveTrackingAvailable(trackingSupported);

        return item;
    }

    public List<AnnouncementDto> getActiveAnnouncements(String scope, String targetId) {
        OffsetDateTime now = OffsetDateTime.now(PARIS_ZONE);
        List<Announcement> list;
        if (scope != null && !scope.isBlank() && targetId != null && !targetId.isBlank()) {
            list = announcementRepository.findActiveByScopeOrAll(now, scope.toUpperCase(), targetId);
        } else {
            list = announcementRepository.findActiveAnnouncements(now);
        }
        return list.stream().map(this::mapAnnouncementToDto).collect(Collectors.toList());
    }

    public DepartureDto getDepartureById(Long id) {
        Departure departure = departureRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Departure not found with id: " + id));
        return mapDepartureToDto(departure);
    }

    public DepartureDto getDepartureByCode(String code) {
        Departure departure = departureRepository.findByDepartureCode(code)
                .orElseThrow(() -> new ResourceNotFoundException("Departure not found with code: " + code));
        return mapDepartureToDto(departure);
    }

    public List<TimetableEntryDto> getTimetable(String routeId, LocalDate date) {
        List<Schedule> schedules = routeId != null ?
                scheduleRepository.findByRouteId(routeId) :
                scheduleRepository.findByActiveTrue();

        LocalDate queryDate = date != null ? date : LocalDate.now(PARIS_ZONE);

        return schedules.stream()
                .filter(s -> !queryDate.isBefore(s.getValidFrom()) && !queryDate.isAfter(s.getValidTo()))
                .map(s -> {
                    TimetableEntryDto dto = new TimetableEntryDto();
                    dto.setTripId(s.getTripId());
                    dto.setServiceId(s.getServiceId());
                    dto.setRouteId(s.getRoute().getId());
                    dto.setRouteName(s.getRoute().getName());
                    dto.setOriginPortId(s.getRoute().getOriginPort().getId());
                    dto.setOriginPortName(s.getRoute().getOriginPort().getName());
                    dto.setDestinationPortId(s.getRoute().getDestinationPort().getId());
                    dto.setDestinationPortName(s.getRoute().getDestinationPort().getName());
                    dto.setDepartureTime(s.getDepartureTime());
                    dto.setArrivalTime(s.getArrivalTime());
                    dto.setDurationMinutes(s.getRoute().getTypicalDurationMin() != null ?
                            s.getRoute().getTypicalDurationMin() : s.getRoute().getCrossingDurationMinutes());
                    Map<String, Boolean> dowMap = Map.of(
                            "monday", Boolean.TRUE.equals(s.getMonday()),
                            "tuesday", Boolean.TRUE.equals(s.getTuesday()),
                            "wednesday", Boolean.TRUE.equals(s.getWednesday()),
                            "thursday", Boolean.TRUE.equals(s.getThursday()),
                            "friday", Boolean.TRUE.equals(s.getFriday()),
                            "saturday", Boolean.TRUE.equals(s.getSaturday()),
                            "sunday", Boolean.TRUE.equals(s.getSunday())
                    );
                    dto.setDaysOfWeek(dowMap);
                    dto.setVesselId(s.getVessel().getId());
                    dto.setVesselName(s.getVessel().getName());
                    dto.setTrackingSupported(s.getRoute().getTrackingSupported());
                    return dto;
                })
                .sorted(Comparator.comparing(TimetableEntryDto::getDepartureTime))
                .collect(Collectors.toList());
    }

    public List<FareRuleDto> getFareRules(String routeId) {
        List<FareRule> rules = routeId != null ?
                fareRuleRepository.findByRouteId(routeId) :
                fareRuleRepository.findAll();

        return rules.stream()
                .map(r -> new FareRuleDto(
                        r.getId(),
                        r.getRoute().getId(),
                        r.getPassengerType(),
                        r.getVehicleType(),
                        r.getBasePriceEur(),
                        r.getCurrency(),
                        r.getValidFrom(),
                        r.getValidTo()
                ))
                .collect(Collectors.toList());
    }

    public List<VesselDto> getAllVessels() {
        return vesselRepository.findAll().stream()
                .map(this::mapVesselToDto)
                .sorted(Comparator.comparing(VesselDto::getName))
                .collect(Collectors.toList());
    }

    public VesselDto getVesselById(String vesselId) {
        Vessel vessel = vesselRepository.findById(vesselId)
                .or(() -> vesselRepository.findByCodeIgnoreCase(vesselId))
                .orElseThrow(() -> new ResourceNotFoundException("Vessel not found: " + vesselId));
        return mapVesselToDto(vessel);
    }

    private PortDto mapPortToDto(Port port) {
        PortDto dto = new PortDto(
                port.getId(),
                port.getCode(),
                port.getName(),
                port.getLatitude(),
                port.getLongitude(),
                port.getTimezone(),
                port.getAmenities(),
                port.getBerthCount()
        );
        dto.setBerthRadiusM(port.getBerthRadiusM());
        dto.setStatus(port.getStatus());
        dto.setAddress(port.getAddress());
        dto.setPhone(port.getPhone());
        dto.setEmail(port.getEmail());
        dto.setFacilities(port.getFacilities());
        dto.setNotes(port.getNotes());
        return dto;
    }

    private RouteDto mapRouteToDto(Route route) {
        return new RouteDto(
                route.getId(),
                route.getCode(),
                route.getName(),
                route.getOriginPort().getId(),
                route.getOriginPort().getName(),
                route.getDestinationPort().getId(),
                route.getDestinationPort().getName(),
                route.getDistanceNm(),
                route.getCrossingDurationMinutes(),
                route.getTrackingSupported()
        );
    }

    private VesselDto mapVesselToDto(Vessel vessel) {
        return new VesselDto(
                vessel.getId(),
                vessel.getCode(),
                vessel.getName(),
                vessel.getMmsi(),
                vessel.getImo(),
                vessel.getCapacityPassengers(),
                vessel.getCapacityVehicles(),
                vessel.getSpeedKnots(),
                vessel.getTrackingVesselId(),
                vessel.getStatus()
        );
    }

    private DepartureDto mapDepartureToDto(Departure dep) {
        DepartureDto dto = new DepartureDto();
        dto.setId(dep.getId());
        dto.setDepartureCode(dep.getDepartureCode());
        dto.setRoute(mapRouteToDto(dep.getRoute()));
        dto.setVessel(mapVesselToDto(dep.getVessel()));
        dto.setScheduledDepartureTime(dep.getScheduledDepartureTime());
        dto.setScheduledArrivalTime(dep.getScheduledArrivalTime());
        dto.setActualDepartureTime(dep.getActualDepartureTime());
        dto.setActualArrivalTime(dep.getActualArrivalTime());
        dto.setStatus(dep.getStatus());
        dto.setDelayMinutes(dep.getDelayMinutes());

        boolean trackingSupported = Boolean.TRUE.equals(dep.getRoute().getTrackingSupported())
                && dep.getVessel().getEngineVesselId() != null;
        dto.setLiveTrackingAvailable(trackingSupported);
        if (trackingSupported) {
            dto.setLiveTrackingUrl("/api/v1/departures/" + dep.getDepartureCode() + "/live");
        }
        dto.setIsHistoricalReplay(true);

        return dto;
    }

    private AnnouncementDto mapAnnouncementToDto(Announcement a) {
        AnnouncementDto dto = new AnnouncementDto();
        dto.setId(a.getId());
        dto.setTitle(a.getTitle());
        dto.setBody(a.getBody());
        dto.setSeverity(a.getSeverity());
        dto.setScope(a.getScope());
        dto.setTargetId(a.getTargetId());
        dto.setStartsAt(a.getStartsAt());
        dto.setEndsAt(a.getEndsAt());
        dto.setCreatedBy(a.getCreatedBy());
        dto.setCreatedAt(a.getCreatedAt());
        return dto;
    }
}
