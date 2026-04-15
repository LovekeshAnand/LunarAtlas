const F = "'Helvetica', 'Helvetica Neue', Arial, sans-serif";

const NM_TICKS = ['200', '300', '400', '500', '600', '700', '800', '900', '1000'];
const GRID_PCTS = [20, 40, 60, 80];

/**
 * SpectralGraph
 * Placeholder container for the wavelength vs. intensity spectral chart.
 * Grid lines, axis labels (Intensity / Wavelength nm), and tick marks are
 * rendered statically; actual chart rendering will replace the SVG hint.
 */
export default function SpectralGraph() {
  return (
    <div
      style={{
        fontFamily: F,
        marginTop: '16px',
        border: '1px solid #ddd',
        borderRadius: '6px',
        background: '#fafafa',
        overflow: 'hidden',
      }}
    >
      {/* ── Chart area ──────────────────────────── */}
      <div style={{ position: 'relative', height: '320px', display: 'flex' }}>

        {/* Y-axis label — rotated "Intensity" */}
        <div
          style={{
            width: '40px',
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <span
            style={{
              fontSize: '10px',
              fontWeight: '600',
              color: '#999',
              letterSpacing: '1.5px',
              textTransform: 'uppercase',
              transform: 'rotate(-90deg)',
              whiteSpace: 'nowrap',
            }}
          >
            Intensity
          </span>
        </div>

        {/* Graph body */}
        <div style={{ flex: 1, position: 'relative', borderLeft: '1px solid #ddd' }}>

          {/* Horizontal grid lines */}
          {GRID_PCTS.map((pct) => (
            <div
              key={`h-${pct}`}
              style={{
                position: 'absolute',
                top: `${pct}%`,
                left: 0,
                right: 0,
                borderTop: '1px dashed #e8e8e8',
              }}
            />
          ))}

          {/* Vertical grid lines */}
          {GRID_PCTS.map((pct) => (
            <div
              key={`v-${pct}`}
              style={{
                position: 'absolute',
                left: `${pct}%`,
                top: 0,
                bottom: 0,
                borderLeft: '1px dashed #e8e8e8',
              }}
            />
          ))}

          {/* Placeholder content */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
            }}
          >
            {/* Indicative spectral curve hint */}
            <svg width="140" height="44" viewBox="0 0 140 44" fill="none">
              <path
                d="M5 38 Q15 38 22 22 Q28 6 34 20 Q40 34 48 30 Q58 22 64 28 Q74 36 84 17 Q90 6 98 20 Q106 34 116 30 Q128 26 135 32"
                stroke="#d0d0d0"
                strokeWidth="1.6"
                fill="none"
                strokeLinecap="round"
              />
            </svg>
            <span style={{ fontSize: '12px', color: '#c0c0c0', letterSpacing: '0.5px' }}>
              Spectral Graph
            </span>
            <span style={{ fontSize: '10px', color: '#d0d0d0', letterSpacing: '0.3px' }}>
              Select parameters above to load data
            </span>
          </div>
        </div>
      </div>

      {/* ── X-axis: wavelength tick labels ──────── */}
      <div
        style={{
          borderTop: '1px solid #ddd',
          display: 'flex',
          alignItems: 'center',
          padding: '8px 8px 8px 48px',
          justifyContent: 'space-between',
        }}
      >
        {NM_TICKS.map((nm) => (
          <span key={nm} style={{ fontSize: '9px', color: '#bbb', letterSpacing: '0.3px' }}>
            {nm}
          </span>
        ))}
        <span
          style={{
            fontSize: '10px',
            fontWeight: '600',
            color: '#999',
            letterSpacing: '1.5px',
            textTransform: 'uppercase',
            marginLeft: '8px',
          }}
        >
          nm
        </span>
      </div>
    </div>
  );
}
