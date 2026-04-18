import { useEffect, useRef, useState } from 'react';

import libsRawCleaned  from '../assets/libs_raw_vs_cleaned.png';
import dbSchemaDiagram from '../assets/db_schema_diagram.png';

// ─────────────────────────────────────────────────────────────
// Tailwind class constants — defined as complete strings so that
// Tailwind JIT detects every class during source scanning.
// ─────────────────────────────────────────────────────────────
const SEC     = 'mb-[72px] scroll-mt-20';
const SEC_TAG = 'text-[9px] font-bold tracking-[2.5px] text-ink-muted uppercase mb-[10px]';
const SEC_H2  = 'text-[22px] font-bold text-ink m-0 mb-5 tracking-[-0.3px] leading-tight';
const SEC_HR  = 'border-0 border-t border-[#eee] m-0 mb-7';
const BODY    = 'text-[13px] text-[#444] leading-[1.78] tracking-[0.2px] [&_p]:mb-4 [&_strong]:text-ink [&_strong]:font-bold [&_em]:italic [&_em]:text-[#555]';
const SUB_H   = 'text-[14px] font-bold text-ink mt-8 mb-[10px]';
const FORMULA = 'bg-[#f7f7f7] border border-border px-5 py-4 my-5 font-mono text-[13px] text-ink overflow-x-auto tracking-[0.3px] border-l-[3px] border-l-ink';
const CALLOUT = 'bg-canvas-alt border border-border px-[18px] py-[14px] my-5 text-[12px] text-[#555] leading-[1.65] border-l-[3px] border-l-[#888] [&_strong]:text-ink';
const CODE    = 'bg-[#f4f4f4] border border-border px-[6px] py-[2px] font-mono text-[11.5px] text-[#333] tracking-[0.1px]';
const CODEBLK = 'bg-[#f7f7f7] border border-border px-5 py-4 my-4 font-mono text-[12px] text-[#222] overflow-x-auto leading-[1.6] whitespace-pre';
const FIGURE  = 'my-7 border border-border';
const FIG_CAP = 'px-[14px] py-[10px] text-[11px] text-[#888] border-t border-[#eee] leading-[1.5] bg-canvas-alt [&_strong]:text-[#555] [&_strong]:font-bold';
const TABLE   = 'w-full border-collapse my-5 text-[12px]';
const TBODY   = '[&>tr:last-child>td]:border-b-0';
const TH      = 'text-left text-[9px] font-bold tracking-[1.5px] text-[#888] uppercase px-[14px] py-2 border-b border-[#ddd] bg-canvas-alt';
const TD      = 'px-[14px] py-[10px] border-b border-[#f0f0f0] text-[#444] leading-[1.5] align-top';
const TD_CODE = 'font-mono text-[11px] text-[#333] bg-[#f4f4f4] border border-border px-1 py-px';
const FLIST   = 'border border-border my-5 overflow-hidden';
const FROW    = 'grid grid-cols-[160px_74px_1fr] gap-x-3 px-4 py-[11px] border-b border-[#f0f0f0] items-center text-[12.5px] last:border-b-0 hover:bg-canvas-alt';
const FNAME   = 'font-semibold text-ink text-[12.5px]';
const FTYPE   = 'font-mono text-[11px] text-[#888] bg-[#f4f4f4] px-[6px] py-[2px] rounded-sm self-center whitespace-nowrap w-fit';
const FDESC   = 'text-[#555] text-[12.5px] leading-[1.55] pl-3';
const STEPS   = 'my-5 flex flex-col border border-border overflow-hidden';
const SROW    = 'flex gap-5 items-start px-[18px] py-[14px] border-b border-[#f0f0f0] last:border-b-0 hover:bg-canvas-alt';
const SNUM    = 'text-[10px] font-bold text-ink-muted tracking-[1px] shrink-0 pt-[2px] min-w-6';
const STITLE  = 'text-[13px] font-semibold text-ink mb-[3px]';
const SDESC   = 'text-[12.5px] text-[#555] leading-[1.6]';

const SECTIONS = [
  { id: 'intro',       label: 'Introduction'     },
  { id: 'data',        label: 'Data Structure'   },
  { id: 'pipeline',    label: 'Cleaning Pipeline' },
  { id: 'schema',      label: 'Database Model'   },
  { id: 'downsampling', label: 'Peak Preservation' },
  { id: 'results',     label: 'Results & Validation' },
];

