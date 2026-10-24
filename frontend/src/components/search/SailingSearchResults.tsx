import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, Ship, Compass, Ticket, ArrowRight, AlertCircle, Filter } from 'lucide-react';
import { Button } from '../common/Button';
import { StatusChip } from '../common/StatusChip';
import { BookingModal } from '../booking/BookingModal';
import { Departure } from '../../types/catalog';

export interface SearchResultItem {
  id: number;
  departureCode: string;
  routeId: string;
  routeName: string;
  originPortId: string;
  originPortName: string;
  destinationPortId: string;
  destinationPortName: string;
  scheduledDepartureTime: string;
  scheduledArrivalTime: string;
  durationMinutes: number;
  vesselId: string;
  vesselName: string;
  status: string;
  statusLabel: string;
  delayMinutes: number;
  seatsAvailable: number;
  fromPriceEur: number;
  liveTrackingAvailable: boolean;
}

export interface SearchResultData {
  originPortId: string;
  originPortName: string;
  destinationPortId: string;
  destinationPortName: string;
  searchDate: string;
  passengers: number;
  totalResults: number;
  departures: SearchResultItem[];
  emptyStateMessage?: string;
  nextAvailableSailing?: SearchResultItem;
}

interface SailingSearchResultsProps {
  data: SearchResultData | null;
  loading: boolean;
  error?: string | null;
  onSelectDate?: (dateStr: string) => void;
  onRetry?: () => void;
}

