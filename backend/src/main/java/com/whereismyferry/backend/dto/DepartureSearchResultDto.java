package com.whereismyferry.backend.dto;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

public class DepartureSearchResultDto {
    private String originPortId;
    private String originPortName;
    private String destinationPortId;
    private String destinationPortName;
    private LocalDate searchDate;
    private int passengers = 1;
    private int totalResults = 0;
    private List<DepartureSearchResultItemDto> departures = new ArrayList<>();
    private String emptyStateMessage;
    private DepartureSearchResultItemDto nextAvailableSailing;

    public DepartureSearchResultDto() {}

    public String getOriginPortId() { return originPortId; }
    public void setOriginPortId(String originPortId) { this.originPortId = originPortId; }

    public String getOriginPortName() { return originPortName; }
    public void setOriginPortName(String originPortName) { this.originPortName = originPortName; }

    public String getDestinationPortId() { return destinationPortId; }
    public void setDestinationPortId(String destinationPortId) { this.destinationPortId = destinationPortId; }

    public String getDestinationPortName() { return destinationPortName; }
    public void setDestinationPortName(String destinationPortName) { this.destinationPortName = destinationPortName; }

    public LocalDate getSearchDate() { return searchDate; }
    public void setSearchDate(LocalDate searchDate) { this.searchDate = searchDate; }

    public int getPassengers() { return passengers; }
    public void setPassengers(int passengers) { this.passengers = passengers; }

    public int getTotalResults() { return totalResults; }
    public void setTotalResults(int totalResults) { this.totalResults = totalResults; }

    public List<DepartureSearchResultItemDto> getDepartures() { return departures; }
    public void setDepartures(List<DepartureSearchResultItemDto> departures) { this.departures = departures; }

    public String getEmptyStateMessage() { return emptyStateMessage; }
    public void setEmptyStateMessage(String emptyStateMessage) { this.emptyStateMessage = emptyStateMessage; }

    public DepartureSearchResultItemDto getNextAvailableSailing() { return nextAvailableSailing; }
    public void setNextAvailableSailing(DepartureSearchResultItemDto nextAvailableSailing) { this.nextAvailableSailing = nextAvailableSailing; }
}
