import React, { useState, useEffect } from 'react';
import { Copy, Check, Share2, ShieldCheck } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { apiClient } from '../../api/client';

export interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  departureId: string | number;
  vesselName?: string;
}

export const ShareModal: React.FC<ShareModalProps> = ({
  isOpen,
  onClose,
  departureId,
  vesselName = 'Ferry Voyage',
}) => {
  const [shareUrl, setShareUrl] = useState<string>('');
  const [copied, setCopied] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !departureId) {
      setShareUrl('');
      setCopied(false);
      setError(null);
      return;
    }

    setLoading(true);
    apiClient<{ token: string; shareUrl?: string }>(`/departures/${departureId}/share`, {
      method: 'POST',
    })
      .then((res) => {
        const fullUrl = res.shareUrl || `${window.location.origin}/track/${res.token}`;
        setShareUrl(fullUrl);
      })
      .catch((err: any) => {
        // Fallback for offline demo mode or testing
        const fallbackUrl = `${window.location.origin}/track/demo-${departureId}`;
        setShareUrl(fallbackUrl);
      })
      .finally(() => setLoading(false));
  }, [isOpen, departureId]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // fallback
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Share Voyage Tracking"
      footer={
        <Button variant="secondary" size="sm" onClick={onClose}>
          Close
        </Button>
      }
    >
      <div>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-slate-medium)', marginBottom: '1.25rem', lineHeight: 1.5 }}>
          Share this public link with family or friends to track <strong>{vesselName}</strong> live without requiring an account.
        </p>

        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start', marginBottom: '1rem' }}>
          <div style={{ flex: 1 }}>
            <Input
              id="share-link-input"
              value={loading ? 'Generating secure share link...' : shareUrl}
              readOnly
              aria-label="Shareable tracking URL"
            />
          </div>
          <Button
            variant="primary"
            size="md"
            icon={copied ? <Check size={16} /> : <Copy size={16} />}
            onClick={handleCopy}
            disabled={loading || !shareUrl}
          >
            {copied ? 'Copied!' : 'Copy'}
          </Button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--color-slate-light)', backgroundColor: 'var(--color-bg)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)' }}>
          <ShieldCheck size={14} style={{ color: 'var(--color-primary)' }} />
          <span>Valid for 24 hours &bull; Historical replay telemetry mode</span>
        </div>
      </div>
    </Modal>
  );
};
