package com.whereismyferry.backend.dto;

import java.util.List;
import java.util.Map;

public record AdminDashboardDto(
        Map<String, Long> sailingsTodayByStatus,
        long shipsInTransit,
        long passengersBookedToday,
        long activeAnnouncements,
        String engineStatus,
        List<DepartureSearchResultItemDto> delayedOrCancelledSailings
) {}
