package com.whereismyferry.backend.dto;

public class VesselDto {
    private String id;
    private String code;
    private String name;
    private String mmsi;
    private String imo;
    private Integer capacityPassengers;
    private Integer capacityVehicles;
    private Double speedKnots;
    private String trackingVesselId;
    private String status;

    public VesselDto() {}

    public VesselDto(String id, String code, String name, String mmsi, String imo, Integer capacityPassengers, Integer capacityVehicles, Double speedKnots, String trackingVesselId, String status) {
        this.id = id;
        this.code = code;
        this.name = name;
        this.mmsi = mmsi;
        this.imo = imo;
        this.capacityPassengers = capacityPassengers;
        this.capacityVehicles = capacityVehicles;
        this.speedKnots = speedKnots;
        this.trackingVesselId = trackingVesselId;
        this.status = status;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getMmsi() { return mmsi; }
    public void setMmsi(String mmsi) { this.mmsi = mmsi; }
    public String getImo() { return imo; }
    public void setImo(String imo) { this.imo = imo; }
    public Integer getCapacityPassengers() { return capacityPassengers; }
    public void setCapacityPassengers(Integer capacityPassengers) { this.capacityPassengers = capacityPassengers; }
    public Integer getCapacityVehicles() { return capacityVehicles; }
    public void setCapacityVehicles(Integer capacityVehicles) { this.capacityVehicles = capacityVehicles; }
    public Double getSpeedKnots() { return speedKnots; }
    public void setSpeedKnots(Double speedKnots) { this.speedKnots = speedKnots; }
    public String getTrackingVesselId() { return trackingVesselId; }
    public void setTrackingVesselId(String trackingVesselId) { this.trackingVesselId = trackingVesselId; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
