package com.whereismyferry.backend.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public class VesselLiveDto {

    @JsonProperty("vessel_id")
    private String vesselId;

    @JsonProperty("synthetic_mmsi")
    private Long syntheticMmsi;

    @JsonProperty("name")
    private String name;

    @JsonProperty("operator")
    private String operator;

    @JsonProperty("corridor")
    private String corridor;

    @JsonProperty("origin_terminal_id")
    private String originTerminalId;

    @JsonProperty("destination_terminal_id")
    private String destinationTerminalId;

    @JsonProperty("lat")
    private Double lat;

    @JsonProperty("lon")
    private Double lon;

    @JsonProperty("sog_knots")
    private Double sogKnots;

    @JsonProperty("cog_degrees")
    private Double cogDegrees;

    @JsonProperty("eta_lifecycle_state")
    private String etaLifecycleState;

    @JsonProperty("position_timestamp_utc")
    private String positionTimestampUtc;

    @JsonProperty("prediction_timestamp_utc")
    private String predictionTimestampUtc;

    @JsonProperty("predicted_arrival_utc")
    private String predictedArrivalUtc;

    @JsonProperty("estimated_remaining_minutes")
    private Double estimatedRemainingMinutes;

    @JsonProperty("uncertainty_lower_minutes")
    private Double uncertaintyLowerMinutes;

    @JsonProperty("uncertainty_upper_minutes")
    private Double uncertaintyUpperMinutes;

    @JsonProperty("distance_remaining_km")
    private Double distanceRemainingKm;

    @JsonProperty("distance_remaining_nm")
    private Double distanceRemainingNm;

    @JsonProperty("telemetry_age_seconds")
    private Double telemetryAgeSeconds;

    @JsonProperty("is_stale")
    private Boolean isStale;

    @JsonProperty("is_arrived")
    private Boolean isArrived;

    @JsonProperty("data_provenance")
    private String dataProvenance;

    @JsonProperty("model_weights_sha256")
    private String modelWeightsSha256;

    @JsonProperty("position_valid")
    private Boolean positionValid;

    public VesselLiveDto() {}

    public String getVesselId() { return vesselId; }
    public void setVesselId(String vesselId) { this.vesselId = vesselId; }

    public Long getSyntheticMmsi() { return syntheticMmsi; }
    public void setSyntheticMmsi(Long syntheticMmsi) { this.syntheticMmsi = syntheticMmsi; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getOperator() { return operator; }
    public void setOperator(String operator) { this.operator = operator; }

    public String getCorridor() { return corridor; }
    public void setCorridor(String corridor) { this.corridor = corridor; }

    public String getOriginTerminalId() { return originTerminalId; }
    public void setOriginTerminalId(String originTerminalId) { this.originTerminalId = originTerminalId; }

    public String getDestinationTerminalId() { return destinationTerminalId; }
    public void setDestinationTerminalId(String destinationTerminalId) { this.destinationTerminalId = destinationTerminalId; }

    public Double getLat() { return lat; }
    public void setLat(Double lat) { this.lat = lat; }

    public Double getLon() { return lon; }
    public void setLon(Double lon) { this.lon = lon; }

    public Double getSogKnots() { return sogKnots; }
    public void setSogKnots(Double sogKnots) { this.sogKnots = sogKnots; }

    public Double getCogDegrees() { return cogDegrees; }
    public void setCogDegrees(Double cogDegrees) { this.cogDegrees = cogDegrees; }

    public String getEtaLifecycleState() { return etaLifecycleState; }
    public void setEtaLifecycleState(String etaLifecycleState) { this.etaLifecycleState = etaLifecycleState; }

    public String getPositionTimestampUtc() { return positionTimestampUtc; }
    public void setPositionTimestampUtc(String positionTimestampUtc) { this.positionTimestampUtc = positionTimestampUtc; }

    public String getPredictionTimestampUtc() { return predictionTimestampUtc; }
    public void setPredictionTimestampUtc(String predictionTimestampUtc) { this.predictionTimestampUtc = predictionTimestampUtc; }

    public String getPredictedArrivalUtc() { return predictedArrivalUtc; }
    public void setPredictedArrivalUtc(String predictedArrivalUtc) { this.predictedArrivalUtc = predictedArrivalUtc; }

    public Double getEstimatedRemainingMinutes() { return estimatedRemainingMinutes; }
    public void setEstimatedRemainingMinutes(Double estimatedRemainingMinutes) { this.estimatedRemainingMinutes = estimatedRemainingMinutes; }

    public Double getUncertaintyLowerMinutes() { return uncertaintyLowerMinutes; }
    public void setUncertaintyLowerMinutes(Double uncertaintyLowerMinutes) { this.uncertaintyLowerMinutes = uncertaintyLowerMinutes; }

    public Double getUncertaintyUpperMinutes() { return uncertaintyUpperMinutes; }
    public void setUncertaintyUpperMinutes(Double uncertaintyUpperMinutes) { this.uncertaintyUpperMinutes = uncertaintyUpperMinutes; }

    public Double getDistanceRemainingKm() { return distanceRemainingKm; }
    public void setDistanceRemainingKm(Double distanceRemainingKm) { this.distanceRemainingKm = distanceRemainingKm; }

    public Double getDistanceRemainingNm() { return distanceRemainingNm; }
    public void setDistanceRemainingNm(Double distanceRemainingNm) { this.distanceRemainingNm = distanceRemainingNm; }

    public Double getTelemetryAgeSeconds() { return telemetryAgeSeconds; }
    public void setTelemetryAgeSeconds(Double telemetryAgeSeconds) { this.telemetryAgeSeconds = telemetryAgeSeconds; }

    public Boolean getIsStale() { return isStale; }
    public void setIsStale(Boolean stale) { isStale = stale; }

    public Boolean getIsArrived() { return isArrived; }
    public void setIsArrived(Boolean arrived) { isArrived = arrived; }

    public String getDataProvenance() { return dataProvenance; }
    public void setDataProvenance(String dataProvenance) { this.dataProvenance = dataProvenance; }

    public String getModelWeightsSha256() { return modelWeightsSha256; }
    public void setModelWeightsSha256(String modelWeightsSha256) { this.modelWeightsSha256 = modelWeightsSha256; }

    public Boolean getPositionValid() { return positionValid; }
    public void setPositionValid(Boolean positionValid) { this.positionValid = positionValid; }
}
