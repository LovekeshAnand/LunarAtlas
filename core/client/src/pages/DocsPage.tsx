import { useEffect, useRef, useState } from 'react';

import dbSchemaDiagram from '../assets/db_schema_diagram.png';

// Publication figures
import fig1Architecture from '../assets/fig1_architecture.png';
import fig2ReshapeSchematic from '../assets/fig2_reshape_schematic.png';
import fig3PrePostOverlay from '../assets/fig3_pre_post_overlay.png';
import fig4SpectralVariability from '../assets/fig4_spectral_variability.png';
import fig5PeakRetention from '../assets/fig5_peak_retention.png';
import fig6AcquisitionSequence from '../assets/fig6_acquisition_sequence.png';
import fig7NistOverlay from '../assets/fig7_nist_overlay.png';
import fig8AdaptiveZoom from '../assets/fig8_adaptive_zoom.png';

// ─────────────────────────────────────────────────────────────
// Tailwind class constants — defined as complete strings so that
// Tailwind JIT detects every class during source scanning.
// ─────────────────────────────────────────────────────────────
const SEC     = 'mb-[72px] scroll-mt-20';
const SEC_TAG = 'text-[9px] font-bold tracking-[2.5px] text-ink-muted dark:text-[#444] uppercase mb-[10px]';
const SEC_H2  = 'text-[22px] font-bold text-ink dark:text-[#f0f0f0] m-0 mb-5 tracking-[-0.3px] leading-tight';
const SEC_HR  = 'border-0 border-t border-[#eee] dark:border-[#1e1e1e] m-0 mb-7';
const BODY    = 'text-[13px] text-[#444] dark:text-[#b0b0b0] leading-[1.78] tracking-[0.2px] [&_p]:mb-4 [&_strong]:text-ink dark:[&_strong]:text-[#f0f0f0] [&_strong]:font-bold [&_em]:italic [&_em]:text-[#555] dark:[&_em]:text-[#888]';
const SUB_H   = 'text-[14px] font-bold text-ink dark:text-[#f0f0f0] mt-8 mb-[10px]';
const FORMULA = 'bg-[#f7f7f7] dark:bg-[#111] border border-border dark:border-[#2a2a2a] px-5 py-4 my-5 font-mono text-[13px] text-ink dark:text-[#d0d0d0] overflow-x-auto tracking-[0.3px] border-l-[3px] border-l-ink dark:border-l-[#d0d0d0]';
const CALLOUT = 'bg-canvas-alt dark:bg-[#141414] border border-border dark:border-[#2a2a2a] px-[18px] py-[14px] my-5 text-[12px] text-[#555] dark:text-[#888] leading-[1.65] border-l-[3px] border-l-[#888] dark:border-l-[#444] [&_strong]:text-ink dark:[&_strong]:text-[#d0d0d0]';
const CODE    = 'bg-[#f4f4f4] dark:bg-[#1e1e1e] border border-border dark:border-[#2a2a2a] px-[6px] py-[2px] font-mono text-[11.5px] text-[#333] dark:text-[#d0d0d0] tracking-[0.1px]';
const CODEBLK = 'bg-[#f7f7f7] dark:bg-[#111] border border-border dark:border-[#222] px-5 py-4 my-4 font-mono text-[12px] text-[#222] dark:text-[#c0c0c0] overflow-x-auto leading-[1.6] whitespace-pre';
const FIGURE  = 'my-7 border border-border dark:border-[#222]';
const FIG_CAP = 'px-[14px] py-[10px] text-[11px] text-[#888] dark:text-[#555] border-t border-[#eee] dark:border-[#1e1e1e] leading-[1.5] bg-canvas-alt dark:bg-[#141414] [&_strong]:text-[#555] dark:[&_strong]:text-[#999] [&_strong]:font-bold';
const TABLE   = 'w-full border-collapse my-5 text-[12px]';
const TBODY   = '[&>tr:last-child>td]:border-b-0';
const TH      = 'text-left text-[9px] font-bold tracking-[1.5px] text-[#888] dark:text-[#555] uppercase px-[14px] py-2 border-b border-[#ddd] dark:border-[#1e1e1e] bg-canvas-alt dark:bg-[#141414]';
const TD      = 'px-[14px] py-[10px] border-b border-[#f0f0f0] dark:border-[#1a1a1a] text-[#444] dark:text-[#aaa] leading-[1.5] align-top';
const TD_CODE = 'font-mono text-[11px] text-[#333] dark:text-[#c0c0c0] bg-[#f4f4f4] dark:bg-[#1e1e1e] border border-border dark:border-[#2a2a2a] px-1 py-px';
const FLIST   = 'border border-border dark:border-[#222] my-5 overflow-hidden';
const FROW    = 'grid grid-cols-[160px_74px_1fr] gap-x-3 px-4 py-[11px] border-b border-[#f0f0f0] dark:border-[#1a1a1a] items-center text-[12.5px] last:border-b-0 hover:bg-canvas-alt dark:hover:bg-[#141414]';
const FNAME   = 'font-semibold text-ink dark:text-[#f0f0f0] text-[12.5px]';
const FTYPE   = 'font-mono text-[11px] text-[#888] dark:text-[#555] bg-[#f4f4f4] dark:bg-[#1e1e1e] px-[6px] py-[2px] rounded-sm self-center whitespace-nowrap w-fit';
const FDESC   = 'text-[#555] dark:text-[#888] text-[12.5px] leading-[1.55] pl-3';
const STEPS   = 'my-5 flex flex-col border border-border dark:border-[#222] overflow-hidden';
const SROW    = 'flex gap-5 items-start px-[18px] py-[14px] border-b border-[#f0f0f0] dark:border-[#1a1a1a] last:border-b-0 hover:bg-canvas-alt dark:hover:bg-[#141414]';
const SNUM    = 'text-[10px] font-bold text-ink-muted dark:text-[#444] tracking-[1px] shrink-0 pt-[2px] min-w-6';
const STITLE  = 'text-[13px] font-semibold text-ink dark:text-[#f0f0f0] mb-[3px]';
const SDESC   = 'text-[12.5px] text-[#555] dark:text-[#888] leading-[1.6]';

