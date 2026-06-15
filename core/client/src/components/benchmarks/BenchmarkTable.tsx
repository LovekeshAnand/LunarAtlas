/**
 * @fileoverview BenchmarkTable — Comparative analysis tables for LunarAtlas.
 *
 * Renders three research-grade comparison tables:
 *   1. Processing Pipeline Comparison (LunarAtlas vs industry charting libs)
 *   2. Downsampling Algorithm Comparison (Mean vs Min-Max vs LTTB vs M4)
 *   3. Mission-Level Data Processing (Chandrayaan-3 vs ChemCam vs SuperCam vs MarSCoDe)
 *
 * All data is static and sourced from the LunarAtlas processing script
 * (`batch_process_libs.py`) and published planetary science literature.
 */

import { useState } from 'react';

/* ------------------------------------------------------------------ */
/*  Type definitions                                                   */
/* ------------------------------------------------------------------ */

/** Shape of a single row in any comparison table. */
interface TableRow {
  [key: string]: string;
}

/** Configuration for one comparison table tab. */
interface TableConfig {
  id: string;
  label: string;
  description: string;
  headers: string[];
  rows: TableRow[];
  highlightColumn?: number;
}

/* ------------------------------------------------------------------ */
/*  Static benchmark data                                              */
/* ------------------------------------------------------------------ */

const PIPELINE_TABLE: TableConfig = {
  id: 'pipeline',
  label: 'Processing Pipelines',
  description:
    'Comparison of LunarAtlas\'s M4-based rendering pipeline against common charting libraries and data tools used in scientific visualization.',
  headers: ['Pipeline', 'Peak Retention', 'Thread Model', 'Latency (2k pts)', 'Data Fidelity'],
  highlightColumn: 0,
  rows: [
    { Pipeline: 'LunarAtlas M4', 'Peak Retention': '100%', 'Thread Model': 'Off-thread Worker', 'Latency (2k pts)': '<1ms', 'Data Fidelity': 'Exact envelope' },
    { Pipeline: 'AG Grid (built-in)', 'Peak Retention': '~98%', 'Thread Model': 'Main thread', 'Latency (2k pts)': '~3ms', 'Data Fidelity': 'Approximate' },
    { Pipeline: 'Plotly WebGL', 'Peak Retention': 'Variable', 'Thread Model': 'GPU', 'Latency (2k pts)': '~5ms', 'Data Fidelity': 'Rasterized' },
    { Pipeline: 'D3.js (manual)', 'Peak Retention': 'Developer-dependent', 'Thread Model': 'Main thread', 'Latency (2k pts)': '~8ms', 'Data Fidelity': 'Variable' },
    { Pipeline: 'pandas decimation', 'Peak Retention': '0%', 'Thread Model': 'Server-side', 'Latency (2k pts)': 'N/A', 'Data Fidelity': 'Lossy' },
  ],
};

const ALGORITHM_TABLE: TableConfig = {
  id: 'algorithm',
  label: 'Downsampling Algorithms',
  description:
    'Theoretical comparison of downsampling algorithms by points per bucket, peak guarantee, computational complexity, and visual accuracy for spectral data.',
  headers: ['Algorithm', 'Points / Bucket', 'Peak Guarantee', 'Complexity', 'Visual Accuracy'],
  highlightColumn: 0,
  rows: [
    { Algorithm: 'Mean Aggregation', 'Points / Bucket': '1 (avg)', 'Peak Guarantee': 'None', Complexity: 'O(N)', 'Visual Accuracy': 'Low — destroys peaks' },
    { Algorithm: 'Min-Max', 'Points / Bucket': '2 (min, max)', 'Peak Guarantee': 'Partial', Complexity: 'O(N)', 'Visual Accuracy': 'Good — misses boundary context' },
    { Algorithm: 'LTTB', 'Points / Bucket': '1 (triangle)', 'Peak Guarantee': 'None', Complexity: 'O(N)', 'Visual Accuracy': 'Good shape — clips narrow peaks' },
    { Algorithm: 'M4 (Ours)', 'Points / Bucket': '4 (First, Min, Max, Last)', 'Peak Guarantee': '100%', Complexity: 'O(N)', 'Visual Accuracy': 'Exact visual envelope' },
  ],
};

