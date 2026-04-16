import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import SignUpModal from '../signUpModal/SignUpModal';
import { useNavigate } from 'react-router-dom';

// ─────────────────────────────────────────────────────────────────
// Header.tsx  (updated)
// Route-aware navigation with Sign Up modal integration.
// Active route is highlighted. Auth state gates "Graph" vs "Sign Up".
// ─────────────────────────────────────────────────────────────────

const F = "'Helvetica', 'Helvetica Neue', Arial, sans-serif";

/** Minimal monochrome spectral/lunar logo — unchanged */
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
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) =>
    path === '/'
      ? location.pathname === '/'
      : location.pathname.startsWith(path);

  const linkStyle = (path: string): React.CSSProperties => ({
    fontSize: '11px',
    fontWeight: isActive(path) ? '700' : '500',
    letterSpacing: '1px',
    color: isActive(path) ? '#111' : '#666',
    textTransform: 'uppercase',
    textDecoration: 'none',
    transition: 'color 0.15s ease',
    borderBottom: isActive(path) ? '1px solid #111' : '1px solid transparent',
    paddingBottom: '2px',
  });

  return (
    <>
      <header style={{ fontFamily: F, borderBottom: '1px solid #ddd', background: '#fff' }}>
        <div
          style={{
            maxWidth: '1400px',
            margin: '0 auto',
            padding: '0 32px',
            height: '60px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {/* ── Brand ─────────────────────────── */}
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none' }}>
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

          {/* ── Nav ───────────────────────────── */}
          <nav style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
            <Link
              to="/"
              id="nav-home"
              style={linkStyle('/')}
              onMouseEnter={(e) => { if (!isActive('/')) (e.currentTarget as HTMLElement).style.color = '#111'; }}
              onMouseLeave={(e) => { if (!isActive('/')) (e.currentTarget as HTMLElement).style.color = '#666'; }}
            >
              Home
            </Link>

            <Link
              to="/paper"
              id="nav-paper"
              style={linkStyle('/paper')}
              onMouseEnter={(e) => { if (!isActive('/paper')) (e.currentTarget as HTMLElement).style.color = '#111'; }}
              onMouseLeave={(e) => { if (!isActive('/paper')) (e.currentTarget as HTMLElement).style.color = '#666'; }}
            >
              Paper
            </Link>

            <Link
              to="/docs"
              id="nav-docs"
              style={linkStyle('/docs')}
              onMouseEnter={(e) => { if (!isActive('/docs')) (e.currentTarget as HTMLElement).style.color = '#111'; }}
              onMouseLeave={(e) => { if (!isActive('/docs')) (e.currentTarget as HTMLElement).style.color = '#666'; }}
            >
              Docs
            </Link>

            {isAuthenticated ? (
              <Link
                to="/graph"
                id="nav-graph"
                style={linkStyle('/graph')}
                onMouseEnter={(e) => { if (!isActive('/graph')) (e.currentTarget as HTMLElement).style.color = '#111'; }}
                onMouseLeave={(e) => { if (!isActive('/graph')) (e.currentTarget as HTMLElement).style.color = '#666'; }}
              >
                Graph →
              </Link>
            ) : (
              <button
                id="nav-signup"
                onClick={() => setShowModal(true)}
                style={{
                  fontFamily: F,
                  fontSize: '11px',
                  fontWeight: '700',
                  letterSpacing: '1px',
                  color: '#fff',
                  textTransform: 'uppercase',
                  background: '#111',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '7px 14px',
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = '#333')}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = '#111')}
              >
                Sign Up
              </button>
            )}
          </nav>
        </div>
      </header>

      {showModal && (
        <SignUpModal
          onClose={() => setShowModal(false)}
          onSuccess={() => { setShowModal(false); navigate('/graph'); }}
        />
      )}
    </>
  );
}
