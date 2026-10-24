package com.whereismyferry.backend.repository;

import com.whereismyferry.backend.entity.Vessel;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface VesselRepository extends JpaRepository<Vessel, String> {
    Optional<Vessel> findByCodeIgnoreCase(String code);
    Optional<Vessel> findByTrackingVesselId(String trackingVesselId);
}
