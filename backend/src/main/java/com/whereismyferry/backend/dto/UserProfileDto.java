package com.whereismyferry.backend.dto;

import java.time.OffsetDateTime;
import java.util.List;

public class UserProfileDto {
    private Long id;
    private String email;
    private String fullName;
    private String firstName;
    private String lastName;
    private String phone;
    private String role;
    private String status;
    private Boolean emailVerified;
    private List<String> roles;
    private OffsetDateTime createdAt;
    private OffsetDateTime lastLoginAt;

    public UserProfileDto() {}

    public UserProfileDto(Long id, String email, String firstName, String lastName, String phone, List<String> roles, OffsetDateTime createdAt) {
        this.id = id;
        this.email = email;
        this.fullName = ((firstName != null ? firstName : "") + " " + (lastName != null ? lastName : "")).trim();
        this.firstName = firstName;
        this.lastName = lastName;
        this.phone = phone;
        this.role = roles != null && roles.contains("ROLE_ADMIN") ? "ADMIN" : "PASSENGER";
        this.status = "ACTIVE";
        this.emailVerified = true;
        this.roles = roles;
        this.createdAt = createdAt;
    }

    public UserProfileDto(Long id, String email, String fullName, String firstName, String lastName, String phone, String role, String status, Boolean emailVerified, List<String> roles, OffsetDateTime createdAt, OffsetDateTime lastLoginAt) {
        this.id = id;
        this.email = email;
        this.fullName = fullName;
        this.firstName = firstName;
        this.lastName = lastName;
        this.phone = phone;
        this.role = role;
        this.status = status;
        this.emailVerified = emailVerified;
        this.roles = roles;
        this.createdAt = createdAt;
        this.lastLoginAt = lastLoginAt;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }
    public String getFirstName() { return firstName; }
    public void setFirstName(String firstName) { this.firstName = firstName; }
    public String getLastName() { return lastName; }
    public void setLastName(String lastName) { this.lastName = lastName; }
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Boolean getEmailVerified() { return emailVerified; }
    public void setEmailVerified(Boolean emailVerified) { this.emailVerified = emailVerified; }
    public List<String> getRoles() { return roles; }
    public void setRoles(List<String> roles) { this.roles = roles; }
    public OffsetDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(OffsetDateTime createdAt) { this.createdAt = createdAt; }
    public OffsetDateTime getLastLoginAt() { return lastLoginAt; }
    public void setLastLoginAt(OffsetDateTime lastLoginAt) { this.lastLoginAt = lastLoginAt; }
}
