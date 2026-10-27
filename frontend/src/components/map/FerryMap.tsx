import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { LiveTelemetry } from '../../types/tracking';
import {
  TileTierConfig,
  TileErrorTracker,
  getTileTiers,
  OFFLINE_VECTOR_CONFIG,
} from '../../map/tileProviders';
import { apiClient } from '../../api/client';

// Fix Leaflet default marker icon paths in Vite bundler
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
});

export interface PortLocation {
  code: string;
  name: string;
  lat: number;
  lon: number;
  berthRadiusM: number;
}

export const PENN_AR_BED_PORTS: PortLocation[] = [
  { code: 'BES', name: 'Brest Port de Commerce', lat: 48.3831, lon: -4.4842, berthRadiusM: 800 },
  { code: 'LCQ', name: 'Le Conquet Gare Maritime', lat: 48.3592, lon: -4.7794, berthRadiusM: 400 },
  { code: 'MOL', name: 'Île-Molène (Quai Nord)', lat: 48.3972, lon: -4.9531, berthRadiusM: 400 },
  { code: 'OUE', name: 'Ouessant (Port du Stiff)', lat: 48.4756, lon: -5.0567, berthRadiusM: 500 },
  { code: 'AUD', name: 'Audierne (Sainte-Évette)', lat: 48.0167, lon: -4.5417, berthRadiusM: 500 },
  { code: 'SEI', name: 'Île de Sein', lat: 48.0375, lon: -4.85, berthRadiusM: 350 },
  { code: 'CAM', name: 'Camaret-sur-Mer', lat: 48.2778, lon: -4.5956, berthRadiusM: 450 },
];

export interface RouteGeometry {
  id: string;
  name: string;
  origin_terminal_id: string;
  destination_terminal_id: string;
  polyline: [number, number][];
  length_km?: number;
  great_circle_km?: number;
}

export const CORRIDOR_TRACKS: [string, [number, number], [number, number]][] = [
  ['Brest — Le Conquet', [48.3831, -4.4842], [48.3592, -4.7794]],
  ['Le Conquet — Molène', [48.3592, -4.7794], [48.3972, -4.9531]],
  ['Molène — Ouessant', [48.3972, -4.9531], [48.4756, -5.0567]],
  ['Brest — Ouessant Direct', [48.3831, -4.4842], [48.4756, -5.0567]],
  ['Audierne — Île de Sein', [48.0167, -4.5417], [48.0375, -4.85]],
  ['Camaret — Brest', [48.2778, -4.5956], [48.3831, -4.4842]],
];

export interface FerryMapProps {
  telemetry?: LiveTelemetry | null;
  trackCoordinates?: [number, number][];
  className?: string;
  height?: string | number;
  connectionStatus?: 'Live' | 'Reconnecting' | 'Stale';
}

function getLifecycleColor(state?: string): string {
  switch (state?.toUpperCase()) {
    case 'UNDERWAY':
    case 'IN_TRANSIT':
    case 'ESTIMATING':
      return '#14B8A6'; // Electric Teal
    case 'BOARDING':
      return '#F59E0B'; // Amber
    case 'ARRIVED':
    case 'DWELLING':
    case 'BERTHED':
      return '#3B82F6'; // Ocean Blue
    case 'DELAYED':
      return '#EF4444'; // Red
    default:
      return '#64748B'; // Slate
  }
}

