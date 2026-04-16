import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Header from '../components/header/Header';
import Footer from '../components/footer/Footer';
import SignUpModal from '../components/signUpModal/SignUpModal';
import './HomePage.css';

// ─────────────────────────────────────────────────────────────────
// HomePage.tsx
// Research landing: Hero → Stats → Abstract → Pipeline Cards
// → Architecture flow. Design: monochrome academic, Helvetica.
// ─────────────────────────────────────────────────────────────────

/** Decorative spectral emission-line waveform — stylised LIBS spectrum */
const SpectralHero = () => (
  <svg
    viewBox="0 0 1200 110"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="hp-wave-svg"
    aria-hidden="true"
  >
    {/* Horizontal grid lines */}
    {[25, 50, 75].map((y) => (
      <line key={y} x1="0" y1={y} x2="1200" y2={y} stroke="#e8e8e8" strokeWidth="0.5" />
    ))}

    {/* Main spectral baseline + curve */}
    <path
      d="
        M0 95 L40 95 L50 94 L55 92 L60 95
        L80 95 L90 93 L100 55 L103 93 L110 95
        L125 94 L132 60 L135 94 L145 95
        L155 94 L162 30 L165 94 L175 95
        L190 95 L200 93 L208 18 L211 93 L220 95
        L235 95 L242 50 L245 95
        L265 94 L272 70 L275 94 L290 95
        L310 95 L318 93 L326 12 L329 93 L340 95
        L355 95 L362 60 L366 95
        L375 94 L382 35 L385 94 L395 95
        L410 94 L418 8 L421 94 L430 95
        L445 95 L452 55 L456 95
        L470 95 L478 80 L482 95
        L500 95 L505 94 L512 25 L515 94 L525 95
        L540 95 L548 75 L552 95
        L568 95 L575 65 L578 95
        L595 94 L601 15 L604 94 L615 95
        L630 95 L636 70 L640 95
        L658 94 L664 50 L668 94 L680 95
        L698 95 L705 80 L708 95
        L720 94 L728 40 L731 94 L745 95
        L760 95 L768 75 L772 95
        L788 94 L795 85 L798 94 L810 95
        L825 95 L832 70 L836 95
        L850 94 L857 55 L860 94 L872 95
        L890 95 L898 80 L902 95
        L920 94 L928 65 L931 94 L945 95
        L960 95 L968 85 L972 95
        L990 94 L998 75 L1001 94 L1015 95
        L1030 95 L1038 85 L1042 95
        L1060 94 L1067 78 L1070 94 L1082 95
        L1100 95 L1110 90 L1115 95
        L1135 94 L1142 88 L1145 94 L1160 95
        L1180 95 L1200 95
      "
      stroke="#111"
      strokeWidth="1.3"
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
    />

    {/* Emission peak vertical markers — thin & subtle */}
    {[100, 162, 208, 326, 418, 512, 601, 728].map((x) => (
      <line
        key={x}
        x1={x}
        y1="93"
        x2={x}
        y2="6"
        stroke="#111"
        strokeWidth="0.6"
        strokeDasharray="2 3"
        opacity="0.25"
      />
    ))}
  </svg>
);

const STATS = [
  { value: '2,049', label: 'Wavelength Channels' },
  { value: '164–878', label: 'nm Spectral Range' },
  { value: '164', label: 'Processed Files' },
  { value: '×7.1', label: 'Baseline Suppression' },
];

const PIPELINE_CARDS = [
  {
    number: '01',
    title: 'Level-1 Cleaning Pipeline',
    body: 'Background subtraction using interleaved plasma and dark shots. Each plasma spectrum is corrected using temporally adjacent dark frames, removing instrument-induced background emission.',
  },
  {
    number: '02',
    title: 'PDS4-Aware Schema',
    body: 'Normalised PostgreSQL structure preserving the full mission hierarchy: Mission → Instrument → Observation → Measurement, with PDS4 logical identifiers encoded at every level.',
  },
  {
    number: '03',
    title: 'Adaptive Visualisation',
    body: 'Min-max downsampling preserves emission-line peaks that standard LTTB would alias away. No spectral peak is lost regardless of the active zoom level or display resolution.',
  },
  {
    number: '04',
    title: 'Reproducibility & Provenance',
    body: 'MD5 checksums and algorithm-version identifiers accompany every processed file. Any spectral record can be traced back to its source PDS4 XML and the precise processing parameters applied.',
  },
];

const ARCH_STEPS = [
  'PDS4 XML Input',
  'Label Parsing',
  'Wide→Long Reshape',
  'Background Subtraction',
  'Analysis-Ready Spectra',
];

