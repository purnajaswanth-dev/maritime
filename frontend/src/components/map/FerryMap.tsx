import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { LiveTelemetry } from '../../types/tracking';

export interface PortLocation {
  code: string;
  name: string;
  lat: number;
  lon: number;
}

export const PENN_AR_BED_PORTS: PortLocation[] = [
  { code: 'BES', name: 'Brest Port de Commerce', lat: 48.3831, lon: -4.4842 },
  { code: 'LCQ', name: 'Le Conquet Gare Maritime', lat: 48.3592, lon: -4.7794 },
  { code: 'MOL', name: '\u00CEle-Mol\u00E8ne (Quai Nord)', lat: 48.3972, lon: -4.9531 },
  { code: 'OUE', name: 'Ouessant (Port du Stiff)', lat: 48.4756, lon: -5.0567 },
  { code: 'AUD', name: 'Audierne (Sainte-\u00C9vette)', lat: 48.0167, lon: -4.5417 },
  { code: 'SEI', name: '\u00CEle de Sein', lat: 48.0375, lon: -4.8500 },
  { code: 'CAM', name: 'Camaret-sur-Mer', lat: 48.2778, lon: -4.5956 },
];

export interface FerryMapProps {
  telemetry?: LiveTelemetry | null;
  trackCoordinates?: [number, number][];
  className?: string;
  height?: string | number;
}

export const FerryMap: React.FC<FerryMapProps> = ({
  telemetry,
  trackCoordinates = [],
  className = '',
  height = '500px',
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const vesselMarkerRef = useRef<L.Marker | null>(null);
  const trackPolylineRef = useRef<L.Polyline | null>(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    // Check if running in headless test environment without full DOM metrics
    if (typeof window === 'undefined' || !mapContainerRef.current.getBoundingClientRect) {
      return;
    }

    try {
      // Center between Brest, Le Conquet, Ouessant, and Sein
      const map = L.map(mapContainerRef.current, {
        center: [48.35, -4.75],
        zoom: 10,
        minZoom: 8,
        maxZoom: 16,
      });

      // CartoDB Positron / OSM Maritime clean base tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(map);

      // Add Penn ar Bed port markers
      PENN_AR_BED_PORTS.forEach((port) => {
        const portIcon = L.divIcon({
          className: 'port-map-marker',
          html: `
            <div style="display:flex;align-items:center;justify-content:center;width:22px;height:22px;background:#0F172A;color:#FFFFFF;border-radius:50%;border:2px solid #FFFFFF;box-shadow:0 2px 4px rgba(0,0,0,0.3);font-size:10px;font-weight:700;">
              ${port.code.substring(0, 2)}
            </div>
          `,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });

        const marker = L.marker([port.lat, port.lon], { icon: portIcon }).addTo(map);
        marker.bindPopup(`
          <div style="font-family:sans-serif;padding:4px;">
            <strong style="color:#0F172A;font-size:13px;">${port.name}</strong><br/>
            <span style="font-size:11px;color:#64748B;">Code: ${port.code}</span><br/>
            <span style="font-size:11px;color:#64748B;">${port.lat.toFixed(4)}\u00B0 N, ${Math.abs(port.lon).toFixed(4)}\u00B0 W</span>
          </div>
        `);
      });

      mapInstanceRef.current = map;
    } catch {
      // Graceful fallback for test environments
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update Track Polyline
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (trackPolylineRef.current) {
      trackPolylineRef.current.remove();
      trackPolylineRef.current = null;
    }

    if (trackCoordinates && trackCoordinates.length > 0) {
      try {
        const polyline = L.polyline(trackCoordinates, {
          color: '#0284C7',
          weight: 3,
          opacity: 0.8,
          dashArray: '6, 6',
        }).addTo(map);
        trackPolylineRef.current = polyline;
      } catch {
        // Fallback
      }
    }
  }, [trackCoordinates]);

  // Update Vessel Marker & Heading
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !telemetry) return;

    const { latitude, longitude, headingDegrees = 0, speedKnots = 0, vesselName } = telemetry;
    if (latitude == null || longitude == null) return;

    try {
      const vesselIcon = L.divIcon({
        className: 'vessel-live-marker',
        html: `
          <div style="position:relative;width:40px;height:40px;display:flex;align-items:center;justify-content:center;">
            <div style="position:absolute;width:34px;height:34px;border-radius:50%;background:rgba(20, 184, 166, 0.25);animation:pulse 2s infinite;"></div>
            <div style="transform:rotate(${headingDegrees}deg);transition:transform 0.5s ease-out;width:28px;height:28px;background:#14B8A6;color:#FFFFFF;border-radius:50%;border:2px solid #FFFFFF;box-shadow:0 2px 6px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 19 21 12 17 5 21 12 2"></polygon>
              </svg>
            </div>
          </div>
        `,
        iconSize: [40, 40],
        iconAnchor: [20, 20],
      });

      if (!vesselMarkerRef.current) {
        const marker = L.marker([latitude, longitude], { icon: vesselIcon, zIndexOffset: 1000 }).addTo(map);
        marker.bindPopup(`
          <div style="font-family:sans-serif;padding:6px;">
            <strong style="color:#0F172A;font-size:14px;">${vesselName}</strong><br/>
            <span style="font-size:12px;color:#0284C7;font-weight:600;">Speed: ${speedKnots.toFixed(1)} kts</span><br/>
            <span style="font-size:11px;color:#64748B;">Heading: ${Math.round(headingDegrees)}\u00B0</span>
          </div>
        `);
        vesselMarkerRef.current = marker;
      } else {
        vesselMarkerRef.current.setLatLng([latitude, longitude]);
        vesselMarkerRef.current.setIcon(vesselIcon);
      }
    } catch {
      // Fallback
    }
  }, [telemetry]);

  return (
    <div
      className={`ferry-map-wrapper ${className}`.trim()}
      style={{
        position: 'relative',
        width: '100%',
        height,
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        border: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-md)',
      }}
      data-testid="ferry-map-container"
    >
      <div
        ref={mapContainerRef}
        style={{ width: '100%', height: '100%' }}
        aria-label="Interactive Brittany and Iroise Sea maritime map"
      />
      {/* Honesty badge overlay */}
      <div
        style={{
          position: 'absolute',
          bottom: '12px',
          left: '12px',
          zIndex: 1000,
          backgroundColor: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(4px)',
          color: '#FFFFFF',
          padding: '4px 10px',
          borderRadius: 'var(--radius-full)',
          fontSize: '11px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          pointerEvents: 'none',
        }}
      >
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: 'var(--color-primary)',
          }}
        />
        Historical replay mode (simulated live)
      </div>
    </div>
  );
};
