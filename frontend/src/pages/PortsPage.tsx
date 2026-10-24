import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  MapPin,
  Navigation,
  Anchor,
  Search,
  Building,
  Shield,
  Clock,
  Compass,
  ArrowRight,
  ArrowLeft,
  Phone,
  Mail,
  AlertTriangle,
  Radio,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';
import { StatusChip } from '../components/common/StatusChip';
import { AnnouncementBanner } from '../components/common/AnnouncementBanner';
import { apiClient } from '../api/client';
import { Departure } from '../types/catalog';

interface PortData {
  id: string;
  code: string;
  name: string;
  latitude: number;
  longitude: number;
  berthRadiusM?: number;
  berthCount?: number;
  status: string; // OPEN or CLOSED
  type?: 'Mainland Hub' | 'Island Terminal' | 'Seasonal Terminal';
  address?: string;
  phone?: string;
  email?: string;
  facilities?: string;
  notes?: string;
}

const DEFAULT_PORTS: PortData[] = [
  {
    id: 'BES',
    code: 'BES',
    name: 'Brest Port de Commerce',
    type: 'Mainland Hub',
    latitude: 48.3831,
    longitude: -4.4842,
    berthCount: 3,
    status: 'OPEN',
    facilities: 'Ticket Office & Waiting Hall, Long-term Parking, PRM Wheelchair Access',
  },
  {
    id: 'LCQ',
    code: 'LCQ',
    name: 'Le Conquet Gare Maritime',
    type: 'Mainland Hub',
    latitude: 48.3592,
    longitude: -4.7794,
    berthCount: 2,
    status: 'OPEN',
    facilities: 'Ticket Counter, Baggage Drop, Drop-off Zone, Waiting Room',
  },
  {
    id: 'MOL',
    code: 'MOL',
    name: 'Île-Molène (Quai Nord)',
    type: 'Island Terminal',
    latitude: 48.3972,
    longitude: -4.9531,
    berthCount: 1,
    status: 'OPEN',
    facilities: 'Passenger Shelter, Cargo Crane, PRM Boarding Ramp',
  },
  {
    id: 'OUE',
    code: 'OUE',
    name: 'Ouessant (Port du Stiff)',
    type: 'Island Terminal',
    latitude: 48.4756,
    longitude: -5.0567,
    berthCount: 2,
    status: 'OPEN',
    facilities: 'Gare Maritime Terminal, Island Shuttle Connections, Luggage Handling',
  },
  {
    id: 'AUD',
    code: 'AUD',
    name: 'Audierne (Sainte-Évette)',
    type: 'Mainland Hub',
    latitude: 48.0167,
    longitude: -4.5417,
    berthCount: 2,
    status: 'OPEN',
    facilities: 'Passenger Terminal, Day Parking, Ticket Counter, Luggage Check',
  },
  {
    id: 'SEI',
    code: 'SEI',
    name: 'Île de Sein',
    type: 'Island Terminal',
    latitude: 48.0375,
    longitude: -4.8500,
    berthCount: 1,
    status: 'OPEN',
    facilities: 'Passenger Shelter, Freight Lift, Wheelchair Assistance',
  },
  {
    id: 'CAM',
    code: 'CAM',
    name: 'Camaret-sur-Mer',
    type: 'Seasonal Terminal',
    latitude: 48.2778,
    longitude: -4.5956,
    berthCount: 1,
    status: 'OPEN',
    facilities: 'Seasonal Ticket Kiosk, Floating Pontoon, Passenger Gangway',
  },
];

interface PortDetailData extends PortData {
  upcomingDepartures?: Departure[];
  upcomingArrivals?: Departure[];
}

