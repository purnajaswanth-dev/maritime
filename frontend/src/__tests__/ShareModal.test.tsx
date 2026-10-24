import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { ShareModal } from '../components/tracking/ShareModal';

describe('ShareModal Component', () => {
  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockImplementation(() => Promise.resolve()),
      },
    });
  });

  it('renders modal when open with vessel name', async () => {
    render(
      <ShareModal
        isOpen={true}
        onClose={() => {}}
        departureId="dep-101"
        vesselName="Fromveur II"
      />
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Share Voyage Tracking')).toBeInTheDocument();
    expect(screen.getByText(/Fromveur II/i)).toBeInTheDocument();
  });

  it('copies shareable URL to clipboard when Copy button is clicked', async () => {
    render(
      <ShareModal
        isOpen={true}
        onClose={() => {}}
        departureId="dep-101"
        vesselName="Fromveur II"
      />
    );

    const copyBtn = screen.getByRole('button', { name: /copy/i });
    await waitFor(() => {
      expect(copyBtn).not.toBeDisabled();
    });

    fireEvent.click(copyBtn);
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });
});
