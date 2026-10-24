package com.whereismyferry.backend.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.util.List;

public class CreateBookingRequestDto {

    @NotNull(message = "Departure ID is required")
    private Long departureId;

    private Long returnDepartureId;

    @Email(message = "Valid contact email is required")
    @NotNull(message = "Contact email is required")
    private String contactEmail;

    private String contactPhone;

    @NotEmpty(message = "At least one passenger is required")
    @Valid
    private List<PassengerItemDto> passengers;

    public CreateBookingRequestDto() {}

    public Long getDepartureId() { return departureId; }
    public void setDepartureId(Long departureId) { this.departureId = departureId; }

    public Long getReturnDepartureId() { return returnDepartureId; }
    public void setReturnDepartureId(Long returnDepartureId) { this.returnDepartureId = returnDepartureId; }

    public String getContactEmail() { return contactEmail; }
    public void setContactEmail(String contactEmail) { this.contactEmail = contactEmail; }

    public String getContactPhone() { return contactPhone; }
    public void setContactPhone(String contactPhone) { this.contactPhone = contactPhone; }

    public List<PassengerItemDto> getPassengers() { return passengers; }
    public void setPassengers(List<PassengerItemDto> passengers) { this.passengers = passengers; }
}
