import { Departure } from './catalog';

export interface BookingPassenger {
  firstName: string;
  lastName: string;
  passengerType: string;
  vehicleType?: string;
  vehicleRegistration?: string;
}

export interface BookingTicket {
  id: number;
  ticketNumber: string;
  passengerName: string;
  passengerType: string;
  qrCodeData: string;
  barcode: string;
  status: string;
  issuedAt?: string;
}

export interface Booking {
  id: number;
  bookingReference: string;
  status: 'CONFIRMED' | 'CANCELLED' | string;
  totalAmountEur: number;
  currency: string;
  paymentStatus: string;
  contactEmail: string;
  contactPhone?: string;
  createdAt: string;
  departure: Departure;
  returnDeparture?: Departure;
  passengers: BookingPassenger[];
  tickets: BookingTicket[];
}

export interface CreateBookingPayload {
  departureId: number | string;
  returnDepartureId?: number | string;
  contactEmail: string;
  contactPhone?: string;
  passengers: BookingPassenger[];
}
