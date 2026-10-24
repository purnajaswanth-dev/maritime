package com.whereismyferry.backend.dto;

import java.math.BigDecimal;
import java.time.LocalDate;

public class FareRuleDto {
    private Long id;
    private String routeId;
    private String passengerType;
    private String vehicleType;
    private BigDecimal basePriceEur;
    private String currency;
    private LocalDate validFrom;
    private LocalDate validTo;

    public FareRuleDto() {}

    public FareRuleDto(Long id, String routeId, String passengerType, String vehicleType, BigDecimal basePriceEur, String currency, LocalDate validFrom, LocalDate validTo) {
        this.id = id;
        this.routeId = routeId;
        this.passengerType = passengerType;
        this.vehicleType = vehicleType;
        this.basePriceEur = basePriceEur;
        this.currency = currency;
        this.validFrom = validFrom;
        this.validTo = validTo;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getRouteId() { return routeId; }
    public void setRouteId(String routeId) { this.routeId = routeId; }
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
}
