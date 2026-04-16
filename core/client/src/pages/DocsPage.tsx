import { useEffect, useRef, useState } from 'react';
import './DocsPage.css';

import libsRawCleaned from '../assets/libs_raw_vs_cleaned.png';
import dbSchemaDiagram from '../assets/db_schema_diagram.png';

const SECTIONS = [
  { id: 'intro',     label: 'Introduction' },
  { id: 'data',      label: 'Data Structure' },
  { id: 'pipeline',  label: 'Cleaning Pipeline' },
  { id: 'schema',    label: 'Database Model' },
  { id: 'downsampling', label: 'Peak Preservation' },
  { id: 'results',   label: 'Results & Validation' },
];

// ─── Sidebar nav with scrollspy ────────────────────────────────
function Sidebar({ activeId }: { activeId: string }) {
  function scrollTo(id: string) {
    const el = document.getElementById(`docs-${id}`);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  return (
    <aside className="docs-sidebar">
      <div className="docs-sidebar-title">Documentation</div>
      {SECTIONS.map(({ id, label }) => (
        <div key={id} className="docs-nav-group">
          <button
            className={`docs-nav-item${activeId === id ? ' active' : ''}`}
            onClick={() => scrollTo(id)}
          >
            {label}
          </button>
        </div>
      ))}

      <div style={{ marginTop: '32px', paddingRight: '20px' }}>
        <div style={{ fontSize: '9px', fontWeight: '700', letterSpacing: '1.5px', color: '#ccc', textTransform: 'uppercase', marginBottom: '8px' }}>
          Source
        </div>
        <div style={{ fontSize: '10px', color: '#bbb', lineHeight: 1.5 }}>
          Anand, L. & Saeed, D.<br />
          <em>LunarAtlas</em>, April 2026
        </div>
      </div>
    </aside>
  );
}

// ═══════════════════════════════════════════════════════════════
export default function DocsPage() {
  const [activeId, setActiveId] = useState('intro');
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    // Scroll to top on mount
    window.scrollTo(0, 0);

    const targets = SECTIONS.map(({ id }) => document.getElementById(`docs-${id}`)).filter(Boolean) as HTMLElement[];

    observerRef.current = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter(e => e.isIntersecting);
        if (visible.length > 0) {
          const top = visible.reduce((a, b) =>
            a.boundingClientRect.top < b.boundingClientRect.top ? a : b
          );
          const id = top.target.id.replace('docs-', '');
          setActiveId(id);
        }
      },
      { rootMargin: '-20% 0px -60% 0px', threshold: 0 }
    );

    targets.forEach(el => observerRef.current!.observe(el));
    return () => observerRef.current?.disconnect();
  }, []);

  return (
    <div className="docs-layout">
      <Sidebar activeId={activeId} />

      <main className="docs-content">

        {/* ══════════════════════════════════════════════
            1. INTRODUCTION
        ══════════════════════════════════════════════ */}
        <section id="docs-intro" className="docs-section">
          <div className="docs-section-tag">Section 1</div>
          <h2 className="docs-section-title">Introduction</h2>
          <hr className="docs-section-divider" />

          <div className="docs-body">
            <p>
              <strong>Laser-Induced Breakdown Spectroscopy (LIBS)</strong> is a versatile technique
              for <em>in situ</em> elemental analysis in planetary environments. By focusing a pulsed
              laser on a target, a transient plasma plume is created whose characteristic emission
              lines encode the elemental composition of the ablated material with no sample
              preparation and no contact requirement.
            </p>
            <p>
              The technique was first demonstrated in a planetary setting aboard NASA's Mars Science
              Laboratory rover <em>Curiosity</em> in 2012, where the <strong>ChemCam</strong>{' '}
              instrument acquired more than 930,000 single-shot spectra from 3,500 unique rock and
              regolith targets. The global scientific community subsequently adopted LIBS for
              <strong> SuperCam</strong> on <em>Perseverance</em> and <strong>MarSCoDe</strong>{' '}
              on China's Zhurong rover.
            </p>

            <div className="docs-subsection-title">Lunar LIBS — A New Frontier</div>
            <p>
              India's Chandrayaan-3 mission, which successfully landed near the lunar south pole
              on <strong>23 August 2023</strong>, marks a milestone: the <em>first deployment of
              LIBS on the Moon</em>. The Pragyan rover carried a miniaturised LIBS instrument
              alongside an Alpha Particle X-ray Spectrometer (APXS).
            </p>
            <p>
              The near-vacuum lunar environment introduces plasma dynamics fundamentally different
              from the ~7 mbar Martian atmosphere where ChemCam was optimised. In lunar vacuum,
              the LIBS plasma expands freely as an unconfined plume, producing distinct spectral
              characteristics that require careful calibration and cleaning.
            </p>

            <div className="docs-subsection-title">Lunar vs. Martian LIBS</div>
            <table className="docs-table">
              <thead>
                <tr>
                  <th>Property</th>
                  <th>Martian LIBS (ChemCam)</th>
                  <th>Lunar LIBS (Chandrayaan-3)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Atmospheric pressure</td>
                  <td>~7 mbar CO₂</td>
                  <td>&lt;10⁻⁶ mbar (near-vacuum)</td>
                </tr>
                <tr>
                  <td>Plasma expansion</td>
                  <td>Confined by atmosphere</td>
                  <td>Freely expanding plume</td>
                </tr>
                <tr>
                  <td>Signal confinement</td>
                  <td>Enhanced by CO₂ pressure</td>
                  <td>Reduced — no confinement</td>
                </tr>
                <tr>
                  <td>Spectral range</td>
                  <td>240–905 nm</td>
                  <td>164.35–878.26 nm</td>
                </tr>
                <tr>
                  <td>Channels per spectrum</td>
                  <td>~8,000–20,000</td>
                  <td>2,049 (L1 products)</td>
                </tr>
                <tr>
                  <td>Background subtraction</td>
                  <td>Wavelet/ALS continuum models</td>
                  <td>Mission-provided background acquisitions</td>
                </tr>
              </tbody>
            </table>

            <p>
              This comparison highlights why a dedicated data infrastructure — designed specifically
              for Chandrayaan-3's L1 products — is necessary. Generic planetary data tools do not
              account for the specific plasma/background interleaving scheme used by Pragyan's LIBS
              instrument.
            </p>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            2. DATA STRUCTURE
        ══════════════════════════════════════════════ */}
        <section id="docs-data" className="docs-section">
          <div className="docs-section-tag">Section 2</div>
          <h2 className="docs-section-title">Data Structure</h2>
          <hr className="docs-section-divider" />

          <div className="docs-body">
            <p>
              Chandrayaan-3 LIBS data are released as calibrated Level-1 (L1) products conforming
              to <strong>PDS4 (Planetary Data System version 4)</strong> standards. Each product
              consists of an XML label paired with a wide-format CSV table.
            </p>

            <div className="docs-subsection-title">The Wide-Table Challenge</div>
            <p>
              The central structural challenge of Chandrayaan-3 L1 data is that intensity values
              are stored in a <strong>wide format</strong>: the 2,049 wavelength channels appear
              directly as <em>column headers</em> (e.g., <code className="docs-code">164.35</code>,{' '}
              <code className="docs-code">164.74</code>, …, <code className="docs-code">878.26</code>).
            </p>

            <div className="docs-callout">
              <strong>Why this matters:</strong> A "wide" table with 2,049 wavelength columns is not
              amenable to SQL queries, background subtraction across all channels, or peak detection.
              LunarAtlas reshapes this into a "long" format where each row represents a single
              (measurement, wavelength, intensity) triple — enabling efficient relational operations.
            </div>

            <div className="docs-subsection-title">L1 CSV Column Organization</div>
            <table className="docs-table">
              <thead>
                <tr>
                  <th>Group</th>
                  <th>Count</th>
                  <th>Contents</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Metadata</strong></td>
                  <td>6</td>
                  <td>Time, Measurement Count, Operation Mode, Measurement Type, Force Reset Status, Laser Fire Status</td>
                </tr>
                <tr>
                  <td><strong>Wavelength Channels</strong></td>
                  <td>2,049</td>
                  <td>Column headers are wavelength values in nm (164.35 – 878.26); cells are intensity counts</td>
                </tr>
                <tr>
                  <td><strong>Housekeeping</strong></td>
                  <td>8</td>
                  <td>Delay Time, Integration Time, Number of Pulses, X-Factor, Laser Energy, Pump Current, PRR, On/Off Status</td>
                </tr>
              </tbody>
            </table>

            <div className="docs-subsection-title">Plasma vs. Background Flags</div>
            <p>
              Background and plasma measurements are distinguished by two binary flag columns that
              must both be checked for correct pairing:
            </p>
            <table className="docs-table">
              <thead>
                <tr>
                  <th>Measurement Type</th>
                  <th>Force_Reset_Status</th>
                  <th>Laser_Fire_Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Background (dark)</strong></td>
                  <td><code className="docs-code">1</code></td>
                  <td><code className="docs-code">0</code></td>
                </tr>
                <tr>
                  <td><strong>Plasma (LIBS shot)</strong></td>
                  <td><code className="docs-code">0</code></td>
                  <td><code className="docs-code">1</code></td>
                </tr>
              </tbody>
            </table>

            <div className="docs-subsection-title">Reshape: Wide → Long</div>
            <p>
              The pipeline identifies all columns parseable as floating-point wavelength values and
              reshapes each wide L1 row using a pandas <code className="docs-code">melt</code> operation
              into long-form records. Each row in the output represents a single
              (measurement, wavelength, intensity) triple with full metadata attached:
            </p>
            <div className="docs-field-list">
              {[
                { name: 'Measurement ID', type: 'integer', desc: 'Unique sequential identifier for this plasma–background pair' },
                { name: 'Time (UTC)', type: 'timestamp', desc: 'Acquisition time from PDS4 label' },
                { name: 'Measurement Count', type: 'integer', desc: 'Sequential count within the observation file' },
                { name: 'Wavelength (nm)', type: 'float', desc: 'Wavelength channel value, 164.35–878.26 nm' },
                { name: 'Raw Intensity', type: 'float', desc: 'Uncleaned intensity counts from the L1 product' },
                { name: 'Is Valid Plasma', type: 'boolean', desc: 'True if this row is a confirmed plasma shot' },
                { name: 'Is Background', type: 'boolean', desc: 'True if this row is a dark/background acquisition' },
                { name: 'Delay Time (μs)', type: 'float', desc: 'Laser delay time setting' },
                { name: 'Integration Time (μs)', type: 'float', desc: 'Detector integration window' },
                { name: 'Number of Pulses', type: 'integer', desc: 'Laser pulse count per acquisition' },
                { name: 'Laser Energy (V)', type: 'float', desc: 'Laser energy proxy — pump current voltage' },
              ].map(({ name, type, desc }) => (
                <div key={name} className="docs-field-row">
                  <div className="docs-field-name">{name}</div>
                  <div className="docs-field-type">{type}</div>
                  <div className="docs-field-desc">{desc}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            3. CLEANING PIPELINE
        ══════════════════════════════════════════════ */}
        <section id="docs-pipeline" className="docs-section">
          <div className="docs-section-tag">Section 3</div>
          <h2 className="docs-section-title">The Cleaning Pipeline</h2>
          <hr className="docs-section-divider" />

          <div className="docs-body">
            <p>
              The LunarAtlas cleaning pipeline transforms calibrated L1 tables into analysis-ready
              spectra through a deterministic, reproducible sequence of operations. Each step is
              version-tracked and bit-reproducible.
            </p>

            <div className="docs-subsection-title">Background Subtraction Formula</div>
            <p>
              For each background–plasma pair, cleaned intensity is computed channel-by-channel as:
            </p>
            <div className="docs-formula">
              I<sub>clean</sub>(λ) = max(0, I<sub>plasma</sub>(λ) − I<sub>background</sub>(λ))
            </div>
            <p>
              The <code className="docs-code">max(0, ·)</code> operator clamps negative values to
              zero. Negative differences arise when shot-to-shot plasma fluctuations cause a given
              wavelength channel to register lower counts than in the background acquisition —
              a physically non-informative result (negative photon count has no meaning).
            </p>

            <div className="docs-callout">
              <strong>Why simple subtraction?</strong> LunarAtlas deliberately uses paired
              subtraction rather than ALS or wavelet methods because: (i) the L1 product already
              provides temporally matched background acquisitions; (ii) reproducibility requires a
              deterministic, parameter-free operation; (iii) the infrastructure goal is a
              standardised cleaned tier — downstream users can apply additional filtering.
            </div>

            {/* Spectral figure */}
            <div className="docs-figure">
              <img src={libsRawCleaned} alt="Raw vs Cleaned LIBS spectrum comparison" />
              <div className="docs-figure-caption">
                <strong>Figure 1.</strong> Full-range Chandrayaan-3 LIBS spectrum. Raw L1 counts
                (blue) and cleaned intensity (orange) for a single plasma measurement spanning
                164.35–878.26 nm. Cleaning removes the continuum background while preserving
                emission features.
              </div>
            </div>

            <div className="docs-subsection-title">The Measurement ID</div>
            <p>
              The <strong>Measurement ID</strong> is the cornerstone identifier of the LunarAtlas
              data model. It is a sequential integer — starting at 1 for the first valid plasma–
              background pair — that uniquely identifies a single cleaned spectral record.
            </p>
            <p>
              Without a Measurement ID, rows in the long-form output would only be identifiable
              by wavelength and timestamp. Since all 2,094 per-wavelength rows of a single
              acquisition share the <em>same</em> timestamp, the Measurement ID is the only
              unambiguous grouping key.
            </p>
            <table className="docs-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Time (UTC)</th>
                  <th>Laser Energy (V)</th>
                  <th>Peak Intensity (cts)</th>
                  <th>% Negative (pre-clamp)</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>1</td><td>11:35:22</td><td>3327</td><td>321 @ 748.0 nm</td><td>22.5%</td></tr>
                <tr><td>2</td><td>11:35:22</td><td>3280</td><td>261 @ 283.1 nm</td><td>76.8%</td></tr>
                <tr><td>3</td><td>11:35:22</td><td>3194</td><td>684 @ 282.3 nm</td><td>12.1%</td></tr>
                <tr><td>4</td><td>11:35:23</td><td>3202</td><td>637 @ 282.7 nm</td><td>9.3%</td></tr>
              </tbody>
            </table>
            <p>
              IDs 1 and 2 share the same timestamp <code className="docs-code">11:35:22</code>,
              proving that the timestamp alone cannot distinguish measurements. The 76.8% negative
              fraction of ID 2 flags it as a near-null acquisition — variability completely hidden
              in bulk averaging.
            </p>

            <div className="docs-subsection-title">Pipeline Steps</div>
            <div className="docs-steps">
              {[
                { n: '01', title: 'XML Label Parsing', desc: 'Extract PDS4 logical identifier, timestamps, and column definitions from the XML label accompanying each L1 CSV file.' },
                { n: '02', title: 'MD5 Checksum', desc: 'Compute and record file integrity checksums before any processing — ensures full bit-level reproducibility.' },
                { n: '03', title: 'Wide-to-Long Reshape', desc: 'Melt 2,049 wavelength columns into long-form rows; each row becomes a single (measurement, wavelength, intensity) triple.' },
                { n: '04', title: 'Plasma / Background Separation', desc: 'Classify each row as a plasma shot or dark acquisition using the Force Reset and Laser Fire flag columns.' },
                { n: '05', title: 'Background Subtraction', desc: 'Apply the cleaning formula per wavelength channel: cleaned intensity = max(0, plasma − background).' },
                { n: '06', title: 'Quality Metric', desc: 'Compute the negative-fraction metric per acquisition to flag anomalous measurements before clamping.' },
                { n: '07', title: 'Metadata Association', desc: 'Attach 19 metadata columns — timing, laser parameters, flags — to every long-form spectral row.' },
                { n: '08', title: 'Database Insertion', desc: 'Write cleaned spectra into the spectral data table, keyed by Measurement ID, wavelength, and cleaned intensity.' },
              ].map(({ n, title, desc }) => (
                <div key={n} className="docs-step-row">
                  <div className="docs-step-num">{n}</div>
                  <div>
                    <div className="docs-step-title">{title}</div>
                    <div className="docs-step-desc">{desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            4. DATABASE MODEL
        ══════════════════════════════════════════════ */}
        <section id="docs-schema" className="docs-section">
          <div className="docs-section-tag">Section 4</div>
          <h2 className="docs-section-title">Database Model</h2>
          <hr className="docs-section-divider" />

          <div className="docs-body">
            <p>
              LunarAtlas maps PDS4 semantics into a normalized PostgreSQL relational schema that
              preserves the full scientific hierarchy and enables SQL-level spectral queries.
            </p>

            <div className="docs-subsection-title">Mission Hierarchy</div>
            <p>
              The schema follows the natural scientific chain from mission down to individual
              spectral samples:
            </p>

            {/* Schema diagram image */}
            <div className="docs-figure">
              <img src={dbSchemaDiagram} alt="LunarAtlas PostgreSQL schema hierarchy" />
              <div className="docs-figure-caption">
                <strong>Figure 2.</strong> LunarAtlas PostgreSQL schema hierarchy. Each level preserves
                provenance from PDS4 logical identifiers down to individual wavelength–intensity pairs.
              </div>
            </div>

            <div className="docs-subsection-title">Core Tables</div>
            <table className="docs-table">
              <thead>
                <tr>
                  <th>Table</th>
                  <th>Key Columns</th>
                  <th>Purpose</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code className="docs-code">mission</code></td>
                  <td>id, name, agency, launch date</td>
                  <td>Top-level mission context</td>
                </tr>
                <tr>
                  <td><code className="docs-code">instrument</code></td>
                  <td>id, mission id, name, type</td>
                  <td>Instrument registration</td>
                </tr>
                <tr>
                  <td><code className="docs-code">observation</code></td>
                  <td>id, instrument id, start / stop time, site</td>
                  <td>Observation context and timing</td>
                </tr>
                <tr>
                  <td><code className="docs-code">file_version</code></td>
                  <td>id, observation id, filename, <strong>md5</strong>, ingested at, algorithm version</td>
                  <td>File provenance and integrity</td>
                </tr>
                <tr>
                  <td><code className="docs-code">measurement</code></td>
                  <td>id, file version id, measurement id, time (UTC), laser energy, pulse count</td>
                  <td>Per-shot acquisition metadata</td>
                </tr>
                <tr>
                  <td><code className="docs-code">spectral_data</code></td>
                  <td>id, measurement id (FK), wavelength (nm), cleaned intensity</td>
                  <td>Long-form spectral samples (primary data)</td>
                </tr>
                <tr>
                  <td><code className="docs-code">nist_lines</code></td>
                  <td>id, element, ionisation, wavelength (nm), Aki</td>
                  <td>NIST Atomic Spectra Database reference</td>
                </tr>
              </tbody>
            </table>

            <div className="docs-subsection-title">Indexing Strategy</div>
            <div className="docs-code-block">{`-- Composite index for spectral range queries
CREATE INDEX idx_spectral_obs_wl
  ON spectral_data (measurement_id, wavelength_nm);

-- BRIN index for wavelength scans
CREATE INDEX idx_spectral_wl_brin
  ON spectral_data USING BRIN (wavelength_nm);

-- MD5 index for integrity checks
CREATE UNIQUE INDEX idx_file_version_md5
  ON file_version (md5);`}</div>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            5. PEAK PRESERVATION
        ══════════════════════════════════════════════ */}
        <section id="docs-downsampling" className="docs-section">
          <div className="docs-section-tag">Section 5</div>
          <h2 className="docs-section-title">Peak Preservation & Adaptive Downsampling</h2>
          <hr className="docs-section-divider" />

          <div className="docs-body">
            <div className="docs-subsection-title">Why Standard Methods Fail</div>
            <p>
              General-purpose time-series downsampling algorithms — mean aggregation, Largest
              Triangle Three Buckets (LTTB), Douglas-Peucker — are designed to preserve the
              <em>visual shape</em> of a curve. For LIBS spectroscopy, this is scientifically
              unacceptable: narrow emission lines (e.g., the Ca II doublet at 393–397 nm, or
              Mg II at 280 nm) may span only 1–3 wavelength channels.
            </p>
            <div className="docs-callout">
              <strong>LTTB's failure mode:</strong> The algorithm selects one representative point
              per visual bucket based on triangle area maximisation. A 2-channel-wide emission
              line in a bucket of 50 channels will be discarded if its triangle area is smaller
              than nearby baseline variation — even if that line is the primary diagnostic signal
              for elemental identification.
            </div>

            <div className="docs-subsection-title">Adaptive Min-Max Algorithm</div>
            <p>
              LunarAtlas uses a zoom-aware min-max downsampling approach. For zoom level{' '}
              <em>z</em> and wavelength span Δλ, the unconstrained bucket size is:
            </p>
            <div className="docs-formula">
              b<sub>size</sub>(z) = Δλ / (BASE_BUCKETS × 2<sup>z</sup>)
            </div>
            <p>
              With BASE_BUCKETS ≈ 1000, this gives roughly one bucket per screen pixel at z = 0.
              A minimum bucket size <code className="docs-code">b_min</code> (e.g., 0.01 nm,
              matching instrument resolution) is enforced:
            </p>
            <div className="docs-formula">
              b<sub>final</sub>(z) = max(b<sub>size</sub>(z), b<sub>min</sub>)
            </div>

            <div className="docs-subsection-title">Zoom Saturation</div>
            <p>
              Beyond a maximum unsaturated zoom level, bucket size clamps to{' '}
              <code className="docs-code">b_min</code> and the API returns <em>raw spectral samples</em>:
            </p>
            <div className="docs-formula">
              z<sub>max</sub>(Δλ) = ⌊log₂(Δλ / (BASE_BUCKETS × b<sub>min</sub>))⌋
            </div>
            <table className="docs-table">
              <thead>
                <tr>
                  <th>Window</th>
                  <th>Δλ (nm)</th>
                  <th>z_max</th>
                  <th>b_size(z_max) (nm)</th>
                  <th>Mode at z &gt; z_max</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Full Chandrayaan-3 band</td>
                  <td>713.9</td>
                  <td>6</td>
                  <td>0.0112</td>
                  <td>Raw data stream</td>
                </tr>
                <tr>
                  <td>100 nm window</td>
                  <td>100.0</td>
                  <td>3</td>
                  <td>0.0125</td>
                  <td>Raw data stream</td>
                </tr>
                <tr>
                  <td>10 nm window</td>
                  <td>10.0</td>
                  <td>0</td>
                  <td>0.0100</td>
                  <td>Raw data stream</td>
                </tr>
              </tbody>
            </table>

            <div className="docs-subsection-title">Overlapping Buckets & NIST Insertion</div>
            <p>
              To prevent narrow peaks from splitting across two adjacent bucket boundaries, each
              bucket is extended by a fractional overlap (5%):
            </p>
            <div className="docs-formula">
              λ<sub>start,ext</sub>(j) = λ<sub>start</sub>(j) − 0.05 × b<sub>final</sub>
            </div>
            <p>
              Any NIST reference line not already present as the bucket's maximum is inserted
              explicitly — guaranteeing <strong>100% retention of reference lines</strong> across
              all zoom levels.
            </p>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            6. RESULTS
        ══════════════════════════════════════════════ */}
        <section id="docs-results" className="docs-section">
          <div className="docs-section-tag">Section 6</div>
          <h2 className="docs-section-title">Results & Validation</h2>
          <hr className="docs-section-divider" />

          <div className="docs-body">
            <div className="docs-subsection-title">Baseline Suppression</div>
            <p>
              Analysis of the representative 560–580 nm window (line-poor region) from the archived
              Chandrayaan-3 measurement demonstrates the quantitative effect of cleaning:
            </p>
            <table className="docs-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Raw L1 Spectrum</th>
                  <th>Cleaned Spectrum</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Mean intensity (560–580 nm)</td>
                  <td>~1,005 counts</td>
                  <td>~141 counts</td>
                </tr>
                <tr>
                  <td>RMS fluctuation</td>
                  <td>~47 counts</td>
                  <td>~184 counts</td>
                </tr>
                <tr>
                  <td>Baseline suppression factor</td>
                  <td colSpan={2}>~7.1× (mean reduction)</td>
                </tr>
                <tr>
                  <td>High-frequency variance increase</td>
                  <td colSpan={2}>~3.9× (σ_clean / σ_raw)</td>
                </tr>
              </tbody>
            </table>
            <p>
              The cleaning strongly reduces low-frequency continuum background (~7×) while
              unavoidably increasing high-frequency residual noise. For peak detection,
              the first effect is <strong>beneficial</strong> — increased peak-to-continuum ratio.
              Peak detection applies 3σ prominence thresholds to mitigate the variance increase.
            </p>

            <div className="docs-subsection-title">Element Identification</div>
            <p>
              Cross-matching detected emission lines against NIST reference lines yields identification
              of the following elements in high-quality Chandrayaan-3 spectra:
            </p>
            <table className="docs-table">
              <thead>
                <tr>
                  <th>Element</th>
                  <th>Key Lines (nm)</th>
                  <th>Detection Status</th>
                </tr>
              </thead>
              <tbody>
                <tr><td><strong>Mg II</strong></td><td>279.6, 280.3, 284.0</td><td>Confirmed (&ge;2 measurements)</td></tr>
                <tr><td><strong>Ca II</strong></td><td>393.4, 396.8</td><td>Confirmed (&ge;2 measurements)</td></tr>
                <tr><td><strong>Si I</strong></td><td>288.2</td><td>Tentative (1 measurement)</td></tr>
                <tr><td><strong>Al I</strong></td><td>308.2, 309.3</td><td>Not confirmed</td></tr>
                <tr><td><strong>Fe I</strong></td><td>373.5, 374.9</td><td>Not confirmed</td></tr>
              </tbody>
            </table>

            <div className="docs-subsection-title">Performance</div>
            <div className="docs-callout">
              On a modest server configuration, end-to-end API response times (database query +
              min-max aggregation + JSON serialization) remain below <strong>~500 ms</strong> for
              typical L1 spectra across all zoom levels. Payload sizes range from 10–400 kB under
              compression. Min-max buckets reduce rendered points by <strong>1–2 orders of
              magnitude</strong> compared to raw spectra while preserving peak positions and amplitudes.
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}