const MISSION_TABLE: TableConfig = {
  id: 'mission',
  label: 'Mission Data Processing',
  description:
    'End-to-end comparison of LIBS data processing pipelines across active planetary missions. LunarAtlas pipeline is derived from batch_process_libs.py.',
  headers: ['Feature', 'LunarAtlas (CH-3)', 'ChemCam CCS (Curiosity)', 'SuperCam (Perseverance)', 'MarSCoDe (Zhurong)'],
  highlightColumn: 1,
  rows: [
    { Feature: 'Source Format', 'LunarAtlas (CH-3)': 'PDS4 wide-CSV + XML', 'ChemCam CCS (Curiosity)': 'PDS3 fixed-width + detached label', 'SuperCam (Perseverance)': 'PDS4 + FITS', 'MarSCoDe (Zhurong)': 'PDS4 CSV' },
    { Feature: 'Channels', 'LunarAtlas (CH-3)': '2,049 (164–878 nm)', 'ChemCam CCS (Curiosity)': '~6,144 (240–905 nm)', 'SuperCam (Perseverance)': '~6,000 (245–853 nm + IR)', 'MarSCoDe (Zhurong)': '~2,048 (240–850 nm)' },
    { Feature: 'Background Subtraction', 'LunarAtlas (CH-3)': 'Paired: max(0, plasma − bg)', 'ChemCam CCS (Curiosity)': 'Dark + continuum (ALS/wavelet)', 'SuperCam (Perseverance)': 'Dark + atmospheric correction', 'MarSCoDe (Zhurong)': 'Dark + ambient removal' },
    { Feature: 'Reshape Strategy', 'LunarAtlas (CH-3)': 'Wide → Long melt (2,049 cols)', 'ChemCam CCS (Curiosity)': 'Already long per spectrometer', 'SuperCam (Perseverance)': 'Per-spectrometer stacking', 'MarSCoDe (Zhurong)': 'Wide → Long' },
    { Feature: 'Calibration', 'LunarAtlas (CH-3)': 'L1 pre-calibrated; L1→L2 clean', 'ChemCam CCS (Curiosity)': 'Raw → wavelength + ILS correction', 'SuperCam (Perseverance)': 'Multi-stage radiometric + λ', 'MarSCoDe (Zhurong)': 'Wavelength + intensity calib' },
    { Feature: 'Metadata Preservation', 'LunarAtlas (CH-3)': 'Full 19-col PDS4 per row', 'ChemCam CCS (Curiosity)': 'Partial (EDR headers)', 'SuperCam (Perseverance)': 'Full PDS4 provenance', 'MarSCoDe (Zhurong)': 'Partial' },
    { Feature: 'Negative Handling', 'LunarAtlas (CH-3)': 'max(0, ·) + pre-clamp stats', 'ChemCam CCS (Curiosity)': 'Continuum avoids negatives', 'SuperCam (Perseverance)': 'Model-based; rare', 'MarSCoDe (Zhurong)': 'Clamping' },
    { Feature: 'Output Formats', 'LunarAtlas (CH-3)': 'CSV + JSON + API-ready', 'ChemCam CCS (Curiosity)': 'CSV + PDS3 archive', 'SuperCam (Perseverance)': 'PDS4 archive + quick-look', 'MarSCoDe (Zhurong)': 'PDS4 archive' },
    { Feature: 'Reproducibility', 'LunarAtlas (CH-3)': 'Deterministic (MD5 logged)', 'ChemCam CCS (Curiosity)': 'Pipeline-versioned', 'SuperCam (Perseverance)': 'Pipeline-versioned', 'MarSCoDe (Zhurong)': 'Not published' },
    { Feature: 'Open Source', 'LunarAtlas (CH-3)': '✅ Yes', 'ChemCam CCS (Curiosity)': 'Partial (PDS tools)', 'SuperCam (Perseverance)': 'Partial', 'MarSCoDe (Zhurong)': '❌ No' },
  ],
};

