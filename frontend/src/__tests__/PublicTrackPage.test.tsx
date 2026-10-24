import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { PublicTrackPage } from '../pages/PublicTrackPage';

describe('PublicTrackPage Component', () => {
  it('renders shared voyage information for valid token', async () => {
    render(
      <MemoryRouter initialEntries={['/track/valid-token-123']}>
        <Routes>
          <Route path="/track/:token" element={<PublicTrackPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: /shared voyage:/i })).toBeInTheDocument();
      expect(screen.getAllByText(/Fromveur II/i).length).toBeGreaterThan(0);
    });
  });
});
