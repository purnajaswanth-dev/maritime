import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
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
  CheckCircle2,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Badge } from '../components/common/Badge';

interface PortDetails {
  id: string;
  code: string;
  name: string;
  frenchName: string;
  latitude: number;
  longitude: number;
  type: 'Mainland Hub' | 'Island Terminal' | 'Seasonal Terminal';
  berthCount: number;
  description: string;
  facilities: string[];
  connectingRoutes: string[];
}

const BRITTANY_PORTS: PortDetails[] = [
  {
    id: 'BES',
    code: 'BES',
    name: 'Brest Port de Commerce',
    frenchName: 'Port de Commerce de Brest',
    latitude: 48.3831,
    longitude: -4.4842,
    type: 'Mainland Hub',
    berthCount: 3,
    description: 'Major regional deep-water commercial and passenger terminal inside the sheltered Rade de Brest.',
    facilities: ['Ticket Office & Waiting Hall', 'Long-term Parking', 'PRM Wheelchair Access', 'Cafeteria & Restrooms'],
    connectingRoutes: ['Brest \u2192 Le Conquet', 'Brest \u2192 \u00CEle-Mol\u00E8ne', 'Brest \u2192 Ouessant (Port du Stiff)'],
  },
  {
    id: 'LCQ',
    code: 'LCQ',
    name: 'Le Conquet Gare Maritime',
    frenchName: 'Gare Maritime du Conquet',
    latitude: 48.3592,
    longitude: -4.7794,
    type: 'Mainland Hub',
    berthCount: 2,
    description: 'Westernmost mainland departure point in France, providing fast crossings to Mol\u00E8ne and Ouessant.',
    facilities: ['Ticket Counter', 'Baggage Drop', 'Drop-off Zone', 'Waiting Room'],
    connectingRoutes: ['Le Conquet \u2192 \u00CEle-Mol\u00E8ne', 'Le Conquet \u2192 Ouessant (Port du Stiff)'],
  },
  {
    id: 'MOL',
    code: 'MOL',
    name: '\u00CEle-Mol\u00E8ne (Quai Nord)',
    frenchName: '\u00CEle-Mol\u00E8ne Quai Nord',
    latitude: 48.3972,
    longitude: -4.9531,
    type: 'Island Terminal',
    berthCount: 1,
    description: 'Island pier in the Mol\u00E8ne archipelago, deeply influenced by tidal windows and currents.',
    facilities: ['Passenger Shelter', 'Cargo Crane', 'PRM Boarding Ramp'],
    connectingRoutes: ['\u00CEle-Mol\u00E8ne \u2192 Le Conquet', '\u00CEle-Mol\u00E8ne \u2192 Ouessant (Port du Stiff)'],
  },
  {
    id: 'OUE',
    code: 'OUE',
    name: 'Ouessant (Port du Stiff)',
    frenchName: 'Ouessant Port du Stiff',
    latitude: 48.4756,
    longitude: -5.0567,
    type: 'Island Terminal',
    berthCount: 2,
    description: 'Primary all-weather island terminal on the eastern bay of Ouessant with roll-on roll-off cargo ramp.',
    facilities: ['Gare Maritime Terminal', 'Island Shuttle Connections', 'Luggage Handling', 'Bicycle Rental'],
    connectingRoutes: ['Ouessant \u2192 Le Conquet', 'Ouessant \u2192 Brest'],
  },
  {
    id: 'AUD',
    code: 'AUD',
    name: 'Audierne (Sainte-\u00C9vette)',
    frenchName: 'Gare Maritime de Sainte-\u00C9vette (Audierne)',
    latitude: 48.0167,
    longitude: -4.5417,
    type: 'Mainland Hub',
    berthCount: 2,
    description: 'Southern mainland terminal nestled in Esquibien bay, servicing daily voyages across the Raz de Sein.',
    facilities: ['Passenger Terminal', 'Day Parking', 'Ticket Counter', 'Luggage Check'],
    connectingRoutes: ['Audierne \u2192 \u00CEle de Sein'],
  },
  {
    id: 'SEI',
    code: 'SEI',
    name: '\u00CEle de Sein',
    frenchName: 'Port de l\'\u00CEle de Sein',
    latitude: 48.0375,
    longitude: -4.8500,
    type: 'Island Terminal',
    berthCount: 1,
    description: 'Low-profile island quay vulnerable to south-westerly swell, home port of the stalwart Enez Sun 3.',
    facilities: ['Passenger Shelter', 'Freight Lift', 'Wheelchair Assistance'],
    connectingRoutes: ['\u00CEle de Sein \u2192 Audierne'],
  },
  {
    id: 'CAM',
    code: 'CAM',
    name: 'Camaret-sur-Mer',
    frenchName: 'Port de Camaret-sur-Mer',
    latitude: 48.2778,
    longitude: -4.5956,
    type: 'Seasonal Terminal',
    berthCount: 1,
    description: 'Seasonal hub on the Crozon peninsula operating during summer tourist peak seasons.',
    facilities: ['Seasonal Ticket Booth', 'Marina Facilities', 'Tour Bus Drop-off'],
    connectingRoutes: ['Camaret \u2192 Ouessant', 'Camaret \u2192 \u00CEle de Sein'],
  },
];

