package com.whereismyferry.backend.client;

import com.whereismyferry.backend.dto.SimulationLiveDto;
import com.whereismyferry.backend.exception.ResourceNotFoundException;
import com.whereismyferry.backend.exception.SimulationEngineUnavailableException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;

@Component
public class RestClientSimulationClient implements SimulationClient {

    private final RestClient restClient;
    private final String daemonUrl;

    public RestClientSimulationClient(
            @Value("${ferry.simulation.daemon-url:http://127.0.0.1:8000}") String daemonUrl,
            @Value("${ferry.simulation.connect-timeout-ms:3000}") int connectTimeoutMs,
            @Value("${ferry.simulation.read-timeout-ms:5000}") int readTimeoutMs) {
        this.daemonUrl = daemonUrl;
        
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(connectTimeoutMs);
        factory.setReadTimeout(readTimeoutMs);

        this.restClient = RestClient.builder()
                .baseUrl(daemonUrl)
                .requestFactory(factory)
                .build();
    }

    @Override
    public SimulationLiveDto getLiveDeparture(String departureId) {
        try {
            return restClient.get()
                    .uri("/internal/v1/departures/{id}/live", departureId)
                    .retrieve()
                    .onStatus(status -> status.value() == 404, (req, resp) -> {
                        throw new ResourceNotFoundException("Live tracking not found for departure " + departureId);
                    })
                    .body(SimulationLiveDto.class);
        } catch (ResourceNotFoundException e) {
            throw e;
        } catch (ResourceAccessException | HttpServerErrorException e) {
            throw new SimulationEngineUnavailableException("Python simulation daemon is unreachable", e);
        } catch (Exception e) {
            throw new SimulationEngineUnavailableException("Failed to retrieve live departure: " + e.getMessage(), e);
        }
    }

    @Override
    public Map<String, Object> getDepartureTrack(String departureId) {
        try {
            return restClient.get()
                    .uri("/internal/v1/departures/{id}/track", departureId)
                    .retrieve()
                    .onStatus(status -> status.value() == 404, (req, resp) -> {
                        throw new ResourceNotFoundException("Track not found for departure " + departureId);
                    })
                    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
        } catch (ResourceNotFoundException e) {
            throw e;
        } catch (ResourceAccessException | HttpServerErrorException e) {
            throw new SimulationEngineUnavailableException("Python simulation daemon is unreachable", e);
        } catch (Exception e) {
            throw new SimulationEngineUnavailableException("Failed to retrieve track: " + e.getMessage(), e);
        }
    }

    @Override
    public List<Map<String, Object>> getTodayTimetable() {
        try {
            return restClient.get()
                    .uri("/internal/v1/timetable/today")
                    .retrieve()
                    .body(new ParameterizedTypeReference<List<Map<String, Object>>>() {});
        } catch (Exception e) {
            throw new SimulationEngineUnavailableException("Python simulation daemon timetable unreachable", e);
        }
    }

    @Override
    public List<Map<String, Object>> getActiveDepartures() {
        try {
            return restClient.get()
                    .uri("/internal/v1/departures")
                    .retrieve()
                    .body(new ParameterizedTypeReference<List<Map<String, Object>>>() {});
        } catch (Exception e) {
            throw new SimulationEngineUnavailableException("Python simulation daemon departures unreachable", e);
        }
    }

    @Override
    public Map<String, Object> getAccuracyStats() {
        try {
            return restClient.get()
                    .uri("/internal/v1/accuracy")
                    .retrieve()
                    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            throw new SimulationEngineUnavailableException("Python simulation daemon accuracy unreachable", e);
        }
    }

    @Override
    public boolean isAvailable() {
        try {
            var response = restClient.get()
                    .uri("/health")
                    .retrieve()
                    .toBodilessEntity();
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            return false;
        }
    }

    @Override
    public Map<String, Object> getSimulationStatus() {
        try {
            return restClient.get()
                    .uri("/internal/v1/status")
                    .retrieve()
                    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            // Fallback status if daemon is offline
            return Map.of(
                    "simulation_available", false,
                    "is_running", false,
                    "is_paused", false,
                    "speed_multiplier", 1.0,
                    "total_events_processed", 0,
                    "active_vessels_count", 0,
                    "mode", "OFFLINE_FALLBACK"
            );
        }
    }

    @Override
    public Map<String, Object> controlSimulation(String action, Double speedMultiplier) {
        java.util.Map<String, Object> req = new java.util.HashMap<>();
        req.put("action", action);
        if (speedMultiplier != null) {
            req.put("speed_multiplier", speedMultiplier);
        }

        try {
            return restClient.post()
                    .uri("/internal/v1/simulation/control")
                    .body(req)
                    .retrieve()
                    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            throw new SimulationEngineUnavailableException("Failed to send simulation control '" + action + "': " + e.getMessage(), e);
        }
    }

    @Override
    public Map<String, Object> triggerScenario(String scenarioId) {
        try {
            return restClient.post()
                    .uri("/internal/v1/simulation/scenarios/{id}", scenarioId)
                    .retrieve()
                    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            throw new SimulationEngineUnavailableException("Failed to trigger scenario '" + scenarioId + "': " + e.getMessage(), e);
        }
    }

    @Override
    public Map<String, Object> getModelHealth() {
        try {
            return restClient.get()
                    .uri("/internal/v1/health")
                    .retrieve()
                    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            return Map.of(
                    "status", "DEGRADED",
                    "model_loaded", false,
                    "simulation_running", false,
                    "active_vessels_count", 0
            );
        }
    }

    @Override
    public List<Map<String, Object>> getFleetSnapshot() {
        try {
            Map<String, Object> resp = restClient.get()
                    .uri("/internal/v1/fleet/snapshot")
                    .retrieve()
                    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
            if (resp != null && resp.get("vessels") instanceof List<?> list) {
                return (List<Map<String, Object>>) list;
            }
            return List.of();
        } catch (Exception e) {
            return List.of();
        }
    }

    @Override
    public Map<String, Object> getPredictionProvenance(String vesselId) {
        try {
            return restClient.get()
                    .uri("/internal/v1/vessels/{id}/eta", vesselId)
                    .retrieve()
                    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            return Map.of("vessel_id", vesselId, "status", "UNAVAILABLE");
        }
    }
}