export default function HomePage() {
  const [showModal, setShowModal] = useState(false);
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleCTA = () => {
    if (isAuthenticated) {
      navigate('/graph');
    } else {
      setShowModal(true);
    }
  };

  return (
    <div className="hp-root">
      <Header />

      {/* ══════════════════════════════════════════
          HERO
      ══════════════════════════════════════════ */}
      <section className="hp-hero">
        {/* Top meta strip */}
        <div className="hp-meta-strip">
          <span>CHANDRAYAAN-3</span>
          <span className="hp-meta-dot">·</span>
          <span>LIBS SPECTROSCOPY</span>
          <span className="hp-meta-dot">·</span>
          <span>LEVEL-1 DATA</span>
          <span className="hp-meta-dot">·</span>
          <span>ISRO / PDS4</span>
        </div>

        {/* Main wordmark + tagline */}
        <div className="hp-hero-body">
          <h1 className="hp-wordmark">
            LUNAR<span className="hp-wordmark-light">ATLAS</span>
          </h1>
          <div className="hp-tagline">
            From PDS4 Archives to Analysis-Ready Spectra
          </div>
          <p className="hp-hero-desc">
            A reproducible data-processing infrastructure that transforms wide-format
            Chandrayaan-3 LIBS archival files into cleaned, normalised spectral records
            with full provenance tracking and adaptive peak-preserving visualisation.
          </p>

          <div className="hp-cta-row">
            <button id="hp-cta-primary" className="hp-btn-primary" onClick={handleCTA}>
              {isAuthenticated ? 'Open Spectral Analysis →' : 'Access Spectral Data →'}
            </button>
            <a href="/docs" className="hp-btn-secondary" id="hp-cta-docs">
              Read Documentation
            </a>
          </div>
        </div>

        {/* Spectral waveform decoration */}
        <div className="hp-wave-container">
          <div className="hp-wave-label hp-wave-label--left">164.35 nm</div>
          <SpectralHero />
          <div className="hp-wave-label hp-wave-label--right">878.26 nm</div>
        </div>
        <div className="hp-wave-axis-label">Wavelength (λ)</div>
      </section>

      {/* ══════════════════════════════════════════
          STATS BAR
      ══════════════════════════════════════════ */}
      <section className="hp-stats">
        {STATS.map((s, i) => (
          <div key={s.value} className="hp-stat-item">
            {i > 0 && <div className="hp-stat-divider" />}
            <div className="hp-stat-value">{s.value}</div>
            <div className="hp-stat-label">{s.label}</div>
          </div>
        ))}
      </section>

      {/* ══════════════════════════════════════════
          PROJECT ABSTRACT
      ══════════════════════════════════════════ */}
      <section className="hp-section hp-abstract">
        <div className="hp-section-tag">Project Abstract</div>
        <div className="hp-abstract-grid">
          <div className="hp-abstract-text">
            <p>
              LunarAtlas provides a reproducible data-processing infrastructure for
              Chandrayaan-3 LIBS Level-1 archival data. The system ingests PDS4 XML
              label files paired with fixed-width binary tables, reshapes the wide-format
              2,049-column wavelength matrix into a normalised long-format schema, and
              applies a background subtraction pipeline that yields "Analysis-Ready Spectra."
            </p>
            <p>
              Each measurement is treated as an independent statistical unit.
              Shot-to-shot variability — with negative-sample fractions ranging
              from <strong>0.5%</strong> to <strong>76.8%</strong> — is preserved
              in the output rather than masked by bulk averaging. The pipeline applies
              the correction I<sub>clean</sub>(λ) = max(0, I<sub>plasma</sub>(λ) −
              I<sub>background</sub>(λ)), achieving a median baseline suppression
              factor of approximately <strong>7.1</strong>.
            </p>
            <p>
              All processed files are accompanied by MD5 checksums and algorithm-version
              identifiers, ensuring that every spectral record is fully reproducible from
              its originating PDS4 archive entry.
            </p>
          </div>

          <div className="hp-abstract-sidebar">
            <div className="hp-sidebar-item">
              <div className="hp-sidebar-key">Mission</div>
              <div className="hp-sidebar-val">Chandrayaan-3</div>
            </div>
            <div className="hp-sidebar-item">
              <div className="hp-sidebar-key">Instrument</div>
              <div className="hp-sidebar-val">LIBS (ChaSTE)</div>
            </div>
            <div className="hp-sidebar-item">
              <div className="hp-sidebar-key">Data Source</div>
              <div className="hp-sidebar-val">ISRO / PDS4 Archive</div>
            </div>
            <div className="hp-sidebar-item">
              <div className="hp-sidebar-key">Correction Formula</div>
              <div className="hp-sidebar-formula">
                I<sub>clean</sub>(λ) = max(0,<br />
                I<sub>plasma</sub>(λ) − I<sub>bg</sub>(λ))
              </div>
            </div>
            <div className="hp-sidebar-item">
              <div className="hp-sidebar-key">Spectral Channels</div>
              <div className="hp-sidebar-val">2,049 per shot</div>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          PIPELINE CARDS
      ══════════════════════════════════════════ */}
      <section className="hp-section hp-cards-section">
        <div className="hp-section-tag">System Capabilities</div>
        <div className="hp-cards-grid">
          {PIPELINE_CARDS.map((c) => (
            <div key={c.number} className="hp-card">
              <div className="hp-card-number">{c.number}</div>
              <div className="hp-card-title">{c.title}</div>
              <div className="hp-card-body">{c.body}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ══════════════════════════════════════════
          ARCHITECTURE FLOW
      ══════════════════════════════════════════ */}
      <section className="hp-section hp-arch-section">
        <div className="hp-section-tag">Processing Pipeline</div>
        <div className="hp-arch-flow">
          {ARCH_STEPS.map((step, i) => (
            <div key={step} className="hp-arch-item">
              <div className="hp-arch-step">
                <div className="hp-arch-index">{String(i + 1).padStart(2, '0')}</div>
                <div className="hp-arch-label">{step}</div>
              </div>
              {i < ARCH_STEPS.length - 1 && (
                <div className="hp-arch-arrow" aria-hidden="true">→</div>
              )}
            </div>
          ))}
        </div>
      </section>

      <Footer />

      {showModal && (
        <SignUpModal
          onClose={() => setShowModal(false)}
          onSuccess={() => { setShowModal(false); navigate('/graph'); }}
        />
      )}
    </div>
  );
}
