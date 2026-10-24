import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Compass, Ship, Clock, ShieldCheck, MapPin, Radio, ArrowRight } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const corridors = [
    {
      id: 'brest-ouessant',
      name: 'Brest / Le Conquet \u2194 Mol\u00E8ne \u2194 Ouessant',
      description: 'Main corridor through the Passage du Fromveur with Fromveur II and Enez Eussa 3.',
      ports: ['Brest', 'Le Conquet', '\u00CEle-Mol\u00E8ne', 'Ouessant (Stiff)'],
      frequency: 'Multiple daily crossings',
    },
    {
      id: 'audierne-sein',
      name: 'Audierne (Sainte-\u00C9vette) \u2194 \u00CEle de Sein',
      description: 'Southern corridor crossing the Raz de Sein with Enez Sun 3.',
      ports: ['Audierne (Sainte-\u00C9vette)', '\u00CEle de Sein'],
      frequency: 'Daily scheduled departures',
    },
  ];

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero-section" style={{
        backgroundColor: 'var(--color-navy)',
        color: '#FFFFFF',
        padding: '3.5rem 1rem',
        borderBottom: '1px solid var(--color-slate-dark)',
      }}>
        <div className="container" style={{ maxWidth: '1000px', margin: '0 auto', textAlign: 'center' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
            <div className="honesty-badge-pill" role="status">
              <Radio size={14} className="pulse-icon" aria-hidden="true" />
              <span>Historical replay mode (simulated live)</span>
            </div>
          </div>

          <h1 style={{
            fontSize: 'clamp(2rem, 5vw, 3.25rem)',
            fontWeight: 800,
            letterSpacing: '-0.03em',
            lineHeight: 1.15,
            marginBottom: '1.25rem',
          }}>
            Real-Time Brittany &amp; Iroise Sea Ferry Tracking
          </h1>

          <p style={{
            fontSize: '1.125rem',
            color: '#94A3B8',
            maxWidth: '680px',
            margin: '0 auto 2rem auto',
            lineHeight: 1.6,
          }}>
            Track Penn ar Bed vessels live between Brest, Le Conquet, Molène, Ouessant, Audierne, and Île de Sein.
            Powered by high-precision physics replay and ML arrival predictions.
          </p>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="primary"
              size="lg"
              icon={<Compass size={18} />}
              onClick={() => navigate('/tracking')}
            >
              Live Fleet Map
            </Button>
            <Button
              variant="secondary"
              size="lg"
              icon={<Clock size={18} />}
              onClick={() => navigate('/timetable')}
              style={{ color: '#FFFFFF', borderColor: '#475569' }}
            >
              View Timetables
            </Button>
          </div>
        </div>
      </section>

      {/* Corridor Cards Section */}
      <section style={{ padding: '3.5rem 1rem' }}>
        <div className="container" style={{ maxWidth: '1100px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
            <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-navy)', marginBottom: '0.5rem' }}>
              Maritime Corridors
            </h2>
            <p style={{ color: 'var(--color-slate-light)', fontSize: '0.9375rem' }}>
              Official ferry links connecting the Finistère mainland with the Ponant islands.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            {corridors.map((c) => (
              <Card key={c.id} style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <Badge variant="info">Penn ar Bed</Badge>
                    <span style={{ fontSize: '0.8125rem', color: 'var(--color-slate-light)' }}>{c.frequency}</span>
                  </div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--color-navy)', marginBottom: '0.5rem' }}>
                    {c.name}
                  </h3>
                  <p style={{ fontSize: '0.875rem', color: 'var(--color-slate-medium)', marginBottom: '1rem', lineHeight: 1.5 }}>
                    {c.description}
                  </p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem', marginBottom: '1.25rem' }}>
                    {c.ports.map((p) => (
                      <span
                        key={p}
                        style={{
                          fontSize: '0.75rem',
                          backgroundColor: 'var(--color-bg)',
                          border: '1px solid var(--color-border)',
                          padding: '0.2rem 0.5rem',
                          borderRadius: 'var(--radius-sm)',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem',
                        }}
                      >
                        <MapPin size={10} aria-hidden="true" />
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
                <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
                  <Link
                    to="/timetable"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      fontWeight: 600,
                      fontSize: '0.875rem',
                    }}
                  >
                    Check corridor departures <ArrowRight size={14} aria-hidden="true" />
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Fleet & Accuracy Disclosure Section */}
      <section style={{ backgroundColor: '#F1F5F9', padding: '3rem 1rem', borderTop: '1px solid var(--color-border)' }}>
        <div className="container" style={{ maxWidth: '1000px', margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '2rem' }}>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <div style={{
                backgroundColor: 'var(--color-primary-light)',
                color: 'var(--color-primary)',
                padding: '0.75rem',
                borderRadius: 'var(--radius-md)',
                height: 'fit-content',
              }}>
                <Ship size={24} aria-hidden="true" />
              </div>
              <div>
                <h4 style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '0.25rem' }}>Penn ar Bed Fleet</h4>
                <p style={{ fontSize: '0.875rem', color: 'var(--color-slate-medium)', lineHeight: 1.5 }}>
                  Active tracking for Fromveur II (350 pax), Enez Eussa 3 (302 pax), and Enez Sun 3 (250 pax).
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <div style={{
                backgroundColor: 'var(--color-secondary-light)',
                color: 'var(--color-secondary)',
                padding: '0.75rem',
                borderRadius: 'var(--radius-md)',
                height: 'fit-content',
              }}>
                <Compass size={24} aria-hidden="true" />
              </div>
              <div>
                <h4 style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '0.25rem' }}>Physics &amp; Tides</h4>
                <p style={{ fontSize: '0.875rem', color: 'var(--color-slate-medium)', lineHeight: 1.5 }}>
                  High tidal currents (up to 9 knots in Fromveur) simulated with Shom marine data alignment.
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <div style={{
                backgroundColor: 'var(--color-success-light)',
                color: 'var(--color-success)',
                padding: '0.75rem',
                borderRadius: 'var(--radius-md)',
                height: 'fit-content',
              }}>
                <ShieldCheck size={24} aria-hidden="true" />
              </div>
              <div>
                <h4 style={{ fontWeight: 600, fontSize: '1rem', marginBottom: '0.25rem' }}>Predictive ML</h4>
                <p style={{ fontSize: '0.875rem', color: 'var(--color-slate-medium)', lineHeight: 1.5 }}>
                  Machine learning model estimating delay minutes and ETA updated in real time via SSE.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
