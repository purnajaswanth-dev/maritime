package com.whereismyferry.backend.repository;

import com.whereismyferry.backend.entity.Route;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface RouteRepository extends JpaRepository<Route, String> {
    Optional<Route> findByCodeIgnoreCase(String code);
    List<Route> findByOriginPortIdAndDestinationPortId(String originPortId, String destinationPortId);
    List<Route> findByOriginPortId(String originPortId);
    List<Route> findByDestinationPortId(String destinationPortId);
}
