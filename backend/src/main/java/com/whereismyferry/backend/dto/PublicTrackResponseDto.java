package com.whereismyferry.backend.dto;

import java.time.OffsetDateTime;
import java.util.Map;

public class PublicTrackResponseDto {
    private String departureCode;
    private RouteDto route;
    private VesselDto vessel;
    private OffsetDateTime scheduledDepartureTime;
    private OffsetDateTime scheduledArrivalTime;
    private String status;
    private Integer delayMinutes;
    private SimulationLiveDto live;
    private Map<String, Object> track;

    public PublicTrackResponseDto() {}

    public String getDepartureCode() { return departureCode; }
    public void setDepartureCode(String departureCode) { this.departureCode = departureCode; }
    public RouteDto getRoute() { return route; }
    public void setRoute(RouteDto route) { this.route = route; }
    public VesselDto getVessel() { return vessel; }
    public void setVessel(VesselDto vessel) { this.vessel = vessel; }
    public OffsetDateTime getScheduledDepartureTime() { return scheduledDepartureTime; }
    public void setScheduledDepartureTime(OffsetDateTime scheduledDepartureTime) { this.scheduledDepartureTime = scheduledDepartureTime; }
    public OffsetDateTime getScheduledArrivalTime() { return scheduledArrivalTime; }
    public void setScheduledArrivalTime(OffsetDateTime scheduledArrivalTime) { this.scheduledArrivalTime = scheduledArrivalTime; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Integer getDelayMinutes() { return delayMinutes; }
    public void setDelayMinutes(Integer delayMinutes) { this.delayMinutes = delayMinutes; }
    public SimulationLiveDto getLive() { return live; }
    public void setLive(SimulationLiveDto live) { this.live = live; }
    public Map<String, Object> getTrack() { return track; }
    public void setTrack(Map<String, Object> track) { this.track = track; }
}
