package com.whereismyferry.backend.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Objects;

@Entity
@Table(name = "fare_rules")
public class FareRule {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.EAGER, optional = false)
    @JoinColumn(name = "route_id", nullable = false)
    private Route route;

    @Column(name = "passenger_type", length = 32, nullable = false)
    private String passengerType; // ADULT, CHILD, SENIOR, RESIDENT

    @Column(name = "vehicle_type", length = 32)
    private String vehicleType; // NONE, STANDARD_CAR, MOTORCYCLE, BICYCLE

    @Column(name = "base_price_eur", precision = 10, scale = 2, nullable = false)
    private BigDecimal basePriceEur;

    @Column(name = "currency", length = 8, nullable = false)
    private String currency = "EUR";

    @Column(name = "valid_from")
    private LocalDate validFrom;

    @Column(name = "valid_to")
    private LocalDate validTo;

    public FareRule() {}

    public FareRule(Route route, String passengerType, String vehicleType, BigDecimal basePriceEur, String currency) {
        this.route = route;
        this.passengerType = passengerType;
        this.vehicleType = vehicleType;
        this.basePriceEur = basePriceEur;
        this.currency = currency != null ? currency : "EUR";
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Route getRoute() { return route; }
    public void setRoute(Route route) { this.route = route; }

    public String getPassengerType() { return passengerType; }
    public void setPassengerType(String passengerType) { this.passengerType = passengerType; }

    public String getVehicleType() { return vehicleType; }
    public void setVehicleType(String vehicleType) { this.vehicleType = vehicleType; }

    public BigDecimal getBasePriceEur() { return basePriceEur; }
    public void setBasePriceEur(BigDecimal basePriceEur) { this.basePriceEur = basePriceEur; }

    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }

    public LocalDate getValidFrom() { return validFrom; }
    public void setValidFrom(LocalDate validFrom) { this.validFrom = validFrom; }

    public LocalDate getValidTo() { return validTo; }
    public void setValidTo(LocalDate validTo) { this.validTo = validTo; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof FareRule fareRule)) return false;
        return Objects.equals(id, fareRule.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
