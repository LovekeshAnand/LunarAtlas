import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

import { apiService } from '../../services/apiService';

interface SignUpModalProps {
  onClose: () => void;
}

const inputBase =
  'font-sans text-[13px] text-ink dark:text-[#d0d0d0] bg-canvas-alt dark:bg-[#1a1a1a] rounded-none px-3 py-[10px] w-full outline-none tracking-[0.2px] border transition-colors duration-150';

export default function SignUpModal({ onClose }: SignUpModalProps) {
  const { login }    = useAuth();
  const navigate     = useNavigate();

  const [mode,        setMode]        = useState<'login' | 'register'>('login');
  const [email,       setEmail]       = useState('');
  const [password,    setPassword]    = useState('');
  const [institution, setInstitution] = useState('');
  const [interest,    setInterest]    = useState('');
  const [agreed,      setAgreed]      = useState(false);
  const [errors,      setErrors]      = useState<Record<string, string>>({});
  const [submitted,   setSubmitted]   = useState(false);
  const [globalError, setGlobalError] = useState('');

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  function validate() {
    const e: Record<string, string> = {};
    if (!email.trim() || !email.includes('@')) e.email = 'Enter a valid email address.';
    if (!password.trim())                      e.password = 'Password is required.';
    
    if (mode === 'register') {
      if (!institution.trim())                   e.institution = 'Institution is required.';
      if (!interest.trim())                      e.interest    = 'Research interest is required.';
      if (!agreed)                               e.agreed      = 'You must acknowledge the data source.';
    }
    return e;
  }

  async function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    setGlobalError('');
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    
    try {
      if (mode === 'register') {
        await apiService.register({ email, password, institution, interest });
      }
      const data = await apiService.login(email, password);
      setSubmitted(true);
      setTimeout(() => {
        login(data.access_token);
        onClose();
        navigate('/graph');
      }, 1400);
    } catch (err: any) {
      setGlobalError(err.message || 'Authentication failed. Please try again.');
    }
  }

  const inputClass = (err?: string) =>
    `${inputBase} ${err ? 'border-[#c55]' : 'border-border-dark dark:border-[#2e2e2e]'}`;

  return (
    <div
      className="fixed inset-0 z-[1000] bg-black/50 backdrop-blur-[6px] flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="bg-canvas dark:bg-[#141414] border border-border-dark dark:border-[#2a2a2a] w-full max-w-[480px] relative font-sans transition-colors duration-200"
        role="dialog"
        aria-modal="true"
        aria-label="Sign Up"
      >
        {/* Header bar */}
        <div className="border-b border-[#eee] dark:border-[#1f1f1f] px-7 pt-5 pb-4 flex items-start justify-between">
          <div>
            <div className="text-[11px] font-bold tracking-[2.5px] text-ink dark:text-[#f0f0f0] uppercase">
              {mode === 'register' ? 'Request Access' : 'Sign In'}
            </div>
            <div className="text-[11px] text-[#999] dark:text-[#555] mt-1 tracking-[0.3px]">
              Chandrayaan-3 LIBS Spectral Database
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="bg-transparent border-0 cursor-pointer text-ink-muted dark:text-[#444] text-[18px] leading-none p-0 -mt-[2px] hover:text-ink-soft dark:hover:text-[#888] transition-colors duration-150"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="px-7 py-6">
          {submitted ? (
            <div className="text-center py-6">
              <div className="text-[28px] mb-3 text-ink dark:text-[#f0f0f0]">✓</div>
              <div className="text-[13px] font-bold tracking-[1px] text-ink dark:text-[#f0f0f0]">Access Granted</div>
              <div className="text-[11px] text-[#999] dark:text-[#555] mt-[6px] tracking-[0.3px]">
                Redirecting to spectral graph…
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate>
              {globalError && <div className="mb-4 px-4 py-3 bg-red-50 border-l-4 border-red-500 text-[11px] text-red-700 font-medium">{globalError}</div>}

              {/* Email */}
              <div className="mb-4">
                <label className="text-[9px] font-bold tracking-[1.5px] text-[#888] dark:text-[#555] uppercase block mb-[5px]">
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
                {errors.email && <div className="text-[10px] text-[#c55] mt-1">{errors.email}</div>}
              </div>
              
              {/* Password */}
              <div className="mb-4">
                <label className="text-[9px] font-bold tracking-[1.5px] text-[#888] dark:text-[#555] uppercase block mb-[5px]">
                  Password
                </label>
                <input
                  id="signup-password"
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className={inputClass(errors.password)}
                />
                {errors.password && <div className="text-[10px] text-[#c55] mt-1">{errors.password}</div>}
              </div>

              {mode === 'register' && (
                <>
                  {/* Institution */}
                  <div className="mb-4">
                    <label className="text-[9px] font-bold tracking-[1.5px] text-[#888] dark:text-[#555] uppercase block mb-[5px]">
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
                    {errors.institution && <div className="text-[10px] text-[#c55] mt-1">{errors.institution}</div>}
                  </div>

                  {/* Research Interest */}
                  <div className="mb-5">
                    <label className="text-[9px] font-bold tracking-[1.5px] text-[#888] dark:text-[#555] uppercase block mb-[5px]">
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
                    {errors.interest && <div className="text-[10px] text-[#c55] mt-1">{errors.interest}</div>}
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
                      className="mt-[2px] accent-ink dark:accent-[#d0d0d0] shrink-0"
                    />
                    <span className="text-[11px] text-[#555] dark:text-[#888] leading-[1.5] tracking-[0.2px]">
                      I acknowledge that all spectral data is sourced from{' '}
                      <strong className="text-ink dark:text-[#d0d0d0]">ISRO's Chandrayaan-3 PDS4 archive</strong>{' '}
                      and agree to cite the original mission data in any derived publications.
                    </span>
                  </label>
                  {errors.agreed && <div className="text-[10px] text-[#c55] mb-[18px]">{errors.agreed}</div>}
                </>
              )}

              {/* Submit */}
              <button
                id="signup-submit"
                type="submit"
                className="w-full py-[13px] bg-ink dark:bg-[#f0f0f0] text-white dark:text-[#0d0d0d] border-0 font-sans text-[11px] font-bold tracking-[2px] uppercase cursor-pointer transition-colors duration-150 hover:bg-[#333] dark:hover:bg-[#d0d0d0] mb-4"
              >
                {mode === 'register' ? 'Request Access' : 'Sign In'}
              </button>
              
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => {
                    setMode(mode === 'register' ? 'login' : 'register');
                    setErrors({});
                    setGlobalError('');
                  }}
                  className="bg-transparent border-none text-[11px] text-blue-500 hover:text-blue-600 cursor-pointer uppercase tracking-widest font-bold"
                >
                  {mode === 'register' ? 'Already have access? Sign In' : 'Need access? Request Access'}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer note */}
        {!submitted && (
          <div className="border-t border-[#eee] dark:border-[#1f1f1f] px-7 py-3 text-[10px] text-ink-muted dark:text-[#404040] tracking-[0.3px]">
            Data provided in accordance with ISRO PDS4 open-data policy.
          </div>
        )}
      </div>
    </div>
  );
}
