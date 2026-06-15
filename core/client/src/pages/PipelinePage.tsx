import { useState, useMemo } from 'react';

// Styling constants matching DocsPage.tsx for design cohesion
const SEC = 'mb-12 scroll-mt-20 bg-white dark:bg-[#121212] p-8 border border-gray-200 dark:border-[#222] rounded-lg shadow-sm';
const SEC_TAG = 'text-[9px] font-bold tracking-[2.5px] text-gray-400 dark:text-[#555] uppercase mb-2';
const SEC_H2 = 'text-[22px] font-bold text-gray-800 dark:text-[#f0f0f0] m-0 mb-4 tracking-[-0.3px] leading-tight';
const SEC_HR = 'border-0 border-t border-gray-100 dark:border-[#1e1e1e] m-0 mb-6';
const BODY = 'text-[13px] text-gray-600 dark:text-[#b0b0b0] leading-[1.78] tracking-[0.2px]';
const SUB_H = 'text-[14px] font-bold text-gray-800 dark:text-[#f0f0f0] mt-6 mb-2';
const CODE = 'bg-[#f4f4f4] dark:bg-[#1e1e1e] border border-gray-200 dark:border-[#2a2a2a] px-[6px] py-[2px] font-mono text-[11.5px] text-[#333] dark:text-[#d0d0d0] tracking-[0.1px]';
const CALLOUT = 'bg-[#f8f9fa] dark:bg-[#141414] border border-gray-200 dark:border-[#2a2a2a] px-[18px] py-[14px] my-5 text-[12px] text-gray-500 dark:text-[#888] leading-[1.65] border-l-[3px] border-l-gray-400 dark:border-l-[#444]';

// 8-stage pipeline steps configuration
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

