package com.whereismyferry.backend.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class RouteGeometryDto {

    @JsonProperty("id")
    private String id;

    @JsonProperty("name")
    private String name;

    @JsonProperty("origin_terminal_id")
    private String originTerminalId;

    @JsonProperty("destination_terminal_id")
    private String destinationTerminalId;

    @JsonProperty("polyline")
    private List<List<Double>> polyline;

    @JsonProperty("length_km")
    private Double lengthKm;

    @JsonProperty("great_circle_km")
    private Double greatCircleKm;

    public RouteGeometryDto() {}

    public RouteGeometryDto(
            String id,
            String name,
            String originTerminalId,
            String destinationTerminalId,
            List<List<Double>> polyline,
            Double lengthKm,
            Double greatCircleKm) {
        this.id = id;
        this.name = name;
        this.originTerminalId = originTerminalId;
        this.destinationTerminalId = destinationTerminalId;
        this.polyline = polyline;
        this.lengthKm = lengthKm;
        this.greatCircleKm = greatCircleKm;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getOriginTerminalId() {
        return originTerminalId;
    }

    public void setOriginTerminalId(String originTerminalId) {
        this.originTerminalId = originTerminalId;
    }

    public String getDestinationTerminalId() {
        return destinationTerminalId;
    }

    public void setDestinationTerminalId(String destinationTerminalId) {
        this.destinationTerminalId = destinationTerminalId;
    }

    public List<List<Double>> getPolyline() {
        return polyline;
    }

    public void setPolyline(List<List<Double>> polyline) {
        this.polyline = polyline;
    }

    public Double getLengthKm() {
        return lengthKm;
    }

    public void setLengthKm(Double lengthKm) {
        this.lengthKm = lengthKm;
    }

    public Double getGreatCircleKm() {
        return greatCircleKm;
    }

    public void setGreatCircleKm(Double greatCircleKm) {
        this.greatCircleKm = greatCircleKm;
    }
}
