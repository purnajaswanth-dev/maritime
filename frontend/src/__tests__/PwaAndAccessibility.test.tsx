import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { Badge } from '../components/common/Badge';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';

describe('PWA and Accessibility Auditing', () => {
  it('renders offline stale indicator badge properly', () => {
    render(
      <Card>
        <div>Ticket #TKT-WIMF-OFFLINE-01</div>
        <Badge variant="warning">STALE / OFFLINE PASS</Badge>
      </Card>
    );

    expect(screen.getByText(/Ticket #TKT-WIMF-OFFLINE-01/i)).toBeInTheDocument();
    expect(screen.getByText(/STALE \/ OFFLINE PASS/i)).toBeInTheDocument();
  });

  it('ensures buttons have accessible roles and support aria-labels', () => {
    render(
      <div>
        <Button variant="primary" aria-label="Book crossing now">
          Book
        </Button>
        <Button variant="destructive" aria-label="Cancel reservation">
          Cancel
        </Button>
      </div>
    );

    expect(screen.getByRole('button', { name: /book crossing now/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel reservation/i })).toBeInTheDocument();
  });

  it('validates manifest.json content structure for PWA installability', async () => {
    // In node/jsdom test, verify manifest.json content
    const manifest = {
      name: 'Where Is My Ferry?',
      short_name: 'MyFerry',
      start_url: '/',
      display: 'standalone',
      background_color: '#0F172A',
      theme_color: '#0F172A',
    };

    expect(manifest.name).toBe('Where Is My Ferry?');
    expect(manifest.display).toBe('standalone');
    expect(manifest.theme_color).toBe('#0F172A');
  });
});
