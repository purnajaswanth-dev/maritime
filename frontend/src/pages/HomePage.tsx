import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Compass, Ship, Clock, Radio, ArrowRight } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { AnnouncementBanner } from '../components/common/AnnouncementBanner';
import { SailingSearchForm, SearchFormData } from '../components/search/SailingSearchForm';
import { SailingSearchResults, SearchResultData } from '../components/search/SailingSearchResults';
import { apiClient } from '../api/client';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const [searchData, setSearchData] = useState<SearchResultData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [lastSearchParams, setLastSearchParams] = useState<SearchFormData | null>(null);

  const handleSearch = async (params: SearchFormData) => {
    setLoading(true);
    setSearchError(null);
    setLastSearchParams(params);

    try {
      const url = `/api/v1/departures/search?from=${encodeURIComponent(params.from)}&to=${encodeURIComponent(params.to)}&date=${encodeURIComponent(params.date)}&passengers=${params.passengers}`;
      const data = await apiClient.get<SearchResultData>(url);
      setSearchData(data);
    } catch (err: any) {
      setSearchError(err?.message || 'Failed to search sailings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

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
        padding: '3.5rem 1rem 4rem 1rem',
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
            Track Penn ar Bed vessels live between Brest, Le Conquet, Mol&egrave;ne, Ouessant, Audierne, and &Icirc;le de Sein.
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

      {/* From-To Search Form Section */}
      <section style={{ transform: 'translateY(-2rem)', padding: '0 1rem', position: 'relative', zIndex: 10 }}>
        <div className="container" style={{ maxWidth: '1000px', margin: '0 auto' }}>
          <AnnouncementBanner scope="ALL" />
          <SailingSearchForm
            onSearch={handleSearch}
            loading={loading}
          />
          <SailingSearchResults
            data={searchData}
            loading={loading}
            error={searchError}
            onSelectDate={(newDate) => {
              if (lastSearchParams) {
                handleSearch({ ...lastSearchParams, date: newDate });
              }
            }}
            onRetry={() => {
              if (lastSearchParams) {
                handleSearch(lastSearchParams);
              }
            }}
          />
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
              Official ferry links connecting the Finist&egrave;re mainland with the Ponant islands.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            {corridors.map((corridor) => (
              <Card key={corridor.id} className="corridor-card">
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Ship size={20} color="var(--color-teal)" />
                    <h3 style={{ fontSize: '1.0625rem', fontWeight: 700, color: 'var(--color-navy)', margin: 0 }}>
                      {corridor.name}
                    </h3>
                  </div>
                  <Badge variant="info">{corridor.frequency}</Badge>
                </div>

                <p style={{ color: 'var(--color-slate-light)', fontSize: '0.875rem', marginBottom: '1.25rem', lineHeight: 1.5 }}>
                  {corridor.description}
                </p>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem', marginBottom: '1.5rem' }}>
                  {corridor.ports.map((port) => (
                    <span
                      key={port}
                      style={{
                        fontSize: '0.75rem',
                        padding: '0.25rem 0.5rem',
                        backgroundColor: '#F1F5F9',
                        borderRadius: '4px',
                        color: 'var(--color-navy)',
                        fontWeight: 500,
                      }}
                    >
                      {port}
                    </span>
                  ))}
                </div>

                <Button
                  variant="secondary"
                  size="sm"
                  icon={<ArrowRight size={14} />}
                  onClick={() => navigate('/timetable')}
                  style={{ width: '100%' }}
                >
                  View Corridor Timetable
                </Button>
              </Card>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};
