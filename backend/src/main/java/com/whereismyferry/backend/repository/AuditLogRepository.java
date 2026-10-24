package com.whereismyferry.backend.repository;

import com.whereismyferry.backend.entity.AuditLog;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AuditLogRepository extends JpaRepository<AuditLog, Long> {
    Page<AuditLog> findAllByOrderByTimestampDesc(Pageable pageable);
    List<AuditLog> findTop50ByOrderByTimestampDesc();

    List<AuditLog> findTop100ByOrderByCreatedAtDesc();
    Page<AuditLog> findAllByOrderByCreatedAtDesc(Pageable pageable);
    List<AuditLog> findByActionContainingIgnoreCaseOrderByCreatedAtDesc(String action);
}
