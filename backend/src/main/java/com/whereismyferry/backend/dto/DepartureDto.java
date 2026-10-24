package com.whereismyferry.backend.dto;

import java.time.OffsetDateTime;

public class DepartureDto {
    private Long id;
    private String departureCode;
    private RouteDto route;
    private VesselDto vessel;
    private OffsetDateTime scheduledDepartureTime;
    private OffsetDateTime scheduledArrivalTime;
    private OffsetDateTime actualDepartureTime;
    private OffsetDateTime actualArrivalTime;
    private String status;
    private Integer delayMinutes;
    private Boolean liveTrackingAvailable;
    private String liveTrackingUrl;
    private Boolean isHistoricalReplay;

    public DepartureDto() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
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
    public OffsetDateTime getActualDepartureTime() { return actualDepartureTime; }
    public void setActualDepartureTime(OffsetDateTime actualDepartureTime) { this.actualDepartureTime = actualDepartureTime; }
    public OffsetDateTime getActualArrivalTime() { return actualArrivalTime; }
    public void setActualArrivalTime(OffsetDateTime actualArrivalTime) { this.actualArrivalTime = actualArrivalTime; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Integer getDelayMinutes() { return delayMinutes; }
    public void setDelayMinutes(Integer delayMinutes) { this.delayMinutes = delayMinutes; }
    public Boolean getLiveTrackingAvailable() { return liveTrackingAvailable; }
    public void setLiveTrackingAvailable(Boolean liveTrackingAvailable) { this.liveTrackingAvailable = liveTrackingAvailable; }
    public String getLiveTrackingUrl() { return liveTrackingUrl; }
    public void setLiveTrackingUrl(String liveTrackingUrl) { this.liveTrackingUrl = liveTrackingUrl; }
    public Boolean getIsHistoricalReplay() { return isHistoricalReplay; }
    public void setIsHistoricalReplay(Boolean isHistoricalReplay) { this.isHistoricalReplay = isHistoricalReplay; }
}