// ─── Sidebar nav with scrollspy ─────────────────────────────
function Sidebar({ activeId }: { activeId: string }) {
  function scrollTo(id: string) {
    const el = document.getElementById(`docs-${id}`);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  return (
    <aside className="w-[220px] shrink-0 sticky top-[61px] h-[calc(100vh-61px)] overflow-y-auto border-r border-border pt-10 pb-10 pl-8 box-border">
      <div className="text-[9px] font-bold tracking-[2px] text-ink-muted uppercase mb-5 pr-5">
        Documentation
      </div>

      {SECTIONS.map(({ id, label }) => (
        <div key={id} className="mb-[6px]">
          <button
            className={`block text-[11.5px] py-[6px] border-0 border-l-2 pl-3 -ml-[14px] tracking-[0.3px] transition-colors duration-150 cursor-pointer bg-transparent font-sans text-left w-full ${
              activeId === id
                ? 'text-ink font-bold border-l-ink'
                : 'text-[#888] font-normal border-l-transparent hover:text-ink'
            }`}
            onClick={() => scrollTo(id)}
          >
            {label}
          </button>
        </div>
      ))}

      <div className="mt-8 pr-5">
        <div className="text-[9px] font-bold tracking-[1.5px] text-[#ccc] uppercase mb-2">
          Source
        </div>
        <div className="text-[10px] text-ink-muted leading-[1.5]">
          Anand, L. &amp; Saeed, D.<br />
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
    window.scrollTo(0, 0);

    const targets = SECTIONS
      .map(({ id }) => document.getElementById(`docs-${id}`))
      .filter(Boolean) as HTMLElement[];

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
    <div className="flex items-start max-w-[1400px] mx-auto min-h-[calc(100vh-61px)]">
      <Sidebar activeId={activeId} />

      <main className="flex-1 px-14 pt-[52px] pb-20 min-w-0 max-w-[860px]">

        {/* ══════════════════════════════════════════════
            1. INTRODUCTION
        ══════════════════════════════════════════════ */}
        <section id="docs-intro" className={SEC}>
          <div className={SEC_TAG}>Section 1</div>
          <h2 className={SEC_H2}>Introduction</h2>
          <hr className={SEC_HR} />

          <div className={BODY}>
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

            <div className={SUB_H}>Lunar LIBS — A New Frontier</div>
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

            <div className={SUB_H}>Lunar vs. Martian LIBS</div>
            <table className={TABLE}>
              <thead>
                <tr>
                  <th className={TH}>Property</th>
                  <th className={TH}>Martian LIBS (ChemCam)</th>
                  <th className={TH}>Lunar LIBS (Chandrayaan-3)</th>
                </tr>
              </thead>
              <tbody className={TBODY}>
                <tr>
                  <td className={TD}>Atmospheric pressure</td>
                  <td className={TD}>~7 mbar CO₂</td>
                  <td className={TD}>&lt;10⁻⁶ mbar (near-vacuum)</td>
                </tr>
                <tr>
                  <td className={TD}>Plasma expansion</td>
                  <td className={TD}>Confined by atmosphere</td>
                  <td className={TD}>Freely expanding plume</td>
                </tr>
                <tr>
                  <td className={TD}>Signal confinement</td>
                  <td className={TD}>Enhanced by CO₂ pressure</td>
                  <td className={TD}>Reduced — no confinement</td>
                </tr>
                <tr>
                  <td className={TD}>Spectral range</td>
                  <td className={TD}>240–905 nm</td>
                  <td className={TD}>164.35–878.26 nm</td>
                </tr>
                <tr>
                  <td className={TD}>Channels per spectrum</td>
                  <td className={TD}>~8,000–20,000</td>
                  <td className={TD}>2,049 (L1 products)</td>
                </tr>
                <tr>
                  <td className={TD}>Background subtraction</td>
                  <td className={TD}>Wavelet/ALS continuum models</td>
                  <td className={TD}>Mission-provided background acquisitions</td>
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
        <section id="docs-data" className={SEC}>
          <div className={SEC_TAG}>Section 2</div>
          <h2 className={SEC_H2}>Data Structure</h2>
          <hr className={SEC_HR} />

          <div className={BODY}>
            <p>
              Chandrayaan-3 LIBS data are released as calibrated Level-1 (L1) products conforming
              to <strong>PDS4 (Planetary Data System version 4)</strong> standards. Each product
              consists of an XML label paired with a wide-format CSV table.
            </p>

            <div className={SUB_H}>The Wide-Table Challenge</div>
            <p>
              The central structural challenge of Chandrayaan-3 L1 data is that intensity values
              are stored in a <strong>wide format</strong>: the 2,049 wavelength channels appear
              directly as <em>column headers</em> (e.g., <code className={CODE}>164.35</code>,{' '}
              <code className={CODE}>164.74</code>, …, <code className={CODE}>878.26</code>).
            </p>

            <div className={CALLOUT}>
              <strong>Why this matters:</strong> A "wide" table with 2,049 wavelength columns is not
              amenable to SQL queries, background subtraction across all channels, or peak detection.
              LunarAtlas reshapes this into a "long" format where each row represents a single
              (measurement, wavelength, intensity) triple — enabling efficient relational operations.
            </div>

            <div className={SUB_H}>L1 CSV Column Organization</div>
            <table className={TABLE}>
              <thead>
                <tr>
                  <th className={TH}>Group</th>
                  <th className={TH}>Count</th>
                  <th className={TH}>Contents</th>
                </tr>
              </thead>
              <tbody className={TBODY}>
                <tr>
                  <td className={TD}><strong>Metadata</strong></td>
                  <td className={TD}>6</td>
                  <td className={TD}>Time, Measurement Count, Operation Mode, Measurement Type, Force Reset Status, Laser Fire Status</td>
                </tr>
                <tr>
                  <td className={TD}><strong>Wavelength Channels</strong></td>
                  <td className={TD}>2,049</td>
                  <td className={TD}>Column headers are wavelength values in nm (164.35 – 878.26); cells are intensity counts</td>
                </tr>
                <tr>
                  <td className={TD}><strong>Housekeeping</strong></td>
                  <td className={TD}>8</td>
                  <td className={TD}>Delay Time, Integration Time, Number of Pulses, X-Factor, Laser Energy, Pump Current, PRR, On/Off Status</td>
                </tr>
              </tbody>
            </table>

            <div className={SUB_H}>Plasma vs. Background Flags</div>
            <p>
              Background and plasma measurements are distinguished by two binary flag columns that
              must both be checked for correct pairing:
            </p>
            <table className={TABLE}>
              <thead>
                <tr>
                  <th className={TH}>Measurement Type</th>
                  <th className={TH}>Force_Reset_Status</th>
                  <th className={TH}>Laser_Fire_Status</th>
                </tr>
              </thead>
              <tbody className={TBODY}>
                <tr>
                  <td className={TD}><strong>Background (dark)</strong></td>
                  <td className={TD}><code className={TD_CODE}>1</code></td>
                  <td className={TD}><code className={TD_CODE}>0</code></td>
                </tr>
                <tr>
                  <td className={TD}><strong>Plasma (LIBS shot)</strong></td>
                  <td className={TD}><code className={TD_CODE}>0</code></td>
                  <td className={TD}><code className={TD_CODE}>1</code></td>
                </tr>
              </tbody>
            </table>

            <div className={SUB_H}>Reshape: Wide → Long</div>
            <p>
              The pipeline identifies all columns parseable as floating-point wavelength values and
              reshapes each wide L1 row using a pandas <code className={CODE}>melt</code> operation
              into long-form records. Each row in the output represents a single
              (measurement, wavelength, intensity) triple with full metadata attached:
            </p>
            <div className={FLIST}>
              {[
                { name: 'Measurement ID',     type: 'integer',   desc: 'Unique sequential identifier for this plasma–background pair' },
                { name: 'Time (UTC)',          type: 'timestamp', desc: 'Acquisition time from PDS4 label' },
                { name: 'Measurement Count',   type: 'integer',   desc: 'Sequential count within the observation file' },
                { name: 'Wavelength (nm)',     type: 'float',     desc: 'Wavelength channel value, 164.35–878.26 nm' },
                { name: 'Raw Intensity',       type: 'float',     desc: 'Uncleaned intensity counts from the L1 product' },
                { name: 'Is Valid Plasma',     type: 'boolean',   desc: 'True if this row is a confirmed plasma shot' },
                { name: 'Is Background',       type: 'boolean',   desc: 'True if this row is a dark/background acquisition' },
                { name: 'Delay Time (μs)',     type: 'float',     desc: 'Laser delay time setting' },
                { name: 'Integration Time (μs)', type: 'float',  desc: 'Detector integration window' },
                { name: 'Number of Pulses',    type: 'integer',   desc: 'Laser pulse count per acquisition' },
                { name: 'Laser Energy (V)',    type: 'float',     desc: 'Laser energy proxy — pump current voltage' },
              ].map(({ name, type, desc }) => (
                <div key={name} className={FROW}>
                  <div className={FNAME}>{name}</div>
                  <div className={FTYPE}>{type}</div>
                  <div className={FDESC}>{desc}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            3. CLEANING PIPELINE
        ══════════════════════════════════════════════ */}
        <section id="docs-pipeline" className={SEC}>
          <div className={SEC_TAG}>Section 3</div>
          <h2 className={SEC_H2}>The Cleaning Pipeline</h2>
          <hr className={SEC_HR} />

          <div className={BODY}>
            <p>
              The LunarAtlas cleaning pipeline transforms calibrated L1 tables into analysis-ready
              spectra through a deterministic, reproducible sequence of operations. Each step is
              version-tracked and bit-reproducible.
            </p>

            <div className={SUB_H}>Background Subtraction Formula</div>
            <p>For each background–plasma pair, cleaned intensity is computed channel-by-channel as:</p>
            <div className={FORMULA}>
              I<sub>clean</sub>(λ) = max(0, I<sub>plasma</sub>(λ) − I<sub>background</sub>(λ))
            </div>
            <p>
              The <code className={CODE}>max(0, ·)</code> operator clamps negative values to
              zero. Negative differences arise when shot-to-shot plasma fluctuations cause a given
              wavelength channel to register lower counts than in the background acquisition —
              a physically non-informative result (negative photon count has no meaning).
            </p>

            <div className={CALLOUT}>
              <strong>Why simple subtraction?</strong> LunarAtlas deliberately uses paired
              subtraction rather than ALS or wavelet methods because: (i) the L1 product already
              provides temporally matched background acquisitions; (ii) reproducibility requires a
              deterministic, parameter-free operation; (iii) the infrastructure goal is a
              standardised cleaned tier — downstream users can apply additional filtering.
            </div>

            {/* Spectral figure */}
            <div className={FIGURE}>
              <img src={libsRawCleaned} alt="Raw vs Cleaned LIBS spectrum comparison" className="w-full block" />
              <div className={FIG_CAP}>
                <strong>Figure 1.</strong> Full-range Chandrayaan-3 LIBS spectrum. Raw L1 counts
                (blue) and cleaned intensity (orange) for a single plasma measurement spanning
                164.35–878.26 nm. Cleaning removes the continuum background while preserving
                emission features.
              </div>
            </div>

            <div className={SUB_H}>The Measurement ID</div>
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
            <table className={TABLE}>
              <thead>
                <tr>
                  <th className={TH}>ID</th>
                  <th className={TH}>Time (UTC)</th>
                  <th className={TH}>Laser Energy (V)</th>
                  <th className={TH}>Peak Intensity (cts)</th>
                  <th className={TH}>% Negative (pre-clamp)</th>
                </tr>
              </thead>
              <tbody className={TBODY}>
                <tr><td className={TD}>1</td><td className={TD}>11:35:22</td><td className={TD}>3327</td><td className={TD}>321 @ 748.0 nm</td><td className={TD}>22.5%</td></tr>
                <tr><td className={TD}>2</td><td className={TD}>11:35:22</td><td className={TD}>3280</td><td className={TD}>261 @ 283.1 nm</td><td className={TD}>76.8%</td></tr>
                <tr><td className={TD}>3</td><td className={TD}>11:35:22</td><td className={TD}>3194</td><td className={TD}>684 @ 282.3 nm</td><td className={TD}>12.1%</td></tr>
                <tr><td className={TD}>4</td><td className={TD}>11:35:23</td><td className={TD}>3202</td><td className={TD}>637 @ 282.7 nm</td><td className={TD}>9.3%</td></tr>
              </tbody>
            </table>
            <p>
              IDs 1 and 2 share the same timestamp <code className={CODE}>11:35:22</code>,
              proving that the timestamp alone cannot distinguish measurements. The 76.8% negative
              fraction of ID 2 flags it as a near-null acquisition — variability completely hidden
              in bulk averaging.
            </p>

            <div className={SUB_H}>Pipeline Steps</div>
            <div className={STEPS}>
              {[
                { n: '01', title: 'XML Label Parsing',        desc: 'Extract PDS4 logical identifier, timestamps, and column definitions from the XML label accompanying each L1 CSV file.' },
                { n: '02', title: 'MD5 Checksum',             desc: 'Compute and record file integrity checksums before any processing — ensures full bit-level reproducibility.' },
                { n: '03', title: 'Wide-to-Long Reshape',     desc: 'Melt 2,049 wavelength columns into long-form rows; each row becomes a single (measurement, wavelength, intensity) triple.' },
                { n: '04', title: 'Plasma / Background Separation', desc: 'Classify each row as a plasma shot or dark acquisition using the Force Reset and Laser Fire flag columns.' },
                { n: '05', title: 'Background Subtraction',   desc: 'Apply the cleaning formula per wavelength channel: cleaned intensity = max(0, plasma − background).' },
                { n: '06', title: 'Quality Metric',           desc: 'Compute the negative-fraction metric per acquisition to flag anomalous measurements before clamping.' },
                { n: '07', title: 'Metadata Association',     desc: 'Attach 19 metadata columns — timing, laser parameters, flags — to every long-form spectral row.' },
                { n: '08', title: 'Database Insertion',       desc: 'Write cleaned spectra into the spectral data table, keyed by Measurement ID, wavelength, and cleaned intensity.' },
              ].map(({ n, title, desc }) => (
                <div key={n} className={SROW}>
                  <div className={SNUM}>{n}</div>
                  <div>
                    <div className={STITLE}>{title}</div>
                    <div className={SDESC}>{desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            4. DATABASE MODEL
        ══════════════════════════════════════════════ */}
        <section id="docs-schema" className={SEC}>
          <div className={SEC_TAG}>Section 4</div>
          <h2 className={SEC_H2}>Database Model</h2>
          <hr className={SEC_HR} />

          <div className={BODY}>
            <p>
              LunarAtlas maps PDS4 semantics into a normalized PostgreSQL relational schema that
              preserves the full scientific hierarchy and enables SQL-level spectral queries.
            </p>

            <div className={SUB_H}>Mission Hierarchy</div>
            <p>
              The schema follows the natural scientific chain from mission down to individual
              spectral samples:
            </p>

            {/* Schema diagram image */}
            <div className={FIGURE}>
              <img src={dbSchemaDiagram} alt="LunarAtlas PostgreSQL schema hierarchy" className="w-full block" />
              <div className={FIG_CAP}>
                <strong>Figure 2.</strong> LunarAtlas PostgreSQL schema hierarchy. Each level preserves
                provenance from PDS4 logical identifiers down to individual wavelength–intensity pairs.
              </div>
            </div>

            <div className={SUB_H}>Core Tables</div>
            <table className={TABLE}>
              <thead>
                <tr>
                  <th className={TH}>Table</th>
                  <th className={TH}>Key Columns</th>
                  <th className={TH}>Purpose</th>
                </tr>
              </thead>
              <tbody className={TBODY}>
                <tr>
                  <td className={TD}><code className={TD_CODE}>mission</code></td>
                  <td className={TD}>id, name, agency, launch date</td>
                  <td className={TD}>Top-level mission context</td>
                </tr>
                <tr>
                  <td className={TD}><code className={TD_CODE}>instrument</code></td>
                  <td className={TD}>id, mission id, name, type</td>
                  <td className={TD}>Instrument registration</td>
                </tr>
                <tr>
                  <td className={TD}><code className={TD_CODE}>observation</code></td>
                  <td className={TD}>id, instrument id, start / stop time, site</td>
                  <td className={TD}>Observation context and timing</td>
                </tr>
                <tr>
                  <td className={TD}><code className={TD_CODE}>file_version</code></td>
                  <td className={TD}>id, observation id, filename, <strong>md5</strong>, ingested at, algorithm version</td>
                  <td className={TD}>File provenance and integrity</td>
                </tr>
                <tr>
                  <td className={TD}><code className={TD_CODE}>measurement</code></td>
                  <td className={TD}>id, file version id, measurement id, time (UTC), laser energy, pulse count</td>
                  <td className={TD}>Per-shot acquisition metadata</td>
                </tr>
                <tr>
                  <td className={TD}><code className={TD_CODE}>spectral_data</code></td>
                  <td className={TD}>id, measurement id (FK), wavelength (nm), cleaned intensity</td>
                  <td className={TD}>Long-form spectral samples (primary data)</td>
                </tr>
                <tr>
                  <td className={TD}><code className={TD_CODE}>nist_lines</code></td>
                  <td className={TD}>id, element, ionisation, wavelength (nm), Aki</td>
                  <td className={TD}>NIST Atomic Spectra Database reference</td>
                </tr>
              </tbody>
            </table>

            <div className={SUB_H}>Indexing Strategy</div>
            <div className={CODEBLK}>{`-- Composite index for spectral range queries
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
        <section id="docs-downsampling" className={SEC}>
          <div className={SEC_TAG}>Section 5</div>
          <h2 className={SEC_H2}>Peak Preservation &amp; Adaptive Downsampling</h2>
          <hr className={SEC_HR} />

          <div className={BODY}>
            <div className={SUB_H}>Why Standard Methods Fail</div>
            <p>
              General-purpose time-series downsampling algorithms — mean aggregation, Largest
              Triangle Three Buckets (LTTB), Douglas-Peucker — are designed to preserve the
              <em>visual shape</em> of a curve. For LIBS spectroscopy, this is scientifically
              unacceptable: narrow emission lines (e.g., the Ca II doublet at 393–397 nm, or
              Mg II at 280 nm) may span only 1–3 wavelength channels.
            </p>
            <div className={CALLOUT}>
              <strong>LTTB's failure mode:</strong> The algorithm selects one representative point
              per visual bucket based on triangle area maximisation. A 2-channel-wide emission
              line in a bucket of 50 channels will be discarded if its triangle area is smaller
              than nearby baseline variation — even if that line is the primary diagnostic signal
              for elemental identification.
            </div>

            <div className={SUB_H}>Adaptive Min-Max Algorithm</div>
            <p>
              LunarAtlas uses a zoom-aware min-max downsampling approach. For zoom level{' '}
              <em>z</em> and wavelength span Δλ, the unconstrained bucket size is:
            </p>
            <div className={FORMULA}>
              b<sub>size</sub>(z) = Δλ / (BASE_BUCKETS × 2<sup>z</sup>)
            </div>
            <p>
              With BASE_BUCKETS ≈ 1000, this gives roughly one bucket per screen pixel at z = 0.
              A minimum bucket size <code className={CODE}>b_min</code> (e.g., 0.01 nm,
              matching instrument resolution) is enforced:
            </p>
            <div className={FORMULA}>
              b<sub>final</sub>(z) = max(b<sub>size</sub>(z), b<sub>min</sub>)
            </div>

            <div className={SUB_H}>Zoom Saturation</div>
            <p>
              Beyond a maximum unsaturated zoom level, bucket size clamps to{' '}
              <code className={CODE}>b_min</code> and the API returns <em>raw spectral samples</em>:
            </p>
            <div className={FORMULA}>
              z<sub>max</sub>(Δλ) = ⌊log₂(Δλ / (BASE_BUCKETS × b<sub>min</sub>))⌋
            </div>
            <table className={TABLE}>
              <thead>
                <tr>
                  <th className={TH}>Window</th>
                  <th className={TH}>Δλ (nm)</th>
                  <th className={TH}>z_max</th>
                  <th className={TH}>b_size(z_max) (nm)</th>
                  <th className={TH}>Mode at z &gt; z_max</th>
                </tr>
              </thead>
              <tbody className={TBODY}>
                <tr>
                  <td className={TD}>Full Chandrayaan-3 band</td>
                  <td className={TD}>713.9</td>
                  <td className={TD}>6</td>
                  <td className={TD}>0.0112</td>
                  <td className={TD}>Raw data stream</td>
                </tr>
                <tr>
                  <td className={TD}>100 nm window</td>
                  <td className={TD}>100.0</td>
                  <td className={TD}>3</td>
                  <td className={TD}>0.0125</td>
                  <td className={TD}>Raw data stream</td>
                </tr>
                <tr>
                  <td className={TD}>10 nm window</td>
                  <td className={TD}>10.0</td>
                  <td className={TD}>0</td>
                  <td className={TD}>0.0100</td>
                  <td className={TD}>Raw data stream</td>
                </tr>
              </tbody>
            </table>

            <div className={SUB_H}>Overlapping Buckets &amp; NIST Insertion</div>
            <p>
              To prevent narrow peaks from splitting across two adjacent bucket boundaries, each
              bucket is extended by a fractional overlap (5%):
            </p>
            <div className={FORMULA}>
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
        <section id="docs-results" className={SEC}>
          <div className={SEC_TAG}>Section 6</div>
          <h2 className={SEC_H2}>Results &amp; Validation</h2>
          <hr className={SEC_HR} />

          <div className={BODY}>
            <div className={SUB_H}>Baseline Suppression</div>
            <p>
              Analysis of the representative 560–580 nm window (line-poor region) from the archived
              Chandrayaan-3 measurement demonstrates the quantitative effect of cleaning:
            </p>
            <table className={TABLE}>
              <thead>
                <tr>
                  <th className={TH}>Metric</th>
                  <th className={TH}>Raw L1 Spectrum</th>
                  <th className={TH}>Cleaned Spectrum</th>
                </tr>
              </thead>
              <tbody className={TBODY}>
                <tr>
                  <td className={TD}>Mean intensity (560–580 nm)</td>
                  <td className={TD}>~1,005 counts</td>
                  <td className={TD}>~141 counts</td>
                </tr>
                <tr>
                  <td className={TD}>RMS fluctuation</td>
                  <td className={TD}>~47 counts</td>
                  <td className={TD}>~184 counts</td>
                </tr>
                <tr>
                  <td className={TD}>Baseline suppression factor</td>
                  <td className={TD} colSpan={2}>~7.1× (mean reduction)</td>
                </tr>
                <tr>
                  <td className={TD}>High-frequency variance increase</td>
                  <td className={TD} colSpan={2}>~3.9× (σ_clean / σ_raw)</td>
                </tr>
              </tbody>
            </table>
            <p>
              The cleaning strongly reduces low-frequency continuum background (~7×) while
              unavoidably increasing high-frequency residual noise. For peak detection,
              the first effect is <strong>beneficial</strong> — increased peak-to-continuum ratio.
              Peak detection applies 3σ prominence thresholds to mitigate the variance increase.
            </p>

            <div className={SUB_H}>Element Identification</div>
            <p>
              Cross-matching detected emission lines against NIST reference lines yields identification
              of the following elements in high-quality Chandrayaan-3 spectra:
            </p>
            <table className={TABLE}>
              <thead>
                <tr>
                  <th className={TH}>Element</th>
                  <th className={TH}>Key Lines (nm)</th>
                  <th className={TH}>Detection Status</th>
                </tr>
              </thead>
              <tbody className={TBODY}>
                <tr><td className={TD}><strong>Mg II</strong></td><td className={TD}>279.6, 280.3, 284.0</td><td className={TD}>Confirmed (≥2 measurements)</td></tr>
                <tr><td className={TD}><strong>Ca II</strong></td><td className={TD}>393.4, 396.8</td>        <td className={TD}>Confirmed (≥2 measurements)</td></tr>
                <tr><td className={TD}><strong>Si I</strong></td> <td className={TD}>288.2</td>              <td className={TD}>Tentative (1 measurement)</td></tr>
                <tr><td className={TD}><strong>Al I</strong></td> <td className={TD}>308.2, 309.3</td>        <td className={TD}>Not confirmed</td></tr>
                <tr><td className={TD}><strong>Fe I</strong></td> <td className={TD}>373.5, 374.9</td>        <td className={TD}>Not confirmed</td></tr>
              </tbody>
            </table>

            <div className={SUB_H}>Performance</div>
            <div className={CALLOUT}>
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
