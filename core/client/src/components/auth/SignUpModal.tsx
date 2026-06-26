import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../services/apiService';

interface SignUpModalProps {
  onClose: () => void;
}

const inputBase =
  'w-full text-[12px] bg-canvas dark:bg-[#18181d] border px-3.5 py-2.5 text-neutral-900 dark:text-neutral-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-700 focus:border-neutral-400 dark:focus:border-neutral-700 transition-all font-sans';

const BTN_PRIMARY = 'w-full py-3.5 text-[10px] font-bold tracking-widest text-white dark:text-neutral-950 bg-neutral-900 hover:bg-neutral-800 dark:bg-white dark:hover:bg-neutral-100 rounded-lg uppercase transition-all duration-150 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 shadow-sm border-0';

export default function SignUpModal({ onClose }: SignUpModalProps) {
  const { login }    = useAuth();
  const navigate     = useNavigate();

  const [mode,        setMode]               = useState<'login' | 'register'>('login');
  const [registerStep, setRegisterStep]       = useState<1 | 2>(1);
  const [email,       setEmail]              = useState('');
  const [username,    setUsername]           = useState('');
  const [role,        setRole]               = useState('researcher');
  const [password,    setPassword]           = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword]       = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [institution, setInstitution]        = useState('');
  const [interest,    setInterest]           = useState('');
  const [agreed,      setAgreed]             = useState(false);
  const [errors,      setErrors]             = useState<Record<string, string>>({});
  const [submitted,   setSubmitted]          = useState(false);
  const [globalError, setGlobalError]        = useState('');

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  function validate(step?: 1 | 2) {
    const e: Record<string, string> = {};
    
    if (mode === 'login') {
      if (!email.trim() || !email.includes('@')) e.email = 'Enter a valid email address.';
      if (!password.trim())                      e.password = 'Password is required.';
      return e;
    }

    if (mode === 'register') {
      const activeStep = step || registerStep;
      if (activeStep === 1) {
        if (!email.trim() || !email.includes('@')) e.email = 'Enter a valid email address.';
        if (!password.trim())                      e.password = 'Password is required.';
        if (!confirmPassword.trim())               e.confirmPassword = 'Confirm your password.';
        if (password && confirmPassword && password !== confirmPassword) {
          e.confirmPassword = 'Passwords do not match.';
        }
        if (!username.trim()) {
          e.username = 'Username is required.';
        } else if (!/^[a-zA-Z0-9_]{3,30}$/.test(username.trim())) {
          e.username = 'Username must be 3-30 characters (alphanumeric or underscores).';
        }
      }
      
      if (activeStep === 2) {
        if (!role.trim()) {
          e.role = 'Role is required.';
        }
        if (!institution.trim())                   e.institution = 'Institution name is required.';
        if (!interest.trim())                      e.interest    = 'Research interest is required.';
        if (!agreed)                               e.agreed      = 'You must acknowledge the data source.';
      }
    }
    return e;
  }

  async function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    setGlobalError('');
    
    if (mode === 'login') {
      const errs = validate();
      if (Object.keys(errs).length) { setErrors(errs); return; }
      
      try {
        const data = await apiService.login(email, password);
        setSubmitted(true);
        setTimeout(() => {
          login(data.access_token);
          onClose();
          navigate('/analyzer');
        }, 1400);
      } catch (err: any) {
        setGlobalError(err.message || 'Incorrect email or password.');
      }
    } else {
      // mode === 'register'
      if (registerStep === 1) {
        const errs = validate(1);
        if (Object.keys(errs).length) { setErrors(errs); return; }
        
        try {
          await apiService.register({
            email,
            username: username.trim(),
            role: 'researcher',
            institution: 'Pending',
            interest: 'Pending',
            password
          });
          
          const data = await apiService.login(email, password);
          await login(data.access_token);
          
          setErrors({});
          setRegisterStep(2);
        } catch (err: any) {
          setGlobalError(err.message || 'Registration failed. Please try again.');
        }
      } else {
        // registerStep === 2
        const errs = validate(2);
        if (Object.keys(errs).length) { setErrors(errs); return; }
        
        try {
          await apiService.updateProfile({
            role,
            institution: institution.trim(),
            interest: interest.trim()
          });
          
          setSubmitted(true);
          setTimeout(() => {
            onClose();
            navigate('/analyzer');
          }, 1400);
        } catch (err: any) {
          setGlobalError(err.message || 'Failed to complete profile details. Please try again.');
        }
      }
    }
  }

  const inputClass = (err?: string) =>
    `${inputBase} ${err ? 'border-red-500/50 dark:border-red-900/50 focus:ring-red-400 dark:focus:ring-red-900 focus:border-red-400' : 'border-neutral-300 dark:border-neutral-850'}`;

  return (
    <div
      className="fixed inset-0 z-[1000] bg-black/60 backdrop-blur-[4px] flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        className="bg-white dark:bg-[#0f0f11] border border-neutral-200 dark:border-neutral-800 w-full max-w-[500px] rounded-xl shadow-2xl relative font-sans transition-colors duration-200 overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Sign Up"
      >
        {/* Header bar */}
        <div className="border-b border-neutral-200 dark:border-neutral-800 px-6 pt-5 pb-4 flex items-start justify-between bg-neutral-50/50 dark:bg-[#121215]/50">
          <div>
            <div className="text-[10px] font-bold tracking-[3px] text-neutral-900 dark:text-white uppercase">
              {mode === 'register'
                ? (registerStep === 1 ? 'Request Access' : 'Academic Details')
                : 'Sign In'}
            </div>
            <div className="text-[11px] text-neutral-700 dark:text-neutral-300 mt-1 tracking-[0.3px]">
              {mode === 'register' && registerStep === 2 
                ? 'Configure your scientific research context' 
                : 'Chandrayaan-3 LIBS Spectral Database'}
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="bg-transparent border-0 cursor-pointer text-neutral-500 dark:text-neutral-400 text-[18px] leading-none p-0 -mt-[2px] hover:text-neutral-900 dark:hover:text-white transition-colors duration-150"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-6">
          {submitted ? (
            <div className="text-center py-6 flex flex-col items-center">
              <div className="mb-3 text-neutral-800 dark:text-white">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <div className="text-[13px] font-bold tracking-[1px] text-neutral-900 dark:text-white uppercase">Access Granted</div>
              <div className="text-[11px] text-neutral-700 dark:text-neutral-300 mt-[6px] tracking-[0.3px]">
                Redirecting to spectral analyzer…
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate>
              {globalError && (
                <div className="mb-4 px-4 py-3 bg-red-500/5 dark:bg-red-950/20 text-[11px] text-red-600 dark:text-red-400 font-medium rounded-lg border border-red-500/20">
                  {globalError}
                </div>
              )}

              {/* Login fields */}
              {mode === 'login' && (
                <div className="space-y-4">
                  {/* Email */}
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-400 mb-2 block">
                      Email Address
                    </label>
                    <input
                      id="login-email"
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="email"
                      className={inputClass(errors.email)}
                    />
                    {errors.email && <div className="text-[10px] text-red-600 dark:text-red-400 mt-1">{errors.email}</div>}
                  </div>
                  
                  {/* Password */}
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-400 mb-2 block">
                      Password
                    </label>
                    <div className="relative">
                      <input
                        id="login-password"
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        placeholder="password"
                        className={`${inputClass(errors.password)} pr-10`}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 bg-transparent border-0 cursor-pointer text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white flex items-center justify-center p-0 transition-colors"
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                      >
                        {showPassword ? (
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                            <line x1="1" y1="1" x2="23" y2="23" />
                          </svg>
                        ) : (
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                            <circle cx="12" cy="12" r="3" />
                          </svg>
                        )}
                      </button>
                    </div>
                    {errors.password && <div className="text-[10px] text-red-600 dark:text-red-400 mt-1">{errors.password}</div>}
                  </div>
                </div>
              )}

              {/* Register Step 1 */}
              {mode === 'register' && registerStep === 1 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-4">
                  {/* Username */}
                  <div className="col-span-1 md:col-span-2">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-400 mb-2 block">
                      Username
                    </label>
                    <input
                      id="signup-username"
                      type="text"
                      value={username}
                      onChange={e => setUsername(e.target.value)}
                      placeholder="username"
                      className={inputClass(errors.username)}
                    />
                    {errors.username && <div className="text-[10px] text-red-600 dark:text-red-400 mt-1">{errors.username}</div>}
                  </div>

                  {/* Email */}
                  <div className="col-span-1 md:col-span-2">
                    <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-400 mb-2 block">
                      Email Address
                    </label>
                    <input
                      id="signup-email"
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="email"
                      className={inputClass(errors.email)}
                    />
                    {errors.email && <div className="text-[10px] text-red-600 dark:text-red-400 mt-1">{errors.email}</div>}
                  </div>

                  {/* Password */}
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-400 mb-2 block">
                      Password
                    </label>
                    <div className="relative">
                      <input
                        id="signup-password"
                        type={showPassword ? 'text' : 'password'}
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        placeholder="password"
                        className={`${inputClass(errors.password)} pr-10`}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 bg-transparent border-0 cursor-pointer text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white flex items-center justify-center p-0 transition-colors"
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                      >
                        {showPassword ? (
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                            <line x1="1" y1="1" x2="23" y2="23" />
                          </svg>
                        ) : (
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                            <circle cx="12" cy="12" r="3" />
                          </svg>
                        )}
                      </button>
                    </div>
                    {errors.password && <div className="text-[10px] text-red-600 dark:text-red-400 mt-1">{errors.password}</div>}
                  </div>

                  {/* Confirm Password */}
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-400 mb-2 block">
                      Confirm Password
                    </label>
                    <div className="relative">
                      <input
                        id="signup-confirm-password"
                        type={showConfirmPassword ? 'text' : 'password'}
                        value={confirmPassword}
                        onChange={e => setConfirmPassword(e.target.value)}
                        placeholder="confirm password"
                        className={`${inputClass(errors.confirmPassword)} pr-10`}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3.5 top-1/2 -translate-y-1/2 bg-transparent border-0 cursor-pointer text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white flex items-center justify-center p-0 transition-colors"
                        aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                      >
                        {showConfirmPassword ? (
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                            <line x1="1" y1="1" x2="23" y2="23" />
                          </svg>
                        ) : (
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                            <circle cx="12" cy="12" r="3" />
                          </svg>
                        )}
                      </button>
                    </div>
                    {errors.confirmPassword && <div className="text-[10px] text-red-600 dark:text-red-400 mt-1">{errors.confirmPassword}</div>}
                  </div>
                </div>
              )}

              {/* Register Step 2 */}
              {mode === 'register' && registerStep === 2 && (
                <div className="space-y-4">
                  {/* Role */}
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-400 mb-2 block">
                      Your Role
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
                    {errors.role && <div className="text-[10px] text-red-600 dark:text-red-400 mt-1">{errors.role}</div>}
                  </div>

                  {/* Institution */}
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-400 mb-2 block">
                      Research Institution / Affiliation
                    </label>
                    <input
                      id="signup-institution"
                      type="text"
                      value={institution}
                      onChange={e => setInstitution(e.target.value)}
                      placeholder="institution"
                      className={inputClass(errors.institution)}
                    />
                    {errors.institution && <div className="text-[10px] text-red-600 dark:text-red-400 mt-1">{errors.institution}</div>}
                  </div>

                  {/* Research Interest */}
                  <div>
                    <label className="text-[10px] font-bold uppercase tracking-wider text-neutral-700 dark:text-neutral-400 mb-2 block">
                      Research Interest
                    </label>
                    <input
                      id="signup-interest"
                      type="text"
                      value={interest}
                      onChange={e => setInterest(e.target.value)}
                      placeholder="research interest"
                      className={inputClass(errors.interest)}
                    />
                    {errors.interest && <div className="text-[10px] text-red-600 dark:text-red-400 mt-1">{errors.interest}</div>}
                  </div>

                  {/* Agreement checkbox */}
                  <label
                    htmlFor="signup-agree"
                    className="flex items-start gap-[10px] cursor-pointer mt-2"
                  >
                    <input
                      id="signup-agree"
                      type="checkbox"
                      checked={agreed}
                      onChange={e => setAgreed(e.target.checked)}
                      className="mt-[2.5px] accent-neutral-900 dark:accent-white shrink-0 h-3.5 w-3.5 cursor-pointer rounded"
                    />
                    <span className="text-[11.5px] text-neutral-700 dark:text-neutral-400 leading-[1.5] tracking-[0.2px] select-none">
                      I acknowledge that all spectral data is sourced from{' '}
                      <strong className="text-neutral-900 dark:text-white">ISRO's Chandrayaan-3 PDS4 archive</strong>{' '}
                      and agree to cite the original mission data in any derived publications.
                    </span>
                  </label>
                  {errors.agreed && <div className="text-[10px] text-red-600 dark:text-red-400 mt-1">{errors.agreed}</div>}
                </div>
              )}

              {/* Submit Button */}
              <button
                id="signup-submit"
                type="submit"
                className={`${BTN_PRIMARY} mt-6 mb-2`}
              >
                {mode === 'register' 
                  ? (registerStep === 1 ? 'Register & Continue' : 'Complete Registration')
                  : 'Sign In'}
              </button>
              
              {/* Switch links */}
              {(!submitted && (mode !== 'register' || registerStep === 1)) && (
                <div className="text-center mt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setMode(mode === 'register' ? 'login' : 'register');
                      setRegisterStep(1);
                      setErrors({});
                      setGlobalError('');
                    }}
                    className="bg-transparent border-none text-[11px] text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white cursor-pointer underline underline-offset-4 font-bold tracking-wider uppercase transition-colors"
                  >
                    {mode === 'register' ? 'Already have an account? Sign In' : "Don't have an account? Create Account"}
                  </button>
                </div>
              )}
            </form>
          )}
        </div>

        {/* Footer note */}
        {!submitted && (
          <div className="border-t border-neutral-200 dark:border-neutral-800 px-6 py-3 text-[10px] text-neutral-600 dark:text-neutral-400 tracking-[0.3px] bg-neutral-50/30 dark:bg-[#121215]/30">
            Data provided in accordance with ISRO PDS4 open-data policy.
          </div>
        )}
      </div>
    </div>
  );
}
