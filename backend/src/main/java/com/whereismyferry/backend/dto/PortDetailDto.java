package com.whereismyferry.backend.dto;

import java.util.List;

public class PortDetailDto extends PortDto {
    private List<DepartureDto> upcomingDepartures;
    private List<DepartureDto> upcomingArrivals;

    public PortDetailDto() {
        super();
    }

    public List<DepartureDto> getUpcomingDepartures() {
        return upcomingDepartures;
    }

    public void setUpcomingDepartures(List<DepartureDto> upcomingDepartures) {
        this.upcomingDepartures = upcomingDepartures;
    }

    public List<DepartureDto> getUpcomingArrivals() {
        return upcomingArrivals;
    }

    public void setUpcomingArrivals(List<DepartureDto> upcomingArrivals) {
        this.upcomingArrivals = upcomingArrivals;
    }
}
