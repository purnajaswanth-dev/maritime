package com.whereismyferry.backend.entity;

import jakarta.persistence.*;
import java.time.OffsetDateTime;
import java.util.Objects;

@Entity
@Table(name = "departures", uniqueConstraints = {
    @UniqueConstraint(name = "uk_vessel_scheduled_time", columnNames = {"vessel_id", "scheduled_departure_time"})
})
public class Departure {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "departure_code", length = 64, nullable = false, unique = true)
    private String departureCode;

    @ManyToOne(fetch = FetchType.EAGER, optional = false)
    @JoinColumn(name = "route_id", nullable = false)
    private Route route;

    @ManyToOne(fetch = FetchType.EAGER, optional = false)
    @JoinColumn(name = "vessel_id", nullable = false)
    private Vessel vessel;

    @Column(name = "scheduled_departure_time", nullable = false)
    private OffsetDateTime scheduledDepartureTime;

    @Column(name = "scheduled_arrival_time", nullable = false)
    private OffsetDateTime scheduledArrivalTime;

    @Column(name = "actual_departure_time")
    private OffsetDateTime actualDepartureTime;

    @Column(name = "actual_arrival_time")
    private OffsetDateTime actualArrivalTime;

    @Column(name = "status", length = 32, nullable = false)
    private String status = "SCHEDULED";

    @Column(name = "delay_minutes")
    private Integer delayMinutes = 0;

    @Column(name = "cancel_reason", columnDefinition = "TEXT")
    private String cancelReason;

    @Column(name = "seats_available")
    private Integer seatsAvailable = 250;

    @Column(name = "service_id")
    private Long serviceId;

    @Column(name = "created_at")
    private OffsetDateTime createdAt = OffsetDateTime.now();

    @Column(name = "updated_at")
    private OffsetDateTime updatedAt = OffsetDateTime.now();

    public Departure() {}

    public Departure(String departureCode, Route route, Vessel vessel, OffsetDateTime scheduledDepartureTime, OffsetDateTime scheduledArrivalTime, String status) {
        this.departureCode = departureCode;
        this.route = route;
        this.vessel = vessel;
        this.scheduledDepartureTime = scheduledDepartureTime;
        this.scheduledArrivalTime = scheduledArrivalTime;
        this.status = status != null ? status : "SCHEDULED";
        this.seatsAvailable = vessel != null && vessel.getCapacity() != null ? vessel.getCapacity() : 250;
        this.createdAt = OffsetDateTime.now();
        this.updatedAt = OffsetDateTime.now();
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getDepartureCode() { return departureCode; }
    public void setDepartureCode(String departureCode) { this.departureCode = departureCode; }

    public Route getRoute() { return route; }
    public void setRoute(Route route) { this.route = route; }

    public Vessel getVessel() { return vessel; }
    public void setVessel(Vessel vessel) { this.vessel = vessel; }

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

    public String getCancelReason() { return cancelReason; }
    public void setCancelReason(String cancelReason) { this.cancelReason = cancelReason; }

    public Integer getSeatsAvailable() { return seatsAvailable; }
    public void setSeatsAvailable(Integer seatsAvailable) { this.seatsAvailable = seatsAvailable; }

    public Long getServiceId() { return serviceId; }
    public void setServiceId(Long serviceId) { this.serviceId = serviceId; }

    public OffsetDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(OffsetDateTime createdAt) { this.createdAt = createdAt; }

    public OffsetDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(OffsetDateTime updatedAt) { this.updatedAt = updatedAt; }

    @PreUpdate
    public void onUpdate() {
        this.updatedAt = OffsetDateTime.now();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Departure departure)) return false;
        return Objects.equals(id, departure.id) || (departureCode != null && Objects.equals(departureCode, departure.departureCode));
    }

    @Override
    public int hashCode() {
        return Objects.hash(departureCode != null ? departureCode : id);
    }
}
