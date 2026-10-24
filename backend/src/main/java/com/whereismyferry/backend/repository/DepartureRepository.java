package com.whereismyferry.backend.repository;

import com.whereismyferry.backend.entity.Departure;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface DepartureRepository extends JpaRepository<Departure, Long> {

    Optional<Departure> findByDepartureCode(String departureCode);

    boolean existsByDepartureCode(String departureCode);

    boolean existsByVesselIdAndScheduledDepartureTime(String vesselId, OffsetDateTime scheduledDepartureTime);

    List<Departure> findByScheduledDepartureTimeBetweenOrderByScheduledDepartureTimeAsc(
            OffsetDateTime start, OffsetDateTime end);

    @Query("SELECT d FROM Departure d WHERE " +
           "(:originPortId IS NULL OR d.route.originPort.id = :originPortId) AND " +
           "(:destPortId IS NULL OR d.route.destinationPort.id = :destPortId) AND " +
           "(d.scheduledDepartureTime >= :start AND d.scheduledDepartureTime <= :end) " +
           "ORDER BY d.scheduledDepartureTime ASC")
    List<Departure> findDepartures(
            @Param("originPortId") String originPortId,
            @Param("destPortId") String destPortId,
            @Param("start") OffsetDateTime start,
            @Param("end") OffsetDateTime end);

    @Query("SELECT d FROM Departure d WHERE " +
           "(:originPortId IS NULL OR d.route.originPort.id = :originPortId) AND " +
           "(:destPortId IS NULL OR d.route.destinationPort.id = :destPortId) AND " +
           "(d.scheduledDepartureTime >= :start AND d.scheduledDepartureTime <= :end)")
    Page<Departure> findDeparturesPaged(
            @Param("originPortId") String originPortId,
            @Param("destPortId") String destPortId,
            @Param("start") OffsetDateTime start,
            @Param("end") OffsetDateTime end,
            Pageable pageable);

    @Query("SELECT d FROM Departure d WHERE d.route.originPort.id = :portId AND " +
           "d.scheduledDepartureTime >= :start AND d.scheduledDepartureTime <= :end " +
           "ORDER BY d.scheduledDepartureTime ASC")
    List<Departure> findDeparturesFromPort(
            @Param("portId") String portId,
            @Param("start") OffsetDateTime start,
            @Param("end") OffsetDateTime end);

    @Query("SELECT d FROM Departure d WHERE d.route.destinationPort.id = :portId AND " +
           "d.scheduledArrivalTime >= :start AND d.scheduledArrivalTime <= :end " +
           "ORDER BY d.scheduledArrivalTime ASC")
    List<Departure> findArrivalsToPort(
            @Param("portId") String portId,
            @Param("start") OffsetDateTime start,
            @Param("end") OffsetDateTime end);
}
