package com.whereismyferry.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

public class SimulationLiveDto {
    @JsonProperty("departure_id")
    private String departureId;

    @JsonProperty("service_id")
    private String serviceId;

    @JsonProperty("corridor")
    private String corridor;

    @JsonProperty("vessel_id")
    private String vesselId;

    @JsonProperty("lifecycle_state")
    private String lifecycleState;

    @JsonProperty("current_position")
    private Map<String, Object> currentPosition;

    @JsonProperty("eta_prediction")
    private Map<String, Object> etaPrediction;

    @JsonProperty("target_berth")
    private Map<String, Object> targetBerth;

    @JsonProperty("confidence_score")
    private Double confidenceScore;

    @JsonProperty("data_source")
    private String dataSource;

    @JsonProperty("model_weights_sha256")
    private String modelWeightsSha256;

    @JsonProperty("message_id")
    private String messageId;

    public SimulationLiveDto() {}

    public String getDepartureId() { return departureId; }
    public void setDepartureId(String departureId) { this.departureId = departureId; }

    public String getServiceId() { return serviceId; }
    public void setServiceId(String serviceId) { this.serviceId = serviceId; }

    public String getCorridor() { return corridor; }
    public void setCorridor(String corridor) { this.corridor = corridor; }

    public String getVesselId() { return vesselId; }
    public void setVesselId(String vesselId) { this.vesselId = vesselId; }

    public String getLifecycleState() { return lifecycleState; }
    public void setLifecycleState(String lifecycleState) { this.lifecycleState = lifecycleState; }

    public Map<String, Object> getCurrentPosition() { return currentPosition; }
    public void setCurrentPosition(Map<String, Object> currentPosition) { this.currentPosition = currentPosition; }

    public Map<String, Object> getEtaPrediction() { return etaPrediction; }
    public void setEtaPrediction(Map<String, Object> etaPrediction) { this.etaPrediction = etaPrediction; }

    public Map<String, Object> getTargetBerth() { return targetBerth; }
    public void setTargetBerth(Map<String, Object> targetBerth) { this.targetBerth = targetBerth; }

    public Double getConfidenceScore() { return confidenceScore; }
    public void setConfidenceScore(Double confidenceScore) { this.confidenceScore = confidenceScore; }

    public String getDataSource() { return dataSource; }
    public void setDataSource(String dataSource) { this.dataSource = dataSource; }

    public String getModelWeightsSha256() { return modelWeightsSha256; }
    public void setModelWeightsSha256(String modelWeightsSha256) { this.modelWeightsSha256 = modelWeightsSha256; }

    public String getMessageId() { return messageId; }
    public void setMessageId(String messageId) { this.messageId = messageId; }
}
