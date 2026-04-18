import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface SignUpModalProps {
  onClose: () => void;
}

// Shared input style — error border toggled via conditional class
const inputBase =
  'font-sans text-[13px] text-ink bg-canvas-alt rounded-none px-3 py-[10px] w-full outline-none tracking-[0.2px] border transition-colors duration-150';

export default function SignUpModal({ onClose }: SignUpModalProps) {
  const { login }    = useAuth();
  const navigate     = useNavigate();

  const [email,       setEmail]       = useState('');
  const [institution, setInstitution] = useState('');
  const [interest,    setInterest]    = useState('');
  const [agreed,      setAgreed]      = useState(false);
  const [errors,      setErrors]      = useState<Record<string, string>>({});
  const [submitted,   setSubmitted]   = useState(false);

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
    if (!email.trim() || !email.includes('@')) e.email       = 'Enter a valid email address.';
    if (!institution.trim())                   e.institution = 'Institution is required.';
    if (!interest.trim())                      e.interest    = 'Research interest is required.';
    if (!agreed)                               e.agreed      = 'You must acknowledge the data source.';
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

  const inputClass = (err?: string) =>
    `${inputBase} ${err ? 'border-[#c55]' : 'border-border-dark'}`;

  return (
    <div
      className="fixed inset-0 z-[1000] bg-black/45 backdrop-blur-[6px] flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="bg-canvas border border-border-dark w-full max-w-[480px] relative font-sans"
        role="dialog"
        aria-modal="true"
        aria-label="Sign Up"
      >
        {/* Header bar */}
        <div className="border-b border-[#eee] px-7 pt-5 pb-4 flex items-start justify-between">
          <div>
            <div className="text-[11px] font-bold tracking-[2.5px] text-ink uppercase">
              Request Access
            </div>
            <div className="text-[11px] text-[#999] mt-1 tracking-[0.3px]">
              Chandrayaan-3 LIBS Spectral Database
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="bg-transparent border-0 cursor-pointer text-ink-muted text-[18px] leading-none p-0 -mt-[2px] hover:text-ink-soft transition-colors duration-150"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="px-7 py-6">
          {submitted ? (
            <div className="text-center py-6">
              <div className="text-[28px] mb-3">✓</div>
              <div className="text-[13px] font-bold tracking-[1px] text-ink">Access Granted</div>
              <div className="text-[11px] text-[#999] mt-[6px] tracking-[0.3px]">
                Redirecting to spectral graph…
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate>

              {/* Email */}
              <div className="mb-4">
                <label className="text-[9px] font-bold tracking-[1.5px] text-[#888] uppercase block mb-[5px]">
                  Email Address
                </label>
                <input
                  id="signup-email"
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="researcher@institution.edu"
                  className={inputClass(errors.email)}
                />
                {errors.email && (
                  <div className="text-[10px] text-[#c55] mt-1">{errors.email}</div>
                )}
              </div>

              {/* Institution */}
              <div className="mb-4">
                <label className="text-[9px] font-bold tracking-[1.5px] text-[#888] uppercase block mb-[5px]">
                  Research Institution / Affiliation
                </label>
                <input
                  id="signup-institution"
                  type="text"
                  value={institution}
                  onChange={e => setInstitution(e.target.value)}
                  placeholder="e.g. ISRO, MIT, IIT Delhi"
                  className={inputClass(errors.institution)}
                />
                {errors.institution && (
                  <div className="text-[10px] text-[#c55] mt-1">{errors.institution}</div>
                )}
              </div>

              {/* Research Interest */}
              <div className="mb-5">
                <label className="text-[9px] font-bold tracking-[1.5px] text-[#888] uppercase block mb-[5px]">
                  Research Interest
                </label>
                <input
                  id="signup-interest"
                  type="text"
                  value={interest}
                  onChange={e => setInterest(e.target.value)}
                  placeholder="e.g. Lunar regolith composition, LIBS spectroscopy"
                  className={inputClass(errors.interest)}
                />
                {errors.interest && (
                  <div className="text-[10px] text-[#c55] mt-1">{errors.interest}</div>
                )}
              </div>

              {/* Agreement checkbox */}
              <label
                htmlFor="signup-agree"
                className={`flex items-start gap-[10px] cursor-pointer ${errors.agreed ? 'mb-[6px]' : 'mb-6'}`}
              >
                <input
                  id="signup-agree"
                  type="checkbox"
                  checked={agreed}
                  onChange={e => setAgreed(e.target.checked)}
                  className="mt-[2px] accent-ink shrink-0"
                />
                <span className="text-[11px] text-[#555] leading-[1.5] tracking-[0.2px]">
                  I acknowledge that all spectral data is sourced from{' '}
                  <strong className="text-ink">ISRO's Chandrayaan-3 PDS4 archive</strong>{' '}
                  and agree to cite the original mission data in any derived publications.
                </span>
              </label>
              {errors.agreed && (
                <div className="text-[10px] text-[#c55] mb-[18px]">{errors.agreed}</div>
              )}

              {/* Submit */}
              <button
                id="signup-submit"
                type="submit"
                className="w-full py-[13px] bg-ink text-white border-0 font-sans text-[11px] font-bold tracking-[2px] uppercase cursor-pointer transition-colors duration-150 hover:bg-[#333]"
              >
                Request Access
              </button>
            </form>
          )}
        </div>

        {/* Footer note */}
        {!submitted && (
          <div className="border-t border-[#eee] px-7 py-3 text-[10px] text-ink-muted tracking-[0.3px]">
            Data provided in accordance with ISRO PDS4 open-data policy.
          </div>
        )}
      </div>
    </div>
  );
}
