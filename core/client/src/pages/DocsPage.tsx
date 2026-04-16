import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/header/Header';
import Footer from '../components/footer/Footer';
import './DocsPage.css';

// ─────────────────────────────────────────────────────────────────
// DocsPage.tsx
// Technical wiki with sticky sidebar navigation and 5 content sections.
// Scrollspy highlights the active section as the user scrolls.
// ─────────────────────────────────────────────────────────────────

const SECTIONS = [
  { id: 'intro',      label: 'Introduction' },
  { id: 'data',       label: 'Data Structure' },
  { id: 'pipeline',   label: 'Cleaning Pipeline' },
  { id: 'schema',     label: 'Database Schema' },
  { id: 'peaks',      label: 'Peak Preservation' },
];

export default function DocsPage() {
  const [activeId, setActiveId] = useState('intro');

  // Scrollspy — track which section is in view
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      { rootMargin: '-20% 0px -70% 0px', threshold: 0 }
    );

    SECTIONS.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="docs-root">
      <Header />

      <div className="docs-layout">
        {/* ── Sidebar ─────────────────────────────── */}
        <aside className="docs-sidebar">
          <div className="docs-sidebar-inner">
            <div className="docs-sidebar-heading">Documentation</div>
            <nav aria-label="Documentation sections">
              {SECTIONS.map(({ id, label }) => (
                <button
                  key={id}
                  className={`docs-nav-link${activeId === id ? ' docs-nav-link--active' : ''}`}
                  onClick={() => scrollTo(id)}
                >
                  {label}
                </button>
              ))}
            </nav>

            <div className="docs-sidebar-sep" />

            <div className="docs-sidebar-meta">
              <div className="docs-meta-item">
                <span className="docs-meta-key">Mission</span>
                <span className="docs-meta-val">Chandrayaan-3</span>
              </div>
              <div className="docs-meta-item">
                <span className="docs-meta-key">Data Level</span>
                <span className="docs-meta-val">Level-1 LIBS</span>
              </div>
              <div className="docs-meta-item">
                <span className="docs-meta-key">Format</span>
                <span className="docs-meta-val">PDS4 / Fixed-Width Binary</span>
              </div>
              <div className="docs-meta-item">
                <span className="docs-meta-key">Source</span>
                <span className="docs-meta-val">ISRO Archive</span>
              </div>
            </div>

            <div className="docs-sidebar-sep" />
            <Link to="/graph" className="docs-sidebar-cta">
              Open Spectral Analysis →
            </Link>
          </div>
        </aside>

        {/* ── Content ─────────────────────────────── */}
        <main className="docs-content">

          {/* ═══════════════════════════════════════
              1. INTRODUCTION
          ═══════════════════════════════════════ */}
          <section id="intro" className="docs-section">
            <div className="docs-section-number">01</div>
            <h2 className="docs-section-title">Introduction</h2>
            <p className="docs-p">
              Laser-Induced Breakdown Spectroscopy (LIBS) is an atomic emission
              technique in which a high-energy pulsed laser is focused on a target surface.
              The laser plasma ablates a small amount of material; the resulting
              plasma emits light that is spectrally resolved to identify constituent elements.
            </p>
            <p className="docs-p">
              On the Moon, the absence of an atmosphere — and hence the absence of
              background gases — fundamentally changes the physics of plasma formation.
              On Mars, Phoenix and Curiosity operate in a CO₂-dominated atmosphere at
              ~600 Pa, which confinement broadens the plasma and increases continuum
              emission. Lunar LIBS operates in high vacuum (~10⁻¹² Pa), producing
              narrower peaks and a lower continuum, but also a less thermally confined
              plasma with steeper shot-to-shot variability.
            </p>
            <p className="docs-p">
              The Chandrayaan-3 LIBS instrument (part of the ChaSTE payload) acquired
              spectra at the lunar south pole during the Vikram lander's surface
              operations in August 2023. The resulting Level-1 data were archived by
              ISRO in PDS4-compliant format and released publicly. LunarAtlas provides
              the first open, reproducible pipeline for processing these archives into
              analysis-ready records.
            </p>

            <div className="docs-callout">
              <div className="docs-callout-label">Key Distinction</div>
              <p>
                Unlike Mars LIBS (ChemCam, SuperCam), lunar LIBS lacks atmospheric
                confinement, making shot ablation depth and plasma geometry more
                variable. This increases the importance of shot-level analysis rather
                than bulk averaging.
              </p>
            </div>
          </section>

          {/* ═══════════════════════════════════════
              2. DATA STRUCTURE
          ═══════════════════════════════════════ */}
          <section id="data" className="docs-section">
            <div className="docs-section-number">02</div>
            <h2 className="docs-section-title">Data Structure</h2>
            <p className="docs-p">
              Each PDS4 product in the Chandrayaan-3 LIBS archive consists of an
              XML label file (<code className="docs-code">.xml</code>) and a paired
              fixed-width binary data file (<code className="docs-code">.fit</code> or
              <code className="docs-code">.dat</code>). The binary table encodes one
              measurement per row, with each row containing{' '}
              <strong>2,049 wavelength channel intensities</strong> as consecutive
              big-endian IEEE-754 float values.
            </p>

            <h3 className="docs-h3">The Wide-Table Challenge</h3>
            <p className="docs-p">
              In the raw archive, wavelength channels are encoded as{' '}
              <strong>column headers</strong> — <em>W_164.35, W_164.70, …, W_878.26</em>.
              This "wide" schema makes row-level operations efficient for the instrument
              firmware but creates serious analytical challenges:
            </p>
            <ul className="docs-list">
              <li>SQL GROUP BY operations across wavelengths require pivoting 2,049 columns</li>
              <li>Statistical aggregation per wavelength requires column-by-column iteration</li>
              <li>Adding new measurement metadata requires schema-level ALTER TABLE</li>
              <li>Index selectivity across 2,049 numeric columns is impractical</li>
            </ul>

            <div className="docs-schema-diagram">
              <div className="docs-schema-title">Wide Format (raw archive)</div>
              <pre className="docs-pre">
{`shot_id  | W_164.35 | W_164.70 | W_165.05 | … | W_878.26
---------+----------+----------+----------+---+----------
shot_001 |  1203.4  |  1198.7  |  1205.2  | … |   892.1
shot_002 |  1210.8  |   944.2  |  1190.6  | … |   876.4
   …`}
              </pre>
              <div className="docs-schema-title" style={{ marginTop: '20px' }}>Long Format (LunarAtlas normalised schema)</div>
              <pre className="docs-pre">
{`measurement_id | wavelength_nm | intensity_counts
---------------+---------------+-----------------
shot_001       |    164.35     |     1203.4
shot_001       |    164.70     |     1198.7
shot_001       |    165.05     |     1205.2
   …           |      …        |       …
shot_001       |    878.26     |      892.1
shot_002       |    164.35     |     1210.8
   …`}
              </pre>
            </div>

            <p className="docs-p">
              The reshape produces <strong>2,049 rows per shot</strong>. For the full
              164-file dataset, this yields approximately <strong>335,000 spectral
              records</strong> before any cleaning step is applied.
            </p>
          </section>

          {/* ═══════════════════════════════════════
              3. CLEANING PIPELINE
          ═══════════════════════════════════════ */}
          <section id="pipeline" className="docs-section">
            <div className="docs-section-number">03</div>
            <h2 className="docs-section-title">The Cleaning Pipeline</h2>
            <p className="docs-p">
              The LIBS instrument records measurements in alternating "plasma" and
              "dark" shots. Plasma shots fire the laser; dark shots are recorded
              with no laser pulse and capture thermal and electronic background noise.
              The Level-1 cleaning pipeline applies the following correction:
            </p>

            {/* Main formula block */}
            <div className="docs-formula-block">
              <div className="docs-formula-label">Background Subtraction Formula</div>
              <div className="docs-formula">
                I<sub>clean</sub>(λ) = max(0,&nbsp;
                I<sub>plasma</sub>(λ) −&nbsp;
                I<sub>background</sub>(λ))
              </div>
              <div className="docs-formula-note">
                The max(0, ·) clamp prevents physically meaningless negative intensities
                that arise from shot-to-shot dark-frame variability.
              </div>
            </div>

            <h3 className="docs-h3">Shot Interleaving</h3>
            <p className="docs-p">
              Dark frames are paired with their temporally adjacent plasma shots.
              Each dark frame is assumed to represent the background of the nearest
              plasma shots in time. The pipeline walks the measurement table in
              acquisition order and applies the formula channel-by-channel.
            </p>

            <h3 className="docs-h3">Negative Sample Fraction</h3>
            <p className="docs-p">
              After applying the subtraction, a fraction of channel values remain
              negative before the clamp (caused by dark-frame variability exceeding
              the plasma signal at low-intensity channels). Across the 164-file
              dataset, this fraction varies from <strong>0.5%</strong> to{' '}
              <strong>76.8%</strong> per shot — indicating significant shot-to-shot
              quality variation that bulk averaging would entirely obscure.
            </p>

            <div className="docs-callout">
              <div className="docs-callout-label">Baseline Suppression Factor</div>
              <p>
                The median baseline suppression factor across the dataset is
                approximately <strong>×7.1</strong>, meaning the cleaned signal
                has, on average, 7.1× less continuum contribution than the raw
                plasma spectra — making emission lines significantly more prominent.
              </p>
            </div>
          </section>

          {/* ═══════════════════════════════════════
              4. DATABASE SCHEMA
          ═══════════════════════════════════════ */}
          <section id="schema" className="docs-section">
            <div className="docs-section-number">04</div>
            <h2 className="docs-section-title">Database Schema</h2>
            <p className="docs-p">
              LunarAtlas uses a normalised PostgreSQL schema that mirrors the PDS4
              mission hierarchy. Each entity level maps to a PDS4 logical identifier
              (LID) component, enabling direct traceability between database records
              and archival source files.
            </p>

            {/* Hierarchy diagram */}
            <div className="docs-hierarchy">
              <div className="docs-hier-node docs-hier-node--l0">
                <div className="docs-hier-label">Mission</div>
                <div className="docs-hier-detail">chandrayaan3</div>
              </div>
              <div className="docs-hier-connector" />
              <div className="docs-hier-node docs-hier-node--l1">
                <div className="docs-hier-label">Instrument</div>
                <div className="docs-hier-detail">libs_chaste</div>
              </div>
              <div className="docs-hier-connector" />
              <div className="docs-hier-node docs-hier-node--l2">
                <div className="docs-hier-label">Observation</div>
                <div className="docs-hier-detail">obs_id · acquisition_date · site</div>
              </div>
              <div className="docs-hier-connector" />
              <div className="docs-hier-node docs-hier-node--l3">
                <div className="docs-hier-label">Measurement</div>
                <div className="docs-hier-detail">measurement_id · shot_type · md5 · algo_version</div>
              </div>
              <div className="docs-hier-connector" />
              <div className="docs-hier-node docs-hier-node--l4">
                <div className="docs-hier-label">SpectralRecord</div>
                <div className="docs-hier-detail">wavelength_nm · intensity_counts · is_cleaned</div>
              </div>
            </div>

            <h3 className="docs-h3">Key Fields</h3>
            <div className="docs-table-wrap">
              <table className="docs-table">
                <thead>
                  <tr>
                    <th>Table</th>
                    <th>Key Column</th>
                    <th>Purpose</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td>measurement</td><td>shot_type</td><td>Distinguishes plasma vs dark shots</td></tr>
                  <tr><td>measurement</td><td>md5_checksum</td><td>Reproducibility fingerprint of source file</td></tr>
                  <tr><td>measurement</td><td>algo_version</td><td>Pipeline version that produced the record</td></tr>
                  <tr><td>measurement</td><td>neg_fraction</td><td>Fraction of channels clamped to zero</td></tr>
                  <tr><td>spectral_record</td><td>wavelength_nm</td><td>Calibrated wavelength in nanometres</td></tr>
                  <tr><td>spectral_record</td><td>intensity_counts</td><td>Raw or background-subtracted DN value</td></tr>
                  <tr><td>spectral_record</td><td>is_cleaned</td><td>Whether background subtraction was applied</td></tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* ═══════════════════════════════════════
              5. PEAK PRESERVATION
          ═══════════════════════════════════════ */}
          <section id="peaks" className="docs-section">
            <div className="docs-section-number">05</div>
            <h2 className="docs-section-title">Peak Preservation</h2>
            <p className="docs-p">
              Rendering 2,049 data points per spectrum at full resolution is unnecessary
              at typical browser zoom levels, but naive downsampling can destroy the
              narrow emission peaks that give LIBS spectra their analytical value.
            </p>

            <h3 className="docs-h3">Why Standard LTTB Fails</h3>
            <p className="docs-p">
              Largest-Triangle-Three-Buckets (LTTB) is a perceptually optimal algorithm
              for general time-series downsampling. However, it optimises for visual
              fidelity of the overall curve shape, not for preserving extrema. A
              narrow emission line (typically 2–5 channels wide in Chandrayaan-3 LIBS
              data) can be eliminated in a single LTTB pass if its triangle area is
              smaller than neighbouring points — yet that line may represent the{' '}
              <strong>only diagnostic signature of an element of interest</strong>.
            </p>

            <h3 className="docs-h3">Adaptive Min-Max Downsampling</h3>
            <p className="docs-p">
              LunarAtlas uses a bucket-based min-max approach: the wavelength range is
              divided into <em>n</em> equal buckets (where <em>n</em> is proportional
              to the available display pixels), and within each bucket both the minimum
              and maximum intensity values are retained. This guarantees that:
            </p>
            <ul className="docs-list">
              <li>No emission-line peak is lost regardless of zoom level</li>
              <li>The output point count scales linearly with display resolution</li>
              <li>Processing is O(n) and occurs client-side in real time</li>
            </ul>

            <div className="docs-callout">
              <div className="docs-callout-label">Zoom Awareness</div>
              <p>
                As the user zooms in on a spectral region, the active wavelength range
                narrows and bucket width decreases. The same algorithm re-runs on the
                visible subset with finer buckets, automatically revealing all
                sub-structure in the zoomed region — including fine structure within
                broad emission complexes.
              </p>
            </div>

            <h3 className="docs-h3">Emission Lines of Interest</h3>
            <div className="docs-table-wrap">
              <table className="docs-table">
                <thead>
                  <tr>
                    <th>Element</th>
                    <th>Peak Wavelength (nm)</th>
                    <th>Significance</th>
                  </tr>
                </thead>
                <tbody>
                  <tr><td>Mg I</td><td>285, 518</td><td>Mafic mineral indicator</td></tr>
                  <tr><td>Al I</td><td>309, 396</td><td>Plagioclase indicator</td></tr>
                  <tr><td>Ca II / Ca I</td><td>317–320, 422</td><td>Anorthosite tracer</td></tr>
                  <tr><td>Fe I</td><td>526–532</td><td>Iron abundance proxy</td></tr>
                  <tr><td>Na I</td><td>589</td><td>Alkali feldspar tracer</td></tr>
                  <tr><td>Ti II</td><td>334, 368</td><td>Ilmenite / high-Ti basalt</td></tr>
                </tbody>
              </table>
            </div>
          </section>

        </main>
      </div>

      <Footer />
    </div>
  );
}
