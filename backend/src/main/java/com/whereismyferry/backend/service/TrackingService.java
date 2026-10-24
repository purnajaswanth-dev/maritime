package com.whereismyferry.backend.service;

import com.whereismyferry.backend.client.SimulationClient;
import com.whereismyferry.backend.dto.*;
import com.whereismyferry.backend.entity.Departure;
import com.whereismyferry.backend.entity.ShareLink;
import com.whereismyferry.backend.exception.ResourceNotFoundException;
import com.whereismyferry.backend.repository.DepartureRepository;
import com.whereismyferry.backend.repository.ShareLinkRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.*;

@Service
public class TrackingService {

    private static final Logger log = LoggerFactory.getLogger(TrackingService.class);

    private final DepartureRepository departureRepository;
    private final ShareLinkRepository shareLinkRepository;
    private final SimulationClient simulationClient;
    private final CatalogService catalogService;
    private final ScheduledExecutorService sseExecutor = Executors.newScheduledThreadPool(4);

    @Value("${app.base-url:https://whereismyferry.bzh}")
    private String baseUrl;

    public TrackingService(
            DepartureRepository departureRepository,
            ShareLinkRepository shareLinkRepository,
            SimulationClient simulationClient,
            CatalogService catalogService) {
        this.departureRepository = departureRepository;
        this.shareLinkRepository = shareLinkRepository;
        this.simulationClient = simulationClient;
        this.catalogService = catalogService;
    }

    public SimulationLiveDto getLiveTracking(String departureIdentifier) {
        String depCode = resolveDepartureCode(departureIdentifier);
        return simulationClient.getLiveDeparture(depCode);
    }

    public Map<String, Object> getVoyageTrack(String departureIdentifier) {
        String depCode = resolveDepartureCode(departureIdentifier);
        return simulationClient.getDepartureTrack(depCode);
    }

    public SseEmitter subscribeFleetVesselsStream() {
        if (!simulationClient.isAvailable()) {
            throw new com.whereismyferry.backend.exception.SimulationEngineUnavailableException(
                    "Python simulation daemon is unreachable. Live vessel telemetry unavailable."
            );
        }

        SseEmitter emitter = new SseEmitter(120_000L);
        final java.util.Map<String, String> lastKnownStates = new java.util.concurrent.ConcurrentHashMap<>();

        // 1. Initial snapshot event
        try {
            java.util.List<com.whereismyferry.backend.dto.VesselLiveDto> initialSnapshot = simulationClient.getFleetVessels();
            for (com.whereismyferry.backend.dto.VesselLiveDto v : initialSnapshot) {
                if (v.getVesselId() != null && v.getEtaLifecycleState() != null) {
                    lastKnownStates.put(v.getVesselId(), v.getEtaLifecycleState());
                }
            }
            emitter.send(SseEmitter.event()
                    .name("snapshot")
                    .data(initialSnapshot));
        } catch (Exception e) {
            log.warn("Failed to send initial fleet snapshot: {}", e.getMessage());
        }

        // 2. Periodic telemetry updates, transition detector, and ping heartbeat
        ScheduledFuture<?> scheduledTask = sseExecutor.scheduleAtFixedRate(new Runnable() {
            private int tick = 0;

            @Override
            public void run() {
                tick++;
                try {
                    java.util.List<com.whereismyferry.backend.dto.VesselLiveDto> vessels = simulationClient.getFleetVessels();

                    // Send telemetry update
                    emitter.send(SseEmitter.event()
                            .name("telemetry_update")
                            .data(vessels));

                    // Check for lifecycle state transitions
                    for (com.whereismyferry.backend.dto.VesselLiveDto v : vessels) {
                        String vid = v.getVesselId();
                        String newState = v.getEtaLifecycleState();
                        if (vid != null && newState != null) {
                            String oldState = lastKnownStates.put(vid, newState);
                            if (oldState != null && !oldState.equals(newState)) {
                                emitter.send(SseEmitter.event()
                                        .name("eta_transition")
                                        .data(Map.of(
                                                "vessel_id", vid,
                                                "previous_state", oldState,
                                                "current_state", newState,
                                                "timestamp_utc", java.time.Instant.now().toString()
                                        )));
                            }
                        }
                    }

                    // Send ping heartbeat every 15 seconds
                    if (tick % 15 == 0) {
                        emitter.send(SseEmitter.event()
                                .name("ping")
                                .data(Map.of("timestamp", java.time.Instant.now().toString())));
                    }
                } catch (Exception e) {
                    log.debug("Fleet SSE emission error: {}", e.getMessage());
                    try {
                        emitter.send(SseEmitter.event()
                                .name("stale")
                                .data(Map.of("message", "Telemetry stream temporarily interrupted")));
                    } catch (Exception ignored) {}
                }
            }
        }, 1, 1, TimeUnit.SECONDS);

        emitter.onCompletion(() -> scheduledTask.cancel(true));
        emitter.onTimeout(() -> scheduledTask.cancel(true));
        emitter.onError(t -> scheduledTask.cancel(true));

        return emitter;
    }

