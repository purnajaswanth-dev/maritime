package com.whereismyferry.backend.controller;

import com.whereismyferry.backend.dto.BookingResponseDto;
import com.whereismyferry.backend.dto.CreateBookingRequestDto;
import com.whereismyferry.backend.entity.User;
import com.whereismyferry.backend.repository.UserRepository;
import com.whereismyferry.backend.service.BookingService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/bookings")
@Tag(name = "Booking", description = "Passenger Ferry Bookings, QR Tickets, and Cancellation")
@CrossOrigin(origins = "*")
public class BookingController {

    private final BookingService bookingService;
    private final UserRepository userRepository;

    public BookingController(BookingService bookingService, UserRepository userRepository) {
        this.bookingService = bookingService;
        this.userRepository = userRepository;
    }

    @PostMapping
    @Operation(summary = "Create a new passenger booking")
    public ResponseEntity<BookingResponseDto> createBooking(
            @Valid @RequestBody CreateBookingRequestDto request,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = resolveUser(userDetails);
        BookingResponseDto response = bookingService.createBooking(request, user);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping
    @Operation(summary = "List all bookings for authenticated passenger")
    public ResponseEntity<List<BookingResponseDto>> getBookings(
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = resolveUser(userDetails);
        return ResponseEntity.ok(bookingService.getUserBookings(user));
    }

    @GetMapping("/{reference}")
    @Operation(summary = "Get booking details by reference code")
    public ResponseEntity<BookingResponseDto> getBooking(
            @PathVariable String reference,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = resolveUser(userDetails);
        return ResponseEntity.ok(bookingService.getBookingByReference(reference, user));
    }

    @DeleteMapping("/{reference}")
    @Operation(summary = "Cancel booking (available up to 24h before departure)")
    public ResponseEntity<BookingResponseDto> cancelBooking(
            @PathVariable String reference,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = resolveUser(userDetails);
        return ResponseEntity.ok(bookingService.cancelBooking(reference, user));
    }

    private User resolveUser(UserDetails userDetails) {
        if (userDetails == null) {
            return null;
        }
        return userRepository.findByEmail(userDetails.getUsername()).orElse(null);
    }
}
