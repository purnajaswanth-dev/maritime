package com.whereismyferry.backend.entity;

import jakarta.persistence.*;
import java.util.Objects;

@Entity
@Table(name = "vessels")
public class Vessel {

    @Id
    @Column(name = "id", length = 64, nullable = false)
    private String id;

    @Column(name = "code", length = 32, nullable = false, unique = true)
    private String code;

    @Column(name = "name", length = 128, nullable = false)
    private String name;

    @Column(name = "mmsi", length = 32)
    private String mmsi;

    @Column(name = "imo", length = 32)
    private String imo;

    @Column(name = "capacity_passengers", nullable = false)
    private Integer capacityPassengers;

    @Column(name = "capacity_vehicles", nullable = false)
    private Integer capacityVehicles = 0;

    @Column(name = "speed_knots", nullable = false)
    private Double speedKnots;

    @Column(name = "tracking_vessel_id", length = 64)
    private String trackingVesselId;

    @Column(name = "status", length = 32, nullable = false)
    private String status = "ACTIVE";

    public Vessel() {}

    public Vessel(String id, String code, String name, String mmsi, String imo, Integer capacityPassengers, Integer capacityVehicles, Double speedKnots, String trackingVesselId, String status) {
        this.id = id;
        this.code = code;
        this.name = name;
        this.mmsi = mmsi;
        this.imo = imo;
        this.capacityPassengers = capacityPassengers;
        this.capacityVehicles = capacityVehicles != null ? capacityVehicles : 0;
        this.speedKnots = speedKnots;
        this.trackingVesselId = trackingVesselId;
        this.status = status != null ? status : "ACTIVE";
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

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Vessel vessel)) return false;
        return Objects.equals(id, vessel.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
