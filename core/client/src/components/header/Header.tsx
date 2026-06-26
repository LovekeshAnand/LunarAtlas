import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import SignUpModal from '../auth/SignUpModal';

// ─── Spectral / lunar logo — uses currentColor so it adapts to dark mode
/**
 * @fileoverview Persistent Global Header.
 * Implements navigation logic that intercepts protected routes for unauthenticated users.
 */


// Unused icons commented out to resolve TypeScript warnings
/*
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

const MoonIcon = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12.5 9.5 A5.5 5.5 0 1 1 5.5 2.5 A4 4 0 0 0 12.5 9.5Z" />
  </svg>
);
*/

/**
 * Primary Navigation Header.
 * Synchronizes the theme state and provides auth-protected navigation links.
 */
export default function Header() {
  const [showModal, setShowModal] = useState(false);
  const { isLoggedIn, logout } = useAuth();

  const location = useLocation();

  const navLinks = [
    { label: 'Home',          to: '/' },
    { label: 'Spectral Analyzer', to: '/analyzer', protected: true },
    { label: 'Documentation', to: '/docs' },
    { label: 'Developers',    to: '/developers' },
    ...(isLoggedIn ? [{ label: 'Dashboard', to: '/dashboard', protected: true }] : []),
  ];

  const isActive = (to: string) =>
    to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);

  const handleProtectedLink = (e: React.MouseEvent, _to: string, isProtected?: boolean) => {
    if (isProtected && !isLoggedIn) {
      e.preventDefault();
      setShowModal(true);
    }
  };


  return (
    <>
      <header className="font-sans border-b border-border-dark dark:border-[#222] bg-canvas dark:bg-[#0d0d0d] sticky top-0 z-[500] transition-colors duration-200">
        <div className="max-w-[1400px] mx-auto px-8 h-[61px] flex items-center justify-between">

          {/* Brand */}
          <Link to="/" className="no-underline flex items-center text-ink dark:text-[#f0f0f0] transition-colors duration-200">
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
            {navLinks.map((link) => {
              const active = isActive(link.to);
              return (
                <Link
                  key={link.label}
                  to={link.to}
                  onClick={(e) => handleProtectedLink(e, link.to, link.protected)}
                  className={`text-[11px] tracking-[1px] uppercase no-underline pb-[2px] transition-colors duration-150 border-b ${
                    active
                      ? 'font-bold text-ink dark:text-[#f0f0f0] border-ink dark:border-[#f0f0f0]'
                      : 'font-medium text-[#888] dark:text-[#555] border-transparent hover:text-ink dark:hover:text-[#d0d0d0]'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}




            {/* GitHub Link */}
            <a
              href="https://github.com/LovekeshAnand/LunarAtlas"
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#888] hover:text-ink transition-colors duration-150 flex items-center"
              aria-label="GitHub Repository"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
              </svg>
            </a>

            {/* Auth area */}
            {isLoggedIn ? (
              <div className="flex items-center gap-3">
                <button
                  id="header-logout"
                  onClick={logout}
                  className="font-sans text-[10px] font-bold tracking-[1.5px] text-ink hover:text-white border border-ink hover:bg-ink px-[18px] py-2 cursor-pointer transition-all duration-150 rounded-sm uppercase bg-transparent"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <button
                id="header-signin"
                onClick={() => setShowModal(true)}
                className="font-sans text-[10px] font-bold tracking-[1.5px] text-ink hover:text-white border border-ink hover:bg-ink px-[18px] py-2 cursor-pointer transition-all duration-150 rounded-sm uppercase bg-transparent"
              >
                Sign In
              </button>
            )}
          </nav>
        </div>
      </header>

      {showModal && <SignUpModal onClose={() => setShowModal(false)} />}
    </>
  );
}
