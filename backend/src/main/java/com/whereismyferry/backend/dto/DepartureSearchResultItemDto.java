package com.whereismyferry.backend.dto;

import java.math.BigDecimal;
import java.time.OffsetDateTime;

public class DepartureSearchResultItemDto {
    private Long id;
    private String departureCode;
    private String routeId;
    private String routeName;
    private String originPortId;
    private String originPortName;
    private String destinationPortId;
    private String destinationPortName;
    private OffsetDateTime scheduledDepartureTime;
    private OffsetDateTime scheduledArrivalTime;
    private double durationMinutes;
    private String vesselId;
    private String vesselName;
    private String status;       // SCHEDULED, BOARDING, IN_TRANSIT, ARRIVED, DELAYED, CANCELLED
    private String statusLabel;  // "On time", "Delayed +12 min", "Cancelled", "Arrived"
    private int delayMinutes;
    private int seatsAvailable;
    private BigDecimal fromPriceEur;
    private boolean liveTrackingAvailable;

    public DepartureSearchResultItemDto() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getDepartureCode() { return departureCode; }
    public void setDepartureCode(String departureCode) { this.departureCode = departureCode; }

    public String getRouteId() { return routeId; }
    public void setRouteId(String routeId) { this.routeId = routeId; }

    public String getRouteName() { return routeName; }
    public void setRouteName(String routeName) { this.routeName = routeName; }

    public String getOriginPortId() { return originPortId; }
    public void setOriginPortId(String originPortId) { this.originPortId = originPortId; }

    public String getOriginPortName() { return originPortName; }
    public void setOriginPortName(String originPortName) { this.originPortName = originPortName; }

    public String getDestinationPortId() { return destinationPortId; }
    public void setDestinationPortId(String destinationPortId) { this.destinationPortId = destinationPortId; }

    public String getDestinationPortName() { return destinationPortName; }
    public void setDestinationPortName(String destinationPortName) { this.destinationPortName = destinationPortName; }

    public OffsetDateTime getScheduledDepartureTime() { return scheduledDepartureTime; }
    public void setScheduledDepartureTime(OffsetDateTime scheduledDepartureTime) { this.scheduledDepartureTime = scheduledDepartureTime; }

    public OffsetDateTime getScheduledArrivalTime() { return scheduledArrivalTime; }
    public void setScheduledArrivalTime(OffsetDateTime scheduledArrivalTime) { this.scheduledArrivalTime = scheduledArrivalTime; }

    public double getDurationMinutes() { return durationMinutes; }
    public void setDurationMinutes(double durationMinutes) { this.durationMinutes = durationMinutes; }

    public String getVesselId() { return vesselId; }
    public void setVesselId(String vesselId) { this.vesselId = vesselId; }

    public String getVesselName() { return vesselName; }
    public void setVesselName(String vesselName) { this.vesselName = vesselName; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getStatusLabel() { return statusLabel; }
    public void setStatusLabel(String statusLabel) { this.statusLabel = statusLabel; }

    public int getDelayMinutes() { return delayMinutes; }
    public void setDelayMinutes(int delayMinutes) { this.delayMinutes = delayMinutes; }

    public int getSeatsAvailable() { return seatsAvailable; }
    public void setSeatsAvailable(int seatsAvailable) { this.seatsAvailable = seatsAvailable; }

    public BigDecimal getFromPriceEur() { return fromPriceEur; }
    public void setFromPriceEur(BigDecimal fromPriceEur) { this.fromPriceEur = fromPriceEur; }

    public boolean isLiveTrackingAvailable() { return liveTrackingAvailable; }
    public void setLiveTrackingAvailable(boolean liveTrackingAvailable) { this.liveTrackingAvailable = liveTrackingAvailable; }
}
