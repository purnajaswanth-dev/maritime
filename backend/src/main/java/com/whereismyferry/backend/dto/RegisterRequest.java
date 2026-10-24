package com.whereismyferry.backend.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class RegisterRequest {

    @NotBlank(message = "Email is required")
    @Email(message = "Valid email address is required")
    private String email;

    @NotBlank(message = "Password is required")
    @Size(min = 10, message = "Password must be at least 10 characters long")
    private String password;

    private String fullName;
    private String firstName;
    private String lastName;
    private String phone;

    public RegisterRequest() {}

    public RegisterRequest(String email, String password, String firstName, String lastName, String phone) {
        this.email = email;
        this.password = password;
        this.firstName = firstName;
        this.lastName = lastName;
        this.fullName = (firstName != null && lastName != null) ? firstName + " " + lastName : null;
        this.phone = phone;
    }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }

    public String getFullName() {
        if (fullName != null && !fullName.isBlank()) return fullName;
        if (firstName != null || lastName != null) {
            return ((firstName != null ? firstName : "") + " " + (lastName != null ? lastName : "")).trim();
        }
        return null;
    }
    public void setFullName(String fullName) { this.fullName = fullName; }

    public String getFirstName() { return firstName != null ? firstName : (fullName != null ? fullName.split(" ")[0] : ""); }
    public void setFirstName(String firstName) { this.firstName = firstName; }

    public String getLastName() {
        if (lastName != null) return lastName;
        if (fullName != null && fullName.contains(" ")) {
            return fullName.substring(fullName.indexOf(' ') + 1);
        }
        return "";
    }
    public void setLastName(String lastName) { this.lastName = lastName; }

    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
}
