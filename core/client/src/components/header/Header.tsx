const F = "'Helvetica', 'Helvetica Neue', Arial, sans-serif";

// Minimal monochrome spectral/lunar logo
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
  return (
    <header
      style={{
        fontFamily: F,
        borderBottom: '1px solid #ddd',
        background: '#fff',
      }}
    >
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
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
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
        </div>

        {/* Nav */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '28px' }}>
          {[
            { label: 'Home', href: '#' },
            { label: 'Documents', href: '#' },
            { label: 'Sign Up', href: '#' },
          ].map(({ label, href }) => (
            <a
              key={label}
              href={href}
              style={{
                fontSize: '11px',
                fontWeight: '500',
                letterSpacing: '1px',
                color: '#444',
                textTransform: 'uppercase',
                transition: 'color 0.15s ease',
              }}
              onMouseEnter={(e) => ((e.target as HTMLElement).style.color = '#111')}
              onMouseLeave={(e) => ((e.target as HTMLElement).style.color = '#444')}
            >
              {label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
