import React from 'react';
import { Link } from 'react-router-dom';
import { Anchor, ShieldCheck, Activity, Radio, ExternalLink } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="site-footer" role="contentinfo">
      <div className="container footer-inner">
        <div className="footer-grid">
          {/* Brand & Honesty Disclosure */}
          <div className="footer-col brand-col">
            <div className="footer-brand">
              <Anchor className="brand-icon" size={24} aria-hidden="true" />
              <span className="brand-title">Where Is My Ferry?</span>
            </div>
            <p className="footer-tagline">
              Real-time AIS vessel telemetry and delay prediction for the Brittany and Iroise Sea ferry network.
            </p>
            <div className="honesty-badge-pill" role="status" aria-label="Replay telemetry mode indicator">
              <Radio size={14} className="pulse-icon" aria-hidden="true" />
              <span>Historical replay mode (simulated live)</span>
            </div>
            <p className="footer-subtext">
              Telemetry driven by 2024 Shom/Cerema marine records with Europe/Paris DST alignment.
            </p>
          </div>

          {/* Penn ar Bed Corridors */}
          <div className="footer-col">
            <h4 className="footer-heading">Corridors & Ports</h4>
            <ul className="footer-links">
              <li><Link to="/ports#brest">Brest Port de Commerce</Link></li>
              <li><Link to="/ports#le-conquet">Le Conquet Gare Maritime</Link></li>
              <li><Link to="/ports#molene">Île-Molène (Quai Nord)</Link></li>
              <li><Link to="/ports#ouessant">Ouessant Port du Stiff</Link></li>
              <li><Link to="/ports#audierne">Audierne Sainte-Évette</Link></li>
              <li><Link to="/ports#sein">Île de Sein</Link></li>
              <li><Link to="/ports#camaret">Camaret-sur-Mer</Link></li>
            </ul>
          </div>

          {/* Operations & Vessels */}
          <div className="footer-col">
            <h4 className="footer-heading">Fleet & Schedules</h4>
            <ul className="footer-links">
              <li><Link to="/tracking">Live Fleet Tracking</Link></li>
              <li><Link to="/timetable">Daily Timetables</Link></li>
              <li><Link to="/fares">Fares & Tariffs</Link></li>
              <li><span className="vessel-tag">Fromveur II (MMSI 228037700)</span></li>
              <li><span className="vessel-tag">Enez Sun 3 (MMSI 227318000)</span></li>
              <li><span className="vessel-tag">Enez Eussa 3 (MMSI 228198900)</span></li>
            </ul>
          </div>

          {/* System & Trust */}
          <div className="footer-col">
            <h4 className="footer-heading">Platform & Trust</h4>
            <ul className="footer-links">
              <li>
                <span className="platform-status">
                  <Activity size={14} className="status-live-icon" aria-hidden="true" />
                  API Gateway: Port 8080
                </span>
              </li>
              <li>
                <span className="platform-status">
                  <ShieldCheck size={14} className="status-live-icon" aria-hidden="true" />
                  ML Daemon: Port 8000 (127.0.0.1)
                </span>
              </li>
              <li><a href="https://pennarbed.fr" target="_blank" rel="noopener noreferrer">Penn ar Bed Official <ExternalLink size={12} aria-hidden="true" /></a></li>
              <li><Link to="/privacy">Privacy & Cookies</Link></li>
              <li><Link to="/terms">Terms of Service</Link></li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <p className="copyright">
            &copy; {new Date().getFullYear()} Where Is My Ferry? Built with Spring Boot, FastAPI &amp; React.
          </p>
          <div className="wcag-compliance-note">
            <span>WCAG 2.1 AA Compliant</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
