package com.whereismyferry.backend.repository;

import com.whereismyferry.backend.entity.Disruption;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DisruptionRepository extends JpaRepository<Disruption, Long> {
    List<Disruption> findByStatus(String status);
    List<Disruption> findByRouteIdAndStatus(String routeId, String status);
}
