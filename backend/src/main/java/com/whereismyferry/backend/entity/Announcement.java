package com.whereismyferry.backend.entity;

import jakarta.persistence.*;
import java.time.OffsetDateTime;
import java.util.Objects;

@Entity
@Table(name = "announcements")
public class Announcement {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "title", length = 128, nullable = false)
    private String title;

    @Column(name = "body", columnDefinition = "TEXT", nullable = false)
    private String body;

    @Column(name = "severity", length = 32, nullable = false)
    private String severity = "INFO"; // INFO, WARNING, CRITICAL

    @Column(name = "scope", length = 32, nullable = false)
    private String scope = "ALL"; // ALL, PORT, ROUTE, DEPARTURE

    @Column(name = "target_id", length = 64)
    private String targetId;

    @Column(name = "starts_at", nullable = false)
    private OffsetDateTime startsAt = OffsetDateTime.now();

    @Column(name = "ends_at")
    private OffsetDateTime endsAt;

    @Column(name = "created_by", length = 128, nullable = false)
    private String createdBy = "SYSTEM";

    @Column(name = "created_at", nullable = false)
    private OffsetDateTime createdAt = OffsetDateTime.now();

    public Announcement() {}

    public Announcement(String title, String body, String severity, String scope, String targetId,
                        OffsetDateTime startsAt, OffsetDateTime endsAt, String createdBy) {
        this.title = title;
        this.body = body;
        this.severity = severity != null ? severity : "INFO";
        this.scope = scope != null ? scope : "ALL";
        this.targetId = targetId;
        this.startsAt = startsAt != null ? startsAt : OffsetDateTime.now();
        this.endsAt = endsAt;
        this.createdBy = createdBy != null ? createdBy : "SYSTEM";
        this.createdAt = OffsetDateTime.now();
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getBody() { return body; }
    public void setBody(String body) { this.body = body; }

    public String getSeverity() { return severity; }
    public void setSeverity(String severity) { this.severity = severity; }

    public String getScope() { return scope; }
    public void setScope(String scope) { this.scope = scope; }

    public String getTargetId() { return targetId; }
    public void setTargetId(String targetId) { this.targetId = targetId; }

    public OffsetDateTime getStartsAt() { return startsAt; }
    public void setStartsAt(OffsetDateTime startsAt) { this.startsAt = startsAt; }

    public OffsetDateTime getEndsAt() { return endsAt; }
    public void setEndsAt(OffsetDateTime endsAt) { this.endsAt = endsAt; }

    public String getCreatedBy() { return createdBy; }
    public void setCreatedBy(String createdBy) { this.createdBy = createdBy; }

    public OffsetDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(OffsetDateTime createdAt) { this.createdAt = createdAt; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Announcement that)) return false;
        return Objects.equals(id, that.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
