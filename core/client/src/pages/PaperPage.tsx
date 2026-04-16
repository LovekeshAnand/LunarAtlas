import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/header/Header';
import Footer from '../components/footer/Footer';
import './PaperPage.css';

// ─────────────────────────────────────────────────────────────────
// PaperPage.tsx
// Full interactive research paper view for
// "LunarAtlas: From PDS4 Archives to Analysis-Ready Spectra"
// Sources: Draft 1–4 (synthesised; Draft 4 / Elsevier version primary).
// Figures from: ch3_lib_002_20230825T104221_00_l1 analysis run.
// ─────────────────────────────────────────────────────────────────

const SECTIONS = [
  { id: 'abstract',      label: 'Abstract' },
  { id: 'introduction',  label: '1. Introduction' },
  { id: 'related',       label: '2. Related Work' },
  { id: 'data',          label: '3. Dataset & PDS4' },
  { id: 'architecture',  label: '4. Architecture' },
  { id: 'processing',    label: '5. Cleaning Pipeline' },
  { id: 'math',          label: '6. Downsampling Math' },
  { id: 'api',           label: '7. API & Workflow' },
  { id: 'results',       label: '8. Results' },
  { id: 'discussion',    label: '9. Discussion' },
  { id: 'conclusion',    label: '10. Conclusion' },
  { id: 'references',    label: 'References' },
];

// Figure helper
function Figure({
  src, label, caption, wide = false,
}: { src: string; label: string; caption: string; wide?: boolean }) {
  return (
    <figure className="paper-figure" style={{ marginLeft: wide ? -48 : 0, marginRight: wide ? -48 : 0 }}>
      <img
        src={src}
        alt={label}
        className="paper-figure-img"
        onError={(e) => {
          const t = e.currentTarget;
          t.style.minHeight = '160px';
          t.style.background = '#f3f3f3';
          t.alt = `[Figure: ${label} — place file in public/figures/]`;
        }}
      />
      <figcaption className="paper-figure-caption">
        <div className="paper-figure-label">{label}</div>
        <div className="paper-figure-text">{caption}</div>
      </figcaption>
    </figure>
  );
}

