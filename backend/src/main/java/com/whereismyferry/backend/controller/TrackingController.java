package com.whereismyferry.backend.controller;

import com.whereismyferry.backend.dto.PublicTrackResponseDto;
import com.whereismyferry.backend.dto.ShareLinkResponseDto;
import com.whereismyferry.backend.dto.SimulationLiveDto;
import com.whereismyferry.backend.service.TrackingService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.Map;

@RestController
@RequestMapping("/api/v1")
@Tag(name = "Tracking", description = "Real-Time Vessel Tracking, Telemetry Streams, and Public Share Links")
@CrossOrigin(origins = "*")
public class TrackingController {

    private final TrackingService trackingService;

    public TrackingController(TrackingService trackingService) {
        this.trackingService = trackingService;
    }

    @GetMapping("/departures/{id}/live")
    @Operation(summary = "Get current live telemetry, coordinates, and ML ETA predictions")
    public ResponseEntity<SimulationLiveDto> getLiveTracking(@PathVariable String id) {
        return ResponseEntity.ok(trackingService.getLiveTracking(id));
    }

    @GetMapping("/departures/{id}/track")
    @Operation(summary = "Get full voyage coordinates and waypoint history for map rendering")
    public ResponseEntity<Map<String, Object>> getVoyageTrack(@PathVariable String id) {
        return ResponseEntity.ok(trackingService.getVoyageTrack(id));
    }

    @GetMapping("/routes/geometry")
    @Operation(summary = "Get official water navigation route geometries for all active corridors")
    public ResponseEntity<java.util.List<com.whereismyferry.backend.dto.RouteGeometryDto>> getRouteGeometries() {
        return ResponseEntity.ok(trackingService.getRouteGeometries());
    }

    @GetMapping(value = "/departures/{id}/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "Subscribe to live 1 Hz Server-Sent Events (SSE) telemetry stream")
    public SseEmitter streamTracking(@PathVariable String id) {
        return trackingService.subscribeLiveStream(id);
    }

    @GetMapping(value = "/stream/vessels", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "Subscribe to fleet-wide real-time Server-Sent Events (SSE) vessel stream")
    public SseEmitter streamFleetVessels() {
        return trackingService.subscribeFleetVesselsStream();
    }

    @PostMapping("/departures/{id}/share")
    @Operation(summary = "Generate a secure, expiring shareable link for public voyage tracking")
    public ResponseEntity<ShareLinkResponseDto> createShareLink(
            @PathVariable String id,
            @RequestParam(defaultValue = "24") int hours) {
        return ResponseEntity.ok(trackingService.createShareLink(id, hours));
    }

    @GetMapping("/track/{token}")
    @Operation(summary = "Resolve public shareable link without authentication")
    public ResponseEntity<PublicTrackResponseDto> getSharedTrack(@PathVariable String token) {
        return ResponseEntity.ok(trackingService.resolveSharedTrack(token));
    }
}
