package com.whereismyferry.backend.service;

import com.whereismyferry.backend.entity.AuditLog;
import com.whereismyferry.backend.entity.User;
import com.whereismyferry.backend.repository.AuditLogRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.List;

@Service
public class AuditService {

    private static final Logger log = LoggerFactory.getLogger(AuditService.class);
    private final AuditLogRepository auditLogRepository;

    public AuditService(AuditLogRepository auditLogRepository) {
        this.auditLogRepository = auditLogRepository;
    }

    /**
     * Appends an immutable audit log entry.
     */
    @Transactional(propagation = Propagation.REQUIRED)
    public AuditLog recordAction(User user, String action, String entityType, String entityId, String details, String ipAddress) {
        AuditLog auditLog = new AuditLog();
        auditLog.setUser(user);
        auditLog.setAction(action);
        auditLog.setEntityType(entityType);
        auditLog.setEntityId(entityId);
        auditLog.setDetails(details);
        auditLog.setIpAddress(ipAddress != null ? ipAddress : "127.0.0.1");
        auditLog.setCreatedAt(OffsetDateTime.now());

        AuditLog saved = auditLogRepository.save(auditLog);
        log.info("AUDIT_LOG [action={}, user={}, entity={}:{}]", action, user != null ? user.getEmail() : "SYSTEM", entityType, entityId);
        return saved;
    }

    @Transactional(readOnly = true)
    public List<AuditLog> getRecentAuditLogs() {
        return auditLogRepository.findTop100ByOrderByCreatedAtDesc();
    }

    @Transactional(readOnly = true)
    public Page<AuditLog> getAuditLogs(Pageable pageable) {
        return auditLogRepository.findAllByOrderByCreatedAtDesc(pageable);
    }

    @Transactional(readOnly = true)
    public List<AuditLog> filterByAction(String action) {
        return auditLogRepository.findByActionContainingIgnoreCaseOrderByCreatedAtDesc(action);
    }

    /**
     * Audit log is append-only: modifications and deletions are explicitly prohibited.
     */
    public void deleteAuditLog(Long id) {
        throw new UnsupportedOperationException("Audit logs are append-only and legally immutable. Deletion is prohibited.");
    }

    public void updateAuditLog(Long id, AuditLog updated) {
        throw new UnsupportedOperationException("Audit logs are append-only and legally immutable. Updates are prohibited.");
    }
}