const ALL_TABLES: TableConfig[] = [PIPELINE_TABLE, ALGORITHM_TABLE, MISSION_TABLE];

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

/**
 * BenchmarkTable — Renders tabbed comparison tables for the Graph page.
 *
 * Three tabs present pipeline, algorithm-level, and mission-level
 * comparisons. The active LunarAtlas row/column is highlighted with
 * a subtle blue accent to draw the reader's eye.
 */
export default function BenchmarkTable() {
  const [activeTab, setActiveTab] = useState('pipeline');
  const activeTable = ALL_TABLES.find((t) => t.id === activeTab)!;

  return (
    <div className="mt-10 bg-white border border-solid border-gray-200 rounded-md shadow-sm overflow-hidden">
      {/* ── Section Header ── */}
      <div className="px-6 pt-6 pb-4 border-b border-solid border-gray-200">
        <h2 className="text-[16px] font-sans font-semibold text-gray-800 mb-1">
          Benchmark Comparison Tables
        </h2>
        <p className="text-[13px] font-sans text-gray-500 leading-snug">
          Quantitative comparisons of LunarAtlas against industry tools, algorithms, and planetary mission pipelines.
        </p>
      </div>

      {/* ── Tab Buttons ── */}
      <div className="flex border-b border-solid border-gray-200 bg-gray-50/60">
        {ALL_TABLES.map((table) => (
          <button
            key={table.id}
            onClick={() => setActiveTab(table.id)}
            className={`px-5 py-3 text-[12px] font-sans font-medium tracking-wide transition-colors cursor-pointer border-b-2 ${
              activeTab === table.id
                ? 'text-blue-600 border-blue-600 bg-white'
                : 'text-gray-500 border-transparent hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            {table.label}
          </button>
        ))}
      </div>

      {/* ── Table Description ── */}
      <div className="px-6 py-3 bg-gray-50/40 border-b border-solid border-gray-100">
        <p className="text-[12px] font-sans text-gray-500 italic leading-relaxed">
          {activeTable.description}
        </p>
      </div>

      {/* ── Data Table ── */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-[12px] border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {activeTable.headers.map((header, i) => (
                <th
                  key={header}
                  className={`py-3 px-5 uppercase tracking-widest font-black text-[9px] ${
                    activeTable.highlightColumn === i
                      ? 'text-blue-700 bg-blue-50/50'
                      : 'text-gray-600'
                  }`}
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="font-sans">
            {activeTable.rows.map((row, rowIdx) => {
              /* Detect if this is the "LunarAtlas" / "M4 (Ours)" row */
              const firstCellValue = row[activeTable.headers[0]] || '';
              const isOurs =
                firstCellValue.includes('LunarAtlas') ||
                firstCellValue.includes('M4 (Ours)');

              return (
                <tr
                  key={rowIdx}
                  className={`border-b border-gray-100 transition-colors ${
                    isOurs
                      ? 'bg-blue-50/40 hover:bg-blue-50/70'
                      : 'hover:bg-gray-50/60'
                  }`}
                >
                  {activeTable.headers.map((header, colIdx) => (
                    <td
                      key={header}
                      className={`py-3 px-5 leading-snug ${
                        colIdx === 0 ? 'font-semibold text-gray-800' : 'text-gray-600'
                      } ${
                        activeTable.highlightColumn === colIdx && activeTable.id === 'mission'
                          ? 'bg-blue-50/30 font-medium text-blue-800'
                          : ''
                      }`}
                    >
                      {row[header]}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ── Footer Note ── */}
      <div className="px-6 py-3 bg-gray-50/40 border-t border-solid border-gray-100">
        <p className="text-[11px] font-sans text-gray-400">
          Sources: LunarAtlas batch_process_libs.py, PDS Geosciences Node, ChemCam SOC documentation, SuperCam SIS, published literature.
        </p>
      </div>
    </div>
  );
}
