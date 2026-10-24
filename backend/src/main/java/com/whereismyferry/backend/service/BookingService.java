package com.whereismyferry.backend.service;

import com.whereismyferry.backend.dto.*;
import com.whereismyferry.backend.entity.*;
import com.whereismyferry.backend.exception.ResourceNotFoundException;
import com.whereismyferry.backend.repository.BookingRepository;
import com.whereismyferry.backend.repository.DepartureRepository;
import com.whereismyferry.backend.repository.TicketRepository;
import com.whereismyferry.backend.repository.UserRepository;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.security.SecureRandom;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

@Service
public class BookingService {

    private final BookingRepository bookingRepository;
    private final DepartureRepository departureRepository;
    private final TicketRepository ticketRepository;
    private final UserRepository userRepository;
    private final CatalogService catalogService;
    private final SystemConfigService systemConfigService;
    private final SecureRandom random = new SecureRandom();

    private static final String ALPHANUM = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

    public BookingService(BookingRepository bookingRepository,
                          DepartureRepository departureRepository,
                          TicketRepository ticketRepository,
                          UserRepository userRepository,
                          CatalogService catalogService,
                          SystemConfigService systemConfigService) {
        this.bookingRepository = bookingRepository;
        this.departureRepository = departureRepository;
        this.ticketRepository = ticketRepository;
        this.userRepository = userRepository;
        this.catalogService = catalogService;
        this.systemConfigService = systemConfigService;
    }

    @Transactional
    public BookingResponseDto createBooking(CreateBookingRequestDto request, User user) {
        if (systemConfigService.isMaintenanceMode()) {
            throw new com.whereismyferry.backend.exception.MaintenanceModeException(
                    "Passenger reservations are temporarily suspended during maintenance mode: " + systemConfigService.getMaintenanceReason()
            );
        }

        Departure departure = departureRepository.findById(request.getDepartureId())
                .orElseThrow(() -> new ResourceNotFoundException("Departure not found with id: " + request.getDepartureId()));

        Departure returnDeparture = null;
        if (request.getReturnDepartureId() != null) {
            returnDeparture = departureRepository.findById(request.getReturnDepartureId())
                    .orElseThrow(() -> new ResourceNotFoundException("Return departure not found with id: " + request.getReturnDepartureId()));
        }

        // Generate reference: WIMF-YYYYMMDD-XXXX
        String datePart = LocalDate.now().format(DateTimeFormatter.BASIC_ISO_DATE);
        String randomPart = generateRandomCode(4);
        String bookingReference = "WIMF-" + datePart + "-" + randomPart;

        Booking booking = new Booking();
        booking.setBookingReference(bookingReference);
        booking.setUser(user);
        booking.setDeparture(departure);
        booking.setReturnDeparture(returnDeparture);
        booking.setStatus("CONFIRMED");
        booking.setPaymentStatus("PAID");
        booking.setContactEmail(request.getContactEmail());
        booking.setContactPhone(request.getContactPhone());

        // Calculate pricing & create passengers
        BigDecimal totalAmount = BigDecimal.ZERO;
        List<Passenger> passengers = new ArrayList<>();
        List<Ticket> tickets = new ArrayList<>();

        int seq = 1;
        for (PassengerItemDto pDto : request.getPassengers()) {
            Passenger p = new Passenger();
            p.setBooking(booking);
            p.setFirstName(pDto.getFirstName());
            p.setLastName(pDto.getLastName());
            String type = pDto.getPassengerType() != null ? pDto.getPassengerType().toUpperCase(Locale.ROOT) : "ADULT";
            p.setPassengerType(type);
            p.setVehicleType(pDto.getVehicleType());
            p.setVehicleRegistration(pDto.getVehicleRegistration());
            passengers.add(p);

            BigDecimal farePrice = calculateFarePrice(type);
            totalAmount = totalAmount.add(farePrice);

            // Generate ticket
            Ticket ticket = new Ticket();
            ticket.setBooking(booking);
            ticket.setPassenger(p);
            String ticketNumber = String.format("TKT-%s-%02d", bookingReference, seq++);
            ticket.setTicketNumber(ticketNumber);
            ticket.setBarcode(ticketNumber.replace("-", ""));
            ticket.setQrCodeData(String.format("{\"ref\":\"%s\",\"tkt\":\"%s\",\"pax\":\"%s %s\",\"status\":\"VALID\"}",
                    bookingReference, ticketNumber, p.getFirstName(), p.getLastName()));
            ticket.setStatus("VALID");
            ticket.setIssuedAt(OffsetDateTime.now());
            tickets.add(ticket);
        }

        booking.setTotalAmountEur(totalAmount);
        booking.setPassengers(passengers);
        booking.setTickets(tickets);

        Booking saved = bookingRepository.save(booking);
        return mapToDto(saved);
    }

