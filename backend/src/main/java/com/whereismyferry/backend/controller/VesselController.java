package com.whereismyferry.backend.controller;

import com.whereismyferry.backend.dto.VesselDto;
import com.whereismyferry.backend.service.CatalogService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/vessels")
@Tag(name = "Vessels", description = "Fleet Vessel Information")
@CrossOrigin(origins = "*")
public class VesselController {

    private final CatalogService catalogService;

    public VesselController(CatalogService catalogService) {
        this.catalogService = catalogService;
    }

    @GetMapping
    @Operation(summary = "List all active fleet vessels")
    public ResponseEntity<List<VesselDto>> getVessels() {
        return ResponseEntity.ok(catalogService.getAllVessels());
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get vessel by ID or code")
    public ResponseEntity<VesselDto> getVessel(@PathVariable String id) {
        return ResponseEntity.ok(catalogService.getVesselById(id));
    }
}
