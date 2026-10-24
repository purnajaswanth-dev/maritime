package com.whereismyferry.backend.dto;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

public class BookingResponseDto {
    private Long id;
    private String bookingReference;
    private DepartureDto departure;
    private DepartureDto returnDeparture;
    private String status;
    private BigDecimal totalAmountEur;
    private String currency;
    private String paymentStatus;
    private String contactEmail;
    private String contactPhone;
    private OffsetDateTime createdAt;
    private List<PassengerItemDto> passengers;
    private List<TicketDto> tickets;

    public BookingResponseDto() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getBookingReference() { return bookingReference; }
    public void setBookingReference(String bookingReference) { this.bookingReference = bookingReference; }

    public DepartureDto getDeparture() { return departure; }
    public void setDeparture(DepartureDto departure) { this.departure = departure; }

    public DepartureDto getReturnDeparture() { return returnDeparture; }
    public void setReturnDeparture(DepartureDto returnDeparture) { this.returnDeparture = returnDeparture; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public BigDecimal getTotalAmountEur() { return totalAmountEur; }
    public void setTotalAmountEur(BigDecimal totalAmountEur) { this.totalAmountEur = totalAmountEur; }

    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }

    public String getPaymentStatus() { return paymentStatus; }
    public void setPaymentStatus(String paymentStatus) { this.paymentStatus = paymentStatus; }

    public String getContactEmail() { return contactEmail; }
    public void setContactEmail(String contactEmail) { this.contactEmail = contactEmail; }

    public String getContactPhone() { return contactPhone; }
    public void setContactPhone(String contactPhone) { this.contactPhone = contactPhone; }

    public OffsetDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(OffsetDateTime createdAt) { this.createdAt = createdAt; }

    public List<PassengerItemDto> getPassengers() { return passengers; }
    public void setPassengers(List<PassengerItemDto> passengers) { this.passengers = passengers; }

    public List<TicketDto> getTickets() { return tickets; }
    public void setTickets(List<TicketDto> tickets) { this.tickets = tickets; }
}
