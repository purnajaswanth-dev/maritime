package com.whereismyferry.backend.repository;

import com.whereismyferry.backend.entity.EtaAccuracyRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface EtaAccuracyRecordRepository extends JpaRepository<EtaAccuracyRecord, Long> {
    List<EtaAccuracyRecord> findByDepartureIdOrderByTimestampUtcAsc(Long departureId);
}
