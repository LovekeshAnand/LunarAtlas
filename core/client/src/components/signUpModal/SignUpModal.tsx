import { useState, useEffect, type FormEvent } from 'react';
import { useAuth } from '../../context/AuthContext';
import './SignUpModal.css';

// ─────────────────────────────────────────────────────────────────
// SignUpModal.tsx
// Centered overlay modal for researcher sign-up.
// On submit: calls login() from AuthContext, then fires onSuccess().
// ─────────────────────────────────────────────────────────────────

interface SignUpModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

const F = "'Helvetica', 'Helvetica Neue', Arial, sans-serif";

export default function SignUpModal({ onClose, onSuccess }: SignUpModalProps) {
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [institution, setInstitution] = useState('');
  const [interest, setInterest] = useState('');
  const [agreed, setAgreed] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  // Prevent body scroll while modal open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      errs.email = 'A valid email address is required.';
    }
    if (!institution.trim()) {
      errs.institution = 'Research institution is required.';
    }
    if (!agreed) {
      errs.agreed = 'You must acknowledge the data usage terms.';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    // Simulate a brief async registration
    setTimeout(() => {
      login(email.trim(), institution.trim());
      onSuccess();
    }, 600);
  };

  return (
    <div className="su-backdrop" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="su-card" role="dialog" aria-modal="true" aria-labelledby="su-title">

        {/* ── Header ──────────────────────────── */}
        <div className="su-card-header">
          <div>
            <div id="su-title" className="su-title">Access Research Data</div>
            <div className="su-subtitle">
              Chandrayaan-3 LIBS · Analysis-Ready Spectra
            </div>
          </div>
          <button className="su-close" onClick={onClose} aria-label="Close modal">✕</button>
        </div>

        {/* ── Divider ─────────────────────────── */}
        <div className="su-divider" />

        {/* ── Form ────────────────────────────── */}
        <form onSubmit={handleSubmit} className="su-form" noValidate>

          {/* Email */}
          <div className="su-field">
            <label className="su-label" htmlFor="su-email">Email Address</label>
            <input
              id="su-email"
              type="email"
              className={`su-input${errors.email ? ' su-input--err' : ''}`}
              placeholder="researcher@university.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              style={{ fontFamily: F }}
            />
            {errors.email && <span className="su-error">{errors.email}</span>}
          </div>

          {/* Institution */}
          <div className="su-field">
            <label className="su-label" htmlFor="su-institution">Research Institution / Affiliation</label>
            <input
              id="su-institution"
              type="text"
              className={`su-input${errors.institution ? ' su-input--err' : ''}`}
              placeholder="e.g. ISRO, MIT, IIT Bombay"
              value={institution}
              onChange={(e) => setInstitution(e.target.value)}
              style={{ fontFamily: F }}
            />
            {errors.institution && <span className="su-error">{errors.institution}</span>}
          </div>

          {/* Research Interest */}
          <div className="su-field">
            <label className="su-label" htmlFor="su-interest">
              Research Interest <span className="su-optional">(optional)</span>
            </label>
            <textarea
              id="su-interest"
              className="su-textarea"
              placeholder="e.g. Lunar surface elemental composition, LIBS peak analysis…"
              rows={3}
              value={interest}
              onChange={(e) => setInterest(e.target.value)}
              style={{ fontFamily: F }}
            />
          </div>

          {/* Agreement checkbox */}
          <div className={`su-check-row${errors.agreed ? ' su-check-row--err' : ''}`}>
            <input
              id="su-agree"
              type="checkbox"
              className="su-checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
            />
            <label htmlFor="su-agree" className="su-check-label">
              I acknowledge that all data originates from{' '}
              <span className="su-check-em">ISRO / PDS4 archives</span> and agree to
              cite the source in any publication or derivative work.
            </label>
          </div>
          {errors.agreed && <span className="su-error su-error--indent">{errors.agreed}</span>}

          {/* Submit */}
          <button
            type="submit"
            id="su-submit"
            className="su-submit"
            disabled={submitting}
            style={{ fontFamily: F }}
          >
            {submitting ? 'Registering…' : 'Register & Access Data →'}
          </button>
        </form>

        {/* ── Footer note ─────────────────────── */}
        <div className="su-footnote">
          No password required. Access is granted for research purposes only.
        </div>
      </div>
    </div>
  );
}
