package com.whereismyferry.backend.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalTime;

public record AdminServiceDto(
        Long id,
        String routeId,
        String routeName,
        String originPortId,
        String originPortName,
        String destinationPortId,
        String destinationPortName,
        String vesselId,
        String vesselName,
        LocalTime departureTime,
        Integer durationMinutes,
        String daysOfWeek,
        LocalDate validFrom,
        LocalDate validTo,
        BigDecimal baseFareEur,
        Integer capacity,
        Boolean active,
        Boolean trackingSupported
) {}
