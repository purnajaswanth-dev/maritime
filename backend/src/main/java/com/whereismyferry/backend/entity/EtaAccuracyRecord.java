package com.whereismyferry.backend.entity;

import jakarta.persistence.*;
import java.time.OffsetDateTime;
import java.util.Objects;

@Entity
@Table(name = "eta_accuracy_records")
public class EtaAccuracyRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "departure_id", nullable = false)
    private Departure departure;

    @Column(name = "timestamp_utc", nullable = false)
    private OffsetDateTime timestampUtc;

    @Column(name = "predicted_minutes_to_arrival")
    private Double predictedMinutesToArrival;

    @Column(name = "actual_remaining_minutes")
    private Double actualRemainingMinutes;

    @Column(name = "error_minutes")
    private Double errorMinutes;

    @Column(name = "distance_to_berth_km")
    private Double distanceToBerthKm;

    public EtaAccuracyRecord() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Departure getDeparture() { return departure; }
    public void setDeparture(Departure departure) { this.departure = departure; }

    public OffsetDateTime getTimestampUtc() { return timestampUtc; }
    public void setTimestampUtc(OffsetDateTime timestampUtc) { this.timestampUtc = timestampUtc; }

    public Double getPredictedMinutesToArrival() { return predictedMinutesToArrival; }
    public void setPredictedMinutesToArrival(Double predictedMinutesToArrival) { this.predictedMinutesToArrival = predictedMinutesToArrival; }

    public Double getActualRemainingMinutes() { return actualRemainingMinutes; }
    public void setActualRemainingMinutes(Double actualRemainingMinutes) { this.actualRemainingMinutes = actualRemainingMinutes; }

    public Double getErrorMinutes() { return errorMinutes; }
    public void setErrorMinutes(Double errorMinutes) { this.errorMinutes = errorMinutes; }

    public Double getDistanceToBerthKm() { return distanceToBerthKm; }
    public void setDistanceToBerthKm(Double distanceToBerthKm) { this.distanceToBerthKm = distanceToBerthKm; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof EtaAccuracyRecord that)) return false;
        return Objects.equals(id, that.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