export const FerryMap: React.FC<FerryMapProps> = ({
  telemetry,
  trackCoordinates = [],
  className = '',
  height = '520px',
  connectionStatus = 'Live',
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const currentTileLayerRef = useRef<L.TileLayer | L.GeoJSON | null>(null);
  const vesselMarkerRef = useRef<L.Marker | null>(null);
  const trackPolylineRef = useRef<L.Polyline | null>(null);
  const corridorPolylinesRef = useRef<L.Polyline[]>([]);
  const breadcrumbRef = useRef<L.Polyline | null>(null);
  const breadcrumbCoords = useRef<[number, number][]>([]);

  const [activeTier, setActiveTier] = useState<TileTierConfig>(() => getTileTiers()[0]);
  const [mapInstance, setMapInstance] = useState<L.Map | null>(null);
  const trackerRef = useRef<TileErrorTracker | null>(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

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

      function switchTileLayer(m: L.Map, tierConfig: TileTierConfig) {
        if (currentTileLayerRef.current) {
          m.removeLayer(currentTileLayerRef.current);
          currentTileLayerRef.current = null;
        }

        if (!tierConfig.isOffline && tierConfig.url) {
          const layer = L.tileLayer(tierConfig.url, {
            attribution: tierConfig.attribution,
            subdomains: tierConfig.subdomains || 'abc',
            maxZoom: tierConfig.maxZoom || 19,
          });

          layer.on('tileerror', () => {
            if (trackerRef.current) {
              trackerRef.current.recordError();
            }
          });

          layer.addTo(m);
          currentTileLayerRef.current = layer;
        } else {
          // Local Offline GeoJSON Vector Layer
          const offlineLayer = L.geoJSON(OFFLINE_VECTOR_CONFIG.geoJson as any, {
            style: {
              color: OFFLINE_VECTOR_CONFIG.landStrokeColor,
              fillColor: OFFLINE_VECTOR_CONFIG.landFillColor,
              weight: 1.5,
              fillOpacity: 0.85,
            },
            attribution: OFFLINE_VECTOR_CONFIG.attribution,
          }).addTo(m);
          currentTileLayerRef.current = offlineLayer;
        }
      }

      const initialTiers = getTileTiers();
      const tracker = new TileErrorTracker(6, 5000, (newTier) => {
        setActiveTier(newTier);
        switchTileLayer(map, newTier);
      });
      trackerRef.current = tracker;

      // Mount initial layer
      switchTileLayer(map, initialTiers[0]);

      // Draw Penn ar Bed port markers with berth radius circles
      PENN_AR_BED_PORTS.forEach((port) => {
        // Berth radius circle
        L.circle([port.lat, port.lon], {
          radius: port.berthRadiusM,
          color: '#14B8A6',
          fillColor: '#14B8A6',
          fillOpacity: 0.12,
          weight: 1,
        }).addTo(map);

        // Terminal div icon
        const portIcon = L.divIcon({
          className: 'port-map-marker',
          html: `
            <div style="display:flex;align-items:center;justify-content:center;width:24px;height:24px;background:#071B2B;color:#F4F8FB;border-radius:50%;border:2px solid #14B8A6;box-shadow:0 2px 6px rgba(0,0,0,0.4);font-size:10px;font-weight:700;">
              ${port.code.substring(0, 2)}
            </div>
          `,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        const marker = L.marker([port.lat, port.lon], { icon: portIcon }).addTo(map);
        marker.bindPopup(`
          <div style="font-family:Inter,sans-serif;padding:4px;color:#071B2B;">
            <strong style="font-size:13px;">${port.name}</strong><br/>
            <span style="font-size:11px;color:#64748B;">Code: ${port.code} • Berth Radius: ${port.berthRadiusM}m</span><br/>
            <span style="font-size:11px;color:#64748B;">${port.lat.toFixed(4)}° N, ${Math.abs(port.lon).toFixed(4)}° W</span>
          </div>
        `);
      });

      mapInstanceRef.current = map;
      setMapInstance(map);
    } catch {
      // Graceful fallback for test environments
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
      setMapInstance(null);
      vesselMarkerRef.current = null;
      breadcrumbRef.current = null;
      trackPolylineRef.current = null;
      corridorPolylinesRef.current.forEach((line) => line.remove());
      corridorPolylinesRef.current = [];
    };
  }, []);

  // Fetch official water corridor polylines from /api/v1/routes/geometry
  useEffect(() => {
    if (!mapInstance) return;

    let isMounted = true;
    apiClient
      .get<RouteGeometry[]>('/routes/geometry')
      .then((routes) => {
        if (!isMounted || !mapInstance) return;
        corridorPolylinesRef.current.forEach((line) => line.remove());
        corridorPolylinesRef.current = [];

        if (Array.isArray(routes)) {
          routes.forEach((route) => {
            if (route.polyline && route.polyline.length > 1) {
              try {
                const poly = L.polyline(route.polyline, {
                  color: '#14B8A6',
                  weight: 1.5,
                  opacity: 0.4,
                  dashArray: '4, 8',
                }).addTo(mapInstance);
                corridorPolylinesRef.current.push(poly);
              } catch {
                // Leaflet polyline safe catch
              }
            }
          });
        }
      })
      .catch(() => {
        // If the request fails, draw NO corridor line (never a straight line over land)
        if (isMounted) {
          corridorPolylinesRef.current.forEach((line) => line.remove());
          corridorPolylinesRef.current = [];
        }
      });

    return () => {
      isMounted = false;
      corridorPolylinesRef.current.forEach((line) => line.remove());
      corridorPolylinesRef.current = [];
    };
  }, [mapInstance]);

  // Update Scheduled Voyage Track Polyline
  useEffect(() => {
    if (!mapInstance) return;

    if (trackPolylineRef.current) {
      trackPolylineRef.current.remove();
      trackPolylineRef.current = null;
    }

    if (trackCoordinates && trackCoordinates.length > 0) {
      try {
        const polyline = L.polyline(trackCoordinates, {
          color: '#0D3045',
          weight: 3,
          opacity: 0.85,
          dashArray: '6, 6',
        }).addTo(mapInstance);
        trackPolylineRef.current = polyline;
      } catch {
        // Ignored in test environment
      }
    }
  }, [mapInstance, trackCoordinates]);

  // Update Vessel Marker, Heading, Breadcrumb & State Color
  useEffect(() => {
    if (!mapInstance || !telemetry) return;

    const {
      latitude,
      longitude,
      headingDegrees = 0,
      speedKnots = 0,
      vesselName,
      state,
    } = telemetry;

    if (latitude == null || longitude == null) return;

    const color = getLifecycleColor(state);
    const speedText = speedKnots ? `${speedKnots.toFixed(1)} kts` : 'At berth';
    const stateLabel = state || 'SCHEDULED';

    // Haversine distance in meters to enforce 300m straight-line interpolation restriction
    const distanceMeters = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
      const R = 6371000;
      const dLat = ((lat2 - lat1) * Math.PI) / 180;
      const dLon = ((lon2 - lon1) * Math.PI) / 180;
      const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos((lat1 * Math.PI) / 180) *
          Math.cos((lat2 * Math.PI) / 180) *
          Math.sin(dLon / 2) *
          Math.sin(dLon / 2);
      return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    };

    // Maintain breadcrumb trail of last 20 coordinates, respecting 300m limit
    const lastCoord = breadcrumbCoords.current[breadcrumbCoords.current.length - 1];
    if (lastCoord) {
      const dist = distanceMeters(lastCoord[0], lastCoord[1], latitude, longitude);
      if (dist > 300) {
        // Discontinuity > 300m: break trail so we never interpolate across land
        breadcrumbCoords.current = [];
      }
    }
    breadcrumbCoords.current.push([latitude, longitude]);
    if (breadcrumbCoords.current.length > 20) {
      breadcrumbCoords.current.shift();
    }

    try {
      if (breadcrumbRef.current) {
        breadcrumbRef.current.setLatLngs(breadcrumbCoords.current);
      } else {
        breadcrumbRef.current = L.polyline(breadcrumbCoords.current, {
          color,
          weight: 2,
          opacity: 0.6,
          dashArray: '3, 6',
        }).addTo(mapInstance);
      }

      const vesselIcon = L.divIcon({
        className: 'vessel-live-marker',
        html: `
          <div style="position:relative;display:flex;flex-direction:column;align-items:center;pointer-events:auto;">
            <!-- Vessel SVG Arrow Rotated by Heading -->
            <div style="transform:rotate(${headingDegrees}deg);transition:transform 0.4s ease-out;width:32px;height:32px;background:${color};color:#FFFFFF;border-radius:50%;border:2px solid #FFFFFF;box-shadow:0 3px 8px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 19 21 12 17 5 21 12 2"></polygon>
              </svg>
            </div>
            <!-- Text Label with Vessel Name and Speed -->
            <div style="background:#071B2B;color:#F4F8FB;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;white-space:nowrap;margin-top:4px;box-shadow:0 1px 4px rgba(0,0,0,0.3);border:1px solid #14B8A6;display:flex;align-items:center;gap:4px;">
              <span>${vesselName}</span>
              <span style="color:#14B8A6;font-family:monospace;">${speedText}</span>
            </div>
          </div>
        `,
        iconSize: [120, 60],
        iconAnchor: [60, 16],
      });

      if (!vesselMarkerRef.current) {
        const marker = L.marker([latitude, longitude], { icon: vesselIcon, zIndexOffset: 1000 }).addTo(mapInstance);
        marker.bindPopup(`
          <div style="font-family:Inter,sans-serif;padding:6px;color:#071B2B;">
            <strong style="font-size:14px;">${vesselName}</strong><br/>
            <span style="font-size:12px;color:${color};font-weight:700;">Status: ${stateLabel}</span><br/>
            <span style="font-size:12px;color:#0D3045;">Speed: ${speedKnots.toFixed(1)} kts • Heading: ${Math.round(headingDegrees)}°</span><br/>
            <span style="font-size:11px;color:#64748B;">GPS: ${latitude.toFixed(4)}° N, ${Math.abs(longitude).toFixed(4)}° W</span>
          </div>
        `);
        vesselMarkerRef.current = marker;
      } else {
        vesselMarkerRef.current.setLatLng([latitude, longitude]);
        vesselMarkerRef.current.setIcon(vesselIcon);
      }
    } catch {
      // Ignored in test environment
    }
  }, [mapInstance, telemetry]);

  const connectionBg =
    connectionStatus === 'Live'
      ? '#14B8A6'
      : connectionStatus === 'Reconnecting'
      ? '#F59E0B'
      : '#EF4444';

  return (
    <div
      className={`ferry-map-wrapper ${className}`.trim()}
      style={{
        position: 'relative',
        width: '100%',
        height,
        minHeight: '480px',
        borderRadius: 'var(--radius-lg, 8px)',
        overflow: 'hidden',
        border: '1px solid var(--color-border, #D8E5ED)',
        boxShadow: '0 4px 12px rgba(7, 27, 43, 0.08)',
        backgroundColor: '#071B2B',
      }}
      data-testid="ferry-map-container"
    >
      <div
        ref={mapContainerRef}
        style={{ width: '100%', height: '100%' }}
        aria-label="Interactive Brittany and Iroise Sea maritime map"
      />

      {/* Top-Right: Connection Status Chip */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          zIndex: 1000,
          backgroundColor: '#071B2B',
          color: '#F4F8FB',
          padding: '4px 10px',
          borderRadius: '6px',
          fontSize: '11px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          boxShadow: '0 2px 6px rgba(0,0,0,0.3)',
          border: '1px solid #1E3A52',
        }}
        data-testid="connection-status-chip"
      >
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: connectionBg,
          }}
        />
        <span>{connectionStatus}</span>
        {activeTier.isOffline && (
          <span
            data-testid="offline-map-badge"
            style={{
              marginLeft: '6px',
              padding: '2px 6px',
              backgroundColor: '#EF4444',
              color: '#FFFFFF',
              borderRadius: '4px',
              fontSize: '10px',
              fontWeight: 700,
            }}
          >
            Offline map
          </span>
        )}
      </div>

      {/* Bottom-Left: Mandatory Honest Labelling Overlay */}
      <div
        style={{
          position: 'absolute',
          bottom: '12px',
          left: '12px',
          zIndex: 1000,
          backgroundColor: 'rgba(7, 27, 43, 0.92)',
          color: '#F4F8FB',
          padding: '4px 10px',
          borderRadius: '6px',
          fontSize: '11px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          pointerEvents: 'none',
          border: '1px solid #1E3A52',
        }}
        data-testid="honesty-badge"
      >
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: '#14B8A6',
          }}
        />
        Historical replay mode (simulated live)
      </div>
    </div>
  );
};