    @Transactional(readOnly = true)
    public List<BookingResponseDto> getUserBookings(User user) {
        List<Booking> list = bookingRepository.findByUserId(user.getId());
        return list.stream().map(this::mapToDto).toList();
    }

    @Transactional(readOnly = true)
    public BookingResponseDto getBookingByReference(String bookingReference, User user) {
        Booking booking = bookingRepository.findByBookingReference(bookingReference)
                .orElseThrow(() -> new ResourceNotFoundException("Booking not found: " + bookingReference));

        validateOwnership(booking, user);
        return mapToDto(booking);
    }

    @Transactional
    public BookingResponseDto cancelBooking(String bookingReference, User user) {
        Booking booking = bookingRepository.findByBookingReference(bookingReference)
                .orElseThrow(() -> new ResourceNotFoundException("Booking not found: " + bookingReference));

        validateOwnership(booking, user);

        // Cancellation policy: at least 24h prior to departure
        OffsetDateTime minCancelTime = OffsetDateTime.now().plusHours(24);
        if (booking.getDeparture().getScheduledDepartureTime().isBefore(minCancelTime)) {
            throw new IllegalArgumentException("Bookings can only be cancelled at least 24 hours prior to departure.");
        }

        booking.setStatus("CANCELLED");
        for (Ticket ticket : booking.getTickets()) {
            ticket.setStatus("CANCELLED");
        }

        Booking updated = bookingRepository.save(booking);
        return mapToDto(updated);
    }

    private void validateOwnership(Booking booking, User user) {
        if (user != null && user.getRoles() != null &&
                user.getRoles().stream().anyMatch(r -> "ROLE_ADMIN".equals(r.getName()))) {
            return;
        }
        if (booking.getUser() != null && (user == null || !booking.getUser().getId().equals(user.getId()))) {
            throw new AccessDeniedException("You are not authorized to view or manage this booking.");
        }
    }

    private BigDecimal calculateFarePrice(String passengerType) {
        return switch (passengerType) {
            case "RESIDENT" -> new BigDecimal("14.50");
            case "CHILD" -> new BigDecimal("21.00");
            case "INFANT" -> BigDecimal.ZERO;
            case "SENIOR" -> new BigDecimal("30.00");
            case "ADULT" -> new BigDecimal("36.00");
            default -> new BigDecimal("36.00");
        };
    }

    private String generateRandomCode(int length) {
        StringBuilder sb = new StringBuilder(length);
        for (int i = 0; i < length; i++) {
            sb.append(ALPHANUM.charAt(random.nextInt(ALPHANUM.length())));
        }
        return sb.toString();
    }

    private BookingResponseDto mapToDto(Booking b) {
        BookingResponseDto dto = new BookingResponseDto();
        dto.setId(b.getId());
        dto.setBookingReference(b.getBookingReference());
        dto.setStatus(b.getStatus());
        dto.setTotalAmountEur(b.getTotalAmountEur());
        dto.setCurrency(b.getCurrency());
        dto.setPaymentStatus(b.getPaymentStatus());
        dto.setContactEmail(b.getContactEmail());
        dto.setContactPhone(b.getContactPhone());
        dto.setCreatedAt(b.getCreatedAt());

        if (b.getDeparture() != null) {
            dto.setDeparture(catalogService.getDepartureById(b.getDeparture().getId()));
        }
        if (b.getReturnDeparture() != null) {
            dto.setReturnDeparture(catalogService.getDepartureById(b.getReturnDeparture().getId()));
        }

        if (b.getPassengers() != null) {
            dto.setPassengers(b.getPassengers().stream().map(p -> {
                PassengerItemDto pDto = new PassengerItemDto(p.getFirstName(), p.getLastName(), p.getPassengerType());
                pDto.setVehicleType(p.getVehicleType());
                pDto.setVehicleRegistration(p.getVehicleRegistration());
                return pDto;
            }).toList());
        }

        if (b.getTickets() != null) {
            dto.setTickets(b.getTickets().stream().map(t -> {
                TicketDto tDto = new TicketDto();
                tDto.setId(t.getId());
                tDto.setTicketNumber(t.getTicketNumber());
                if (t.getPassenger() != null) {
                    tDto.setPassengerName(t.getPassenger().getFirstName() + " " + t.getPassenger().getLastName());
                    tDto.setPassengerType(t.getPassenger().getPassengerType());
                }
                tDto.setQrCodeData(t.getQrCodeData());
                tDto.setBarcode(t.getBarcode());
                tDto.setStatus(t.getStatus());
                tDto.setIssuedAt(t.getIssuedAt());
                return tDto;
            }).toList());
        }

        return dto;
    }
}
