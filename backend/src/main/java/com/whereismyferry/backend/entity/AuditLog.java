package com.whereismyferry.backend.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "audit_log")
public class AuditLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    @JsonIgnore
    private User user;

    @Column(name = "actor", length = 128, nullable = false)
    private String actor = "SYSTEM";

    @Column(name = "action", length = 64, nullable = false)
    private String action;

    @Column(name = "target", length = 128)
    private String target;

    @Column(name = "entity_type", length = 64)
    private String entityType;

    @Column(name = "entity_id", length = 64)
    private String entityId;

    @Column(name = "timestamp", nullable = false)
    private OffsetDateTime timestamp = OffsetDateTime.now();

    @Column(name = "created_at")
    private OffsetDateTime createdAt = OffsetDateTime.now();

    @Column(name = "ip", length = 64)
    private String ip;

    @Column(name = "ip_address", length = 64)
    private String ipAddress;

    @Column(name = "details", columnDefinition = "TEXT")
    private String details;

    public AuditLog() {}

    public AuditLog(String actor, String action, String target, String ip, String details) {
        this.actor = actor;
        this.action = action;
        this.target = target;
        this.ip = ip;
        this.ipAddress = ip;
        this.details = details;
        this.timestamp = OffsetDateTime.now();
        this.createdAt = this.timestamp;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    @JsonIgnore
    public User getUser() { return user; }
    public void setUser(User user) {
        this.user = user;
        if (user != null && (this.actor == null || this.actor.isBlank())) {
            this.actor = user.getEmail();
        }
    }

    @com.fasterxml.jackson.annotation.JsonProperty("user")
    public java.util.Map<String, Object> getUserSummary() {
        String email = getActor();
        return java.util.Map.of("email", email != null ? email : "SYSTEM");
    }

    public String getActor() {
        if (actor != null && !actor.isBlank()) return actor;
        return "SYSTEM";
    }
    public void setActor(String actor) { this.actor = actor; }

    public String getAction() { return action; }
    public void setAction(String action) { this.action = action; }

    public String getTarget() {
        if (target != null && !target.isBlank()) return target;
        if (entityType != null || entityId != null) {
            return (entityType != null ? entityType : "") + ":" + (entityId != null ? entityId : "");
        }
        return null;
    }
    public void setTarget(String target) { this.target = target; }

    public String getEntityType() { return entityType; }
    public void setEntityType(String entityType) {
        this.entityType = entityType;
        if (this.target == null && entityType != null) {
            this.target = entityType + (entityId != null ? ":" + entityId : "");
        }
    }

    public String getEntityId() { return entityId; }
    public void setEntityId(String entityId) {
        this.entityId = entityId;
        if (this.target == null && entityId != null) {
            this.target = (entityType != null ? entityType + ":" : "") + entityId;
        }
    }

    public OffsetDateTime getTimestamp() { return timestamp != null ? timestamp : createdAt; }
    public void setTimestamp(OffsetDateTime timestamp) {
        this.timestamp = timestamp;
        this.createdAt = timestamp;
    }

    public OffsetDateTime getCreatedAt() { return createdAt != null ? createdAt : timestamp; }
    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
        this.timestamp = createdAt;
    }

    public String getIp() { return ip != null ? ip : ipAddress; }
    public void setIp(String ip) {
        this.ip = ip;
        this.ipAddress = ip;
    }

    public String getIpAddress() { return ipAddress != null ? ipAddress : ip; }
    public void setIpAddress(String ipAddress) {
        this.ipAddress = ipAddress;
        this.ip = ipAddress;
    }

    public String getDetails() { return details; }
    public void setDetails(String details) { this.details = details; }
}
