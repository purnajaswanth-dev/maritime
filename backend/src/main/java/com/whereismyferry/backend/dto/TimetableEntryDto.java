package com.whereismyferry.backend.dto;

import java.time.LocalTime;
import java.util.Map;

public class TimetableEntryDto {
    private String tripId;
    private String serviceId;
    private String routeId;
    private String routeName;
    private String originPortId;
    private String originPortName;
    private String destinationPortId;
    private String destinationPortName;
    private LocalTime departureTime;
    private LocalTime arrivalTime;
    private Double durationMinutes;
    private String vesselId;
    private String vesselName;
    private Boolean trackingSupported;
    private Map<String, Boolean> daysOfWeek;

    public TimetableEntryDto() {}

    public String getTripId() { return tripId; }
    public void setTripId(String tripId) { this.tripId = tripId; }
    public String getServiceId() { return serviceId; }
    public void setServiceId(String serviceId) { this.serviceId = serviceId; }
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
    public LocalTime getDepartureTime() { return departureTime; }
    public void setDepartureTime(LocalTime departureTime) { this.departureTime = departureTime; }
    public LocalTime getArrivalTime() { return arrivalTime; }
    public void setArrivalTime(LocalTime arrivalTime) { this.arrivalTime = arrivalTime; }
    public Double getDurationMinutes() { return durationMinutes; }
    public void setDurationMinutes(Double durationMinutes) { this.durationMinutes = durationMinutes; }
    public String getVesselId() { return vesselId; }
    public void setVesselId(String vesselId) { this.vesselId = vesselId; }
    public String getVesselName() { return vesselName; }
    public void setVesselName(String vesselName) { this.vesselName = vesselName; }
    public Boolean getTrackingSupported() { return trackingSupported; }
    public void setTrackingSupported(Boolean trackingSupported) { this.trackingSupported = trackingSupported; }
    public Map<String, Boolean> getDaysOfWeek() { return daysOfWeek; }
    public void setDaysOfWeek(Map<String, Boolean> daysOfWeek) { this.daysOfWeek = daysOfWeek; }
}
