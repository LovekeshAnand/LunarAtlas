const F = "'Helvetica', 'Helvetica Neue', Arial, sans-serif";

export default function Footer() {
  return (
    <footer
      style={{
        fontFamily: F,
        borderTop: '1px solid #ddd',
        background: '#fff',
      }}
    >
      <div
        style={{
          maxWidth: '1400px',
          margin: '0 auto',
          padding: '14px 32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '24px',
        }}
      >
        <span style={{ fontSize: '11px', color: '#999', letterSpacing: '0.5px' }}>
          © 2026 LunarAtlas
        </span>
        <span style={{ color: '#ddd' }}>|</span>
        <span style={{ fontSize: '11px', color: '#bbb', letterSpacing: '0.5px' }}>
          Spectral Analysis System
        </span>
      </div>
    </footer>
  );
}
