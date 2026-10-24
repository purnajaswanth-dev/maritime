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
    private Integer berthRadiusM;
    private String status;
    private String address;
    private String phone;
    private String email;
    private String facilities;
    private String notes;

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
    public Integer getBerthRadiusM() { return berthRadiusM; }
    public void setBerthRadiusM(Integer berthRadiusM) { this.berthRadiusM = berthRadiusM; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getAddress() { return address; }
    public void setAddress(String address) { this.address = address; }
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getFacilities() { return facilities; }
    public void setFacilities(String facilities) { this.facilities = facilities; }
    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }
}