export const SailingSearchResults: React.FC<SailingSearchResultsProps> = ({
  data,
  loading,
  error,
  onSelectDate,
  onRetry,
}) => {
  const navigate = useNavigate();

  const [timeFilter, setTimeFilter] = useState<'all' | 'morning' | 'afternoon' | 'evening'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'on_time' | 'delayed' | 'cancelled'>('all');
  const [selectedDepartureForBooking, setSelectedDepartureForBooking] = useState<Departure | null>(null);

  if (loading) {
    return (
      <div className="search-results-skeleton" style={{ marginTop: '2rem' }}>
        <div style={{ height: '36px', backgroundColor: '#E2E8F0', borderRadius: '6px', marginBottom: '1rem', width: '280px' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              style={{
                height: '80px',
                backgroundColor: '#F8FAFC',
                border: '1px solid #E2E8F0',
                borderRadius: '8px',
              }}
            />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        role="alert"
        style={{
          marginTop: '2rem',
          padding: '1.5rem',
          backgroundColor: '#FEF2F2',
          border: '1px solid #F87171',
          borderRadius: '8px',
          textAlign: 'center',
        }}
      >
        <AlertCircle size={28} color="#DC2626" style={{ margin: '0 auto 0.75rem auto' }} />
        <p style={{ color: '#991B1B', fontWeight: 600, marginBottom: '0.75rem' }}>{error}</p>
        {onRetry && (
          <Button variant="secondary" onClick={onRetry}>
            Retry Search
          </Button>
        )}
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // Format tabular times
  const formatTime = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString('fr-FR', {
        timeZone: 'Europe/Paris',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      });
    } catch {
      return isoStr;
    }
  };

  // Client-side filtering
  const filteredDepartures = data.departures.filter((dep) => {
    // Time filter
    if (timeFilter !== 'all') {
      const depDate = new Date(dep.scheduledDepartureTime);
      const hour = depDate.getHours();
      if (timeFilter === 'morning' && (hour < 5 || hour >= 12)) return false;
      if (timeFilter === 'afternoon' && (hour < 12 || hour >= 18)) return false;
      if (timeFilter === 'evening' && hour < 18) return false;
    }

    // Status filter
    if (statusFilter === 'on_time') {
      return dep.status === 'SCHEDULED' && (!dep.delayMinutes || dep.delayMinutes === 0);
    }
    if (statusFilter === 'delayed') {
      return dep.delayMinutes > 0 || dep.status === 'DELAYED';
    }
    if (statusFilter === 'cancelled') {
      return dep.status === 'CANCELLED';
    }

    return true;
  });

  const handleOpenBooking = (item: SearchResultItem) => {
    const dep: Departure = {
      id: item.id,
      departureCode: item.departureCode,
      route: {
        id: item.routeId,
        code: item.routeId,
        name: item.routeName,
        originPortId: item.originPortId,
        originPortName: item.originPortName,
        destinationPortId: item.destinationPortId,
        destinationPortName: item.destinationPortName,
        distanceNm: 15.0,
        crossingDurationMinutes: Math.round(item.durationMinutes),
      },
      vessel: {
        id: item.vesselId,
        name: item.vesselName,
        mmsi: 227005551,
        passengerCapacity: item.seatsAvailable || 300,
        serviceSpeedKnots: 18.0,
      },
      scheduledDepartureTime: item.scheduledDepartureTime,
      scheduledArrivalTime: item.scheduledArrivalTime,
      status: item.status,
      liveTrackingAvailable: item.liveTrackingAvailable,
    };
    setSelectedDepartureForBooking(dep);
  };

  return (
    <div className="search-results-section" style={{ marginTop: '2.5rem' }}>
      {/* Header & Filter Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          marginBottom: '1.25rem',
          paddingBottom: '0.75rem',
          borderBottom: '1px solid var(--color-slate-dark)',
        }}
      >
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-navy)', margin: 0 }}>
            {data.originPortName} → {data.destinationPortName}
          </h2>
          <span style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)' }}>
            {filteredDepartures.length} of {data.totalResults} sailings found for {data.searchDate} ({data.passengers} {data.passengers === 1 ? 'passenger' : 'passengers'})
          </span>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <select
            value={timeFilter}
            onChange={(e) => setTimeFilter(e.target.value as any)}
            style={{
              padding: '0.375rem 0.625rem',
              borderRadius: '6px',
              border: '1px solid var(--color-slate-dark)',
              fontSize: '0.8125rem',
              color: 'var(--color-navy)',
              backgroundColor: '#FFFFFF',
            }}
            aria-label="Filter by time of day"
          >
            <option value="all">All departure times</option>
            <option value="morning">Morning (05:00 - 11:59)</option>
            <option value="afternoon">Afternoon (12:00 - 17:59)</option>
            <option value="evening">Evening (18:00+)</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            style={{
              padding: '0.375rem 0.625rem',
              borderRadius: '6px',
              border: '1px solid var(--color-slate-dark)',
              fontSize: '0.8125rem',
              color: 'var(--color-navy)',
              backgroundColor: '#FFFFFF',
            }}
            aria-label="Filter by status"
          >
            <option value="all">All statuses</option>
            <option value="on_time">On time</option>
            <option value="delayed">Delayed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Empty State */}
      {filteredDepartures.length === 0 ? (
        <div
          style={{
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            backgroundColor: '#F8FAFC',
            borderRadius: '8px',
            border: '1px dashed var(--color-slate-dark)',
          }}
        >
          <Ship size={32} color="#94A3B8" style={{ margin: '0 auto 0.75rem auto' }} />
          <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--color-navy)', marginBottom: '0.5rem' }}>
            {data.emptyStateMessage || 'No sailings on this date.'}
          </p>
          {data.nextAvailableSailing && (
            <div style={{ marginTop: '1rem' }}>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  const nextDateStr = data.nextAvailableSailing?.scheduledDepartureTime.split('T')[0];
                  if (nextDateStr && onSelectDate) {
                    onSelectDate(nextDateStr);
                  }
                }}
              >
                Jump to next available sailing &rarr;
              </Button>
            </div>
          )}
        </div>
      ) : (
        /* Results Table */
        <div style={{ overflowX: 'auto', border: '1px solid var(--color-slate-dark)', borderRadius: '8px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid var(--color-slate-dark)' }}>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)' }}>Departure</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)' }}>Arrival</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)' }}>Duration</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)' }}>Ship</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)' }}>Status</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)' }}>Price</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDepartures.map((dep) => (
                <tr
                  key={dep.id}
                  style={{
                    borderBottom: '1px solid #F1F5F9',
                    transition: 'background-color 0.15s',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8FAFC')}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                >
                  {/* Departure */}
                  <td style={{ padding: '1rem', fontVariantNumeric: 'tabular-nums' }}>
                    <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-navy)' }}>
                      {formatTime(dep.scheduledDepartureTime)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
                      {dep.originPortName}
                    </div>
                  </td>

                  {/* Arrival */}
                  <td style={{ padding: '1rem', fontVariantNumeric: 'tabular-nums' }}>
                    <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-navy)' }}>
                      {formatTime(dep.scheduledArrivalTime)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
                      {dep.destinationPortName}
                    </div>
                  </td>

                  {/* Duration */}
                  <td style={{ padding: '1rem', fontVariantNumeric: 'tabular-nums', color: 'var(--color-slate-light)' }}>
                    {Math.round(dep.durationMinutes)} min
                  </td>

                  {/* Vessel */}
                  <td style={{ padding: '1rem' }}>
                    <div style={{ fontWeight: 600, color: 'var(--color-navy)' }}>{dep.vesselName}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
                      {dep.seatsAvailable} seats left
                    </div>
                  </td>

                  {/* Status */}
                  <td style={{ padding: '1rem' }}>
                    <span
                      style={{
                        display: 'inline-block',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        backgroundColor:
                          dep.status === 'CANCELLED'
                            ? '#FEF2F2'
                            : dep.delayMinutes > 0
                            ? '#FFFBEB'
                            : dep.status === 'ARRIVED'
                            ? '#F0FDF4'
                            : '#EFF6FF',
                        color:
                          dep.status === 'CANCELLED'
                            ? '#991B1B'
                            : dep.delayMinutes > 0
                            ? '#92400E'
                            : dep.status === 'ARRIVED'
                            ? '#166534'
                            : '#1E40AF',
                      }}
                    >
                      {dep.statusLabel || dep.status}
                    </span>
                  </td>

                  {/* Price */}
                  <td style={{ padding: '1rem', fontVariantNumeric: 'tabular-nums' }}>
                    <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--color-navy)' }}>
                      {Number(dep.fromPriceEur).toFixed(2)} &euro;
                    </div>
                    <div style={{ fontSize: '0.6875rem', color: 'var(--color-slate-light)' }}>
                      Total ({data.passengers} pax)
                    </div>
                  </td>

                  {/* Actions: Book and Track */}
                  <td style={{ padding: '1rem', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '0.5rem', alignItems: 'center' }}>
                      <Button
                        variant="primary"
                        size="sm"
                        icon={<Ticket size={14} />}
                        onClick={() => handleOpenBooking(dep)}
                      >
                        Book
                      </Button>

                      {dep.liveTrackingAvailable ? (
                        <Button
                          variant="secondary"
                          size="sm"
                          icon={<Compass size={14} />}
                          onClick={() => navigate(`/track/departures/${dep.departureCode}`)}
                        >
                          Track
                        </Button>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: '#94A3B8', padding: '0 0.5rem' }}>
                          Schedule only
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Booking Modal */}
      {selectedDepartureForBooking && (
        <BookingModal
          isOpen={true}
          departure={selectedDepartureForBooking}
          passengerCount={data.passengers}
          onClose={() => setSelectedDepartureForBooking(null)}
          onBookingComplete={(booking) => {
            setSelectedDepartureForBooking(null);
            navigate(`/bookings?ref=${booking.bookingReference}`);
          }}
        />
      )}
    </div>
  );
};
