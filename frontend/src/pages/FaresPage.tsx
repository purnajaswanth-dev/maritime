import React, { useState, useMemo } from 'react';
import {
  Tag,
  Users,
  Check,
  Calculator,
  ShieldCheck,
  Info,
  Bike,
  Baby,
  UserCheck,
  HelpCircle,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { Select } from '../components/common/Select';

interface FareStructure {
  routeCode: string;
  routeName: string;
  adult: number;
  resident: number;
  child: number;
  infant: number;
  bike: number;
}

const FARE_RATES: Record<string, FareStructure> = {
  'BES-OUE': {
    routeCode: 'BES-OUE',
    routeName: 'Brest \u2192 Ouessant (Port du Stiff)',
    adult: 42.0,
    resident: 16.5,
    child: 24.0,
    infant: 0.0,
    bike: 10.0,
  },
  'LCQ-OUE': {
    routeCode: 'LCQ-OUE',
    routeName: 'Le Conquet \u2192 Ouessant (Port du Stiff)',
    adult: 36.0,
    resident: 14.5,
    child: 21.0,
    infant: 0.0,
    bike: 8.5,
  },
  'LCQ-MOL': {
    routeCode: 'LCQ-MOL',
    routeName: 'Le Conquet \u2192 \u00CEle-Mol\u00E8ne',
    adult: 30.0,
    resident: 12.0,
    child: 18.0,
    infant: 0.0,
    bike: 7.0,
  },
  'AUD-SEI': {
    routeCode: 'AUD-SEI',
    routeName: 'Audierne (Sainte-\u00C9vette) \u2192 \u00CEle de Sein',
    adult: 34.0,
    resident: 13.5,
    child: 19.5,
    infant: 0.0,
    bike: 8.0,
  },
};

export const FaresPage: React.FC = () => {
  const [selectedRoute, setSelectedRoute] = useState<string>('LCQ-OUE');
  const [adults, setAdults] = useState<number>(1);
  const [residents, setResidents] = useState<number>(0);
  const [children, setChildren] = useState<number>(0);
  const [infants, setInfants] = useState<number>(0);
  const [bikes, setBikes] = useState<number>(0);

  const currentRate = FARE_RATES[selectedRoute] || FARE_RATES['LCQ-OUE'];

  const calculation = useMemo(() => {
    const adultTotal = adults * currentRate.adult;
    const residentTotal = residents * currentRate.resident;
    const childTotal = children * currentRate.child;
    const infantTotal = infants * currentRate.infant;
    const bikeTotal = bikes * currentRate.bike;

    const total = adultTotal + residentTotal + childTotal + infantTotal + bikeTotal;
    const totalPassengers = adults + residents + children + infants;

    return {
      adultTotal,
      residentTotal,
      childTotal,
      infantTotal,
      bikeTotal,
      total,
      totalPassengers,
    };
  }, [adults, residents, children, infants, bikes, currentRate]);

  const routeSelectOptions = [
    { label: 'Le Conquet \u2192 Ouessant (Port du Stiff)', value: 'LCQ-OUE' },
    { label: 'Brest \u2192 Ouessant (Port du Stiff)', value: 'BES-OUE' },
    { label: 'Le Conquet \u2192 \u00CEle-Mol\u00E8ne', value: 'LCQ-MOL' },
    { label: 'Audierne \u2192 \u00CEle de Sein', value: 'AUD-SEI' },
  ];

  return (
    <div className="container" style={{ padding: '2rem 1rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '0.25rem' }}>
          Fares &amp; Pricing Calculator
        </h1>
        <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem' }}>
          Official public passenger tariffs and subsidized resident fares for Brittany island ferry services.
        </p>
      </div>

      {/* Main Grid: Calculator (Left) + Tariff Cards (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.3fr) minmax(320px, 1fr)', gap: '2rem', alignItems: 'start' }}>
        {/* Interactive Fare Calculator */}
        <Card style={{ padding: '1.75rem', backgroundColor: '#FFFFFF' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.75rem' }}>
            <Calculator size={20} style={{ color: 'var(--color-primary)' }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-navy)', margin: 0 }}>
              Live Fare Estimator
            </h2>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <Select
              id="calc-route"
              label="Selected Crossing Route"
              options={routeSelectOptions}
              value={selectedRoute}
              onChange={(e) => setSelectedRoute(e.target.value)}
            />
          </div>

          {/* Passenger Counters */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
            {/* Adult Standard */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--color-bg)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--color-navy)' }}>
                  Adult Standard
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
                  &euro;{currentRate.adult.toFixed(2)} per person
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Button variant="secondary" size="sm" onClick={() => setAdults(Math.max(0, adults - 1))} aria-label="Decrease adult count">
                  -
                </Button>
                <span style={{ minWidth: '24px', textAlign: 'center', fontWeight: 700 }}>{adults}</span>
                <Button variant="secondary" size="sm" onClick={() => setAdults(adults + 1)} aria-label="Increase adult count">
                  +
                </Button>
              </div>
            </div>

            {/* Island Resident */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--color-bg)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--color-navy)' }}>
                    Island Resident
                  </span>
                  <Badge variant="warning">Subsidized</Badge>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
                  &euro;{currentRate.resident.toFixed(2)} with valid island card
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Button variant="secondary" size="sm" onClick={() => setResidents(Math.max(0, residents - 1))} aria-label="Decrease resident count">
                  -
                </Button>
                <span style={{ minWidth: '24px', textAlign: 'center', fontWeight: 700 }}>{residents}</span>
                <Button variant="secondary" size="sm" onClick={() => setResidents(residents + 1)} aria-label="Increase resident count">
                  +
                </Button>
              </div>
            </div>

            {/* Child (4-18) */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--color-bg)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--color-navy)' }}>
                  Child / Youth (4-18)
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
                  &euro;{currentRate.child.toFixed(2)} per child
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Button variant="secondary" size="sm" onClick={() => setChildren(Math.max(0, children - 1))} aria-label="Decrease child count">
                  -
                </Button>
                <span style={{ minWidth: '24px', textAlign: 'center', fontWeight: 700 }}>{children}</span>
                <Button variant="secondary" size="sm" onClick={() => setChildren(children + 1)} aria-label="Increase child count">
                  +
                </Button>
              </div>
            </div>

            {/* Bicycle */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'var(--color-bg)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--color-navy)' }}>
                  Bicycle / E-Bike
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
                  &euro;{currentRate.bike.toFixed(2)} cargo slot
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Button variant="secondary" size="sm" onClick={() => setBikes(Math.max(0, bikes - 1))} aria-label="Decrease bike count">
                  -
                </Button>
                <span style={{ minWidth: '24px', textAlign: 'center', fontWeight: 700 }}>{bikes}</span>
                <Button variant="secondary" size="sm" onClick={() => setBikes(bikes + 1)} aria-label="Increase bike count">
                  +
                </Button>
              </div>
            </div>
          </div>

          {/* Total Summary */}
          <div style={{ borderTop: '2px solid var(--color-border)', paddingTop: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)' }}>
                Estimated Round-Trip Total ({calculation.totalPassengers} {calculation.totalPassengers === 1 ? 'passenger' : 'passengers'})
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-light)' }}>
                TVA included (10% passenger transport rate)
              </div>
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-navy)' }}>
              &euro;{calculation.total.toFixed(2)}
            </div>
          </div>
        </Card>

        {/* Fare Rules & Passenger Info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <Card style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--color-navy)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShieldCheck size={18} style={{ color: 'var(--color-primary)' }} />
              Passenger Tariff Rules
            </h3>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.625rem', fontSize: '0.8125rem', color: 'var(--color-slate-medium)' }}>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                <Check size={14} style={{ color: 'var(--color-success)', marginTop: '2px', flexShrink: 0 }} />
                <span><strong>Luggage:</strong> 1 piece of checked luggage (up to 20 kg) and 1 small carry-on bag included per passenger ticket.</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                <Check size={14} style={{ color: 'var(--color-success)', marginTop: '2px', flexShrink: 0 }} />
                <span><strong>Infants under 4:</strong> Travel free of charge when accompanied by a ticketed adult passenger.</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                <Check size={14} style={{ color: 'var(--color-success)', marginTop: '2px', flexShrink: 0 }} />
                <span><strong>Resident Card:</strong> Valid <em>Carte Insulaire</em> issued by the municipality must be shown at boarding.</span>
              </li>
              <li style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                <Check size={14} style={{ color: 'var(--color-success)', marginTop: '2px', flexShrink: 0 }} />
                <span><strong>Weather Guarantee:</strong> Full refund or rebooking to next sailing if service is cancelled due to heavy sea conditions.</span>
              </li>
            </ul>
          </Card>

          <Card style={{ padding: '1.25rem', backgroundColor: '#F8FAFC', border: '1px dashed var(--color-border-hover)' }}>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <Info size={18} style={{ color: 'var(--color-secondary)', flexShrink: 0, marginTop: '2px' }} />
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-slate-medium)', lineHeight: 1.5 }}>
                Online booking automatically issues certified tickets with QR codes and SMS boarding updates.
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
