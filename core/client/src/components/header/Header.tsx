import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import SignUpModal from '../auth/SignUpModal';

const F = "'Helvetica', 'Helvetica Neue', Arial, sans-serif";

// ─── Minimal monochrome spectral/lunar logo ──────────────
const Logo = () => (
  <svg width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="19" cy="19" r="16" stroke="#111" strokeWidth="1.5" />
    {/* Moon crescent */}
    <path
      d="M19 4 A15 15 0 0 1 19 34 A10 10 0 0 0 19 4Z"
      fill="#111"
      opacity="0.12"
    />
    {/* Spectral lines (horizontal) */}
    <line x1="7" y1="14" x2="31" y2="14" stroke="#111" strokeWidth="0.7" opacity="0.25" />
    <line x1="7" y1="19" x2="31" y2="19" stroke="#111" strokeWidth="0.7" opacity="0.25" />
    <line x1="7" y1="24" x2="31" y2="24" stroke="#111" strokeWidth="0.7" opacity="0.25" />
    {/* Emission line markers */}
    <line x1="14" y1="11" x2="14" y2="27" stroke="#111" strokeWidth="1.4" />
    <line x1="23" y1="11" x2="23" y2="27" stroke="#111" strokeWidth="1.4" />
  </svg>
);

export default function Header() {
  const [showModal, setShowModal] = useState(false);
  const { isLoggedIn, user, logout } = useAuth();
  const location = useLocation();

  const navLinks = [
    { label: 'Home', to: '/' },
    { label: 'Documentation', to: '/docs' },
    { label: 'Graph', to: '/graph' },
  ];

  const isActive = (to: string) =>
    to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);

  return (
    <>
      <header
        style={{
          fontFamily: F,
          borderBottom: '1px solid #ddd',
          background: '#fff',
          position: 'sticky',
          top: 0,
          zIndex: 500,
        }}
      >
        <div
          style={{
            maxWidth: '1400px',
            margin: '0 auto',
            padding: '0 32px',
            height: '61px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {/* Brand */}
          <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Logo />
            <div>
              <div
                style={{
                  fontSize: '13px',
                  fontWeight: '700',
                  letterSpacing: '3px',
                  color: '#111',
                  lineHeight: 1,
                }}
              >
                LUNAR<span style={{ fontWeight: '300' }}>ATLAS</span>
              </div>
              <div
                style={{
                  fontSize: '8.5px',
                  letterSpacing: '1.8px',
                  color: '#999',
                  marginTop: '3px',
                  fontWeight: '400',
                }}
              >
                SPECTRAL ANALYSIS SYSTEM
              </div>
            </div>
          </Link>

          {/* Nav */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
            {navLinks.map(({ label, to }) => {
              const active = isActive(to);
              return (
                <Link
                  key={label}
                  to={to}
                  style={{
                    fontSize: '11px',
                    fontWeight: active ? '700' : '500',
                    letterSpacing: '1px',
                    color: active ? '#111' : '#888',
                    textTransform: 'uppercase',
                    textDecoration: 'none',
                    borderBottom: active ? '1px solid #111' : '1px solid transparent',
                    paddingBottom: '2px',
                    transition: 'color 0.15s ease',
                  }}
                  onMouseEnter={e => { if (!active) (e.currentTarget as HTMLElement).style.color = '#111'; }}
                  onMouseLeave={e => { if (!active) (e.currentTarget as HTMLElement).style.color = '#888'; }}
                >
                  {label}
                </Link>
              );
            })}

            {/* Auth area */}
            {isLoggedIn ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {/* User badge */}
                <div style={{
                  border: '1px solid #e0e0e0',
                  padding: '4px 12px',
                  display: 'flex', alignItems: 'center', gap: '7px',
                }}>
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#111', flexShrink: 0 }} />
                  <span style={{ fontSize: '10px', color: '#555', letterSpacing: '0.3px', maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {user?.email}
                  </span>
                </div>
                <button
                  id="header-logout"
                  onClick={logout}
                  style={{
                    fontFamily: F,
                    fontSize: '10px',
                    fontWeight: '500',
                    letterSpacing: '1px',
                    color: '#999',
                    textTransform: 'uppercase',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    transition: 'color 0.15s ease',
                    padding: 0,
                  }}
                  onMouseEnter={e => (e.currentTarget.style.color = '#111')}
                  onMouseLeave={e => (e.currentTarget.style.color = '#999')}
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <button
                id="header-signup"
                onClick={() => setShowModal(true)}
                style={{
                  fontFamily: F,
                  fontSize: '10px',
                  fontWeight: '700',
                  letterSpacing: '1.5px',
                  color: '#fff',
                  textTransform: 'uppercase',
                  background: '#111',
                  border: 'none',
                  padding: '8px 18px',
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = '#333')}
                onMouseLeave={e => (e.currentTarget.style.background = '#111')}
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