const PIPELINE_STAGES = [
  {
    n: '01',
    title: 'Directory Scan (Discovery)',
    script: 'Pipeline/step1_structure_study.py',
    desc: 'Scans the raw ISRO PDS4 directory structure to build a JSON summary metadata index. This discovers all available observation directories and prevents duplicate attempts.',
    inputs: 'Raw PDS4 archive directories',
    outputs: 'study_summary.json summary manifest'
  },
  {
    n: '02',
    title: 'Core Reshaping & Pairing (Melting)',
    script: 'Pipeline/step2_process_l1_data.py',
    desc: 'Parses XML labels for observation metadata, reshapes the 2,094 wavelength columns into long-form spectral samples, separates background/plasma shots, pairs each shot temporally, and applies paired background subtraction with zero-clamping.',
    inputs: 'Calibrated L1 CSV data tables + XML metadata labels',
    outputs: 'Cleaned spectral CSVs mapped by Measurement ID'
  },
  {
    n: '03',
    title: 'NIST Graph Plotting (Visualization)',
    script: 'Pipeline/step3_graph_plotting.py',
    desc: 'Renders publication-quality overlay plots of each cleaned spectrum with a 32-line NIST atomic spectra overlay. Figures are saved at 300 DPI for paper submission.',
    inputs: 'Cleaned spectral CSV files',
    outputs: '300 DPI publication overlay plots (PNG)'
  },
  {
    n: '04',
    title: 'Peak Detection (Verification)',
    script: 'Pipeline/step4_nist_verification_logs.py',
    desc: 'Performs peak detection on each cleaned spectrum and cross-references them against the NIST database within a 0.5 nm offset tolerance. Creates a verification audit trail.',
    inputs: 'Cleaned spectral CSV files',
    outputs: 'nist_verification_log.csv logs'
  },
  {
    n: '05',
    title: 'Integrity Checksums (Signing)',
    script: 'Pipeline/step5_md5_checksums.py',
    desc: 'Generates MD5 digital checksum signatures for every processed CSV and PNG plot. Ensures full traceability and scientific auditability.',
    inputs: 'Processed CSV and PNG files',
    outputs: 'checksums.md5 manifest file'
  },
  {
    n: '06',
    title: 'Folder Hierarchy Replication',
    script: 'Pipeline/step6_segregate_data_folders.py',
    desc: 'Re-organizes and moves all outputs (CSVs, PNGs, logs, checksums) into directories replicating the official ISRO folder structure for clean archival storage.',
    inputs: 'All generated pipeline outputs',
    outputs: 'Structured PDS4-compliant folder architecture'
  },
  {
    n: '07',
    title: 'Database Bulk Loading (Ingestion)',
    script: 'Pipeline/step7_db_ingestion.py',
    desc: 'Bulk loads observations, measurements, file versions, and all cleaned spectral channels into PostgreSQL tables using page-size batching for optimized ingestion.',
    inputs: 'Structured processed directories',
    outputs: 'Relational PostgreSQL database tables'
  },
  {
    n: '08',
    title: 'Post-Ingestion Audit (Auditing)',
    script: 'Pipeline/step8_data_verification.py',
    desc: 'Performs an end-to-end database integrity scan, verifying that file row counts, relational measurement links, and database checksums match the checksum manifest.',
    inputs: 'Database tables + checksums.md5 manifest',
    outputs: 'PASS/FAIL system audit report'
  }
];

const SIDEBAR_GROUPS = [
  {
    title: 'Science Reference',
    items: [
      { id: 'intro',       label: 'Introduction'     },
      { id: 'data',        label: 'Data Structure'   },
      { id: 'pipeline',    label: 'Cleaning Pipeline' },
      { id: 'schema',      label: 'Database Model'   },
      { id: 'downsampling', label: 'Peak Preservation' },
      { id: 'results',     label: 'Results & Validation' },
      { id: 'authenticity', label: 'Data Authenticity' },
      { id: 'pds3',        label: 'PDS3 Future Scope' },
    ]
  },
  {
    title: 'Ingestion & Data Tutorial',
    items: [
      { id: 'structure',   label: 'PRADAN Structure' },
      { id: 'ingestion',   label: 'Ingestion & Download' },
    ]
  }
];

