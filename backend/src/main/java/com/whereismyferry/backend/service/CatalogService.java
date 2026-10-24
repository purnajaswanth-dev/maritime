package com.whereismyferry.backend.service;

import com.whereismyferry.backend.dto.*;
import com.whereismyferry.backend.entity.*;
import com.whereismyferry.backend.exception.ResourceNotFoundException;
import com.whereismyferry.backend.repository.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
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

    public CatalogService(
            PortRepository portRepository,
            RouteRepository routeRepository,
            VesselRepository vesselRepository,
            ScheduleRepository scheduleRepository,
            DepartureRepository departureRepository,
            FareRuleRepository fareRuleRepository) {
        this.portRepository = portRepository;
        this.routeRepository = routeRepository;
        this.vesselRepository = vesselRepository;
        this.scheduleRepository = scheduleRepository;
        this.departureRepository = departureRepository;
        this.fareRuleRepository = fareRuleRepository;
    }

    public List<PortDto> getAllPorts() {
        return portRepository.findAll().stream()
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
                    dto.setDurationMinutes(s.getRoute().getCrossingDurationMinutes());
                    dto.setVesselId(s.getVessel().getId());
                    dto.setVesselName(s.getVessel().getName());
                    dto.setTrackingSupported(s.getRoute().getTrackingSupported());
                    dto.setDaysOfWeek(Map.of(
                            "monday", s.getMonday(),
                            "tuesday", s.getTuesday(),
                            "wednesday", s.getWednesday(),
                            "thursday", s.getThursday(),
                            "friday", s.getFriday(),
                            "saturday", s.getSaturday(),
                            "sunday", s.getSunday()
                    ));
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
        return new PortDto(
                port.getId(),
                port.getCode(),
                port.getName(),
                port.getLatitude(),
                port.getLongitude(),
                port.getTimezone(),
                port.getAmenities(),
                port.getBerthCount()
        );
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

        boolean trackingSupported = Boolean.TRUE.equals(dep.getRoute().getTrackingSupported());
        dto.setLiveTrackingAvailable(trackingSupported);
        if (trackingSupported) {
            dto.setLiveTrackingUrl("/api/v1/departures/" + dep.getDepartureCode() + "/live");
        }
        dto.setIsHistoricalReplay(true);

        return dto;
    }
}
