package com.whereismyferry.backend.dto;

public record AdminShipDto(
        String id,
        String name,
        Integer passengerCapacity,
        String homePortId,
        String homePortName,
        String status,
        String engineVesselId,
        long sailingsTodayCount,
        boolean trackingSupported,
        Double currentLatitude,
        Double currentLongitude,
        Double currentSpeedKnots,
        Double currentHeadingDegrees,
        String currentLifecycleState
) {}
