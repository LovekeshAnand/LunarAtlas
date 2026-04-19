import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import SignUpModal from '../auth/SignUpModal';

// ─── Spectral / lunar logo — uses currentColor so it adapts to dark mode
const Logo = () => (
  <svg width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="19" cy="19" r="16" stroke="currentColor" strokeWidth="1.5" />
    <path d="M19 4 A15 15 0 0 1 19 34 A10 10 0 0 0 19 4Z" fill="currentColor" opacity="0.12" />
    <line x1="7"  y1="14" x2="31" y2="14" stroke="currentColor" strokeWidth="0.7" opacity="0.25" />
    <line x1="7"  y1="19" x2="31" y2="19" stroke="currentColor" strokeWidth="0.7" opacity="0.25" />
    <line x1="7"  y1="24" x2="31" y2="24" stroke="currentColor" strokeWidth="0.7" opacity="0.25" />
    <line x1="14" y1="11" x2="14" y2="27" stroke="currentColor" strokeWidth="1.4" />
    <line x1="23" y1="11" x2="23" y2="27" stroke="currentColor" strokeWidth="1.4" />
  </svg>
);

// ─── Sun icon — shown in dark mode (click to go light)
const SunIcon = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
    <circle cx="7.5" cy="7.5" r="2.8" />
    <line x1="7.5" y1="1"    x2="7.5" y2="2.6"  />
    <line x1="7.5" y1="12.4" x2="7.5" y2="14"   />
    <line x1="1"   y1="7.5"  x2="2.6"  y2="7.5"  />
    <line x1="12.4" y1="7.5" x2="14"   y2="7.5"  />
    <line x1="2.9"  y1="2.9" x2="3.95" y2="3.95" />
    <line x1="11.05" y1="11.05" x2="12.1" y2="12.1" />
    <line x1="12.1"  y1="2.9"   x2="11.05" y2="3.95" />
    <line x1="3.95"  y1="11.05" x2="2.9"   y2="12.1" />
  </svg>
);

// ─── Moon icon — shown in light mode (click to go dark)
const MoonIcon = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12.5 9.5 A5.5 5.5 0 1 1 5.5 2.5 A4 4 0 0 0 12.5 9.5Z" />
  </svg>
);

export default function Header() {
  const [showModal, setShowModal] = useState(false);
  const { isLoggedIn, user, logout } = useAuth();
  const { isDark, toggle } = useTheme();
  const location = useLocation();

  const navLinks = [
    { label: 'Home',          to: '/' },
    { label: 'Documentation', to: '/docs' },
    { label: 'Graph',         to: '/graph' },
  ];

  const isActive = (to: string) =>
    to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);

  const handleProtectedLink = (e: React.MouseEvent, to: string) => {
    if (to !== '/' && !isLoggedIn) {
      e.preventDefault();
      setShowModal(true);
    }
  };


  return (
    <>
      <header className="font-sans border-b border-border-dark dark:border-[#222] bg-canvas dark:bg-[#0d0d0d] sticky top-0 z-[500] transition-colors duration-200">
        <div className="max-w-[1400px] mx-auto px-8 h-[61px] flex items-center justify-between">

          {/* Brand */}
          <Link to="/" className="no-underline flex items-center gap-3 text-ink dark:text-[#f0f0f0] transition-colors duration-200">
            <Logo />
            <div>
              <div className="text-[13px] font-bold tracking-[3px] leading-none">
                LUNAR<span className="font-light">ATLAS</span>
              </div>
              <div className="text-[8.5px] tracking-[1.8px] text-[#999] dark:text-[#555] mt-[3px] font-normal transition-colors duration-200">
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
                  onClick={(e) => handleProtectedLink(e, to)}
                  className={`text-[11px] tracking-[1px] uppercase no-underline pb-[2px] transition-colors duration-150 border-b ${
                    active
                      ? 'font-bold text-ink dark:text-[#f0f0f0] border-ink dark:border-[#f0f0f0]'
                      : 'font-medium text-[#888] dark:text-[#555] border-transparent hover:text-ink dark:hover:text-[#d0d0d0]'
                  }`}
                >
                  {label}
                </Link>
              );
            })}


            {/* Dark / light toggle */}
            <button
              id="header-theme-toggle"
              onClick={toggle}
              aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
              className="p-[7px] border-0 bg-transparent cursor-pointer text-[#999] dark:text-[#555] hover:text-ink dark:hover:text-[#d0d0d0] transition-colors duration-150"
            >
              {isDark ? <SunIcon /> : <MoonIcon />}
            </button>

            {/* Auth area */}
            {isLoggedIn ? (
              <div className="flex items-center gap-3">
                <div className="border border-[#e0e0e0] dark:border-[#2a2a2a] px-3 py-1 flex items-center gap-[7px]">
                  <div className="w-[6px] h-[6px] rounded-full bg-ink dark:bg-[#d0d0d0] shrink-0" />
                  <span className="text-[10px] text-[#555] dark:text-[#888] tracking-[0.3px] max-w-[160px] overflow-hidden text-ellipsis whitespace-nowrap">
                    {user?.email}
                  </span>
                </div>
                <button
                  id="header-logout"
                  onClick={logout}
                  className="font-sans text-[10px] font-medium tracking-[1px] text-[#999] dark:text-[#555] uppercase bg-transparent border-0 cursor-pointer transition-colors duration-150 p-0 hover:text-ink dark:hover:text-[#d0d0d0]"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <button
                id="header-signup"
                onClick={() => setShowModal(true)}
                className="font-sans text-[10px] font-bold tracking-[1.5px] text-white dark:text-[#0d0d0d] uppercase bg-ink dark:bg-[#f0f0f0] border-0 px-[18px] py-2 cursor-pointer transition-colors duration-150 hover:bg-[#333] dark:hover:bg-[#d0d0d0]"
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