export const PortsPage: React.FC = () => {
  const { code: portCodeParam } = useParams<{ code?: string }>();
  const navigate = useNavigate();

  const [ports, setPorts] = useState<PortData[]>(DEFAULT_PORTS);
  const [portDetail, setPortDetail] = useState<PortDetailData | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'all' | 'mainland' | 'islands'>('all');
  const [loading, setLoading] = useState<boolean>(false);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load all ports from backend
  useEffect(() => {
    apiClient.get<PortData[]>('/api/v1/ports')
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          // Merge with DEFAULT_PORTS to preserve types/labels
          const merged = DEFAULT_PORTS.map((def) => {
            const found = data.find((d) => d.code === def.code || d.id === def.id);
            return found ? { ...def, ...found } : def;
          });
          setPorts(merged);
        }
      })
      .catch(() => {
        // Fallback already in place
      });
  }, []);

  // If portCodeParam is provided, load port details
  useEffect(() => {
    if (!portCodeParam) {
      setPortDetail(null);
      return;
    }

    setDetailLoading(true);
    apiClient.get<PortDetailData>(`/api/v1/ports/${encodeURIComponent(portCodeParam)}`)
      .then((data) => {
        setPortDetail(data);
      })
      .catch(() => {
        const fallback = ports.find((p) => p.code.toLowerCase() === portCodeParam.toLowerCase() || p.id.toLowerCase() === portCodeParam.toLowerCase());
        if (fallback) {
          setPortDetail(fallback);
        } else {
          setError(`Failed to load details for port ${portCodeParam}`);
        }
      })
      .finally(() => setDetailLoading(false));
  }, [portCodeParam, ports]);

  const filteredPorts = useMemo(() => {
    return ports.filter((p) => {
      if (activeTab === 'mainland' && p.type !== 'Mainland Hub') return false;
      if (activeTab === 'islands' && p.type !== 'Island Terminal') return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          p.name.toLowerCase().includes(q) ||
          p.code.toLowerCase().includes(q) ||
          (p.facilities && p.facilities.toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [ports, activeTab, searchQuery]);

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

  // Render Port Detail View if code param is present
  if (portCodeParam && portDetail) {
    return (
      <div className="container" style={{ padding: '2rem 1rem', maxWidth: '1100px', margin: '0 auto' }}>
        {/* Navigation Breadcrumb */}
        <div style={{ marginBottom: '1.5rem' }}>
          <button
            onClick={() => navigate('/ports')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'transparent',
              border: 'none',
              color: 'var(--color-teal)',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
              padding: 0,
            }}
          >
            <ArrowLeft size={16} /> Back to all ports
          </button>
        </div>

        {/* Port Header Card */}
        <Card style={{ padding: '1.5rem', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <Anchor size={24} color="var(--color-teal)" />
                <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-navy)', margin: 0 }}>
                  {portDetail.name}
                </h1>
                <Badge variant={portDetail.status === 'CLOSED' ? 'danger' : 'success'}>
                  {portDetail.status || 'OPEN'}
                </Badge>
              </div>

              <div style={{ fontSize: '0.875rem', color: 'var(--color-slate-light)', display: 'flex', gap: '1.25rem', flexWrap: 'wrap' }}>
                <span><strong>Code:</strong> {portDetail.code}</span>
                <span><strong>Berth Radius:</strong> {portDetail.berthRadiusM || 800}m</span>
                <span><strong>Coordinates:</strong> {portDetail.latitude.toFixed(4)}°N, {Math.abs(portDetail.longitude).toFixed(4)}°W</span>
              </div>
            </div>

            {portDetail.status === 'CLOSED' && (
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', backgroundColor: '#FEF2F2', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #FCA5A5', color: '#B91C1C', fontSize: '0.8125rem' }}>
                <AlertTriangle size={16} />
                <span>Port is currently closed to maritime traffic.</span>
              </div>
            )}
          </div>

          {portDetail.facilities && (
            <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #F1F5F9', fontSize: '0.875rem', color: 'var(--color-slate-medium)' }}>
              <strong>Terminal Facilities:</strong> {portDetail.facilities}
            </div>
          )}
        </Card>

        {/* Port-Scoped Announcements */}
        <div style={{ marginBottom: '2rem' }}>
          <AnnouncementBanner scope="PORT" targetId={portDetail.id || portCodeParam} />
        </div>

        {/* Live Boards: Departing & Arriving */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {/* Departing Board */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Navigation size={18} color="var(--color-teal)" />
              <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-navy)', margin: 0 }}>
                Departing from {portDetail.name}
              </h2>
            </div>

            {(!portDetail.upcomingDepartures || portDetail.upcomingDepartures.length === 0) ? (
              <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#F8FAFC', borderRadius: '8px', border: '1px solid var(--color-slate-dark)' }}>
                <p style={{ color: 'var(--color-slate-light)', margin: 0 }}>No upcoming departures scheduled today.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {portDetail.upcomingDepartures.map((dep) => (
                  <Card key={dep.id} style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.375rem' }}>
                      <div style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 700, fontSize: '1.125rem', color: 'var(--color-navy)' }}>
                        {formatTime(dep.scheduledDepartureTime)}
                      </div>
                      <StatusChip status={dep.status as any} />
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-navy)' }}>
                      To {dep.route?.destinationPortName}
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)', display: 'flex', justifyContent: 'space-between', marginTop: '0.375rem' }}>
                      <span>{dep.vessel?.name}</span>
                      {dep.liveTrackingAvailable && (
                        <button
                          onClick={() => navigate(`/track/departures/${dep.departureCode}`)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--color-teal)',
                            fontWeight: 600,
                            cursor: 'pointer',
                            fontSize: '0.8125rem',
                          }}
                        >
                          Track sailing &rarr;
                        </button>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Arriving Board */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Clock size={18} color="var(--color-navy)" />
              <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-navy)', margin: 0 }}>
                Arriving at {portDetail.name}
              </h2>
            </div>

            {(!portDetail.upcomingArrivals || portDetail.upcomingArrivals.length === 0) ? (
              <div style={{ padding: '2rem', textAlign: 'center', backgroundColor: '#F8FAFC', borderRadius: '8px', border: '1px solid var(--color-slate-dark)' }}>
                <p style={{ color: 'var(--color-slate-light)', margin: 0 }}>No upcoming arrivals scheduled today.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {portDetail.upcomingArrivals.map((dep) => (
                  <Card key={dep.id} style={{ padding: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.375rem' }}>
                      <div style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 700, fontSize: '1.125rem', color: 'var(--color-navy)' }}>
                        {formatTime(dep.scheduledArrivalTime)}
                      </div>
                      <StatusChip status={dep.status as any} />
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-navy)' }}>
                      From {dep.route?.originPortName}
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)', display: 'flex', justifyContent: 'space-between', marginTop: '0.375rem' }}>
                      <span>{dep.vessel?.name}</span>
                      {dep.liveTrackingAvailable && (
                        <button
                          onClick={() => navigate(`/track/departures/${dep.departureCode}`)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--color-teal)',
                            fontWeight: 600,
                            cursor: 'pointer',
                            fontSize: '0.8125rem',
                          }}
                        >
                          Track sailing &rarr;
                        </button>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Render All Ports Directory
  return (
    <div className="container" style={{ padding: '2rem 1rem', maxWidth: '1100px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '0.25rem' }}>
          Ports &amp; Maritime Terminals
        </h1>
        <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
          Mainland ferry hubs and Ponant island arrival terminals across Finistère and the Iroise Sea.
        </p>
      </div>

      <AnnouncementBanner scope="ALL" />

      {/* Search Input & Category Filters */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
        <Input
          id="ports-search-input"
          placeholder="Search port by name, code, or facilities..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          icon={<Search size={16} />}
        />

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Button
            variant={activeTab === 'all' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setActiveTab('all')}
          >
            All Terminals
          </Button>
          <Button
            variant={activeTab === 'mainland' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setActiveTab('mainland')}
          >
            Mainland
          </Button>
          <Button
            variant={activeTab === 'islands' ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setActiveTab('islands')}
          >
            Islands
          </Button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {filteredPorts.map((port) => (
          <Card
            key={port.id}
            style={{ padding: '1.25rem', cursor: 'pointer', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
            onClick={() => navigate(`/ports/${port.id}`)}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Anchor size={18} color="var(--color-teal)" />
                  <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, color: 'var(--color-navy)', margin: 0 }}>
                    {port.name}
                  </h3>
                </div>
                <Badge variant={port.status === 'CLOSED' ? 'danger' : 'success'}>
                  {port.status || 'OPEN'}
                </Badge>
              </div>

              <div style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)', marginBottom: '0.75rem' }}>
                {port.facilities || 'Ticket office, Waiting hall, Quayside boarding'}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.75rem', borderTop: '1px solid #F1F5F9' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
                {port.berthCount || 1} Berth &bull; {port.berthRadiusM || 800}m radius
              </span>
              <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-teal)', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                Live boards <ArrowRight size={14} />
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
