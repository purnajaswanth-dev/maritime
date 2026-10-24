package com.whereismyferry.backend.service;

import com.whereismyferry.backend.entity.AuditLog;
import com.whereismyferry.backend.repository.AuditLogRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuditLogService {

    private final AuditLogRepository auditLogRepository;

    public AuditLogService(AuditLogRepository auditLogRepository) {
        this.auditLogRepository = auditLogRepository;
    }

    @Transactional
    public void record(String actor, String action, String target, String ip, String details) {
        AuditLog entry = new AuditLog(actor, action, target, ip, details);
        auditLogRepository.save(entry);
    }
}
