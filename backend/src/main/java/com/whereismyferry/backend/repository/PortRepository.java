package com.whereismyferry.backend.repository;

import com.whereismyferry.backend.entity.Port;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface PortRepository extends JpaRepository<Port, String> {
    Optional<Port> findByCodeIgnoreCase(String code);
}