// ─── Sidebar nav with scrollspy ─────────────────────────────
function Sidebar({ activeId }: { activeId: string }) {
  function scrollTo(id: string) {
    const el = document.getElementById(`docs-${id}`);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  return (
    <aside className="w-[220px] shrink-0 sticky top-[61px] h-[calc(100vh-61px)] overflow-y-auto border-r border-border dark:border-[#222] pt-10 pb-10 pl-8 box-border transition-colors duration-200">
      {SIDEBAR_GROUPS.map((group) => (
        <div key={group.title} className="mb-6">
          <div className="text-[9px] font-bold tracking-[2px] text-ink-muted dark:text-[#555] uppercase mb-3 pr-5">
            {group.title}
          </div>
          {group.items.map(({ id, label }) => (
            <div key={id} className="mb-[6px]">
              <button
                className={`block text-[11.5px] py-[6px] border-0 border-l-2 pl-3 -ml-[14px] tracking-[0.3px] transition-colors duration-150 cursor-pointer bg-transparent font-sans text-left w-full ${
                  activeId === id
                    ? 'text-ink dark:text-[#f0f0f0] font-bold border-l-ink dark:border-l-[#f0f0f0]'
                    : 'text-[#888] dark:text-[#555] font-normal border-l-transparent hover:text-ink dark:hover:text-[#d0d0d0]'
                }`}
                onClick={() => scrollTo(id)}
              >
                {label}
              </button>
            </div>
          ))}
        </div>
      ))}

      <div className="mt-8 pr-5 border-t border-border dark:border-[#222] pt-4">
        <div className="text-[9px] font-bold tracking-[1.5px] text-[#ccc] dark:text-[#333] uppercase mb-2">
          Source
        </div>
        <div className="text-[10px] text-ink-muted dark:text-[#444] leading-[1.5]">
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
  const [ingestTab, setIngestTab] = useState<'tutorial' | 'pipeline'>('tutorial');
  const [ingestStep, setIngestStep] = useState(1);
  const observerRef = useRef<IntersectionObserver | null>(null);

  useEffect(() => {
    window.scrollTo(0, 0);

    const targets = SIDEBAR_GROUPS
      .flatMap((g) => g.items)
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
              The technique was first demonstrated in a planetary setting aboard the Mars Science
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

            <div className={SUB_H}>LunarAtlas System Architecture</div>
            <p>
              To support open science and reproducible planetary research, LunarAtlas provides an end-to-end processing and interactive visualization infrastructure. The architecture spans from physical PDS4 label parsing to web-based telemetry rendering, structured across three distinct tiers:
            </p>

            <div className={FIGURE}>
              <img src={fig1Architecture} alt="LunarAtlas system architecture diagram" className="w-full block" />
              <div className={FIG_CAP}>
                <strong>Figure 1. End-to-end LunarAtlas architecture.</strong> The system diagram outlines data flow and component interactions across three functional layers: the PostgreSQL Data Layer, Python/FastAPI Logic Layer, and React Presentation Layer.
              </div>
            </div>

            <ul className="list-disc pl-5 space-y-2 my-4">
              <li>
                <strong>Data Layer (PostgreSQL 16.3)</strong>: Stores mission contexts, instrument schemas, observations, measurements, and individual spectral records. Long-form storage of spectral data is optimized using a composite primary key <code className={CODE}>(measurement_id, wavelength_nm)</code> and indexed using a **BRIN (Block Range Index)** for efficient range-based wavelength scans across millions of data points.
              </li>
              <li>
                <strong>Logic Layer (Python 3.11 &amp; FastAPI 0.111)</strong>: Handles raw PDS4 ingestion, XML metadata extraction, MD5 signing, background-subtraction pairing, peak detection, and NIST Atomic Spectra matching. It serves spectral API endpoints at sub-500 ms latency using a Largest Triangle Three Buckets (LTTB) downsampling implementation integrated with a Peak-Union Lock.
              </li>
              <li>
                <strong>Presentation Layer (React 18 &amp; TypeScript)</strong>: Features an interactive telemetry dashboard with smooth multi-curve graphs, raw vs. cleaned overlays, individual measurement grids, and responsive dark-mode styling. High-performance browser rendering is achieved via Web Workers executing client-side downsampling off the main thread.
              </li>
            </ul>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            1.5 PRADAN STRUCTURE
        ══════════════════════════════════════════════ */}
        <section id="docs-structure" className={SEC}>
          <div className={SEC_TAG}>Section 2</div>
          <h2 className={SEC_H2}>ISRO PRADAN Directory Structure</h2>
          <hr className={SEC_HR} />

          <div className={BODY}>
            <p>
              When researchers download Chandrayaan-3 LIBS datasets from the official <strong>ISRO PRADAN</strong> portal, 
              the archive is unpacked into a strict, standardized PDS4 bundle structure. Understanding this raw directory structure 
              is essential for tracing back how database entries map to the physical files of the spacecraft's observations.
            </p>

            <p>
              Below is the comprehensive hierarchical layout of a raw downloaded PRADAN LIBS bundle:
            </p>

            <pre className={CODEBLK}>{`ch3_libs/
└── lib-v2/                                          # LIBS Version 2 Bundle Root
    ├── bundle_lib.xml                                # PDS4 Bundle manifest (Root metadata)
    ├── readme.txt                                    # Dataset overview, mission outline & terms
    ├── document/                                     # User guides, calibration reports & documents
    ├── miscellaneous/                                # Support scripts & ancillary catalog metadata
    └── data/
        ├── collection_data_inventory.csv             # CSV list indexing all data products
        ├── collection_data_inventory.xml             # PDS4 collection label for indexing catalog
        ├── raw/                                      # Raw (L0) uncalibrated sensor products
        └── calibrated/                               # Calibrated (L1) science spectral products
            ├── 20230825/                             # Date folder (Format: YYYYMMDD)
            │   ├── ch3_lib_002_20230825T104221_00_l1/    # Observation session folder
            │   │   ├── ch3_lib_002_20230825T104221_00_l1.csv     # Combined session observations table
            │   │   ├── ch3_lib_002_20230825T104221_00_l1.xml     # PDS4 XML label for the session table
            │   │   ├── ch3_lib_002_20230825T104221_00_l1_0_1.csv # Shot 0, Zap 1 (Calibrated spectrum)
            │   │   ├── ch3_lib_002_20230825T104221_00_l1_0_1.xml # PDS4 XML label for Shot 0, Zap 1
            │   │   ├── ch3_lib_002_20230825T104221_00_l1_0_3.csv # Shot 0, Zap 3
            │   │   ├── ch3_lib_002_20230825T104221_00_l1_1_2.csv # Shot 1, Zap 2
            │   │   ├── ...                                       # Remaining measurement CSV/XML files
            │   │   └── cleaned_libs_data/                        # Pipeline-processed output files
            │   ├── ch3_lib_002_20230825T145453_00_l1/
            │   ├── ch3_lib_002_20230825T145453_01_l1/
            │   └── ch3_lib_002_20230825T145453_02_l1/
            ├── 20230826/
            ├── 20230827/
            ├── 20230828/
            ├── 20230829/
            ├── 20230830/
            ├── 20230831/
            ├── 20230901/
            └── 20230902/                             # Chandrayaan-3 active operations dates`}</pre>

            <div className={SUB_H}>Folder &amp; File Naming Conventions</div>
            <p>
              The folder structures and files follow strict PDS4 naming conventions encoding key telemetry details:
            </p>
            <ul className="list-disc pl-5 space-y-2 my-4">
              <li>
                <strong>Bundle Root (<code>bundle_lib.xml</code>)</strong>: The entry-point manifest specifying the schema version, 
                instrument characteristics, and collection list.
              </li>
              <li>
                <strong>Observation Sessions</strong>: Folders named as <code>ch3_lib_002_&#123;date&#125;T&#123;time&#125;_&#123;sub_index&#125;_l1</code> 
                represent a contiguous collection of laser discharges on a single target spot.
              </li>
              <li>
                <strong>Individual Measurements</strong>: CSV and XML files suffixed with <code>_&#123;shot_index&#125;_&#123;zap_index&#125;</code> (e.g. <code>_0_1</code>) 
                indicate the specific shot number (from 0 to 4) and zap index (from 1 to 5) in a sequence.
              </li>
            </ul>

            <div className={SUB_H}>Laser-Induced Breakdown Spectroscopy Acquisition Sequence</div>
            <p>
              Pragyan's LIBS data acquisition follows a strict operational sequence designed to calibrate the detector against ambient thermal and electronic noise in the harsh lunar vacuum. Each observation sequence comprises alternating plasma shots (laser zaps) and dark-field calibrations (laser off).
            </p>

            <div className={FIGURE}>
              <img src={fig6AcquisitionSequence} alt="ISRO LIBS acquisition sequence timeline" className="w-full block" />
              <div className={FIG_CAP}>
                <strong>Figure 2. In-situ data acquisition sequence.</strong> The timeline diagram shows the alternating interleaving pattern of high-power laser discharges (Plasma Shots) and background dark-field calibrations (Background darks) recorded sequentially.
              </div>
            </div>

            <p>
              During active rover operations:
            </p>
            <ol className="list-decimal pl-5 space-y-2 my-4">
              <li>
                The instrument first fires a set of laser pulses on a target site, generating a short-lived plasma plume whose emission is gathered by a spectrometer.
              </li>
              <li>
                In between laser pulses, the detector registers dark-field counts without any laser ignition.
              </li>
              <li>
                These acquisitions are interleaved inside a single observation session file, marked by binary housekeeping status flags. The pipeline pairs each plasma shot with the nearest preceding or succeeding background measurement.
              </li>
            </ol>

            <div className={CALLOUT}>
              <strong>Database Integration:</strong> During ingestion, LunarAtlas automatically maps the PDS4 
              manifests and CSV data into relative tables. An "Observation" record corresponds to a session folder, 
              and its "Measurement" records relate directly to individual laser zap CSV entries.
            </div>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            2.5 INGESTION PIPELINE & DOWNLOAD
        ══════════════════════════════════════════════ */}
        <section id="docs-ingestion" className={SEC}>
          <div className={SEC_TAG}>Section 3</div>
          <h2 className={SEC_H2}>Ingestion Pipeline &amp; Data Tutorial</h2>
          <hr className={SEC_HR} />

          <div className="flex gap-2 mb-6 border-b border-border dark:border-[#222] pb-px bg-canvas-alt dark:bg-[#121215]/40 p-1.5 rounded-lg max-w-md">
            {[
              { id: 'tutorial', label: 'PRADAN Download Guide' },
              { id: 'pipeline', label: '8-Stage Ingestion Pipeline' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setIngestTab(tab.id as any)}
                className={`flex-1 py-2 text-center text-[10px] font-bold tracking-widest uppercase rounded-md transition-all cursor-pointer ${
                  ingestTab === tab.id
                    ? 'bg-canvas dark:bg-[#1b1b22] text-ink dark:text-white border border-border dark:border-[#2a2a35]'
                    : 'text-[#888] hover:text-[#bbb] border border-transparent'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {ingestTab === 'tutorial' && (
            <div className={BODY}>
              <p>
                The Indian Space Research Organisation (ISRO) releases scientific data from planetary missions
                through its <strong>Indian Space Science Data Centre (ISSDC)</strong> web portal. Calibrated Level-1 (L1) LIBS data tables
                for the Pragyan rover are archived under PDS4 compliance and are free for public download.
              </p>

              <div className={SUB_H}>Step-by-Step Data Acquisition Guide</div>
              <p>
                To obtain raw LIBS telemetry data from ISRO, follow these steps:
              </p>
              <ol className="list-decimal pl-6 mb-5 flex flex-col gap-2.5 text-[13px]">
                <li>
                  Navigate to the official <strong>ISRO PRADAN</strong> portal at{' '}
                  <a href="https://pradan.issdc.gov.in/pradan/" target="_blank" rel="noreferrer" className="text-emerald-500 font-semibold hover:underline">
                    https://pradan.issdc.gov.in/pradan/
                  </a>.
                </li>
                <li>
                  On the portal landing page, click on the <strong>Chandrayaan-3</strong> mission category.
                </li>
                <li>
                  Perform a <strong>Login</strong> with your credentials, or <strong>Sign Up</strong> to create a free account if you do not have one.
                </li>
                <li>
                  Select the <strong>LIBS</strong> payload dataset, which is directly visible on the page (no deep folder navigation required).
                </li>
                <li>
                  Download the selected data, which will download a <strong>ZIP file</strong> onto your system.
                </li>
              </ol>

              <div className={SUB_H}>Extracting and Archiving the ZIP Dataset</div>
              <p>
                Once the ZIP file is installed on your local computer, extract its contents to a local directory (e.g., <code className={CODE}>D:\\ch3_libs\\</code>). The extracted directory will automatically preserve the PDS4 compliant structure, containing both the <code className={CODE}>data/calibrated/</code> subdirectory and its corresponding XML descriptors.
              </p>

              <div className={SUB_H}>Understanding the PDS4 Naming Standard</div>
              <p>
                Files are structured using Planetary Data System version 4 (PDS4) descriptors. A typical observation
                comprises two paired files:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
                <div className="border border-border dark:border-[#2b2b2b] p-4 rounded bg-canvas-alt dark:bg-[#151515]">
                  <span className="font-mono text-[12.5px] font-bold text-ink dark:text-gray-200 block">
                    *.xml (PDS4 Label)
                  </span>
                  <span className="text-[12px] text-ink-muted dark:text-gray-400 mt-2 block leading-normal">
                    Contains logical identifiers (LID), target metadata coordinates, timestamps, and column descriptors for the CSV file.
                  </span>
                </div>
                <div className="border border-border dark:border-[#2b2b2b] p-4 rounded bg-canvas-alt dark:bg-[#151515]">
                  <span className="font-mono text-[12.5px] font-bold text-ink dark:text-gray-200 block">
                    *.csv (Data Table)
                  </span>
                  <span className="text-[12px] text-ink-muted dark:text-gray-400 mt-2 block leading-normal">
                    The tabular data where each row contains flag bytes, housekeeping variables, and the 2,049 wide intensity columns.
                  </span>
                </div>
              </div>

              <div className={CALLOUT}>
                <strong>Naming Breakdown Example:</strong><br />
                <code className={CODE}>ch3_lib_002_20230825T104221_00_l1.csv</code><br />
                - <strong>ch3</strong>: Chandrayaan-3 Mission<br />
                - <strong>lib</strong>: LIBS payload instrument<br />
                - <strong>002</strong>: Ingestion index sequence<br />
                - <strong>20230825T104221</strong>: Timestamp of initial measurement (UTC)<br />
                - <strong>l1</strong>: Calibrated Level-1 processing standard
              </div>

              <div className={SUB_H}>Ingesting Downloaded Data in LunarAtlas</div>
              <p>
                After downloading and extracting the entire LIBS dataset ZIP from the ISRO PRADAN portal, execute the ingestion pipeline by pointing the script directly to the extracted <code className={CODE}>calibrated/</code> subdirectory.
              </p>
              <pre className={CODEBLK}>{`# Ingest and process extracted files automatically by pointing to the calibrated folder
python Pipeline/step2_process_l1_data.py "path/to/extracted/LIBS/data/calibrated/"`}</pre>
            </div>
          )}

          {ingestTab === 'pipeline' && (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-[240px_1fr] gap-6 items-start">
                
                {/* Steps Left List */}
                <div className="bg-canvas-alt dark:bg-[#121212] border border-border dark:border-[#222] rounded-lg p-4 flex flex-col gap-1.5 shadow-sm">
                  <span className="text-[10px] font-bold tracking-[2px] text-ink-muted dark:text-[#555] uppercase mb-4 block">
                    Pipeline Stages
                  </span>
                  {PIPELINE_STAGES.map((stage, idx) => {
                    const isCurrent = ingestStep === (idx + 1);
                    return (
                      <button
                        key={stage.n}
                        type="button"
                        onClick={() => setIngestStep(idx + 1)}
                        className={`text-left text-[11.5px] font-medium py-2 px-3 border-0 border-l-2 pl-3 tracking-[0.2px] transition-all cursor-pointer bg-transparent w-full ${
                          isCurrent
                            ? 'text-emerald-600 dark:text-[#a3e635] font-bold border-l-emerald-500 dark:border-l-[#a3e635] bg-canvas dark:bg-[#181818]'
                            : 'text-[#888] dark:text-[#555] border-l-transparent hover:text-ink dark:hover:text-[#fff]'
                        }`}
                      >
                        Stage {stage.n}: {stage.title}
                      </button>
                    );
                  })}
                </div>

                {/* Stepper Content Frame */}
                <div className="bg-canvas-alt dark:bg-[#121212] p-6 border border-border dark:border-[#222] rounded-lg shadow-sm">
                  {(() => {
                    const stage = PIPELINE_STAGES[ingestStep - 1];
                    return (
                      <div>
                        <div className={SEC_TAG}>Pipeline Stage {stage.n} of 08</div>
                        <h3 className="text-[16px] font-bold text-ink dark:text-[#f0f0f0] m-0 mb-4 tracking-[-0.3px] leading-tight">{stage.title}</h3>
                        <hr className={SEC_HR} />

                        <div className="flex flex-col gap-5">
                          <div>
                            <span className="text-[10.5px] text-[#888] dark:text-[#555] uppercase font-bold tracking-wide">
                              Underlying Python Module File
                            </span>
                            <div className="mt-1 font-mono text-[12px] bg-canvas dark:bg-[#181818] border border-border dark:border-[#2b2b2b] px-4 py-2 text-ink dark:text-white font-semibold w-fit rounded">
                              {stage.script}
                            </div>
                          </div>

                          <div className={BODY}>
                            <span className="text-[10.5px] text-[#888] dark:text-[#555] uppercase font-bold tracking-wide block mb-1">
                              Purpose and Logic
                            </span>
                            <p className="m-0 leading-relaxed text-[13px]">
                              {stage.desc}
                            </p>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
                            <div className="bg-canvas dark:bg-[#181818] border border-border dark:border-[#222] p-4 rounded">
                              <span className="text-[10.5px] text-[#888] dark:text-[#555] uppercase font-bold tracking-wider">
                                Input Assets
                              </span>
                              <span className="block mt-1.5 text-[12px] text-ink dark:text-gray-300 font-medium">
                                {stage.inputs}
                              </span>
                            </div>
                            <div className="bg-canvas dark:bg-[#181818] border border-border dark:border-[#222] p-4 rounded">
                              <span className="text-[10.5px] text-[#888] dark:text-[#555] uppercase font-bold tracking-wider">
                                Output Results
                              </span>
                              <span className="block mt-1.5 text-[12px] text-ink dark:text-gray-300 font-medium">
                                {stage.outputs}
                              </span>
                            </div>
                          </div>

                          {/* Navigation Stepper Buttons */}
                          <div className="mt-6 flex justify-between border-t border-border dark:border-[#1e1e1e] pt-5">
                            <button
                              type="button"
                              disabled={ingestStep === 1}
                              onClick={() => setIngestStep(s => s - 1)}
                              className="px-4 py-2 border border-border dark:border-[#333] text-[11px] font-bold uppercase tracking-wide rounded cursor-pointer hover:bg-canvas-alt dark:hover:bg-[#1e1e1e] disabled:opacity-40 disabled:cursor-not-allowed text-ink dark:text-white bg-transparent"
                            >
                              Previous Stage
                            </button>
                            <button
                              type="button"
                              disabled={ingestStep === PIPELINE_STAGES.length}
                              onClick={() => setIngestStep(s => s + 1)}
                              className="px-4 py-2 bg-emerald-600 dark:bg-[#a3e635] text-white dark:text-black border-0 text-[11px] font-bold uppercase tracking-wide rounded cursor-pointer hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
                            >
                              Next Stage
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>

              </div>
            </div>
          )}
        </section>

        {/* ══════════════════════════════════════════════
            3. DATA STRUCTURE
        ══════════════════════════════════════════════ */}
        <section id="docs-data" className={SEC}>
          <div className={SEC_TAG}>Section 4</div>
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
              into long-form records.
            </p>

            <div className={FIGURE}>
              <img src={fig2ReshapeSchematic} alt="Wide to long reshape schema" className="w-full block" />
              <div className={FIG_CAP}>
                <strong>Figure 3. Wide-to-long schema reshaping.</strong> This schematic shows how wide-format rows containing 2,049 wavelength columns are normalized and melted into a relational database layout (long format) key-linked by measurement IDs.
              </div>
            </div>

            <p>
              Each row in the output represents a single (measurement, wavelength, intensity) triple with full metadata attached:
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
          <div className={SEC_TAG}>Section 5</div>
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
              <img src={fig3PrePostOverlay} alt="Raw vs Cleaned LIBS spectrum comparison" className="w-full block" />
              <div className={FIG_CAP}>
                <strong>Figure 4. Pre and post background subtraction overlay.</strong> Full-range Chandrayaan-3 LIBS spectrum showing Raw L1 counts (grey dashed) and cleaned intensity (solid blue/purple) for a single plasma measurement spanning 164.35–878.26 nm. Background subtraction successfully removes the underlying thermal/electronic baseline while preserving narrow emission features.
              </div>
            </div>

            <div className={SUB_H}>The Measurement ID &amp; Spectral Variability</div>
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

            <div className={FIGURE}>
              <img src={fig4SpectralVariability} alt="Spectral variability across multiple shots" className="w-full block" />
              <div className={FIG_CAP}>
                <strong>Figure 5. Shot-to-shot spectral variability.</strong> Overlay of five consecutive cleaned spectra taken on the same spot target. The figure highlights significant intensity and profile fluctuations between individual laser discharges, emphasizing why averaging hiding this variability must be avoided and why individual Measurement IDs are essential.
              </div>
            </div>

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
                { n: '08', title: 'Database Ingestion',       desc: 'Write cleaned spectra into the spectral data table, keyed by Measurement ID, wavelength, and cleaned intensity.' },
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
          <div className={SEC_TAG}>Section 6</div>
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
                <strong>Figure 6.</strong> LunarAtlas PostgreSQL schema hierarchy. Each level preserves
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
          <div className={SEC_TAG}>Section 7</div>
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

            <div className={SUB_H}>The NIST Peak-Union Lock Solution</div>
            <p>
              To solve the visual preservation vs. scientific fidelity trade-off, LunarAtlas introduces the <strong>NIST Peak-Union Lock</strong>. The algorithm enforces a Peak-Union selection:
            </p>
            <div className={FORMULA}>
              P<sub>final</sub> = LTTB(data) ∪ Peaks<sub>NIST</sub>(data)
            </div>
            <p>
              where <code className={CODE}>Peaks_NIST(data)</code> is the set of raw channel indices nearest to each of the curated NIST reference wavelengths for target elements. This guarantees that diagnostic lines (e.g., Ca, Mg, Si, Fe) are never decimated out, regardless of zoom level or bucket width.
            </p>

            <div className={FIGURE}>
              <img src={fig5PeakRetention} alt="Peak retention downsampling comparison" className="w-full block" />
              <div className={FIG_CAP}>
                <strong>Figure 7. Downsampling algorithm comparison.</strong> Visual comparison of Uniform Decimation, Max-Binning, Standard LTTB, and LTTB + NIST Peak Lock at 10% density. Standard LTTB and decimation drop crucial narrow emission peaks, whereas the Peak Lock guarantees 100% peak retention.
              </div>
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

            <div className={SUB_H}>Zoom Saturation &amp; Level Transitions</div>
            <p>
              Beyond a maximum unsaturated zoom level, bucket size clamps to{' '}
              <code className={CODE}>b_min</code> and the API returns <em>raw spectral samples</em>:
            </p>
            <div className={FORMULA}>
              z<sub>max</sub>(Δλ) = ⌊log₂(Δλ / (BASE_BUCKETS × b<sub>min</sub>))⌋
            </div>

            <div className={FIGURE}>
              <img src={fig8AdaptiveZoom} alt="Adaptive zoom levels details" className="w-full block" />
              <div className={FIG_CAP}>
                <strong>Figure 8. Adaptive zoom and downsampling levels.</strong> Detailed transitions showing how spectral resolution adjusts dynamically from full-range view down to highly focused zoom windows, keeping peak detail intact.
              </div>
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

            <div className={SUB_H}>Overlapping Buckets</div>
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
          <div className={SEC_TAG}>Section 8</div>
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

            <div className={SUB_H}>Element Identification &amp; NIST Overlay</div>
            <p>
              To confirm the elemental presence in lunar regolith target sites, detected peaks are cross-referenced directly with the atomic line positions registered in the NIST Atomic Spectra Database. 
            </p>

            <div className={FIGURE}>
              <img src={fig7NistOverlay} alt="NIST database spectral line overlay" className="w-full block" />
              <div className={FIG_CAP}>
                <strong>Figure 9. Cleaned spectrum with NIST overlays.</strong> Cleaned spectrum of a Chandrayaan-3 target overlaying NIST emission reference wavelengths for key element species (Ca II, Mg II, Si I). Prominent peaks show precise matches within the 0.5 nm threshold.
              </div>
            </div>

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
                <tr>
                  <td className={TD}><strong>Mg II</strong></td>
                  <td className={TD}>279.6, 280.3, 284.0</td>
                  <td className={TD}>Confirmed (≥2 measurements)</td>
                </tr>
                <tr>
                  <td className={TD}><strong>Ca II</strong></td>
                  <td className={TD}>393.4, 396.8</td>
                  <td className={TD}>Confirmed (≥2 measurements)</td>
                </tr>
                <tr>
                  <td className={TD}><strong>Si I</strong></td>
                  <td className={TD}>288.2</td>
                  <td className={TD}>Tentative (1 measurement)</td>
                </tr>
                <tr>
                  <td className={TD}><strong>Al I</strong></td>
                  <td className={TD}>308.2, 309.3</td>
                  <td className={TD}>Not confirmed</td>
                </tr>
                <tr>
                  <td className={TD}><strong>Fe I</strong></td>
                  <td className={TD}>373.5, 374.9</td>
                  <td className={TD}>Not confirmed</td>
                </tr>
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

        {/* ══════════════════════════════════════════════
            7. DATA AUTHENTICITY & INTEGRITY
        ══════════════════════════════════════════════ */}
        <section id="docs-authenticity" className={SEC}>
          <div className={SEC_TAG}>Section 9</div>
          <h2 className={SEC_H2}>Data Authenticity &amp; Integrity</h2>
          <hr className={SEC_HR} />

          <div className={BODY}>
            <p>
              A central design goal of LunarAtlas is to ensure that <strong>every cleaned
              spectrum is fully traceable</strong> back to its original PDS4 L1 source product.
              Scientific reproducibility demands that no lossy or irreversible transformation
              is applied without explicit documentation.
            </p>

            <div className={SUB_H}>Provenance Chain</div>
            <p>
              The database schema encodes a strict provenance hierarchy from mission to
              individual wavelength–intensity pairs. Every <code className={CODE}>spectral_data</code>{' '}
              row links back through <code className={CODE}>measurement</code> →{' '}
              <code className={CODE}>file_version</code> → <code className={CODE}>observation</code>{' '}
              → <code className={CODE}>instrument</code> → <code className={CODE}>mission</code>.
            </p>

            <div className={SUB_H}>Bit-Level Reproducibility</div>
            <div className={STEPS}>
              {[
                { n: '01', title: 'MD5 Checksum on Ingest',          desc: 'Every L1 CSV is checksummed before processing and the hash is stored in the file_version table. Re-ingesting the same file is idempotent.' },
                { n: '02', title: 'Deterministic Cleaning Formula',   desc: 'I_clean(λ) = max(0, I_plasma(λ) − I_background(λ)). No stochastic parameters, no fitting, no model selection.' },
                { n: '03', title: 'Timestamp-Logged Processing Runs', desc: 'Each batch run records a processing_timestamp in the output logs. Researchers can identify exactly which pipeline version produced a given dataset.' },
                { n: '04', title: 'Full Metadata Attachment',         desc: 'All 19 PDS4 columns are preserved per spectral row — no metadata is dropped during reshape or cleaning.' },
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

            <div className={SUB_H}>L1-Raw → L1-Processed Re-Derivability</div>
            <p>
              The cleaning operation is <strong>fully reversible</strong> in principle: given
              the original L1 plasma and background spectra (both stored), the L1-processed
              spectrum can be recomputed at any time. LunarAtlas stores both raw plasma
              counts and background counts alongside the cleaned intensity, enabling
              researchers to apply alternative cleaning methods or validate our subtraction.
            </p>

            <div className={CALLOUT}>
              <strong>No lossy transformations:</strong> Unlike pipelines that apply smoothing
              filters or continuum models (which discard information), LunarAtlas's paired
              subtraction with <code className={CODE}>max(0, ·)</code> clamping is a deterministic,
              parameter-free operation. The only information "lost" is the sign of negative
              differences — and those are physically meaningless (negative photon counts).
            </div>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            8. PDS3 FUTURE SCOPE
        ══════════════════════════════════════════════ */}
        <section id="docs-pds3" className={SEC}>
          <div className={SEC_TAG}>Section 10</div>
          <h2 className={SEC_H2}>Future Scope — PDS3 Compatibility</h2>
          <hr className={SEC_HR} />

          <div className={BODY}>
            <p>
              LunarAtlas currently ingests <strong>PDS4</strong> products exclusively.
              A planned extension targets <strong>PDS3 (Planetary Data System v3)</strong>{' '}
              products from legacy missions — most importantly the <em>ChemCam</em>{' '}
              instrument on the <em>Curiosity</em> rover, which has generated the largest
              corpus of planetary LIBS spectra to date (930,000+ single-shot spectra).
            </p>

            <div className={SUB_H}>PDS3 vs PDS4 Structural Differences</div>
            <table className={TABLE}>
              <thead>
                <tr>
                  <th className={TH}>Feature</th>
                  <th className={TH}>PDS3</th>
                  <th className={TH}>PDS4</th>
                </tr>
              </thead>
              <tbody className={TBODY}>
                <tr>
                  <td className={TD}>Label format</td>
                  <td className={TD}>Keyword = Value (flat text)</td>
                  <td className={TD}>XML with namespace schemas</td>
                </tr>
                <tr>
                  <td className={TD}>Data tables</td>
                  <td className={TD}>Fixed-width ASCII or binary tables</td>
                  <td className={TD}>Delimited CSV or binary with XML description</td>
                </tr>
                <tr>
                  <td className={TD}>Label attachment</td>
                  <td className={TD}>Attached (prepended) or detached (.lbl file)</td>
                  <td className={TD}>Always detached (.xml file)</td>
                </tr>
                <tr>
                  <td className={TD}>Identifiers</td>
                  <td className={TD}>PRODUCT_ID string</td>
                  <td className={TD}>logical_identifier URN</td>
                </tr>
                <tr>
                  <td className={TD}>Schema validation</td>
                  <td className={TD}>Minimal (keyword dictionary)</td>
                  <td className={TD}>Full XML Schema + Schematron rules</td>
                </tr>
              </tbody>
            </table>

            <div className={SUB_H}>Planned Parser Extensions</div>
            <div className={STEPS}>
              {[
                { n: '01', title: 'PDS3 Label Parser',              desc: 'Parse keyword=value label format to extract PRODUCT_ID, START_TIME, INSTRUMENT_ID, and column definitions.' },
                { n: '02', title: 'Fixed-Width Table Reader',        desc: 'Read fixed-width ASCII tables using byte offsets from the label, supporting ChemCam\'s 3-spectrometer layout (UV, Vis, VNIR).' },
                { n: '03', title: 'Cross-Mission Schema Mapping',    desc: 'Map PDS3 metadata fields to the LunarAtlas relational schema, enabling unified SQL queries across Chandrayaan-3 and ChemCam data.' },
                { n: '04', title: 'Spectral Range Normalisation',    desc: 'Align Chandrayaan-3\'s 164–878 nm range with ChemCam\'s 240–905 nm range for overlapping-region comparison.' },
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

            <div className={SUB_H}>Motivation: Cross-Mission Spectral Comparison</div>
            <p>
              Ingesting PDS3 ChemCam data would enable <strong>the first direct
              comparison</strong> of Lunar vs. Martian LIBS spectra within a single
              analytical platform. Key scientific questions that this enables:
            </p>
            <div className={CALLOUT}>
              <strong>Research opportunities:</strong> (1) Compare plasma behaviour in vacuum
              (Moon) vs. 7 mbar CO₂ atmosphere (Mars). (2) Cross-validate elemental
              identification algorithms against ChemCam's extensively studied targets.
              (3) Benchmark LunarAtlas's simple paired subtraction against ChemCam's
              multi-step continuum removal pipeline.
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}
