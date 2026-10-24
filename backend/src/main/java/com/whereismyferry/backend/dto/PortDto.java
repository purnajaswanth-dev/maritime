package com.whereismyferry.backend.dto;

import java.util.List;

public class PortDto {
    private String id;
    private String code;
    private String name;
    private Double latitude;
    private Double longitude;
    private String timezone;
    private String amenities;
    private Integer berthCount;

    public PortDto() {}

    public PortDto(String id, String code, String name, Double latitude, Double longitude, String timezone, String amenities, Integer berthCount) {
        this.id = id;
        this.code = code;
        this.name = name;
        this.latitude = latitude;
        this.longitude = longitude;
        this.timezone = timezone;
        this.amenities = amenities;
        this.berthCount = berthCount;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public Double getLatitude() { return latitude; }
    public void setLatitude(Double latitude) { this.latitude = latitude; }
    public Double getLongitude() { return longitude; }
    public void setLongitude(Double longitude) { this.longitude = longitude; }
    public String getTimezone() { return timezone; }
    public void setTimezone(String timezone) { this.timezone = timezone; }
    public String getAmenities() { return amenities; }
    public void setAmenities(String amenities) { this.amenities = amenities; }
    public Integer getBerthCount() { return berthCount; }
    public void setBerthCount(Integer berthCount) { this.berthCount = berthCount; }
}
