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
  const [username,    setUsername]    = useState('');
  const [role,        setRole]        = useState('researcher');
  const [password,    setPassword]    = useState('');
  const [showPassword, setShowPassword] = useState(false);
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
      if (!username.trim()) {
        e.username = 'Username is required.';
      } else if (!/^[a-zA-Z0-9_]{3,30}$/.test(username.trim())) {
        e.username = 'Username must be 3-30 characters (alphanumeric or underscores).';
      }
      if (!role.trim()) {
        e.role = 'Role is required.';
      }
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
        await apiService.register({ email, username: username.trim(), role, institution: institution.trim(), interest: interest.trim(), password });
      }
      const data = await apiService.login(email, password);
      setSubmitted(true);
      setTimeout(() => {
        login(data.access_token);
        onClose();
        navigate('/analyzer');
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
        className={`bg-canvas dark:bg-[#141414] border border-border-dark dark:border-[#2a2a2a] w-full ${
          mode === 'register' ? 'max-w-[640px]' : 'max-w-[480px]'
        } relative font-sans transition-colors duration-200`}
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
            <div className="text-center py-6 flex flex-col items-center">
              <div className="mb-3 text-emerald-500">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <div className="text-[13px] font-bold tracking-[1px] text-ink dark:text-[#f0f0f0]">Access Granted</div>
              <div className="text-[11px] text-[#999] dark:text-[#555] mt-[6px] tracking-[0.3px]">
                Redirecting to spectral analyzer…
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate>
              {globalError && <div className="mb-4 px-4 py-3 bg-red-50 border-l-4 border-red-500 text-[11px] text-red-700 font-medium">{globalError}</div>}

              <div className={mode === 'register' ? 'grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-3' : 'space-y-4'}>
                {/* Email */}
                <div>
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
                <div>
                  <label className="text-[9px] font-bold tracking-[1.5px] text-[#888] dark:text-[#555] uppercase block mb-[5px]">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="signup-password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className={`${inputClass(errors.password)} pr-10`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 bg-transparent border-0 cursor-pointer text-[#888] hover:text-ink dark:text-[#555] dark:hover:text-[#d0d0d0] flex items-center justify-center p-0 transition-colors"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                          <line x1="1" y1="1" x2="23" y2="23" />
                        </svg>
                      ) : (
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                          <circle cx="12" cy="12" r="3" />
                        </svg>
                      )}
                    </button>
                  </div>
                  {errors.password && <div className="text-[10px] text-[#c55] mt-1">{errors.password}</div>}
                </div>

                {mode === 'register' && (
                  <>
                    {/* Username */}
                    <div>
                      <label className="text-[9px] font-bold tracking-[1.5px] text-[#888] dark:text-[#555] uppercase block mb-[5px]">
                        Username
                      </label>
                      <input
                        id="signup-username"
                        type="text"
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        placeholder="e.g. scientist_libs"
                        className={inputClass(errors.username)}
                      />
                      {errors.username && <div className="text-[10px] text-[#c55] mt-1">{errors.username}</div>}
                    </div>

                    {/* Role */}
                    <div>
                      <label className="text-[9px] font-bold tracking-[1.5px] text-[#888] dark:text-[#555] uppercase block mb-[5px]">
                        Role
                      </label>
                      <select
                        id="signup-role"
                        value={role}
                        onChange={e => setRole(e.target.value)}
                        className={`${inputClass(errors.role)} cursor-pointer`}
                        style={{ colorScheme: 'dark' }}
                      >
                        <option value="researcher">Researcher</option>
                        <option value="developer">Developer</option>
                        <option value="student">Student</option>
                        <option value="data_scientist">Data Scientist</option>
                      </select>
                      {errors.role && <div className="text-[10px] text-[#c55] mt-1">{errors.role}</div>}
                    </div>

                    {/* Institution */}
                    <div>
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
                    <div>
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
                      className="flex items-start gap-[10px] cursor-pointer col-span-1 md:col-span-2 mt-2"
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
                    {errors.agreed && <div className="text-[10px] text-[#c55] col-span-1 md:col-span-2 -mt-1">{errors.agreed}</div>}
                  </>
                )}
              </div>

              {/* Submit */}
              <button
                id="signup-submit"
                type="submit"
                className="w-full py-[13px] bg-ink dark:bg-[#f0f0f0] text-white dark:text-[#0d0d0d] border-0 font-sans text-[11px] font-bold tracking-[2px] uppercase cursor-pointer transition-colors duration-150 hover:bg-[#333] dark:hover:bg-[#d0d0d0] mt-6 mb-4"
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
                  className="bg-transparent border-none text-[11px] text-emerald-500 hover:text-emerald-600 dark:text-[#a3e635] dark:hover:text-[#bef264] cursor-pointer uppercase tracking-widest font-bold transition-colors"
                >
                  {mode === 'register' ? 'Already have access? Sign In' : 'Create Account'}
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
