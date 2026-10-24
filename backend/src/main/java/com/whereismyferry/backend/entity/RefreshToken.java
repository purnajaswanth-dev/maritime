package com.whereismyferry.backend.entity;

import jakarta.persistence.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "refresh_tokens")
public class RefreshToken {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "token_hash", length = 256, nullable = false, unique = true)
    private String tokenHash;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "expiry", nullable = false)
    private OffsetDateTime expiry;

    @Column(name = "revoked", nullable = false)
    private Boolean revoked = false;

    @Column(name = "user_agent", length = 256)
    private String userAgent;

    @Column(name = "created_at")
    private OffsetDateTime createdAt = OffsetDateTime.now();

    public RefreshToken() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getTokenHash() { return tokenHash; }
    public void setTokenHash(String tokenHash) { this.tokenHash = tokenHash; }

    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }

    public OffsetDateTime getExpiry() { return expiry; }
    public void setExpiry(OffsetDateTime expiry) { this.expiry = expiry; }

    public Boolean getRevoked() { return revoked; }
    public void setRevoked(Boolean revoked) { this.revoked = revoked; }

    public String getUserAgent() { return userAgent; }
    public void setUserAgent(String userAgent) { this.userAgent = userAgent; }

    public OffsetDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(OffsetDateTime createdAt) { this.createdAt = createdAt; }

    public boolean isExpired() {
        return expiry.isBefore(OffsetDateTime.now());
    }
}
