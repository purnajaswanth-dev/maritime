package com.whereismyferry.backend.repository;

import com.whereismyferry.backend.entity.ServiceEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface ServiceEntityRepository extends JpaRepository<ServiceEntity, Long> {
    List<ServiceEntity> findByActiveTrue();
    List<ServiceEntity> findByRouteId(String routeId);
    List<ServiceEntity> findByVesselId(String vesselId);
    List<ServiceEntity> findByActiveTrueAndValidFromLessThanEqualAndValidToGreaterThanEqual(LocalDate fromDate, LocalDate toDate);
}
