import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  Clock,
  Compass,
  Ship,
  Search,
  Filter,
  ArrowRight,
  RefreshCw,
  Users,
  Ticket,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Select } from '../components/common/Select';
import { StatusChip } from '../components/common/StatusChip';
import { Badge } from '../components/common/Badge';
import { BookingModal } from '../components/booking/BookingModal';
import { apiClient } from '../api/client';
import { Departure, Route } from '../types/catalog';

const FALLBACK_DEPARTURES: Departure[] = [
  {
    id: 1,
    departureCode: 'DEP-20241024-BES-LCQ-0830',
    route: {
      id: 'BES-LCQ',
      code: 'BES-LCQ',
      name: 'Brest \u2192 Le Conquet',
      originPortId: 'BES',
      originPortName: 'Brest Port de Commerce',
      destinationPortId: 'LCQ',
      destinationPortName: 'Le Conquet Gare Maritime',
      distanceNm: 15.2,
      crossingDurationMinutes: 75,
    },
    vessel: {
      id: 'ves-1',
      name: 'Fromveur II',
      mmsi: 228037700,
      passengerCapacity: 350,
      serviceSpeedKnots: 15.5,
    },
    scheduledDepartureTime: '2026-10-24T08:30:00Z',
    scheduledArrivalTime: '2026-10-24T09:45:00Z',
    status: 'UNDERWAY',
    liveTrackingAvailable: true,
  },
  {
    id: 2,
    departureCode: 'DEP-20241024-LCQ-OUE-1000',
    route: {
      id: 'LCQ-OUE',
      code: 'LCQ-OUE',
      name: 'Le Conquet \u2192 Ouessant (Port du Stiff)',
      originPortId: 'LCQ',
      originPortName: 'Le Conquet Gare Maritime',
      destinationPortId: 'OUE',
      destinationPortName: 'Ouessant (Port du Stiff)',
      distanceNm: 13.5,
      crossingDurationMinutes: 65,
    },
    vessel: {
      id: 'ves-1',
      name: 'Fromveur II',
      mmsi: 228037700,
      passengerCapacity: 350,
      serviceSpeedKnots: 15.5,
    },
    scheduledDepartureTime: '2026-10-24T10:00:00Z',
    scheduledArrivalTime: '2026-10-24T11:05:00Z',
    status: 'SCHEDULED',
    liveTrackingAvailable: true,
  },
  {
    id: 3,
    departureCode: 'DEP-20241024-AUD-SEI-0930',
    route: {
      id: 'AUD-SEI',
      code: 'AUD-SEI',
      name: 'Audierne (Sainte-\u00C9vette) \u2192 \u00CEle de Sein',
      originPortId: 'AUD',
      originPortName: 'Audierne (Sainte-\u00C9vette)',
      destinationPortId: 'SEI',
      destinationPortName: '\u00CEle de Sein',
      distanceNm: 9.8,
      crossingDurationMinutes: 60,
    },
    vessel: {
      id: 'ves-2',
      name: 'Enez Sun 3',
      mmsi: 227318000,
      passengerCapacity: 250,
      serviceSpeedKnots: 14.0,
    },
    scheduledDepartureTime: '2026-10-24T09:30:00Z',
    scheduledArrivalTime: '2026-10-24T10:30:00Z',
    status: 'SCHEDULED',
    liveTrackingAvailable: true,
  },
  {
    id: 4,
    departureCode: 'DEP-20241024-LCQ-MOL-1130',
    route: {
      id: 'LCQ-MOL',
      code: 'LCQ-MOL',
      name: 'Le Conquet \u2192 \u00CEle-Mol\u00E8ne',
      originPortId: 'LCQ',
      originPortName: 'Le Conquet Gare Maritime',
      destinationPortId: 'MOL',
      destinationPortName: '\u00CEle-Mol\u00E8ne (Quai Nord)',
      distanceNm: 8.2,
      crossingDurationMinutes: 45,
    },
    vessel: {
      id: 'ves-3',
      name: 'Enez Eussa 3',
      mmsi: 228198900,
      passengerCapacity: 302,
      serviceSpeedKnots: 16.0,
    },
    scheduledDepartureTime: '2026-10-24T11:30:00Z',
    scheduledArrivalTime: '2026-10-24T12:15:00Z',
    status: 'SCHEDULED',
    liveTrackingAvailable: true,
  },
];

