import React, { useState, useEffect } from 'react';
import { ArrowLeftRight, Calendar, Users, MapPin, Search } from 'lucide-react';
import { Button } from '../common/Button';
import { apiClient } from '../../api/client';
import { Port } from '../../types/catalog';

export interface SearchFormData {
  from: string;
  to: string;
  date: string;
  passengers: number;
}

interface SailingSearchFormProps {
  initialFrom?: string;
  initialTo?: string;
  initialDate?: string;
  initialPassengers?: number;
  onSearch: (data: SearchFormData) => void;
  loading?: boolean;
}

export const SailingSearchForm: React.FC<SailingSearchFormProps> = ({
  initialFrom = '',
  initialTo = '',
  initialDate,
  initialPassengers = 1,
  onSearch,
  loading = false,
}) => {
  const todayStr = new Date().toISOString().split('T')[0];

  const [allPorts, setAllPorts] = useState<Port[]>([]);
  const [reachablePorts, setReachablePorts] = useState<Port[]>([]);
  const [from, setFrom] = useState<string>(initialFrom);
  const [to, setTo] = useState<string>(initialTo);
  const [date, setDate] = useState<string>(initialDate || todayStr);
  const [passengers, setPassengers] = useState<number>(initialPassengers);
  const [error, setError] = useState<string | null>(null);

  // Load all ports on mount
  useEffect(() => {
    let isMounted = true;
    apiClient.get<Port[]>('/api/v1/ports')
      .then((data) => {
        if (isMounted && Array.isArray(data)) {
          setAllPorts(data);
          if (!from && data.length > 0) {
            setFrom(data[0].id);
          }
        }
      })
      .catch(() => {
        // Fallback default ports if offline
      });
    return () => { isMounted = false; };
  }, []);

  // When 'from' changes, fetch reachable destinations
  useEffect(() => {
    if (!from) {
      setReachablePorts([]);
      return;
    }

    let isMounted = true;
    apiClient.get<Port[]>(`/api/v1/ports/${encodeURIComponent(from)}/destinations`)
      .then((data) => {
        if (isMounted && Array.isArray(data)) {
          setReachablePorts(data);
          // If current 'to' is not among reachable ports, reset or pick first
          const stillValid = data.some((p) => p.id === to);
          if (!stillValid) {
            setTo(data.length > 0 ? data[0].id : '');
          }
        }
      })
      .catch(() => {
        if (isMounted) setReachablePorts([]);
      });

    return () => { isMounted = false; };
  }, [from]);

  const handleSwap = () => {
    if (!to) return;
    const oldFrom = from;
    const oldTo = to;
    setFrom(oldTo);
    setTo(oldFrom);
    setError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!from || !to) {
      setError('Please select both origin and destination ports.');
      return;
    }
    if (from.toLowerCase() === to.toLowerCase()) {
      setError('Origin and destination ports cannot be the same.');
      return;
    }
    if (passengers < 1 || passengers > 10) {
      setError('Number of passengers must be between 1 and 10.');
      return;
    }
    if (date < todayStr) {
      setError('Cannot search departures in the past.');
      return;
    }

    onSearch({ from, to, date, passengers });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="sailing-search-form"
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '8px',
        border: '1px solid var(--color-slate-dark)',
        padding: '1.25rem',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
      }}
    >
      {error && (
        <div
          role="alert"
          style={{
            marginBottom: '1rem',
            padding: '0.625rem 0.875rem',
            backgroundColor: '#FEF2F2',
            border: '1px solid #F87171',
            borderRadius: '6px',
            color: '#991B1B',
            fontSize: '0.875rem',
          }}
        >
          {error}
        </div>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '1rem',
          alignItems: 'flex-end',
        }}
      >
        {/* Origin Port */}
        <div>
          <label
            htmlFor="search-from-port"
            style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-slate-light)', marginBottom: '0.375rem' }}
          >
            From
          </label>
          <div style={{ position: 'relative' }}>
            <select
              id="search-from-port"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="form-control"
              style={{
                width: '100%',
                padding: '0.625rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid var(--color-slate-dark)',
                backgroundColor: '#FFFFFF',
                color: 'var(--color-navy)',
                fontSize: '0.875rem',
                fontWeight: 500,
              }}
            >
              {allPorts.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Swap Button */}
        <div style={{ display: 'flex', justifyContent: 'center', paddingBottom: '0.375rem' }}>
          <button
            type="button"
            id="search-swap-ports-btn"
            onClick={handleSwap}
            disabled={!to}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.375rem',
              background: 'transparent',
              border: '1px solid var(--color-slate-dark)',
              borderRadius: '6px',
              padding: '0.5rem 0.75rem',
              color: 'var(--color-teal)',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: to ? 'pointer' : 'not-allowed',
              opacity: to ? 1 : 0.5,
            }}
          >
            <ArrowLeftRight size={14} />
            <span>Swap</span>
          </button>
        </div>

        {/* Destination Port */}
        <div>
          <label
            htmlFor="search-to-port"
            style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-slate-light)', marginBottom: '0.375rem' }}
          >
            To
          </label>
          <select
            id="search-to-port"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            disabled={reachablePorts.length === 0}
            className="form-control"
            style={{
              width: '100%',
              padding: '0.625rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid var(--color-slate-dark)',
              backgroundColor: reachablePorts.length === 0 ? '#F1F5F9' : '#FFFFFF',
              color: 'var(--color-navy)',
              fontSize: '0.875rem',
              fontWeight: 500,
            }}
          >
            {reachablePorts.length === 0 ? (
              <option value="">No direct destinations</option>
            ) : (
              reachablePorts.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))
            )}
          </select>
        </div>

        {/* Date */}
        <div>
          <label
            htmlFor="search-date"
            style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-slate-light)', marginBottom: '0.375rem' }}
          >
            Date
          </label>
          <input
            type="date"
            id="search-date"
            value={date}
            min={todayStr}
            onChange={(e) => setDate(e.target.value)}
            style={{
              width: '100%',
              padding: '0.625rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid var(--color-slate-dark)',
              backgroundColor: '#FFFFFF',
              color: 'var(--color-navy)',
              fontSize: '0.875rem',
              fontVariantNumeric: 'tabular-nums',
            }}
          />
        </div>

        {/* Passengers */}
        <div>
          <label
            htmlFor="search-passengers"
            style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-slate-light)', marginBottom: '0.375rem' }}
          >
            Passengers
          </label>
          <select
            id="search-passengers"
            value={passengers}
            onChange={(e) => setPassengers(Number(e.target.value))}
            style={{
              width: '100%',
              padding: '0.625rem 0.75rem',
              borderRadius: '6px',
              border: '1px solid var(--color-slate-dark)',
              backgroundColor: '#FFFFFF',
              color: 'var(--color-navy)',
              fontSize: '0.875rem',
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
              <option key={num} value={num}>
                {num} {num === 1 ? 'Passenger' : 'Passengers'}
              </option>
            ))}
          </select>
        </div>

        {/* Submit Primary Button */}
        <div>
          <Button
            type="submit"
            variant="primary"
            disabled={loading || !from || !to}
            icon={<Search size={16} />}
            style={{ width: '100%', padding: '0.625rem 1rem' }}
          >
            {loading ? 'Searching...' : 'Search sailings'}
          </Button>
        </div>
      </div>
    </form>
  );
};