export default function PaperPage() {
  const [activeId, setActiveId] = useState('abstract');

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActiveId(entry.target.id);
        });
      },
      { rootMargin: '-15% 0px -70% 0px', threshold: 0 }
    );

    SECTIONS.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollTo = (id: string) =>
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });

  return (
    <div className="paper-root">
      <Header />

      <div className="paper-layout">

        {/* ── Sidebar ─────────────────────────────── */}
        <aside className="paper-sidebar">
          <div className="paper-sidebar-inner">
            <div className="paper-preprint-badge">Preprint · April 2026</div>
            <div className="paper-sidebar-heading">Contents</div>

            <nav aria-label="Paper sections">
              {SECTIONS.map(({ id, label }) => (
                <button
                  key={id}
                  id={`nav-paper-${id}`}
                  className={`paper-nav-link${activeId === id ? ' paper-nav-link--active' : ''}`}
                  onClick={() => scrollTo(id)}
                >
                  {label}
                </button>
              ))}
            </nav>

            <div className="paper-sidebar-sep" />

            <div className="paper-sidebar-meta">
              <div className="paper-meta-item">
                <span className="paper-meta-key">Journal Target</span>
                <span className="paper-meta-val">Elsevier / Icarus</span>
              </div>
              <div className="paper-meta-item">
                <span className="paper-meta-key">Status</span>
                <span className="paper-meta-val">Draft · Unpublished</span>
              </div>
              <div className="paper-meta-item">
                <span className="paper-meta-key">Dataset</span>
                <span className="paper-meta-val">Chandrayaan-3 L1 LIBS</span>
              </div>
              <div className="paper-meta-item">
                <span className="paper-meta-key">Archive</span>
                <span className="paper-meta-val">ISRO PDS4</span>
              </div>
            </div>

            <div className="paper-sidebar-sep" />

            <Link to="/graph" className="docs-sidebar-cta" style={{ display: 'block', fontSize: '11px', fontWeight: 700, color: '#111', textDecoration: 'none', border: '1px solid #111', padding: '8px 12px', borderRadius: 3, textAlign: 'center', letterSpacing: '0.5px' }}>
              Open Spectral Viewer →
            </Link>
          </div>
        </aside>

        {/* ── Main Content ─────────────────────────── */}
        <main className="paper-content">

          {/* ── Title block ────────────────────────── */}
          <div className="paper-title-block">
            <div className="paper-breadcrumb">
              <Link to="/">Home</Link> / Research Paper
            </div>

            <h1 className="paper-main-title">
              LunarAtlas: From PDS4 Archives to Analysis-Ready Spectra —
              A Reproducible Infrastructure for Chandrayaan-3 LIBS Level-1 Data
            </h1>

            <div className="paper-authors">
              <strong>Lovekesh Anand</strong><sup>a</sup>,&ensp;
              <strong>Dua Saeed</strong><sup>a</sup>
            </div>
            <div className="paper-affiliation">
              <sup>a</sup>Independent Researchers, India
            </div>
            <div className="paper-date-line">April 2026 · Preprint · Unpublished Draft — Confidential</div>
          </div>

          {/* ── CTA strip ──────────────────────────── */}
          <div className="paper-cta-strip">
            <Link to="/docs" className="paper-cta-btn paper-cta-btn--primary">
              Read Docs ↗
            </Link>
            <Link to="/graph" className="paper-cta-btn paper-cta-btn--secondary">
              Open Spectral Viewer
            </Link>
            <span className="paper-cta-label">· Chandrayaan-3 LIBS · ISRO PDS4 Archive · April 2026</span>
          </div>

          {/* ══════════════════════════════════════════
              ABSTRACT
          ══════════════════════════════════════════ */}
          <section id="abstract" className="paper-section">
            <div className="paper-abstract-box">
              <div className="paper-abstract-label">Abstract</div>

              <p className="paper-abstract-text">
                We present <strong>LunarAtlas</strong>, a reproducible data-processing
                infrastructure that transforms publicly available Chandrayaan-3
                Laser-Induced Breakdown Spectroscopy (LIBS) Level-1 (L1) products into
                cleaned, machine-accessible, long-form spectral records suitable for
                quantitative lunar science. Starting from calibrated L1 tables released
                through ISRO's PDS4-compliant archive, LunarAtlas implements a transparent
                Python pipeline that: (i) parses XML metadata; (ii) reshapes wide-format
                Chandrayaan-3 L1 tables — in which 2,049 wavelength channels appear as
                column headers spanning 164.35–878.26 nm — into normalised per-wavelength
                long-form records; (iii) identifies and correctly pairs plasma and background
                measurements using mission flag columns (<code>Laser_Fire_Status</code>,{' '}
                <code>Force_Reset_Status</code>); and (iv) performs physically motivated
                background subtraction, <em>I</em><sub>clean</sub>(λ) = max(0,{' '}
                <em>I</em><sub>plasma</sub>(λ) − <em>I</em><sub>background</sub>(λ)),
                with non-physical negatives clamped to zero.
              </p>

              <p className="paper-abstract-text">
                Applied to <code>ch3_lib_002_20230825T104221_00_l1.csv</code>, the pipeline
                yields four cleaned measurements (<strong>Measurement IDs 1–4</strong>),
                each with 2,094 wavelength channels and 19 metadata columns. A baseline
                suppression factor of ∼7.1 and a high-frequency variance increase of ∼3.9
                are observed, validating the physical correctness of the pipeline. The
                fraction of negative samples before clamping ranges from{' '}
                <strong>0.5%</strong> (ID 3, high-quality plasma) to{' '}
                <strong>76.8%</strong> (ID 2, near-null acquisition), demonstrating that
                the <strong>Measurement ID</strong> is essential for identifying shot-to-shot
                variability hidden by bulk averaging.
              </p>

              <p className="paper-abstract-text">
                LunarAtlas further provides a PDS4-aware PostgreSQL schema, adaptive
                min–max downsampling with a mathematically defined zoom-saturation criterion,
                and a versioned API with sub-500 ms response times. The system offers a
                replicable methodology for Chandrayaan-4, Artemis-era VIPER, and CLPS LIBS
                instruments.
              </p>

              <div className="paper-keywords">
                <strong>Keywords:</strong> Laser-Induced Breakdown Spectroscopy ·
                Chandrayaan-3 · Lunar Regolith · PDS4 · Data Cleaning ·
                Spectral Reproducibility · Background Subtraction · NIST Validation ·
                Measurement ID
              </div>
            </div>
          </section>

          {/* ══════════════════════════════════════════
              1. INTRODUCTION
          ══════════════════════════════════════════ */}
          <section id="introduction" className="paper-section">
            <div className="paper-section-number">Section 01</div>
            <h2 className="paper-section-title">Introduction</h2>

            <h3 className="paper-subsection-title">1.1 The Promise of Lunar In-Situ Spectroscopy</h3>
            <p className="paper-p">
              The elemental composition of the lunar surface encodes four billion years of
              planetary evolution — from the primordial magma ocean, through impact gardening,
              to ongoing solar-wind implantation of hydrogen and helium. Laser-Induced
              Breakdown Spectroscopy (LIBS) offers a path for rapid <em>in situ</em> elemental
              analysis: a pulsed laser focused on a surface target ablates a few nanograms to
              micrograms of material, generating a transient plasma whose characteristic
              optical emission encodes elemental abundances with no sample preparation and no
              contact requirement.
            </p>
            <p className="paper-p">
              LIBS was first demonstrated in a planetary setting by NASA's ChemCam instrument
              aboard <em>Curiosity</em> in 2012, which acquired more than 930,000 single-shot
              spectra from 3,500 rock and regolith targets in Gale Crater. SuperCam on{' '}
              <em>Perseverance</em> and MarSCoDe on Zhurong followed, cementing LIBS as the
              de facto in-situ geochemical sensor for planetary surfaces. India's
              Chandrayaan-3 mission achieved the first deployment of LIBS on the Moon in
              August 2023, introducing a fundamentally different plasma regime — near-vacuum
              rather than the ∼7 mbar Martian atmosphere — that requires careful handling of
              raw data.
            </p>

            <h3 className="paper-subsection-title">1.2 The Data Accessibility Gap</h3>
            <p className="paper-p">
              ISRO released Chandrayaan-3 LIBS data as calibrated Level-1 (L1) products
              conforming to PDS4 standards. Each L1 file stores 2,049 wavelength channels
              as <em>column headers</em> spanning 164.35–878.26 nm, with six leading
              metadata columns (<code>Time</code>, <code>Measurement Count</code>,{' '}
              <code>Operation Mode</code>, <code>Measurement Type</code>,{' '}
              <code>Force Reset Status</code>, <code>Laser Fire Status</code>) and eight
              trailing housekeeping columns. This wide-format structure is not amenable to
              relational storage, systematic plasma/background pairing, or reproducible
              background subtraction without a dedicated pipeline.
            </p>

            <h3 className="paper-subsection-title">1.3 Research Question and Contributions</h3>

            <div className="paper-research-q">
              How can Chandrayaan-3 LIBS Level-1 data — as released through ISRO's
              PDS4-compliant archive — be cleaned, normalised, and structured into a
              reproducible, queryable, and machine-accessible resource without compromising
              spectral fidelity or peak integrity?
            </div>

            <div className="paper-contributions">
              {[
                {
                  num: 'C1',
                  label: 'Level-1 cleaning pipeline',
                  text: 'A transparent Python pipeline that ingests Chandrayaan-3 LIBS L1 tables, correctly identifies plasma vs background measurements using mission flag columns, reshapes wide-format data into normalised long-form spectra, and performs physically motivated background subtraction.',
                },
                {
                  num: 'C2',
                  label: 'Measurement ID semantics',
                  text: 'A formal definition and implementation of the Measurement ID — the key identifier linking each cleaned spectral record to its originating plasma shot, instrument configuration, and acquisition timestamp.',
                },
                {
                  num: 'C3',
                  label: 'PDS4-aware data model',
                  text: 'A normalised PostgreSQL schema preserving the complete mission hierarchy (mission → instrument → observation → measurement → wavelength → intensity) with MD5 file checksums and algorithm-version metadata.',
                },
                {
                  num: 'C4',
                  label: 'Zoom-aware visualisation',
                  text: 'An adaptive min–max downsampling formulation — mathematically defined in terms of zoom level and wavelength span — that preserves emission-line peaks across all zoom levels, with an analytic zoom-saturation criterion.',
                },
                {
                  num: 'C5',
                  label: 'Empirical cleaning validation',
                  text: 'Quantitative characterisation of the effect of background subtraction on a real Chandrayaan-3 L1 file, including baseline suppression factors and high-frequency variance behaviour, reported for the first time for this mission product.',
                },
              ].map(({ num, label, text }) => (
                <div key={num} className="paper-contrib-item">
                  <span className="paper-contrib-num">{num}</span>
                  <span className="paper-contrib-text">
                    <span className="paper-contrib-label">{label}. </span>
                    {text}
                  </span>
                </div>
              ))}
            </div>
          </section>

          {/* ══════════════════════════════════════════
              2. RELATED WORK
          ══════════════════════════════════════════ */}
          <section id="related" className="paper-section">
            <div className="paper-section-number">Section 02</div>
            <h2 className="paper-section-title">Related Work</h2>

            <h3 className="paper-subsection-title">2.1 Planetary LIBS Instruments and Mission Heritage</h3>
            <p className="paper-p">
              ChemCam on MSL <em>Curiosity</em> uses three Czerny-Turner spectrometers
              covering 240–907 nm with a Nd:KGW laser at 1067 nm for remote analysis up
              to 7 m. After 4,000+ Martian sols it has characterised Gale Crater
              chemostratigraphy, detected boron in-situ for the first time on Mars, and
              quantified hydrogen as a hydration proxy. SuperCam on <em>Perseverance</em>{' '}
              integrates LIBS with Raman, VNIR, and acoustic measurements. MarSCoDe on
              Zhurong covers 240–2400 nm, combining LIBS and SWIR spectroscopy.
            </p>
            <p className="paper-p">
              For lunar LIBS, simulation studies demonstrated acceptable signal-to-noise
              in pressures below 10<sup>−3</sup> mbar. The Chandrayaan-3 instrument, a
              miniaturised design (~1.1 kg, &lt;1.2 W) developed at ISRO's Space Physics
              Laboratory, represents the first operational lunar LIBS deployment.
            </p>

            <h3 className="paper-subsection-title">2.2 Planetary Data Systems and PDS4</h3>
            <p className="paper-p">
              PDS4 was adopted by NASA and partner agencies to supersede PDS3, offering
              self-describing XML labels paired with data files. While theoretically
              self-sufficient, PDS4 archives are designed for archival preservation rather
              than interactive analysis: no relational abstractions, no query APIs, and no
              standard tooling for pairing observational products. Published analyses of
              Chandrayaan-3 data have typically relied on unversioned, unarchived scripts.
            </p>

            <h3 className="paper-subsection-title">2.3 Spectral Background Subtraction</h3>
            <p className="paper-p">
              ChemCam employs passive background measurements and wavelet-based continuum
              modelling. Extensive preprocessing pipelines using Stationary Wavelet Transform
              (SWT) denoising, Asymmetric Least Squares (ALS) baseline correction, and
              wavelength calibration against Ti emission lines have been developed for Mars
              LIBS. For Chandrayaan-3, Sridhar et al. applied Savitzky-Golay filtering and
              ALS, identifying Mg II, Al I, Ca II, Fe I, Si I, and O I lines in L0 data.
              LunarAtlas complements this by focusing on the L1 data tier with a formal,
              reproducible data model.
            </p>

            <h3 className="paper-subsection-title">2.4 Downsampling for Interactive Spectral Visualisation</h3>
            <p className="paper-p">
              General-purpose time-series downsampling (mean aggregation, Douglas-Peucker,
              Largest Triangle Three Buckets / LTTB) are widely deployed in web visualisation
              frameworks. These methods minimise visual distortion but provide no guarantee
              of retaining narrow emission lines — which may span only 1–3 wavelength channels.
              For LIBS spectroscopy, where a narrow Ca II doublet at 393–397 nm or Mg II at
              280 nm can be the primary diagnostic of an element, this is scientifically
              unacceptable. The min–max strategy in LunarAtlas specifically addresses this gap.
            </p>
          </section>

          {/* ══════════════════════════════════════════
              3. DATASET & PDS4
          ══════════════════════════════════════════ */}
          <section id="data" className="paper-section">
            <div className="paper-section-number">Section 03</div>
            <h2 className="paper-section-title">Chandrayaan-3 LIBS Dataset and PDS4 Context</h2>

            <h3 className="paper-subsection-title">3.1 Mission Overview</h3>
            <p className="paper-p">
              Chandrayaan-3 launched 14 July 2023 and achieved a soft landing near the lunar
              south pole (69.37°S, 32.35°E — <em>Shiv Shakti Point</em>) on 23 August 2023,
              making India the first nation to land in the high southern polar region. The
              <em>Vikram</em> lander deployed the <em>Pragyan</em> rover, which operated for
              ∼14 Earth days and traversed approximately 100 m before entering sleep mode.
            </p>

            <h3 className="paper-subsection-title">3.2 The Pragyan LIBS Instrument</h3>
            <p className="paper-p">
              The LIBS instrument is a miniaturised, low-mass design (~1.1 kg, &lt;1.2 W)
              employing a pulsed Nd:YAG laser in a near-vacuum environment where the plasma
              expands as an unconfined plume — qualitatively different from Martian LIBS.
              The operational sequence alternates <em>background</em> acquisitions (laser
              not fired, recording ambient signal) with <em>plasma</em> acquisitions (laser
              fired), enabling paired subtraction to isolate true LIBS emission.
            </p>

            <h3 className="paper-subsection-title">3.3 Level-1 Data Format: Wide-Table Structure</h3>
            <p className="paper-p">
              The L1 products use a wide-format tabular structure where 2,049 wavelength
              channels appear as column headers. The file reviewed here —{' '}
              <code>ch3_lib_002_20230825T104221_00_l1.csv</code> — contains eight rows
              (four background + four plasma acquisitions) yielding four usable pairs.
            </p>

            <div className="paper-table-wrap">
              <div className="paper-table-caption">
                <span className="paper-table-label">Table 1.</span> Column organisation of
                Chandrayaan-3 LIBS Level-1 CSV files.
              </div>
              <table className="paper-table">
                <thead>
                  <tr>
                    <th>Column Group</th>
                    <th>Count</th>
                    <th>Contents</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Metadata</td>
                    <td>6</td>
                    <td>Time, Measurement Count, Operation Mode, Measurement Type, Force Reset Status, Laser Fire Status</td>
                  </tr>
                  <tr>
                    <td>Wavelength channels</td>
                    <td>2,049</td>
                    <td>Column headers are wavelength values in nm (164.35–878.26); cells are intensity counts</td>
                  </tr>
                  <tr>
                    <td>Housekeeping</td>
                    <td>8</td>
                    <td>Delay Time, Integration Time, Number of Pulses, X-Factor, Laser Energy, Pump Current, PRR, On/Off Status</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h3 className="paper-subsection-title">3.4 Plasma and Background Flag Semantics</h3>
            <p className="paper-p">
              Background and plasma measurements are distinguished by two binary flag columns:
            </p>
            <ul className="paper-list">
              <li><strong>Force_Reset_Status:</strong> value 1 indicates a background (dark) acquisition; value 0 indicates a normal operational acquisition.</li>
              <li><strong>Laser_Fire_Status:</strong> value 0 for background (laser not fired); value 1 for plasma (laser fired).</li>
            </ul>
            <p className="paper-p">
              A valid plasma measurement satisfies <code>Force_Reset_Status = 0</code> AND{' '}
              <code>Laser_Fire_Status = 1</code>. A valid background measurement satisfies{' '}
              <code>Force_Reset_Status = 1</code> AND <code>Laser_Fire_Status = 0</code>.
            </p>
          </section>

          {/* ══════════════════════════════════════════
              4. ARCHITECTURE
          ══════════════════════════════════════════ */}
          <section id="architecture" className="paper-section">
            <div className="paper-section-number">Section 04</div>
            <h2 className="paper-section-title">LunarAtlas System Architecture</h2>

            <h3 className="paper-subsection-title">4.1 Design Principles</h3>
            <ol className="paper-ol">
              <li><strong>Single source of scientific truth.</strong> All domain logic — background pairing, subtraction, peak detection, NIST matching, downsampling — resides exclusively in the backend. The visualisation layer performs no scientific computation.</li>
              <li><strong>Reproducibility by design.</strong> Every ingestion step records its algorithm version, timestamp, and MD5 checksum. Any API response or figure can be traced to the exact L1 product and pipeline configuration.</li>
              <li><strong>Separation of concerns.</strong> Data persistence, scientific logic, and presentation are implemented in distinct, independently testable tiers.</li>
            </ol>

            <h3 className="paper-subsection-title">4.2 Three-Tier Architecture</h3>

            <div className="paper-hierarchy">
              <div className="paper-hier-node paper-hier-node--l0">
                <div className="paper-hier-label">Data Layer — PostgreSQL</div>
                <div className="paper-hier-detail">mission · instrument · observation · file_version · measurement · spectral_data</div>
              </div>
              <div className="paper-hier-connector" />
              <div className="paper-hier-node paper-hier-node--l1">
                <div className="paper-hier-label">Logic Layer — Python / FastAPI</div>
                <div className="paper-hier-detail">XML parsing · wide-to-long reshape · plasma/BG pairing · subtraction · MD5 · min-max · NIST</div>
              </div>
              <div className="paper-hier-connector" />
              <div className="paper-hier-node paper-hier-node--l2">
                <div className="paper-hier-label">Presentation Layer — React + amCharts</div>
                <div className="paper-hier-detail">viewport state · zoom/pan · chart rendering · pure consumer of backend data</div>
              </div>
            </div>

            <h3 className="paper-subsection-title">4.3 Database Schema Highlights</h3>

            <div className="paper-table-wrap">
              <div className="paper-table-caption">
                <span className="paper-table-label">Table 2.</span> Core LunarAtlas database tables and key columns.
              </div>
              <table className="paper-table">
                <thead>
                  <tr><th>Table</th><th>Key Columns</th></tr>
                </thead>
                <tbody>
                  {[
                    ['mission', 'id, name, agency, launch_date'],
                    ['instrument', 'id, mission_id, name, type'],
                    ['observation', 'id, instrument_id, start/stop_time, site'],
                    ['file_version', 'id, observation_id, filename, md5, ingested_at, algorithm_version'],
                    ['measurement', 'id, file_version_id, measurement_id, time_utc, laser_energy_v, n_pulses'],
                    ['spectral_data', 'id, measurement_id (FK), wavelength_nm, cleaned_intensity'],
                    ['nist_lines', 'id, element, ionisation, wavelength_nm, aki, ei/ek_ev'],
                  ].map(([tbl, cols]) => (
                    <tr key={tbl}>
                      <td><code>{tbl}</code></td>
                      <td style={{ fontSize: '11px' }}>{cols}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* ══════════════════════════════════════════
              5. CLEANING PIPELINE
          ══════════════════════════════════════════ */}
          <section id="processing" className="paper-section">
            <div className="paper-section-number">Section 05</div>
            <h2 className="paper-section-title">Data Processing and Cleaning Pipeline</h2>

            <h3 className="paper-subsection-title">5.1 Pipeline Overview</h3>
            <p className="paper-p">
              The cleaning pipeline consists of two primary Python modules:
            </p>
            <ul className="paper-list">
              <li><strong>batch_process_libs.py</strong> — reads L1 CSV files, validates column structure, reshapes wide tables into long-form records, pairs plasma/background shots, performs background subtraction, computes MD5 checksums, and writes cleaned spectra.</li>
              <li><strong>plot_libs_spectra.py</strong> — generates four diagnostic plot types: overlaid spectra, individual subplots, spectral heatmap, and peak comparison bar charts.</li>
            </ul>

            <h3 className="paper-subsection-title">5.2 Steps 1–3: XML Parsing, MD5, Wide-to-Long</h3>
            <p className="paper-p">
              The pipeline first parses the PDS4 XML label extracting logical identifiers,
              observation times, column definitions, and instrument context. Before any
              processing, an MD5 checksum of the source L1 file is recorded for corruption
              detection, traceability, and deduplication. The L1 CSV is then loaded into
              a pandas DataFrame; columns parseable as floating-point numbers are treated
              as 2,049 wavelength channels and <code>melt</code>-ed into long-form rows.
            </p>

            <h3 className="paper-subsection-title">5.3 Step 4–5: Plasma/Background Pairing and Subtraction</h3>

            <div className="paper-formula-block">
              <div className="paper-formula-label">Background Subtraction Formula</div>
              <div className="paper-formula">
                <em>I</em><sub>clean</sub>(λ) = max(0, &nbsp;
                <em>I</em><sub>plasma</sub>(λ) − <em>I</em><sub>background</sub>(λ))
              </div>
              <div className="paper-formula-note">
                The max(0, ·) clamp prevents physically meaningless negative intensities
                arising from shot-to-shot dark-frame variability. The fraction of negative
                samples before clamping is logged per pair as a quality diagnostic.
              </div>
            </div>

            <p className="paper-p">
              LunarAtlas deliberately adopts simple paired subtraction for three reasons:
              (i) the L1 product already provides temporally matched background acquisitions,
              making model-free subtraction physically grounded; (ii) reproducibility requires
              a deterministic, parameter-free operation — ALS and wavelet methods introduce
              tuneable smoothing parameters; and (iii) the infrastructure goal is a
              standardised cleaned tier — downstream users can apply additional filtering.
            </p>

            <h3 className="paper-subsection-title">5.4 The Measurement ID: Definition and Significance</h3>
            <p className="paper-p">
              The <strong>Measurement ID</strong> is a sequential integer — starting at 1
              for the first valid plasma–background pair — that uniquely identifies a single
              cleaned spectral record within a given L1 file. Without it, acquisitions sharing
              the same timestamp (which occurs when resolution is 1 second and multiple pulses
              are fired per second) cannot be distinguished. The ID is the primary axis in all
              visualisation plots, the foreign key linking spectral data to metadata, and
              the grouping key for per-shot peak detection and NIST matching.
            </p>

            <div className="paper-table-wrap">
              <div className="paper-table-caption">
                <span className="paper-table-label">Table 3.</span> Measurement ID characteristics for
                the archival Chandrayaan-3 LIBS observation.
              </div>
              <table className="paper-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Time (UTC)</th>
                    <th>Laser Energy (V)</th>
                    <th>Peak Intensity (cts)</th>
                    <th>Peak λ (nm)</th>
                    <th>% Negative</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ['1', '11:35:22', '3327', '321', '748.0', '22.5%'],
                    ['2', '11:35:22', '3280', '261', '283.1', '76.8%'],
                    ['3', '11:35:22', '3194', '684', '282.3', '0.5%'],
                    ['4', '11:35:23', '3202', '637', '282.7', '28.1%'],
                  ].map(row => (
                    <tr key={row[0]}>
                      {row.map((v, i) => <td key={i}>{v}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h3 className="paper-subsection-title">5.5 Diagnostic Figures</h3>

            {/* Figure 1 — All overlaid */}
            <Figure
              src="/figures/fig_01_all_overlaid.png"
              label="Figure 1. All Measurements Overlaid"
              caption="All four Measurement IDs overlaid for observation ch3_lib_002_20230825T104221_00_l1_cleaned. Cleaned intensity vs wavelength for IDs 1–4 (blue, orange, green, purple). ID 3 (green, E = 3194 V) dominates with the highest continuum; ID 2 (orange) shows the lowest intensity after background subtraction, consistent with efficient continuum removal."
              wide
            />

            {/* Figure 2 — Individual subplots */}
            <Figure
              src="/figures/fig_02_individual_subplots.png"
              label="Figure 2. Individual Spectra — Measurement IDs 1–4"
              caption="Individual cleaned spectra (top-left to bottom-right, IDs 1–4). Each panel annotates instrument parameters (laser energy, pulses, integration time, PRR). Grey dashed lines mark known emission lines. Structured Mg II emission near 280 nm and Ca II near 393 nm are clearly resolved in IDs 3 and 4."
              wide
            />

            {/* Figure 3 — Heatmap */}
            <Figure
              src="/figures/fig_03_heatmap.png"
              label="Figure 3. Spectral Heatmap (Measurement × Wavelength)"
              caption="Spectral heatmap for the four Measurement IDs (rows, bottom to top: IDs 1–4) versus wavelength channels. Colour encodes cleaned intensity (inferno scale). The bright vertical stripe near 282 nm (Mg II) is prominent in IDs 3 and 4; the 'black band' of ID 2 confirms near-zero cleaned intensity across almost the entire spectral range."
              wide
            />
          </section>

          {/* ══════════════════════════════════════════
              6. DOWNSAMPLING MATH
          ══════════════════════════════════════════ */}
          <section id="math" className="paper-section">
            <div className="paper-section-number">Section 06</div>
            <h2 className="paper-section-title">Mathematical Formulation of Adaptive Min–Max Downsampling</h2>

            <h3 className="paper-subsection-title">6.1 Zoom-Dependent Bucket Size</h3>
            <p className="paper-p">
              Let <em>S</em> = &#123;(λ<sub>i</sub>, <em>I</em><sub>i</sub>) : <em>i</em> = 1, …, <em>N</em>&#125; be a cleaned spectrum sorted by wavelength, with Δλ = λ<sub>max</sub> − λ<sub>min</sub>. For zoom level <em>z</em> ∈ ℤ<sub>≥0</sub>, the unconstrained bucket size is:
            </p>

            <div className="paper-formula-block">
              <div className="paper-formula-label">Equation 1 — Zoom-Dependent Bucket Size</div>
              <div className="paper-formula">
                b<sub>size</sub>(<em>z</em>) = Δλ / (BASE_BUCKETS × 2<sup><em>z</em></sup>)
              </div>
              <div className="paper-formula-note">
                With BASE_BUCKETS ≈ 1000, this gives approximately one bucket per screen pixel at z = 0. To prevent buckets smaller than the instrument's spectral resolution, a minimum bucket size b<sub>min</sub> (e.g., 0.01 nm) is enforced: b<sub>final</sub>(z) = max(b<sub>size</sub>(z), b<sub>min</sub>).
              </div>
            </div>

            <h3 className="paper-subsection-title">6.2 Zoom Saturation Threshold</h3>
            <p className="paper-p">
              The maximum zoom level at which b<sub>size</sub>(<em>z</em>) ≥ b<sub>min</sub>:
            </p>

            <div className="paper-formula-block">
              <div className="paper-formula-label">Equation 2 — Zoom Saturation (z_max)</div>
              <div className="paper-formula">
                z<sub>max</sub>(Δλ) = ⌊ log<sub>2</sub>( Δλ / (BASE_BUCKETS × b<sub>min</sub>) ) ⌋
              </div>
              <div className="paper-formula-note">
                For z &gt; z_max, bucket size clamps at b_min and the backend returns raw spectral samples in the requested window.
              </div>
            </div>

            <div className="paper-table-wrap">
              <div className="paper-table-caption">
                <span className="paper-table-label">Table 4.</span> Zoom saturation analysis.
                Parameters: BASE_BUCKETS = 1000, b_min = 0.01 nm.
              </div>
              <table className="paper-table">
                <thead>
                  <tr>
                    <th>Window</th>
                    <th>Δλ (nm)</th>
                    <th>z_max</th>
                    <th>b(z_max) (nm)</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ['Full Chandrayaan-3 band', '713.9', '6', '0.0112'],
                    ['100 nm window', '100.0', '3', '0.0125'],
                    ['10 nm window', '10.0', '0', '0.0100'],
                  ].map(row => (
                    <tr key={row[0]}>
                      {row.map((v, i) => <td key={i}>{v}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h3 className="paper-subsection-title">6.3 Min–Max Aggregation with Overlapping Boundaries</h3>
            <p className="paper-p">
              To prevent narrow peaks from being split across two adjacent buckets, each
              bucket <em>j</em> is extended by an overlap fraction o<sub>pct</sub> = 0.05 (5%).
              For all wavelength samples (λ<sub>i</sub>, <em>I</em><sub>i</sub>) falling
              within bucket <em>j</em>'s extended boundaries, the bucket records:
            </p>
            <ul className="paper-list">
              <li><em>I</em><sub>min</sub>(<em>j</em>) and λ<sub>min</sub>(<em>j</em>): the minimum intensity and its wavelength (preserves baseline structure)</li>
              <li><em>I</em><sub>max</sub>(<em>j</em>) and λ<sub>max</sub>(<em>j</em>): the maximum intensity and its wavelength (preserves emission-line peaks)</li>
              <li><em>N</em><sub>points</sub>(<em>j</em>): the number of contributing samples</li>
            </ul>

            <h3 className="paper-subsection-title">6.4 NIST-Guided Peak Insertion</h3>
            <p className="paper-p">
              After bucket aggregation, any NIST reference line whose nearest wavelength
              sample falls within a bucket but whose peak intensity is not the <em>I</em><sub>max</sub>
              of that bucket is explicitly inserted into the output as a single-point record.
              This guarantees 100% retention of reference lines regardless of bucket size.
            </p>
          </section>

          {/* ══════════════════════════════════════════
              7. API & WORKFLOW
          ══════════════════════════════════════════ */}
          <section id="api" className="paper-section">
            <div className="paper-section-number">Section 07</div>
            <h2 className="paper-section-title">API Design and Visualisation Workflow</h2>

            <h3 className="paper-subsection-title">7.1 Primary Spectral Endpoint</h3>

            <div className="paper-schema-diagram">
              <div className="paper-schema-title">Primary Endpoint</div>
              <pre className="paper-pre">{`GET /api/v1/spectral
  ?observation_id=<id>
  &min_wavelength=164.35
  &max_wavelength=878.26
  &zoom_level=0
  &include_nist=true

// Response JSON
{
  "metadata": {
    "observation_id": "...",
    "file_md5": "a7f3...",
    "algorithm_version": "v1.2.0"
  },
  "bucket_params": {
    "b_final_nm": 0.714,
    "n_buckets": 1000,
    "z_max": 6
  },
  "buckets": [
    {
      "lambda_min": 164.35, "i_min": 12.4,
      "lambda_max": 165.07, "i_max": 847.3,
      "n_points": 2,
      "nist_match": { "element": "Mg II", "confidence": 0.94 }
    },
    ...
  ]
}`}</pre>
            </div>

            <h3 className="paper-subsection-title">7.2 Progressive Loading Strategy</h3>
            <ol className="paper-ol">
              <li>On initial load, request the full-range spectrum at z = 0 for an overview.</li>
              <li>On each zoom/pan event, extract the new viewport [λ_a, λ_b], compute z_max(λ_b − λ_a), and request the appropriate zoom level.</li>
              <li>At z &gt; z_max, the backend returns raw samples, providing full spectral resolution inspection.</li>
              <li>Render bucket arrays as filled vertical ranges (I_min to I_max) with optional NIST line overlays.</li>
            </ol>

            <div className="paper-callout">
              <div className="paper-callout-label">Design Guarantee</div>
              <p>The visualisation is always scientifically faithful at every zoom level, with no client-side interpolation or approximation. The frontend performs zero scientific computation.</p>
            </div>
          </section>

          {/* ══════════════════════════════════════════
              8. RESULTS
          ══════════════════════════════════════════ */}
          <section id="results" className="paper-section">
            <div className="paper-section-number">Section 08</div>
            <h2 className="paper-section-title">Results and Experimental Validation</h2>

            <h3 className="paper-subsection-title">8.1 Baseline Suppression and Noise Behaviour</h3>
            <p className="paper-p">
              Analysing a representative 20 nm window (560–580 nm) of the Chandrayaan-3
              spectrum — expected to be relatively free of strong emission lines:
            </p>

            <div className="paper-formula-block">
              <div className="paper-formula-label">Cleaning Effectiveness Metrics (560–580 nm window)</div>
              <span className="paper-formula-eq">
                Raw: <em>Ī</em><sub>raw</sub> ≈ 1005 counts, σ<sub>raw</sub> ≈ 47 counts
              </span>
              <span className="paper-formula-eq">
                Cleaned: <em>Ī</em><sub>clean</sub> ≈ 141 counts, σ<sub>clean</sub> ≈ 184 counts
              </span>
              <span className="paper-formula-eq">
                Baseline suppression: <em>Ī</em><sub>raw</sub> / <em>Ī</em><sub>clean</sub> ≈ <strong>7.1×</strong>
              </span>
              <span className="paper-formula-eq">
                Variance increase: σ<sub>clean</sub> / σ<sub>raw</sub> ≈ <strong>3.9×</strong>
              </span>
            </div>

            <p className="paper-p">
              The cleaning pipeline strongly reduces the low-frequency continuum background
              while unavoidably increasing high-frequency residual noise — a direct
              consequence of subtracting two shot-noise-limited measurements. For peak
              detection, the baseline reduction is beneficial (increased peak-to-continuum
              ratio), requiring appropriate prominence thresholds.
            </p>

            <h3 className="paper-subsection-title">8.2 Inter-Measurement Variability and Peak Comparison</h3>

            {/* Figure 4 — Peak comparison */}
            <Figure
              src="/figures/fig_04_peak_comparison.png"
              label="Figure 4. Measurement Comparison — Peak Intensity and Laser Energy"
              caption="Left: peak cleaned intensity per Measurement ID, annotated with peak wavelength. IDs 3 and 4 reach peak intensities of 684 and 637 counts near 282–283 nm (Mg II). Right: laser energy (V) per Measurement ID. IDs 3 and 4 have the lowest laser energy settings yet the highest peak intensities, suggesting target coupling heterogeneities dominate over raw laser voltage."
            />

            <h3 className="paper-subsection-title">8.3 Emission Line Identification and Element Detection</h3>

            {/* Figure 5 — Element detection */}
            <Figure
              src="/figures/fig_05_element_detection.png"
              label="Figure 5. Mg/Ca Ratios and Element Detection Frequency"
              caption="Left: Mg/Ca intensity ratio per Measurement ID, with Apollo 16 highland (blue dashed) and Apollo 11 mare (red dashed) references. The ratio of 1.90 in ID 3 significantly exceeds the highland reference, indicating Mg-rich plasma-surface coupling in this acquisition. Right: element detection frequency across all four Measurement IDs. Mg and Ca are confirmed (≥2 measurements); Si is tentative (1 measurement); H, O, Fe, and Al are not detected."
            />

            <div className="paper-table-wrap">
              <div className="paper-table-caption">
                <span className="paper-table-label">Table 5.</span> Prominent LIBS emission lines
                identified in cleaned Chandrayaan-3 spectra.
              </div>
              <table className="paper-table">
                <thead>
                  <tr>
                    <th>Line</th>
                    <th>λ_NIST (nm)</th>
                    <th>Significance</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ['Mg II', '279.55 / 280.27', 'Dominant doublet; major regolith constituent'],
                    ['Si I', '288.16', 'Major silicate component'],
                    ['Ca II', '393.37 / 396.85', 'Strong lines; abundant in highlands'],
                    ['Fe I', '404.58', 'Iron abundance diagnostic'],
                    ['Ca I', '422.67', 'Neutral calcium complement'],
                    ['Mg I', '518.36', 'Neutral magnesium'],
                    ['Na I', '588.99', 'Sodium doublet'],
                    ['H I', '656.28', 'Hydrogen; potential hydration indicator'],
                    ['O I', '777.40', 'Oxygen; lunar regolith major component'],
                  ].map(row => (
                    <tr key={row[0]}>
                      {row.map((v, i) => <td key={i}>{v}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h3 className="paper-subsection-title">8.4 Performance Metrics</h3>
            <p className="paper-p">
              On a modest server configuration (Intel Core i7, 16 GB RAM, PostgreSQL 14 on SSD),
              end-to-end API response times remain below 500 ms for typical L1 spectra across
              all zoom levels. Payload sizes range from ∼10 to ∼400 kB under HTTP compression.
              The composite index on <code>(measurement_id, wavelength_nm)</code> provides
              approximately 15× speedup for spectral-range queries compared to a full table scan.
            </p>
          </section>

          {/* ══════════════════════════════════════════
              9. DISCUSSION
          ══════════════════════════════════════════ */}
          <section id="discussion" className="paper-section">
            <div className="paper-section-number">Section 09</div>
            <h2 className="paper-section-title">Discussion</h2>

            <h3 className="paper-subsection-title">9.1 The Reproducibility Gap in Planetary LIBS</h3>
            <p className="paper-p">
              The cleaning and normalisation of Chandrayaan-3 LIBS data is not merely a
              pre-processing convenience — it is a precondition for reproducible science.
              Published analyses of planetary LIBS data have consistently identified the
              lack of standardised, versioned preprocessing pipelines as a bottleneck for
              cross-team reproducibility. LunarAtlas addresses this by: formalising the
              wide-to-long reshaping as an explicit documented transformation; recording
              algorithm version and MD5 checksum with every processed file; and providing
              the pipeline as an open, documented Python module rather than a group-specific
              script.
            </p>

            <h3 className="paper-subsection-title">9.2 The Measurement ID as a Scientific Primitive</h3>
            <p className="paper-p">
              The Measurement ID may appear trivial — it is simply an integer — but it
              encodes a scientifically important unit of analysis. In LIBS, each acquisition
              (plasma shot) is an independent sample of surface composition under a specific
              set of instrument conditions. IDs 3 and 1 in Table 3 exemplify this: despite
              being acquired within the same 1-second window, their peak intensities differ
              by a factor of two and their negative-sample fractions differ from 0.5% to
              22.5%. Lumping these into a single averaged spectrum would be scientifically
              misleading.
            </p>

            <h3 className="paper-subsection-title">9.3 Limitations and Future Work</h3>
            <p className="paper-p">
              Current limitations include: manual quality assessment of cleaned spectra;
              absence of automated continuum fitting and multi-peak deconvolution; limited
              NIST coverage for minor and trace elements; and no real-time ingestion pipeline
              for ongoing missions. Future work will address these through ML-based quality
              scoring, integration of spectral fitting libraries (lmfit, pyspeckit), expanded
              reference databases, and streaming ingestion for near-real-time mission support.
              The design pattern generalises to Mars LIBS, Raman, XRF, imaging spectroscopy,
              and future lunar instruments (Chandrayaan-4, VIPER, CLPS payloads).
            </p>
          </section>

          {/* ══════════════════════════════════════════
              10. CONCLUSION
          ══════════════════════════════════════════ */}
          <section id="conclusion" className="paper-section">
            <div className="paper-section-number">Section 10</div>
            <h2 className="paper-section-title">Conclusion</h2>

            <p className="paper-p">
              LunarAtlas demonstrates how Chandrayaan-3 LIBS Level-1 data can be cleaned
              and structured into a reproducible, interactive, and scientifically rigorous
              spectral infrastructure. Key elements: a PDS4-aware ingestion pipeline;
              physically motivated plasma/background cleaning with quality diagnostics;
              the Measurement ID concept for per-shot traceability; a mathematically defined
              adaptive min–max downsampling algorithm with explicit zoom-saturation analysis;
              and a backend-centric API serving cleaned, NIST-validated spectra to thin
              visualization clients.
            </p>
            <p className="paper-p">
              The system achieves strong baseline suppression (∼7.1× continuum reduction),
              preserves emission-line features across all zoom levels, provides well-understood
              zoom behaviour, and maintains sub-500 ms response times. By treating spectral
              data, processing algorithms, and derived visualisations as tightly coupled,
              versioned artefacts, LunarAtlas provides both a working implementation for
              Chandrayaan-3 and a generalizable blueprint for future planetary spectroscopy
              data systems.
            </p>

            <h3 className="paper-subsection-title">Acknowledgments</h3>
            <p className="paper-p">
              We acknowledge the Indian Space Research Organisation (ISRO) for the public
              release of Chandrayaan-3 LIBS data through PDS4-compliant archives, and the
              National Institute of Standards and Technology (NIST) for maintaining the
              Atomic Spectra Database. We thank Aditya Bhardwaj (Scientist, ISRO NRSC,
              TEDxMAIT speaker) for public talks on India's space programme that helped shape
              LunarAtlas's broader vision. We acknowledge the open-source scientific Python
              ecosystem (NumPy, SciPy, Pandas, Astropy).
            </p>

            <div className="paper-author-contrib">
              <div className="paper-author-card">
                <div className="paper-author-name">Lovekesh Anand</div>
                <div className="paper-author-role">
                  Conceptualization · system architecture · algorithm development ·
                  database design · API implementation · data analysis · writing — original draft and editing
                </div>
              </div>
              <div className="paper-author-card">
                <div className="paper-author-name">Dua Saeed</div>
                <div className="paper-author-role">
                  Data processing pipeline · PDS4 parsing · NIST validation integration ·
                  visualization design · performance benchmarking · writing — review and editing
                </div>
              </div>
            </div>
          </section>

          {/* ══════════════════════════════════════════
              REFERENCES
          ══════════════════════════════════════════ */}
          <section id="references" className="paper-section">
            <div className="paper-section-number">References</div>
            <h2 className="paper-section-title">Bibliography</h2>

            <ol className="paper-bib-list">
              {[
                ['1', 'Cremers, D. A. and Radziemski, L. J. (2013). Handbook of Laser-Induced Breakdown Spectroscopy, 2nd ed. Wiley.'],
                ['2', 'Wiens, R. C. et al. (2012). The ChemCam Instrument Suite on the Mars Science Laboratory (MSL) Rover: Body Unit and Combined System Tests. Space Sci. Rev., 170, 167–227.'],
                ['3', 'Maurice, S. et al. (2012). The ChemCam Instrument Suite on the MSL Rover: Science Objectives and Mast Unit Description. Space Sci. Rev., 170, 95–166.'],
                ['4', 'Gasnault, O. et al. (2023). ChemCam operations and science at Jezero crater. J. Geophys. Res. Planets.'],
                ['5', 'Wiens, R. C. et al. (2020). The SuperCam Instrument Suite on the NASA Mars 2020 Rover. Space Sci. Rev., 216, 89.'],
                ['6', `Xu, W. et al. (2021). The MarSCoDe Instrument Suite on the Mars Rover of China's Tianwen-1 Mission. Space Sci. Rev., 217, 64.`],
                ['7', 'ISROCh3. Indian Space Research Organisation, Chandrayaan-3: Details. https://www.isro.gov.in/Chandrayaan3.html, accessed April 2026.'],
                ['8', `Laxmiprasad, A. S. et al. (2020). Pragyan rover's LIBS instrument: Design and calibration. Curr. Sci., 118, 577–585.`],
                ['9', 'Hughes, S. J., Raugh, A. C., and Crichton, T. L. (2018). Planetary Data System Standards Reference. NASA PDS, version 1.14.0.'],
                ['10', 'Sridhar, V. et al. (2025). Chandrayaan-3 LIBS L0 spectral analysis using Savitzky-Golay filtering and ALS baseline correction. Icarus (in review).'],
                ['11', 'Kramida, A., Ralchenko, Y., Reader, J., and NIST ASD Team (2023). NIST Atomic Spectra Database (version 5.11). NIST, Gaithersburg, MD.'],
                ['12', 'Steinarsson, S. (2013). Downsampling Time Series for Visual Representation. M.Sc. thesis, University of Iceland.'],
                ['13', 'Clegg, S. M. et al. (2017). Recalibration of the Mars Science Laboratory ChemCam instrument with an expanded geochemical database. Spectrochim. Acta Part B, 129, 64–85.'],
                ['14', 'Anderson, R. B. et al. (2022). Post-landing major element quantification using SuperCam laser-induced breakdown spectroscopy. Spectrochim. Acta Part B, 188, 106347.'],
                ['15', 'Knight, A. K. et al. (2000). Characterization of LIBS at low pressures and in vacuum. Spectrochim. Acta Part B, 55, 1085–1099.'],
              ].map(([num, text]) => (
                <li key={num} className="paper-bib-item">
                  <span className="paper-bib-num">[{num}]</span>
                  <span className="paper-bib-text">{text}</span>
                </li>
              ))}
            </ol>
          </section>

        </main>
      </div>

      <Footer />
    </div>
  );
}
