package com.whereismyferry.backend.dto;

import java.util.List;

public class UserSummaryDto {
    private Long id;
    private String email;
    private String fullName;
    private String firstName;
    private String lastName;
    private String role;
    private List<String> roles;

    public UserSummaryDto() {}

    public UserSummaryDto(Long id, String email, String fullName, String firstName, String lastName, String role, List<String> roles) {
        this.id = id;
        this.email = email;
        this.fullName = fullName;
        this.firstName = firstName;
        this.lastName = lastName;
        this.role = role;
        this.roles = roles;
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
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    public List<String> getRoles() { return roles; }
    public void setRoles(List<String> roles) { this.roles = roles; }
}
