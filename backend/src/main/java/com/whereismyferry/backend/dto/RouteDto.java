package com.whereismyferry.backend.dto;

public class RouteDto {
    private String id;
    private String code;
    private String name;
    private String originPortId;
    private String originPortName;
    private String destinationPortId;
    private String destinationPortName;
    private Double distanceNm;
    private Double crossingDurationMinutes;
    private Boolean trackingSupported;

    public RouteDto() {}

    public RouteDto(String id, String code, String name, String originPortId, String originPortName, String destinationPortId, String destinationPortName, Double distanceNm, Double crossingDurationMinutes, Boolean trackingSupported) {
        this.id = id;
        this.code = code;
        this.name = name;
        this.originPortId = originPortId;
        this.originPortName = originPortName;
        this.destinationPortId = destinationPortId;
        this.destinationPortName = destinationPortName;
        this.distanceNm = distanceNm;
        this.crossingDurationMinutes = crossingDurationMinutes;
        this.trackingSupported = trackingSupported;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getOriginPortId() { return originPortId; }
    public void setOriginPortId(String originPortId) { this.originPortId = originPortId; }
    public String getOriginPortName() { return originPortName; }
    public void setOriginPortName(String originPortName) { this.originPortName = originPortName; }
    public String getDestinationPortId() { return destinationPortId; }
    public void setDestinationPortId(String destinationPortId) { this.destinationPortId = destinationPortId; }
    public String getDestinationPortName() { return destinationPortName; }
    public void setDestinationPortName(String destinationPortName) { this.destinationPortName = destinationPortName; }
    public Double getDistanceNm() { return distanceNm; }
    public void setDistanceNm(Double distanceNm) { this.distanceNm = distanceNm; }
    public Double getCrossingDurationMinutes() { return crossingDurationMinutes; }
    public void setCrossingDurationMinutes(Double crossingDurationMinutes) { this.crossingDurationMinutes = crossingDurationMinutes; }
    public Boolean getTrackingSupported() { return trackingSupported; }
    public void setTrackingSupported(Boolean trackingSupported) { this.trackingSupported = trackingSupported; }
}