    public SseEmitter subscribeLiveStream(String departureIdentifier) {
        String depCode = resolveDepartureCode(departureIdentifier);

        // 120-second timeout per SSE connection (client auto-reconnects per SSE spec)
        SseEmitter emitter = new SseEmitter(120_000L);

        ScheduledFuture<?> scheduledTask = sseExecutor.scheduleAtFixedRate(() -> {
            try {
                SimulationLiveDto live = simulationClient.getLiveDeparture(depCode);
                emitter.send(SseEmitter.event()
                        .name("live-update")
                        .data(live));
            } catch (Exception e) {
                log.debug("SSE emission error for departure {}: {}", depCode, e.getMessage());
                try {
                    emitter.send(SseEmitter.event()
                            .name("error")
                            .data(Map.of("message", "Telemetry stream temporarily interrupted")));
                } catch (Exception ignored) {}
            }
        }, 0, 1, TimeUnit.SECONDS);

        emitter.onCompletion(() -> scheduledTask.cancel(true));
        emitter.onTimeout(() -> scheduledTask.cancel(true));
        emitter.onError(t -> scheduledTask.cancel(true));

        return emitter;
    }

    @Transactional
    public ShareLinkResponseDto createShareLink(String departureIdentifier, int validHours) {
        Departure departure = findDeparture(departureIdentifier);
        int hours = validHours > 0 ? validHours : 24;
        OffsetDateTime expiresAt = OffsetDateTime.now().plusHours(hours);

        String token = UUID.randomUUID().toString().replace("-", "");

        ShareLink shareLink = new ShareLink();
        shareLink.setDeparture(departure);
        shareLink.setToken(token);
        shareLink.setExpiresAt(expiresAt);

        shareLinkRepository.save(shareLink);

        String shareUrl = baseUrl + "/track/" + token;
        return new ShareLinkResponseDto(token, shareUrl, departure.getDepartureCode(), expiresAt);
    }

    @Transactional(readOnly = true)
    public PublicTrackResponseDto resolveSharedTrack(String token) {
        ShareLink link = shareLinkRepository.findByToken(token)
                .orElseThrow(() -> new ResourceNotFoundException("Share link has expired or is invalid."));

        if (link.getExpiresAt().isBefore(OffsetDateTime.now())) {
            throw new ResourceNotFoundException("Share link has expired.");
        }

        Departure dep = link.getDeparture();
        DepartureDto depDto = catalogService.getDepartureById(dep.getId());

        PublicTrackResponseDto response = new PublicTrackResponseDto();
        response.setDepartureCode(dep.getDepartureCode());
        response.setRoute(depDto.getRoute());
        response.setVessel(depDto.getVessel());
        response.setScheduledDepartureTime(dep.getScheduledDepartureTime());
        response.setScheduledArrivalTime(dep.getScheduledArrivalTime());
        response.setStatus(dep.getStatus());
        response.setDelayMinutes(dep.getDelayMinutes());

        try {
            response.setLive(simulationClient.getLiveDeparture(dep.getDepartureCode()));
        } catch (Exception e) {
            log.warn("Could not fetch live telemetry for shared link {}: {}", token, e.getMessage());
        }

        try {
            response.setTrack(simulationClient.getDepartureTrack(dep.getDepartureCode()));
        } catch (Exception e) {
            log.warn("Could not fetch track coordinates for shared link {}: {}", token, e.getMessage());
        }

        return response;
    }

    private String resolveDepartureCode(String identifier) {
        try {
            Long numericId = Long.parseLong(identifier);
            return departureRepository.findById(numericId)
                    .map(Departure::getDepartureCode)
                    .orElse(identifier);
        } catch (NumberFormatException e) {
            return identifier;
        }
    }

    private Departure findDeparture(String identifier) {
        try {
            Long numericId = Long.parseLong(identifier);
            return departureRepository.findById(numericId)
                    .orElseThrow(() -> new ResourceNotFoundException("Departure not found: " + identifier));
        } catch (NumberFormatException e) {
            return departureRepository.findByDepartureCode(identifier)
                    .orElseThrow(() -> new ResourceNotFoundException("Departure not found with code: " + identifier));
        }
    }
}