export default function PipelinePage() {
  const [activeTab, setActiveTab] = useState<'tutorial' | 'pipeline'>('tutorial');
  const [activeStep, setActiveStep] = useState(1);

  return (
    <div className="w-full px-6 py-6 box-border font-sans min-h-screen bg-[#f8f9fb] dark:bg-[#0c0c0c] transition-colors duration-200">
      <div className="max-w-[1400px] mx-auto flex flex-col gap-6">
        
        {/* Header Block */}
        <div className="border border-gray-200 dark:border-[#222] bg-white dark:bg-[#121212] p-8 rounded-lg shadow-sm">
          <div className="inline-flex items-center gap-2 border border-gray-300 dark:border-[#333] px-[14px] py-[5px] mb-4">
            <span className="w-[6px] h-[6px] rounded-full bg-blue-600 dark:bg-blue-400 inline-block" />
            <span className="text-[9px] font-bold tracking-[2px] text-gray-500 dark:text-[#888] uppercase">
              Scientific Pipeline Tutorials &amp; Guide
            </span>
          </div>
          <h1 className="text-[26px] font-bold text-gray-800 dark:text-[#f0f0f0] tracking-[-0.5px] m-0 leading-tight">
            Ingestion Pipeline &amp; Data Tutorial
          </h1>
          <p className="text-[13px] text-gray-500 dark:text-[#888] mt-2 max-w-[800px] leading-relaxed">
            LunarAtlas processes raw Chandrayaan-3 LIBS CSV data through a structured 8-stage pipeline.
            Explore the instructions to download original data and read the detailed pipeline stage breakdowns.
          </p>
          
          {/* Tabs Navigation */}
          <div className="flex gap-2 mt-6 border-b border-gray-200 dark:border-[#222] pb-px">
            {[
              { id: 'tutorial', label: 'ISRO PRADAN Download Guide' },
              { id: 'pipeline', label: '8-Stage Ingestion Pipeline' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`text-[11px] font-bold tracking-[1.5px] uppercase border-b-2 px-5 py-3 cursor-pointer transition-colors duration-150 -mb-px ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-gray-600 dark:hover:text-[#ccc]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* ═══════════════════════════════════════════════════════════════
            TAB 2: 8-STAGE PIPELINE STEPPER
        ═══════════════════════════════════════════════════════════════ */}
        {activeTab === 'pipeline' && (
          <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] gap-6 items-start">
            
            {/* Steps Left List */}
            <div className="bg-white dark:bg-[#121212] border border-gray-200 dark:border-[#222] rounded-lg p-5 flex flex-col gap-1.5 shadow-sm">
              <span className="text-[10px] font-bold tracking-[2px] text-gray-400 dark:text-[#555] uppercase mb-4 block">
                Pipeline Ingestion Stages
              </span>
              {PIPELINE_STAGES.map((stage, idx) => {
                const isCurrent = activeStep === (idx + 1);
                return (
                  <button
                    key={stage.n}
                    onClick={() => setActiveStep(idx + 1)}
                    className={`text-left text-[12px] font-medium py-2 px-3 border-0 border-l-2 pl-3 tracking-[0.2px] transition-all cursor-pointer bg-transparent w-full ${
                      isCurrent
                        ? 'text-blue-600 dark:text-blue-400 font-bold border-l-blue-600 dark:border-l-blue-400 bg-gray-50 dark:bg-[#181818]'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-[#fff] border-l-transparent'
                    }`}
                  >
                    Stage {stage.n}: {stage.title}
                  </button>
                );
              })}
            </div>

            {/* Stepper Content Frame */}
            <div className={SEC}>
              {(() => {
                const stage = PIPELINE_STAGES[activeStep - 1];
                return (
                  <div>
                    <div className={SEC_TAG}>Pipeline Stage {stage.n} of 08</div>
                    <h2 className={SEC_H2}>{stage.title}</h2>
                    <hr className={SEC_HR} />

                    <div className="flex flex-col gap-5">
                      <div>
                        <span className="text-[10.5px] text-gray-400 dark:text-gray-500 uppercase font-bold tracking-wide">
                          Underlying Python Module File
                        </span>
                        <div className="mt-1 font-mono text-[12px] bg-[#f8f9fa] dark:bg-[#181818] border border-gray-200 dark:border-[#2b2b2b] px-4 py-2 text-blue-600 dark:text-blue-400 font-semibold w-fit rounded">
                          {stage.script}
                        </div>
                      </div>

                      <div className={BODY}>
                        <span className="text-[10.5px] text-gray-400 dark:text-gray-500 uppercase font-bold tracking-wide block mb-1">
                          Purpose and Logic
                        </span>
                        <p className="m-0 leading-relaxed text-[13px]">
                          {stage.desc}
                        </p>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
                        <div className="bg-[#f8f9fa] dark:bg-[#181818] border border-gray-100 dark:border-[#222] p-4 rounded">
                          <span className="text-[10.5px] text-gray-400 uppercase font-bold tracking-wider">
                            Input Assets
                          </span>
                          <span className="block mt-1.5 text-[12px] text-gray-600 dark:text-gray-300 font-medium">
                            {stage.inputs}
                          </span>
                        </div>
                        <div className="bg-[#f8f9fa] dark:bg-[#181818] border border-gray-100 dark:border-[#222] p-4 rounded">
                          <span className="text-[10.5px] text-gray-400 uppercase font-bold tracking-wider">
                            Output Results
                          </span>
                          <span className="block mt-1.5 text-[12px] text-gray-600 dark:text-gray-300 font-medium">
                            {stage.outputs}
                          </span>
                        </div>
                      </div>

                      {/* Navigation Stepper Buttons */}
                      <div className="mt-6 flex justify-between border-t border-gray-100 dark:border-[#1e1e1e] pt-5">
                        <button
                          disabled={activeStep === 1}
                          onClick={() => setActiveStep(s => s - 1)}
                          className="px-4 py-2 border border-gray-300 dark:border-[#333] text-[11px] font-bold uppercase tracking-wide rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-[#1e1e1e] disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          Previous Stage
                        </button>
                        <button
                          disabled={activeStep === PIPELINE_STAGES.length}
                          onClick={() => setActiveStep(s => s + 1)}
                          className="px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white border-0 text-[11px] font-bold uppercase tracking-wide rounded cursor-pointer hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed"
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
        )}

        {/* ═══════════════════════════════════════════════════════════════
            TAB 3: ISRO PRADAN DOWNLOAD GUIDE
        ═══════════════════════════════════════════════════════════════ */}
        {activeTab === 'tutorial' && (
          <div className="flex flex-col gap-6">
            
            {/* Guide frame */}
            <div className={SEC}>
              <div className={SEC_TAG}>Tutorial document</div>
              <h2 className={SEC_H2}>Downloading Chandrayaan-3 Data from ISRO PRADAN</h2>
              <hr className={SEC_HR} />

              <div className={BODY}>
                <p>
                  The Indian Space Research Organisation (ISRO) releases scientific data from planetary missions
                  through its **Indian Space Science Data Centre (ISSDC)** web portal. Calibrated Level-1 (L1) LIBS data tables
                  for the Pragyan rover are archived under PDS4 compliance and are free for public download.
                </p>

                <div className={SUB_H}>Step 1: Portal Registration</div>
                <p>
                  To download mission datasets, you must register a free user account:
                </p>
                <ol className="list-decimal pl-6 mb-4 flex flex-col gap-1 text-[13px]">
                  <li>Navigate to the official ISRO PRADAN portal URL: <a href="https://pradan.issdc.gov.in/pradan/" target="_blank" rel="noreferrer" className="text-blue-600 dark:text-blue-400 font-semibold hover:underline">https://pradan.issdc.gov.in/pradan/</a></li>
                  <li>Click on **Register** to create a researcher credentials profile.</li>
                  <li>Verify your account through the activation link sent to your registered email address.</li>
                </ol>

                <div className={SUB_H}>Step 2: Locating the LIBS Datasets</div>
                <p>
                  Once logged in, follow this hierarchical structure within the repository file tree:
                </p>
                <div className="bg-[#f7f7f7] dark:bg-[#111] border border-gray-200 dark:border-[#2a2a2a] p-4 rounded font-mono text-[12px] leading-relaxed my-4">
                  <div>ISSDC PRADAN Archive root/</div>
                  <div>└── Chandrayaan-3/</div>
                  <div>    └── PRAGYAN_ROVER/</div>
                  <div>        └── LIBS/</div>
                  <div>            ├── metadata/ (XML labels specifying bounds)</div>
                  <div>            └── data/</div>
                  <div>                └── calibrated/  &lt;-- DOWNLOAD THIS FOLDER</div>
                </div>

                <div className={SUB_H}>Understanding the PDS4 Naming Standard</div>
                <p>
                  Files are structured using Planetary Data System version 4 (PDS4) descriptors. A typical observation
                  comprises two paired files:
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-4">
                  <div className="border border-gray-200 dark:border-[#2b2b2b] p-4 rounded bg-[#fafafa] dark:bg-[#151515]">
                    <span className="font-mono text-[12.5px] font-bold text-gray-800 dark:text-gray-200 block">
                      *.xml (PDS4 Label)
                    </span>
                    <span className="text-[12px] text-gray-500 dark:text-gray-400 mt-2 block leading-normal">
                      Contains logical identifiers (LID), target metadata coordinates, timestamps, and column descriptors for the CSV file.
                    </span>
                  </div>
                  <div className="border border-gray-200 dark:border-[#2b2b2b] p-4 rounded bg-[#fafafa] dark:bg-[#151515]">
                    <span className="font-mono text-[12.5px] font-bold text-gray-800 dark:text-gray-200 block">
                      *.csv (Data Table)
                    </span>
                    <span className="text-[12px] text-gray-500 dark:text-gray-400 mt-2 block leading-normal">
                      The tabular data where each row contains flag bytes, housekeeping variables, and the 2,049 wide intensity columns.
                    </span>
                  </div>
                </div>

                <div className={CALLOUT}>
                  <strong>Naming Breakdown Example:</strong><br />
                  <code className={CODE}>ch3_lib_002_20230825T104221_00_l1.csv</code><br />
                  - <code className="font-bold">ch3</code>: Chandrayaan-3 Mission<br />
                  - <code className="font-bold">lib</code>: LIBS payload instrument<br />
                  - <code className="font-bold">002</code>: Ingestion index sequence<br />
                  - <code className="font-bold">20230825T104221</code>: Timestamp of initial measurement (UTC)<br />
                  - <code className="font-bold">l1</code>: Calibrated Level-1 processing standard
                </div>
              </div>
            </div>

            {/* Ingestion command card */}
            <div className="bg-white dark:bg-[#121212] p-8 border border-gray-200 dark:border-[#222] rounded-lg shadow-sm">
              <h3 className="text-[15px] font-bold text-gray-800 dark:text-[#f0f0f0] mt-0 mb-3 tracking-wide">
                Ingesting Downloaded Data in LunarAtlas
              </h3>
              <p className="text-[13px] text-gray-500 dark:text-gray-400 leading-relaxed m-0 mb-4">
                After downloading raw L1 CSV and XML pairs from the ISRO portal, place them in a directory (e.g. <code className={CODE}>datasets/uploads/</code>)
                and execute the processing script.
              </p>
              <div className="font-mono text-[12px] bg-[#f7f7f7] dark:bg-[#111] border border-gray-200 dark:border-[#2a2a2a] p-4 rounded text-gray-800 dark:text-gray-300 leading-relaxed overflow-x-auto">
                <div># Ingest and process downloaded files automatically</div>
                <div className="text-blue-600 dark:text-blue-400 font-semibold mt-1">python Pipeline/step2_process_l1_data.py "path/to/downloaded/calibrated/"</div>
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
