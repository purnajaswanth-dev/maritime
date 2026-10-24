package com.whereismyferry.backend.entity;

import jakarta.persistence.*;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.Objects;

@Entity
@Table(name = "schedules")
public class Schedule {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "service_id", length = 64, nullable = false)
    private String serviceId;

    @Column(name = "trip_id", length = 64, nullable = false, unique = true)
    private String tripId;

    @ManyToOne(fetch = FetchType.EAGER, optional = false)
    @JoinColumn(name = "route_id", nullable = false)
    private Route route;

    @ManyToOne(fetch = FetchType.EAGER, optional = false)
    @JoinColumn(name = "vessel_id", nullable = false)
    private Vessel vessel;

    @Column(name = "departure_time", nullable = false)
    private LocalTime departureTime;

    @Column(name = "arrival_time", nullable = false)
    private LocalTime arrivalTime;

    @Column(name = "monday", nullable = false)
    private Boolean monday = true;

    @Column(name = "tuesday", nullable = false)
    private Boolean tuesday = true;

    @Column(name = "wednesday", nullable = false)
    private Boolean wednesday = true;

    @Column(name = "thursday", nullable = false)
    private Boolean thursday = true;

    @Column(name = "friday", nullable = false)
    private Boolean friday = true;

    @Column(name = "saturday", nullable = false)
    private Boolean saturday = true;

    @Column(name = "sunday", nullable = false)
    private Boolean sunday = true;

    @Column(name = "valid_from", nullable = false)
    private LocalDate validFrom;

    @Column(name = "valid_to", nullable = false)
    private LocalDate validTo;

    @Column(name = "active", nullable = false)
    private Boolean active = true;

    public Schedule() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getServiceId() { return serviceId; }
    public void setServiceId(String serviceId) { this.serviceId = serviceId; }

    public String getTripId() { return tripId; }
    public void setTripId(String tripId) { this.tripId = tripId; }

    public Route getRoute() { return route; }
    public void setRoute(Route route) { this.route = route; }

    public Vessel getVessel() { return vessel; }
    public void setVessel(Vessel vessel) { this.vessel = vessel; }

    public LocalTime getDepartureTime() { return departureTime; }
    public void setDepartureTime(LocalTime departureTime) { this.departureTime = departureTime; }

    public LocalTime getArrivalTime() { return arrivalTime; }
    public void setArrivalTime(LocalTime arrivalTime) { this.arrivalTime = arrivalTime; }

    public Boolean getMonday() { return monday; }
    public void setMonday(Boolean monday) { this.monday = monday; }

    public Boolean getTuesday() { return tuesday; }
    public void setTuesday(Boolean tuesday) { this.tuesday = tuesday; }

    public Boolean getWednesday() { return wednesday; }
    public void setWednesday(Boolean wednesday) { this.wednesday = wednesday; }

    public Boolean getThursday() { return thursday; }
    public void setThursday(Boolean thursday) { this.thursday = thursday; }

    public Boolean getFriday() { return friday; }
    public void setFriday(Boolean friday) { this.friday = friday; }

    public Boolean getSaturday() { return saturday; }
    public void setSaturday(Boolean saturday) { this.saturday = saturday; }

    public Boolean getSunday() { return sunday; }
    public void setSunday(Boolean sunday) { this.sunday = sunday; }

    public LocalDate getValidFrom() { return validFrom; }
    public void setValidFrom(LocalDate validFrom) { this.validFrom = validFrom; }

    public LocalDate getValidTo() { return validTo; }
    public void setValidTo(LocalDate validTo) { this.validTo = validTo; }

    public Boolean getActive() { return active; }
    public void setActive(Boolean active) { this.active = active; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Schedule schedule)) return false;
        return Objects.equals(id, schedule.id) || (tripId != null && Objects.equals(tripId, schedule.tripId));
    }

    @Override
    public int hashCode() {
        return Objects.hash(tripId != null ? tripId : id);
    }
}
