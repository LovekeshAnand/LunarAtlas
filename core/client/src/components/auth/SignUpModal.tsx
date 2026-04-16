import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const F = "'Helvetica', 'Helvetica Neue', Arial, sans-serif";

interface SignUpModalProps {
  onClose: () => void;
}

export default function SignUpModal({ onClose }: SignUpModalProps) {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [institution, setInstitution] = useState('');
  const [interest, setInterest] = useState('');
  const [agreed, setAgreed] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);

  // Lock body scroll when open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  function validate() {
    const e: Record<string, string> = {};
    if (!email.trim() || !email.includes('@')) e.email = 'Enter a valid email address.';
    if (!institution.trim()) e.institution = 'Institution is required.';
    if (!interest.trim()) e.interest = 'Research interest is required.';
    if (!agreed) e.agreed = 'You must acknowledge the data source.';
    return e;
  }

  function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setSubmitted(true);
    setTimeout(() => {
      login({ email, institution, interest });
      onClose();
      navigate('/graph');
    }, 1400);
  }

  const inputStyle = (err?: string): React.CSSProperties => ({
    fontFamily: F,
    fontSize: '13px',
    color: '#111',
    background: '#fafafa',
    border: `1px solid ${err ? '#c55' : '#ddd'}`,
    borderRadius: '0',
    padding: '10px 12px',
    width: '100%',
    boxSizing: 'border-box',
    outline: 'none',
    letterSpacing: '0.2px',
  });

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.45)',
        backdropFilter: 'blur(6px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '16px',
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        style={{
          background: '#fff',
          border: '1px solid #ddd',
          width: '100%',
          maxWidth: '480px',
          position: 'relative',
          fontFamily: F,
        }}
        role="dialog"
        aria-modal="true"
        aria-label="Sign Up"
      >
        {/* Header bar */}
        <div style={{
          borderBottom: '1px solid #eee',
          padding: '20px 28px 16px',
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: '11px', fontWeight: '700', letterSpacing: '2.5px', color: '#111', textTransform: 'uppercase' }}>
              Request Access
            </div>
            <div style={{ fontSize: '11px', color: '#999', marginTop: '4px', letterSpacing: '0.3px' }}>
              Chandrayaan-3 LIBS Spectral Database
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: '#bbb', fontSize: '18px', lineHeight: 1, padding: '0',
              marginTop: '-2px',
            }}
          >×</button>
        </div>

        {/* Body */}
        <div style={{ padding: '24px 28px' }}>
          {submitted ? (
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <div style={{ fontSize: '28px', marginBottom: '12px' }}>✓</div>
              <div style={{ fontSize: '13px', fontWeight: '700', letterSpacing: '1px', color: '#111' }}>
                Access Granted
              </div>
              <div style={{ fontSize: '11px', color: '#999', marginTop: '6px', letterSpacing: '0.3px' }}>
                Redirecting to spectral graph…
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate>
              {/* Email */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '9px', fontWeight: '700', letterSpacing: '1.5px', color: '#888', textTransform: 'uppercase', display: 'block', marginBottom: '5px' }}>
                  Email Address
                </label>
                <input
                  id="signup-email"
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="researcher@institution.edu"
                  style={inputStyle(errors.email)}
                />
                {errors.email && <div style={{ fontSize: '10px', color: '#c55', marginTop: '4px' }}>{errors.email}</div>}
              </div>

              {/* Institution */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '9px', fontWeight: '700', letterSpacing: '1.5px', color: '#888', textTransform: 'uppercase', display: 'block', marginBottom: '5px' }}>
                  Research Institution / Affiliation
                </label>
                <input
                  id="signup-institution"
                  type="text"
                  value={institution}
                  onChange={e => setInstitution(e.target.value)}
                  placeholder="e.g. ISRO, MIT, IIT Delhi"
                  style={inputStyle(errors.institution)}
                />
                {errors.institution && <div style={{ fontSize: '10px', color: '#c55', marginTop: '4px' }}>{errors.institution}</div>}
              </div>

              {/* Research Interest */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{ fontSize: '9px', fontWeight: '700', letterSpacing: '1.5px', color: '#888', textTransform: 'uppercase', display: 'block', marginBottom: '5px' }}>
                  Research Interest
                </label>
                <input
                  id="signup-interest"
                  type="text"
                  value={interest}
                  onChange={e => setInterest(e.target.value)}
                  placeholder="e.g. Lunar regolith composition, LIBS spectroscopy"
                  style={inputStyle(errors.interest)}
                />
                {errors.interest && <div style={{ fontSize: '10px', color: '#c55', marginTop: '4px' }}>{errors.interest}</div>}
              </div>

              {/* Agreement checkbox */}
              <label
                htmlFor="signup-agree"
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: '10px',
                  cursor: 'pointer', marginBottom: errors.agreed ? '6px' : '24px',
                }}
              >
                <input
                  id="signup-agree"
                  type="checkbox"
                  checked={agreed}
                  onChange={e => setAgreed(e.target.checked)}
                  style={{ marginTop: '2px', accentColor: '#111', flexShrink: 0 }}
                />
                <span style={{ fontSize: '11px', color: '#555', lineHeight: '1.5', letterSpacing: '0.2px' }}>
                  I acknowledge that all spectral data is sourced from{' '}
                  <strong style={{ color: '#111' }}>ISRO's Chandrayaan-3 PDS4 archive</strong>{' '}
                  and agree to cite the original mission data in any derived publications.
                </span>
              </label>
              {errors.agreed && <div style={{ fontSize: '10px', color: '#c55', marginBottom: '18px' }}>{errors.agreed}</div>}

              {/* Submit */}
              <button
                id="signup-submit"
                type="submit"
                style={{
                  width: '100%',
                  padding: '13px',
                  background: '#111',
                  color: '#fff',
                  border: 'none',
                  fontFamily: F,
                  fontSize: '11px',
                  fontWeight: '700',
                  letterSpacing: '2px',
                  textTransform: 'uppercase',
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = '#333')}
                onMouseLeave={e => (e.currentTarget.style.background = '#111')}
              >
                Request Access
              </button>
            </form>
          )}
        </div>

        {/* Footer note */}
        {!submitted && (
          <div style={{
            borderTop: '1px solid #eee',
            padding: '12px 28px',
            fontSize: '10px',
            color: '#bbb',
            letterSpacing: '0.3px',
          }}>
            Data provided in accordance with ISRO PDS4 open-data policy.
          </div>
        )}
      </div>
    </div>
  );
}
