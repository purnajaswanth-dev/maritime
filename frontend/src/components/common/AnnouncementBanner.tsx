import React, { useEffect, useState } from 'react';
import { AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import { apiClient } from '../../api/client';

export interface Announcement {
  id: number;
  title: string;
  body: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | string;
  scope: 'ALL' | 'PORT' | 'ROUTE' | 'DEPARTURE' | string;
  targetId?: string;
  startsAt: string;
  endsAt?: string;
}

interface AnnouncementBannerProps {
  scope?: string;
  targetId?: string;
}

export const AnnouncementBanner: React.FC<AnnouncementBannerProps> = ({ scope, targetId }) => {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [dismissedIds, setDismissedIds] = useState<number[]>([]);

  useEffect(() => {
    let isMounted = true;
    const fetchAnnouncements = async () => {
      try {
        let url = '/api/v1/announcements';
        const params: string[] = [];
        if (scope) params.push(`scope=${encodeURIComponent(scope)}`);
        if (targetId) params.push(`targetId=${encodeURIComponent(targetId)}`);
        if (params.length > 0) {
          url += `?${params.join('&')}`;
        }
        const data = await apiClient.get<Announcement[]>(url);
        if (isMounted && Array.isArray(data)) {
          setAnnouncements(data);
        }
      } catch (err) {
        // Silently ignore if offline or empty
      }
    };

    fetchAnnouncements();
    return () => { isMounted = false; };
  }, [scope, targetId]);

  const visible = announcements.filter((a) => !dismissedIds.includes(a.id));

  if (visible.length === 0) {
    return null;
  }

  return (
    <div className="announcements-container" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.25rem' }}>
      {visible.map((ann) => {
        const severity = ann.severity?.toUpperCase() || 'INFO';
        const isCritical = severity === 'CRITICAL';
        const isWarning = severity === 'WARNING';

        const bg = isCritical ? '#FEF2F2' : isWarning ? '#FFFBEB' : '#F0F9FF';
        const border = isCritical ? '#F87171' : isWarning ? '#FBBF24' : '#38BDF8';
        const color = isCritical ? '#991B1B' : isWarning ? '#92400E' : '#0369A1';

        const Icon = isCritical ? AlertCircle : isWarning ? AlertTriangle : Info;

        return (
          <div
            key={ann.id}
            role="alert"
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              padding: '0.75rem 1rem',
              backgroundColor: bg,
              border: `1px solid ${border}`,
              borderRadius: '8px',
              color: color,
            }}
          >
            <Icon size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div style={{ flex: 1, fontSize: '0.875rem' }}>
              <div style={{ fontWeight: 600, marginBottom: '0.125rem' }}>{ann.title}</div>
              <div>{ann.body}</div>
            </div>
            <button
              onClick={() => setDismissedIds((prev) => [...prev, ann.id])}
              style={{
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                color: 'inherit',
                opacity: 0.7,
                padding: '2px',
              }}
              aria-label="Dismiss announcement"
            >
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
};
