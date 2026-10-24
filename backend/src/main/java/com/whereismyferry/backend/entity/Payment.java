package com.whereismyferry.backend.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.Objects;

@Entity
@Table(name = "payments")
public class Payment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "booking_id", nullable = false)
    private Booking booking;

    @Column(name = "payment_intent_id", length = 128, nullable = false, unique = true)
    private String paymentIntentId;

    @Column(name = "amount_eur", precision = 10, scale = 2, nullable = false)
    private BigDecimal amountEur;

    @Column(name = "currency", length = 8, nullable = false)
    private String currency = "EUR";

    @Column(name = "status", length = 32, nullable = false)
    private String status = "COMPLETED";

    @Column(name = "payment_method", length = 32, nullable = false)
    private String paymentMethod = "CARD";

    @Column(name = "simulated", nullable = false)
    private Boolean simulated = true;

    @Column(name = "created_at")
    private OffsetDateTime createdAt = OffsetDateTime.now();

    public Payment() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Booking getBooking() { return booking; }
    public void setBooking(Booking booking) { this.booking = booking; }

    public String getPaymentIntentId() { return paymentIntentId; }
    public void setPaymentIntentId(String paymentIntentId) { this.paymentIntentId = paymentIntentId; }

    public BigDecimal getAmountEur() { return amountEur; }
    public void setAmountEur(BigDecimal amountEur) { this.amountEur = amountEur; }

    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getPaymentMethod() { return paymentMethod; }
    public void setPaymentMethod(String paymentMethod) { this.paymentMethod = paymentMethod; }

    public Boolean getSimulated() { return simulated; }
    public void setSimulated(Boolean simulated) { this.simulated = simulated; }

    public OffsetDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(OffsetDateTime createdAt) { this.createdAt = createdAt; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Payment payment)) return false;
        return Objects.equals(id, payment.id) || (paymentIntentId != null && Objects.equals(paymentIntentId, payment.paymentIntentId));
    }

    @Override
    public int hashCode() {
        return Objects.hash(paymentIntentId != null ? paymentIntentId : id);
    }
}
