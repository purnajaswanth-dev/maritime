package com.whereismyferry.backend.dto;

import java.time.OffsetDateTime;
import java.util.List;

public record AdminPassengerDto(
        Long id,
        String fullName,
        String email,
        String phone,
        String status,
        long bookingsCount,
        OffsetDateTime lastLoginAt,
        OffsetDateTime createdAt,
        boolean hasUpcomingTrip,
        List<BookingResponseDto> recentBookings
) {}
