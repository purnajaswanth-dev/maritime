package com.whereismyferry.backend.client;

import com.whereismyferry.backend.dto.SimulationLiveDto;

import java.util.List;
import java.util.Map;
import java.util.Optional;

public interface SimulationClient {
    SimulationLiveDto getLiveDeparture(String departureId);
    Map<String, Object> getDepartureTrack(String departureId);
    List<Map<String, Object>> getTodayTimetable();
    List<Map<String, Object>> getActiveDepartures();
    Map<String, Object> getAccuracyStats();
    boolean isAvailable();

    Map<String, Object> getSimulationStatus();
    Map<String, Object> controlSimulation(String action, Double speedMultiplier);
    Map<String, Object> triggerScenario(String scenarioId);
    Map<String, Object> getModelHealth();
    List<Map<String, Object>> getFleetSnapshot();
    Map<String, Object> getPredictionProvenance(String vesselId);
}
