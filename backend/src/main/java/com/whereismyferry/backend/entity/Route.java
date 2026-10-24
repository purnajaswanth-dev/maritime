package com.whereismyferry.backend.entity;

import jakarta.persistence.*;
import java.util.Objects;

@Entity
@Table(name = "routes")
public class Route {

    @Id
    @Column(name = "id", length = 64, nullable = false)
    private String id;

    @Column(name = "code", length = 32, nullable = false, unique = true)
    private String code;

    @ManyToOne(fetch = FetchType.EAGER, optional = false)
    @JoinColumn(name = "origin_port_id", nullable = false)
    private Port originPort;

    @ManyToOne(fetch = FetchType.EAGER, optional = false)
    @JoinColumn(name = "destination_port_id", nullable = false)
    private Port destinationPort;

    @Column(name = "name", length = 128, nullable = false)
    private String name;

    @Column(name = "distance_nm")
    private Double distanceNm;

    @Column(name = "crossing_duration_minutes", nullable = false)
    private Double crossingDurationMinutes;

    @Column(name = "tracking_supported", nullable = false)
    private Boolean trackingSupported = false;

    public Route() {}

    public Route(String id, String code, Port originPort, Port destinationPort, String name, Double distanceNm, Double crossingDurationMinutes, Boolean trackingSupported) {
        this.id = id;
        this.code = code;
        this.originPort = originPort;
        this.destinationPort = destinationPort;
        this.name = name;
        this.distanceNm = distanceNm;
        this.crossingDurationMinutes = crossingDurationMinutes;
        this.trackingSupported = trackingSupported != null ? trackingSupported : false;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }

    public Port getOriginPort() { return originPort; }
    public void setOriginPort(Port originPort) { this.originPort = originPort; }

    public Port getDestinationPort() { return destinationPort; }
    public void setDestinationPort(Port destinationPort) { this.destinationPort = destinationPort; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Double getDistanceNm() { return distanceNm; }
    public void setDistanceNm(Double distanceNm) { this.distanceNm = distanceNm; }

    public Double getCrossingDurationMinutes() { return crossingDurationMinutes; }
    public void setCrossingDurationMinutes(Double crossingDurationMinutes) { this.crossingDurationMinutes = crossingDurationMinutes; }

    public Boolean getTrackingSupported() { return trackingSupported; }
    public void setTrackingSupported(Boolean trackingSupported) { this.trackingSupported = trackingSupported; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Route route)) return false;
        return Objects.equals(id, route.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
