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
import { AnnouncementBanner } from '../components/common/AnnouncementBanner';
import { SailingSearchForm, SearchFormData } from '../components/search/SailingSearchForm';
import { SailingSearchResults, SearchResultData } from '../components/search/SailingSearchResults';
import { apiClient } from '../api/client';
import { Departure, Route, TimetableEntry } from '../types/catalog';

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
];

export const TimetablePage: React.FC = () => {
  const navigate = useNavigate();

  // Search State
  const [searchData, setSearchData] = useState<SearchResultData | null>(null);
  const [searchLoading, setSearchLoading] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [lastSearchParams, setLastSearchParams] = useState<SearchFormData | null>(null);

  // Timetable State
  const [departures, setDepartures] = useState<Departure[]>(FALLBACK_DEPARTURES);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [timetableEntries, setTimetableEntries] = useState<TimetableEntry[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<string>('all');
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const [viewMode, setViewMode] = useState<'day' | 'weekly'>('day');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedBookingDeparture, setSelectedBookingDeparture] = useState<Departure | null>(null);

  const handleFromToSearch = async (params: SearchFormData) => {
    setSearchLoading(true);
    setSearchError(null);
    setLastSearchParams(params);

    try {
      const url = `/api/v1/departures/search?from=${encodeURIComponent(params.from)}&to=${encodeURIComponent(params.to)}&date=${encodeURIComponent(params.date)}&passengers=${params.passengers}`;
      const data = await apiClient.get<SearchResultData>(url);
      setSearchData(data);
    } catch (err: any) {
      setSearchError(err?.message || 'Failed to search sailings.');
    } finally {
      setSearchLoading(false);
    }
  };

  useEffect(() => {
    Promise.all([
      apiClient.get<Departure[]>('/api/v1/departures').catch(() => []),
      apiClient.get<Route[]>('/api/v1/routes').catch(() => []),
      apiClient.get<TimetableEntry[]>('/api/v1/timetable').catch(() => []),
    ])
      .then(([depData, routeData, ttData]) => {
        if (Array.isArray(depData) && depData.length > 0) setDepartures(depData);
        if (Array.isArray(routeData) && routeData.length > 0) setRoutes(routeData);
        if (Array.isArray(ttData) && ttData.length > 0) setTimetableEntries(ttData);
      })
      .catch(() => {});
  }, []);

  const routeOptions = useMemo(() => {
    const defaultOpt = [{ label: 'All Corridors & Routes', value: 'all' }];
    if (routes.length > 0) {
      return [
        ...defaultOpt,
        ...routes.map((r) => ({
          label: `${r.originPortName} \u2192 ${r.destinationPortName}`,
          value: r.code || r.id,
        })),
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
      if (selectedRoute !== 'all') {
        const routeCode = dep.route?.code || dep.route?.id;
        if (routeCode !== selectedRoute) return false;
      }
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

  const filteredWeeklyEntries = useMemo(() => {
    if (selectedRoute === 'all') return timetableEntries;
    return timetableEntries.filter((t) => t.routeId === selectedRoute);
  }, [timetableEntries, selectedRoute]);

  const formatTime = (isoString?: string) => {
    if (!isoString) return '--:--';
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString('fr-FR', {
        timeZone: 'Europe/Paris',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="container" style={{ padding: '2rem 1rem', maxWidth: '1100px', margin: '0 auto' }}>
      {/* Title & Introduction */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '0.25rem' }}>
          Daily Ferry Timetable &amp; Sailings
        </h1>
        <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
          Scheduled Brittany passenger crossings between the Finistère mainland and Ponant islands.
        </p>
      </div>

      <AnnouncementBanner scope="ALL" />

      {/* 1. From-To Search Form */}
      <div style={{ marginBottom: '2.5rem' }}>
        <SailingSearchForm
          onSearch={handleFromToSearch}
          loading={searchLoading}
        />
        <SailingSearchResults
          data={searchData}
          loading={searchLoading}
          error={searchError}
          onSelectDate={(newDate) => {
            if (lastSearchParams) {
              handleFromToSearch({ ...lastSearchParams, date: newDate });
            }
          }}
          onRetry={() => {
            if (lastSearchParams) {
              handleFromToSearch(lastSearchParams);
            }
          }}
        />
      </div>

      {/* 2. Route & Weekly Timetable Browser */}
      <div style={{ paddingTop: '1.5rem', borderTop: '2px solid var(--color-slate-dark)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-navy)', margin: 0 }}>
              Route Timetable Schedule
            </h2>
            <span style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)' }}>
              Standard operating timetable across Penn ar Bed maritime corridors
            </span>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Button
              variant={viewMode === 'day' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setViewMode('day')}
            >
              Today's Sailings
            </Button>
            <Button
              variant={viewMode === 'weekly' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setViewMode('weekly')}
            >
              Weekly Schedule
            </Button>
          </div>
        </div>

        {/* Filter & Search Bar */}
        <Card style={{ padding: '1.25rem', marginBottom: '1.5rem', backgroundColor: '#FFFFFF' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', alignItems: 'flex-end' }}>
            <div>
              <Input
                id="timetable-date"
                label="Travel Date"
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
              <Input
                id="timetable-search"
                label="Search Sailings"
                placeholder="Search port, vessel, or code..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ marginBottom: 0 }}
              />
            </div>

            <div>
              <Button
                variant="secondary"
                size="sm"
                icon={<RefreshCw size={14} />}
                onClick={() => { setSelectedRoute('all'); setSearchQuery(''); }}
                style={{ width: '100%', height: '42px' }}
              >
                Reset Filters
              </Button>
            </div>
          </div>
        </Card>

        {/* Content View: Day Cards vs Weekly Table */}
        {viewMode === 'weekly' ? (
          <div style={{ overflowX: 'auto', border: '1px solid var(--color-slate-dark)', borderRadius: '8px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#F8FAFC', borderBottom: '1px solid var(--color-slate-dark)' }}>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)' }}>Route</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)' }}>Dep. Time</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)' }}>Arr. Time</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)' }}>Operating Days</th>
                  <th style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-slate-light)' }}>Tracking</th>
                </tr>
              </thead>
              <tbody>
                {filteredWeeklyEntries.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-slate-light)' }}>
                      No weekly timetable entries found for this corridor.
                    </td>
                  </tr>
                ) : (
                  filteredWeeklyEntries.map((t, idx) => (
                    <tr key={t.tripId || idx} style={{ borderBottom: '1px solid #F1F5F9' }}>
                      <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--color-navy)' }}>
                        {t.routeName || `${t.originPortName} \u2192 ${t.destinationPortName}`}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', fontVariantNumeric: 'tabular-nums' }}>
                        {typeof t.departureTime === 'string' ? t.departureTime.substring(0, 5) : '--:--'}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', fontVariantNumeric: 'tabular-nums' }}>
                        {typeof t.arrivalTime === 'string' ? t.arrivalTime.substring(0, 5) : '--:--'}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', fontSize: '0.8125rem', color: 'var(--color-slate-light)' }}>
                        Daily (Mon - Sun)
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        {t.trackingSupported ? (
                          <Badge variant="success">Live Tracking</Badge>
                        ) : (
                          <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>Schedule only</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
            {filteredDepartures.length === 0 ? (
              <div style={{ gridColumn: '1 / -1', padding: '3rem', textAlign: 'center', backgroundColor: '#F8FAFC', borderRadius: '8px' }}>
                <p style={{ color: 'var(--color-slate-light)', margin: 0 }}>No sailings match the selected route or search criteria.</p>
              </div>
            ) : (
              filteredDepartures.map((dep) => (
                <Card key={dep.id} style={{ padding: '1.25rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                    <div style={{ fontVariantNumeric: 'tabular-nums' }}>
                      <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-navy)' }}>
                        {formatTime(dep.scheduledDepartureTime)}
                      </span>
                      <span style={{ fontSize: '0.875rem', color: 'var(--color-slate-light)', margin: '0 0.5rem' }}>&rarr;</span>
                      <span style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-navy)' }}>
                        {formatTime(dep.scheduledArrivalTime)}
                      </span>
                    </div>
                    <StatusChip status={dep.status as any} />
                  </div>

                  <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-navy)', marginBottom: '0.25rem' }}>
                    {dep.route?.originPortName} &rarr; {dep.route?.destinationPortName}
                  </div>

                  <div style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)', marginBottom: '1rem' }}>
                    {dep.vessel?.name} &bull; {dep.departureCode}
                  </div>

                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<Ticket size={14} />}
                      onClick={() => setSelectedBookingDeparture(dep)}
                      style={{ flex: 1 }}
                    >
                      Book Now
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      icon={<Compass size={14} />}
                      onClick={() => navigate(dep.liveTrackingAvailable ? `/track/departures/${dep.departureCode || dep.id}` : '/tracking')}
                      style={{ flex: 1 }}
                    >
                      Track Live
                    </Button>
                  </div>
                </Card>
              ))
            )}
          </div>
        )}
      </div>

      {/* Booking Modal */}
      {selectedBookingDeparture && (
        <BookingModal
          isOpen={true}
          departure={selectedBookingDeparture}
          onClose={() => setSelectedBookingDeparture(null)}
          onBookingComplete={(booking) => {
            setSelectedBookingDeparture(null);
            navigate(`/bookings?ref=${booking.bookingReference}`);
          }}
        />
      )}
    </div>
  );
};
