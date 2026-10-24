package com.whereismyferry.backend.repository;

import com.whereismyferry.backend.entity.Schedule;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface ScheduleRepository extends JpaRepository<Schedule, Long> {
    Optional<Schedule> findByTripId(String tripId);
    List<Schedule> findByRouteId(String routeId);
    List<Schedule> findByActiveTrue();
    List<Schedule> findByActiveTrueAndValidFromLessThanEqualAndValidToGreaterThanEqual(LocalDate date1, LocalDate date2);
}
