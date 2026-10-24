package com.whereismyferry.backend.dto;

import java.time.OffsetDateTime;

public class AnnouncementDto {
    private Long id;
    private String title;
    private String body;
    private String severity; // INFO, WARNING, CRITICAL
    private String scope;    // ALL, PORT, ROUTE, DEPARTURE
    private String targetId;
    private OffsetDateTime startsAt;
    private OffsetDateTime endsAt;
    private String createdBy;
    private OffsetDateTime createdAt;

    public AnnouncementDto() {}

    public AnnouncementDto(Long id, String title, String body, String severity, String scope, String targetId, OffsetDateTime startsAt, OffsetDateTime endsAt, String createdBy, OffsetDateTime createdAt) {
        this.id = id;
        this.title = title;
        this.body = body;
        this.severity = severity;
        this.scope = scope;
        this.targetId = targetId;
        this.startsAt = startsAt;
        this.endsAt = endsAt;
        this.createdBy = createdBy;
        this.createdAt = createdAt;
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
}