export const TimetablePage: React.FC = () => {
  const [departures, setDepartures] = useState<Departure[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<string>('all');
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedBookingDeparture, setSelectedBookingDeparture] = useState<Departure | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiClient<Departure[]>('/departures').catch(() => FALLBACK_DEPARTURES),
      apiClient<Route[]>('/routes').catch(() => []),
    ])
      .then(([depData, routeData]) => {
        setDepartures(depData && depData.length > 0 ? depData : FALLBACK_DEPARTURES);
        setRoutes(routeData || []);
      })
      .finally(() => setLoading(false));
  }, []);

  const routeOptions = useMemo(() => {
    const defaultOpt = [{ label: 'All Corridors & Routes', value: 'all' }];
    if (routes.length > 0) {
      return [
        ...defaultOpt,
        ...routes.map((r) => ({ label: `${r.originPortName} \u2192 ${r.destinationPortName}`, value: r.code })),
      ];
    }
    return [
      ...defaultOpt,
      { label: 'Brest \u2192 Le Conquet', value: 'BES-LCQ' },
      { label: 'Le Conquet \u2192 Ouessant', value: 'LCQ-OUE' },
      { label: 'Audierne \u2192 \u00CEle de Sein', value: 'AUD-SEI' },
      { label: 'Le Conquet \u2192 \u00CEle-Mol\u00E8ne', value: 'LCQ-MOL' },
    ];
  }, [routes]);

  const filteredDepartures = useMemo(() => {
    return departures.filter((dep) => {
      // Route filter
      if (selectedRoute !== 'all') {
        const routeCode = dep.route?.code || dep.route?.id;
        if (routeCode !== selectedRoute) return false;
      }
      // Search query filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const origin = (dep.route?.originPortName || '').toLowerCase();
        const dest = (dep.route?.destinationPortName || '').toLowerCase();
        const vessel = (dep.vessel?.name || '').toLowerCase();
        const code = (dep.departureCode || '').toLowerCase();
        if (!origin.includes(query) && !dest.includes(query) && !vessel.includes(query) && !code.includes(query)) {
          return false;
        }
      }
      return true;
    });
  }, [departures, selectedRoute, searchQuery]);

  const formatTime = (isoString?: string) => {
    if (!isoString) return '--:--';
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="container" style={{ padding: '2rem 1rem' }}>
      {/* Title & Introduction */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '0.25rem' }}>
          Daily Ferry Timetable &amp; Sailings
        </h1>
        <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
          Scheduled Brittany passenger crossings between the Finistère mainland and Ponant islands.
        </p>
      </div>

      {/* Filter & Search Bar */}
      <Card style={{ padding: '1.25rem', marginBottom: '2rem', backgroundColor: '#FFFFFF' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', alignItems: 'flex-end' }}>
          <div>
            <label htmlFor="timetable-date" style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-slate-medium)', display: 'block', marginBottom: '0.35rem' }}>
              Travel Date
            </label>
            <Input
              id="timetable-date"
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              style={{ marginBottom: 0 }}
            />
          </div>

          <div>
            <Select
              id="timetable-corridor"
              label="Corridor / Route"
              options={routeOptions}
              value={selectedRoute}
              onChange={(e) => setSelectedRoute(e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="timetable-search" style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-slate-medium)', display: 'block', marginBottom: '0.35rem' }}>
              Search Sailings
            </label>
            <Input
              id="timetable-search"
              placeholder="Search port, vessel, or code..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ marginBottom: 0 }}
            />
          </div>
        </div>
      </Card>

      {/* Results Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--color-navy)', margin: 0 }}>
          Scheduled Departures ({filteredDepartures.length})
        </h2>
        <span style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)' }}>
          Timezone: Europe/Paris
        </span>
      </div>

      {/* Departures List */}
      {filteredDepartures.length === 0 ? (
        <Card style={{ padding: '3rem 1.5rem', textAlign: 'center' }}>
          <Compass size={36} style={{ color: 'var(--color-slate-light)', margin: '0 auto 1rem auto' }} />
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--color-navy)', marginBottom: '0.5rem' }}>
            No departures found
          </h3>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-slate-medium)', maxWidth: '420px', margin: '0 auto 1rem auto' }}>
            No scheduled sailings matched your route or search criteria. Try selecting another corridor.
          </p>
          <Button variant="secondary" size="sm" onClick={() => { setSelectedRoute('all'); setSearchQuery(''); }}>
            Reset Filters
          </Button>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredDepartures.map((dep) => (
            <Card key={dep.id} style={{ padding: '1.25rem 1.5rem', transition: 'box-shadow 0.2s ease' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.25rem' }}>
                {/* Route & Times */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
                  {/* Time Block */}
                  <div style={{ textAlign: 'center', minWidth: '90px' }}>
                    <div style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--color-navy)' }}>
                      {formatTime(dep.scheduledDepartureTime)}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
                      Arr: {formatTime(dep.scheduledArrivalTime)}
                    </div>
                  </div>

                  {/* Route & Vessel */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--color-navy)' }}>
                        {dep.route?.originPortName || 'Mainland'} → {dep.route?.destinationPortName || 'Island'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', fontSize: '0.8125rem', color: 'var(--color-slate-medium)' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Ship size={14} style={{ color: 'var(--color-primary)' }} />
                        <strong>{dep.vessel?.name || 'Penn ar Bed Ferry'}</strong>
                      </span>
                      {dep.vessel?.passengerCapacity && (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: 'var(--color-slate-light)' }}>
                          <Users size={12} />
                          {dep.vessel.passengerCapacity} pax
                        </span>
                      )}
                      {dep.route?.crossingDurationMinutes && (
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: 'var(--color-slate-light)' }}>
                          <Clock size={12} />
                          {dep.route.crossingDurationMinutes} min
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Status & Actions */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                  <StatusChip status={dep.status || 'SCHEDULED'} />
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Ticket size={14} />}
                    onClick={() => setSelectedBookingDeparture(dep)}
                  >
                    Book Now
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    icon={<Compass size={14} />}
                    onClick={() => navigate('/tracking')}
                  >
                    Track Live
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {selectedBookingDeparture && (
        <BookingModal
          isOpen={!!selectedBookingDeparture}
          onClose={() => setSelectedBookingDeparture(null)}
          departure={selectedBookingDeparture}
        />
      )}
    </div>
  );
};
