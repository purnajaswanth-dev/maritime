package com.whereismyferry.backend.controller;

import com.whereismyferry.backend.dto.*;
import com.whereismyferry.backend.service.CatalogService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/v1")
@Tag(name = "Catalog", description = "Public Ferry Network Catalog, Timetables, and Sailings")
@CrossOrigin(origins = "*")
public class CatalogController {

    private final CatalogService catalogService;

    public CatalogController(CatalogService catalogService) {
        this.catalogService = catalogService;
    }

    @GetMapping("/ports")
    @Operation(summary = "List all ferry ports and terminals")
    public ResponseEntity<List<PortDto>> getPorts() {
        return ResponseEntity.ok(catalogService.getAllPorts());
    }

    @GetMapping("/ports/{id}")
    @Operation(summary = "Get port details with live departure and arrival boards")
    public ResponseEntity<PortDetailDto> getPortDetail(@PathVariable String id) {
        return ResponseEntity.ok(catalogService.getPortDetail(id));
    }

    @GetMapping("/routes")
    @Operation(summary = "List all network routes")
    public ResponseEntity<List<RouteDto>> getRoutes() {
        return ResponseEntity.ok(catalogService.getAllRoutes());
    }

    @GetMapping("/routes/{id}")
    @Operation(summary = "Get route details by ID or code")
    public ResponseEntity<RouteDto> getRoute(@PathVariable String id) {
        return ResponseEntity.ok(catalogService.getRouteById(id));
    }

    @GetMapping("/departures")
    @Operation(summary = "Search departures by origin, destination, date, and passenger capacity")
    public ResponseEntity<List<DepartureDto>> getDepartures(
            @RequestParam(required = false) String from,
            @RequestParam(required = false) String to,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date,
            @RequestParam(required = false) Integer passengers) {
        return ResponseEntity.ok(catalogService.searchDepartures(from, to, date, passengers));
    }

    @GetMapping("/departures/{id}")
    @Operation(summary = "Get departure details by ID or departure code")
    public ResponseEntity<DepartureDto> getDeparture(@PathVariable String id) {
        try {
            Long numericId = Long.parseLong(id);
            return ResponseEntity.ok(catalogService.getDepartureById(numericId));
        } catch (NumberFormatException e) {
            return ResponseEntity.ok(catalogService.getDepartureByCode(id));
        }
    }

    @GetMapping("/timetable")
    @Operation(summary = "Get recurring timetable entries by route and date")
    public ResponseEntity<List<TimetableEntryDto>> getTimetable(
            @RequestParam(required = false) String route,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date) {
        return ResponseEntity.ok(catalogService.getTimetable(route, date));
    }

    @GetMapping("/fares")
    @Operation(summary = "Get fare rules and pricing structure by route")
    public ResponseEntity<List<FareRuleDto>> getFares(@RequestParam(required = false) String route) {
        return ResponseEntity.ok(catalogService.getFareRules(route));
    }
}
