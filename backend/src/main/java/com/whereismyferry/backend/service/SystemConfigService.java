package com.whereismyferry.backend.service;

import com.whereismyferry.backend.entity.User;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;

@Service
public class SystemConfigService {

    private static final Logger log = LoggerFactory.getLogger(SystemConfigService.class);

    private final AtomicBoolean maintenanceMode = new AtomicBoolean(false);
    private volatile String maintenanceReason = "Scheduled system maintenance";
    private volatile OffsetDateTime maintenanceActivatedAt = null;
    private volatile String maintenanceActivatedBy = "SYSTEM";

    private final Map<String, Boolean> featureFlags = new ConcurrentHashMap<>();
    private final AuditService auditService;

    public SystemConfigService(AuditService auditService) {
        this.auditService = auditService;
        // Default feature flags
        featureFlags.put("ENABLE_AIS_REPLAY", true);
        featureFlags.put("ENABLE_SSE_STREAMING", true);
        featureFlags.put("ENABLE_ML_PREDICTIONS", true);
        featureFlags.put("ENABLE_ONLINE_BOOKINGS", true);
    }

    public boolean isMaintenanceMode() {
        return maintenanceMode.get();
    }

    public void setMaintenanceMode(boolean enabled, User adminUser, String reason) {
        boolean oldVal = maintenanceMode.getAndSet(enabled);
        this.maintenanceReason = reason != null ? reason : "Scheduled maritime system update";
        if (enabled) {
            this.maintenanceActivatedAt = OffsetDateTime.now();
            this.maintenanceActivatedBy = adminUser != null ? adminUser.getEmail() : "SYSTEM";
        } else {
            this.maintenanceActivatedAt = null;
        }

        auditService.recordAction(
                adminUser,
                enabled ? "ENABLE_MAINTENANCE_MODE" : "DISABLE_MAINTENANCE_MODE",
                "SYSTEM_CONFIG",
                "MAINTENANCE",
                "Reason: " + this.maintenanceReason + " (was " + oldVal + ")",
                "127.0.0.1"
        );
        log.warn("SYSTEM MAINTENANCE MODE changed to {} by {} [Reason: {}]", enabled, maintenanceActivatedBy, this.maintenanceReason);
    }

    public String getMaintenanceReason() {
        return maintenanceReason;
    }

    public OffsetDateTime getMaintenanceActivatedAt() {
        return maintenanceActivatedAt;
    }

    public String getMaintenanceActivatedBy() {
        return maintenanceActivatedBy;
    }

    public Map<String, Boolean> getFeatureFlags() {
        return Map.copyOf(featureFlags);
    }

    public void setFeatureFlag(String key, boolean value, User adminUser) {
        featureFlags.put(key, value);
        auditService.recordAction(
                adminUser,
                "UPDATE_FEATURE_FLAG",
                "SYSTEM_CONFIG",
                key,
                "Set to " + value,
                "127.0.0.1"
        );
    }
}
