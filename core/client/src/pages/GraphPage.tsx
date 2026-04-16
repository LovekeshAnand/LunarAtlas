import RangeSelectorPanel from '../components/rangeSelector/rangeSelector';
import SpectralGraph from '../components/graph/SpectralGraph';

const F = "'Helvetica', 'Helvetica Neue', Arial, sans-serif";

export default function GraphPage() {
  return (
    <div
      style={{
        maxWidth: '1400px',
        width: '100%',
        margin: '0 auto',
        padding: '28px 32px',
        boxSizing: 'border-box' as const,
        fontFamily: F,
      }}
    >
      {/* Page heading */}
      <div style={{ marginBottom: '20px' }}>
        <h1
          style={{
            fontFamily: F,
            fontSize: '13px',
            fontWeight: '700',
            letterSpacing: '2.5px',
            color: '#111',
            textTransform: 'uppercase',
            margin: 0,
          }}
        >
          Spectral Analysis
        </h1>
        <p
          style={{
            fontFamily: F,
            fontSize: '11px',
            color: '#999',
            letterSpacing: '0.3px',
            marginTop: '4px',
            marginBottom: 0,
          }}
        >
          Configure observation parameters and wavelength range below.
        </p>
      </div>

      {/* ── Range Selector Panel ────── */}
      <RangeSelectorPanel />

      {/* ── Spectral Graph ──────────── */}
      <SpectralGraph />
    </div>
  );
}
