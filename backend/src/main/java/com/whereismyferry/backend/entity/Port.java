package com.whereismyferry.backend.entity;

import jakarta.persistence.*;
import java.util.Objects;

@Entity
@Table(name = "ports")
public class Port {

    @Id
    @Column(name = "id", length = 64, nullable = false)
    private String id;

    @Column(name = "code", length = 32, nullable = false, unique = true)
    private String code;

    @Column(name = "name", length = 128, nullable = false)
    private String name;

    @Column(name = "latitude", nullable = false)
    private Double latitude;

    @Column(name = "longitude", nullable = false)
    private Double longitude;

    @Column(name = "timezone", length = 64, nullable = false)
    private String timezone = "Europe/Paris";

    @Column(name = "amenities", columnDefinition = "TEXT")
    private String amenities;

    @Column(name = "berth_count", nullable = false)
    private Integer berthCount = 1;

    @Column(name = "berth_radius_m")
    private Integer berthRadiusM = 800;

    @Column(name = "status", length = 32, nullable = false)
    private String status = "OPEN";

    @Column(name = "address", columnDefinition = "TEXT")
    private String address;

    @Column(name = "phone", length = 64)
    private String phone;

    @Column(name = "email", length = 128)
    private String email;

    @Column(name = "facilities", columnDefinition = "TEXT")
    private String facilities;

    @Column(name = "notes", columnDefinition = "TEXT")
    private String notes;

    public Port() {}

    public Port(String id, String code, String name, Double latitude, Double longitude, String timezone, String amenities, Integer berthCount) {
        this.id = id;
        this.code = code;
        this.name = name;
        this.latitude = latitude;
        this.longitude = longitude;
        this.timezone = timezone != null ? timezone : "Europe/Paris";
        this.amenities = amenities;
        this.berthCount = berthCount != null ? berthCount : 1;
        this.berthRadiusM = 800;
        this.status = "OPEN";
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

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Port port)) return false;
        return Objects.equals(id, port.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