export const PortsPage: React.FC = () => {
  const [search, setSearch] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const navigate = useNavigate();

  const filteredPorts = useMemo(() => {
    return BRITTANY_PORTS.filter((port) => {
      if (selectedType !== 'all' && port.type !== selectedType) {
        return false;
      }
      if (search.trim()) {
        const query = search.toLowerCase();
        return (
          port.name.toLowerCase().includes(query) ||
          port.code.toLowerCase().includes(query) ||
          port.frenchName.toLowerCase().includes(query) ||
          port.description.toLowerCase().includes(query)
        );
      }
      return true;
    });
  }, [search, selectedType]);

  return (
    <div className="container" style={{ padding: '2rem 1rem' }}>
      {/* Page Heading */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '0.25rem' }}>
          Ports &amp; Maritime Terminals
        </h1>
        <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
          Explore the 7 certified passenger terminals serving the Penn ar Bed Brittany network.
        </p>
      </div>

      {/* Filter / Search Bar */}
      <Card style={{ padding: '1.25rem', marginBottom: '2rem', backgroundColor: '#FFFFFF' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '1rem', alignItems: 'center' }}>
          <Input
            id="ports-search"
            placeholder="Search port by name, code (e.g. BES, LCQ), or island..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ marginBottom: 0 }}
          />
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Button
              variant={selectedType === 'all' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setSelectedType('all')}
            >
              All Ports
            </Button>
            <Button
              variant={selectedType === 'Mainland Hub' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setSelectedType('Mainland Hub')}
            >
              Mainland
            </Button>
            <Button
              variant={selectedType === 'Island Terminal' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setSelectedType('Island Terminal')}
            >
              Islands
            </Button>
          </div>
        </div>
      </Card>

      {/* Ports Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
        {filteredPorts.map((port) => (
          <Card key={port.code} style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-primary)', letterSpacing: '0.05em' }}>
                      {port.code}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
                      &bull; {port.berthCount} {port.berthCount > 1 ? 'berths' : 'berth'}
                    </span>
                  </div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--color-navy)', marginTop: '0.2rem', marginBottom: '0.1rem' }}>
                    {port.name}
                  </h3>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)', fontStyle: 'italic' }}>
                    {port.frenchName}
                  </div>
                </div>
                <Badge variant={port.type === 'Island Terminal' ? 'warning' : 'info'}>
                  {port.type}
                </Badge>
              </div>

              {/* Description */}
              <p style={{ fontSize: '0.875rem', color: 'var(--color-slate-medium)', lineHeight: 1.5, marginBottom: '1.25rem' }}>
                {port.description}
              </p>

              {/* Facilities */}
              <div style={{ marginBottom: '1.25rem' }}>
                <h4 style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-slate-light)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
                  Terminal Facilities
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                  {port.facilities.map((fac) => (
                    <span
                      key={fac}
                      style={{
                        fontSize: '0.75rem',
                        backgroundColor: 'var(--color-bg)',
                        border: '1px solid var(--color-border)',
                        padding: '0.2rem 0.5rem',
                        borderRadius: 'var(--radius-sm)',
                        color: 'var(--color-slate-medium)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                      }}
                    >
                      <CheckCircle2 size={11} style={{ color: 'var(--color-success)' }} />
                      {fac}
                    </span>
                  ))}
                </div>
              </div>

              {/* Connecting Routes */}
              <div style={{ marginBottom: '1.25rem' }}>
                <h4 style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-slate-light)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
                  Corridor Connections
                </h4>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                  {port.connectingRoutes.map((r) => (
                    <li key={r} style={{ fontSize: '0.8125rem', color: 'var(--color-slate-medium)', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                      <Anchor size={12} style={{ color: 'var(--color-primary)' }} />
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Footer with GPS & Action */}
            <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)', display: 'inline-flex', alignItems: 'center', gap: '0.375rem' }}>
                <Navigation size={12} />
                <span>{port.latitude.toFixed(4)}&deg; N, {Math.abs(port.longitude).toFixed(4)}&deg; W</span>
              </div>
              <Button
                variant="secondary"
                size="sm"
                icon={<ArrowRight size={14} />}
                onClick={() => navigate('/timetable')}
              >
                View Sailings
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
