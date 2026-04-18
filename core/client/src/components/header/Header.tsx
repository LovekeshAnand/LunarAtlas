import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import SignUpModal from '../auth/SignUpModal';

// ─── Minimal monochrome spectral/lunar logo ──────────────────
const Logo = () => (
  <svg width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="19" cy="19" r="16" stroke="#111" strokeWidth="1.5" />
    <path d="M19 4 A15 15 0 0 1 19 34 A10 10 0 0 0 19 4Z" fill="#111" opacity="0.12" />
    <line x1="7"  y1="14" x2="31" y2="14" stroke="#111" strokeWidth="0.7" opacity="0.25" />
    <line x1="7"  y1="19" x2="31" y2="19" stroke="#111" strokeWidth="0.7" opacity="0.25" />
    <line x1="7"  y1="24" x2="31" y2="24" stroke="#111" strokeWidth="0.7" opacity="0.25" />
    <line x1="14" y1="11" x2="14" y2="27" stroke="#111" strokeWidth="1.4" />
    <line x1="23" y1="11" x2="23" y2="27" stroke="#111" strokeWidth="1.4" />
  </svg>
);

export default function Header() {
  const [showModal, setShowModal] = useState(false);
  const { isLoggedIn, user, logout } = useAuth();
  const location = useLocation();

  const navLinks = [
    { label: 'Home',          to: '/' },
    { label: 'Documentation', to: '/docs' },
    { label: 'Graph',         to: '/graph' },
  ];

  const isActive = (to: string) =>
    to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);

  return (
    <>
      <header className="font-sans border-b border-border-dark bg-canvas sticky top-0 z-[500]">
        <div className="max-w-[1400px] mx-auto px-8 h-[61px] flex items-center justify-between">

          {/* Brand */}
          <Link to="/" className="no-underline flex items-center gap-3">
            <Logo />
            <div>
              <div className="text-[13px] font-bold tracking-[3px] text-ink leading-none">
                LUNAR<span className="font-light">ATLAS</span>
              </div>
              <div className="text-[8.5px] tracking-[1.8px] text-[#999] mt-[3px] font-normal">
                SPECTRAL ANALYSIS SYSTEM
              </div>
            </div>
          </Link>

          {/* Nav */}
          <nav className="flex items-center gap-7">
            {navLinks.map(({ label, to }) => {
              const active = isActive(to);
              return (
                <Link
                  key={label}
                  to={to}
                  className={`text-[11px] tracking-[1px] uppercase no-underline pb-[2px] transition-colors duration-150 border-b ${
                    active
                      ? 'font-bold text-ink border-ink'
                      : 'font-medium text-[#888] border-transparent hover:text-ink'
                  }`}
                >
                  {label}
                </Link>
              );
            })}

            {/* Auth area */}
            {isLoggedIn ? (
              <div className="flex items-center gap-3">
                <div className="border border-[#e0e0e0] px-3 py-1 flex items-center gap-[7px]">
                  <div className="w-[6px] h-[6px] rounded-full bg-ink shrink-0" />
                  <span className="text-[10px] text-[#555] tracking-[0.3px] max-w-[160px] overflow-hidden text-ellipsis whitespace-nowrap">
                    {user?.email}
                  </span>
                </div>
                <button
                  id="header-logout"
                  onClick={logout}
                  className="font-sans text-[10px] font-medium tracking-[1px] text-[#999] uppercase bg-transparent border-0 cursor-pointer transition-colors duration-150 p-0 hover:text-ink"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <button
                id="header-signup"
                onClick={() => setShowModal(true)}
                className="font-sans text-[10px] font-bold tracking-[1.5px] text-white uppercase bg-ink border-0 px-[18px] py-2 cursor-pointer transition-colors duration-150 hover:bg-[#333]"
              >
                Sign Up
              </button>
            )}
          </nav>
        </div>
      </header>

      {showModal && <SignUpModal onClose={() => setShowModal(false)} />}
    </>
  );
}
