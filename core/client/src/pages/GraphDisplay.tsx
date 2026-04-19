import { useState, useEffect } from 'react';
import { Activity, Check, CircleDot, Info } from 'lucide-react';

import SpectralGraph from '../components/graph/SpectralGraph';
import RangeSelectorPanel from '../components/rangeSelector/rangeSelector';
import { mockDataService, type SpectralData, type PeakDetection } from '../services/mockDataService';

/**
 * @fileoverview Main Spectral Graph Page.
 * Orchestrates the data flow between the Range Selector and the Spectral Visualization.
 * Implements the L1 -> L2 processing pipeline visualization and metadata management.
 */

export default function GraphDisplay() {
  // --- State Architecture ---
  const [data, setData] = useState<SpectralData[]>([]);
  const [peaks, setPeaks] = useState<PeakDetection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  /** Current active measurement ID. Pinning a specific plasma/background shot pair. */
  const [measurementId, setMeasurementId] = useState('m_001');
  
  /** Global processing context: L1 (Raw/Calibrated) or L2 (Cleaned/Subtracted) */
  const [viewMode, setViewMode] = useState<'L1' | 'L2'>('L2');
  
  /** Discrete zoom level for detailed spectral feature analysis */
  const [zoom, setZoom] = useState(1);

  /**
   * EFFECT: Synchronizes spectral data when the Measurement ID changes.
   * Simulates a production backend fetch with error handling.
   */
  useEffect(() => {
    let isMounted = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsLoading(true);


    mockDataService.fetchSpectrum(measurementId)
      .then((res) => {
        if (!isMounted) return;
        setData(res.data);
        setPeaks(res.peaks);
      })
      .catch((err) => {
        console.error('[Pipeline Error] Failed to fetch spectral sequence:', err);
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => { isMounted = false; };
  }, [measurementId]);


  return (
    <div className="max-w-[1400px] mx-auto px-8 py-7 box-border font-sans">
      <div className="flex flex-col gap-6 w-full">
        <div className="flex items-center justify-between border-b border-gray-100 dark:border-[#222] pb-4">
          <h1 className="text-[14px] font-bold tracking-[2px] text-[#111] dark:text-[#f0f0f0] uppercase">
             Target Parameters
          </h1>
        </div>



      {/* Restored detailed range selector panel */}
      <RangeSelectorPanel 
        mode={viewMode} onModeChange={setViewMode} 
        zoom={zoom} onZoomChange={setZoom}
      />


      <div className="flex flex-col lg:flex-row gap-6 mt-4">
        {/* Main Graph Area */}
        <section className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <Activity size={16} className="text-[#111]" />
              <h2 className="text-[14px] font-bold tracking-[2px] text-[#111] uppercase">
                 Analysis-Ready Spectra
              </h2>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 group relative">
                <Info size={14} className="text-[#999] hover:text-[#111] cursor-help transition-colors" />
                <div className="absolute right-0 top-full mt-2 w-80 p-4 bg-[#111] text-white text-[11px] leading-relaxed hidden group-hover:block z-50 rounded-sm shadow-xl">
                  <div className="font-bold uppercase tracking-wider mb-2 border-b border-gray-700 pb-1">What is Measurement ID?</div>
                  The formal definition of a Measurement ID is the sequential integer that pairs a specific plasma shot with its nearest chronological background acquisition. This ensures we don't accidentally interleave missing shots or temporal telemetry deviations.
                </div>
              </div>
              <select 
                value={measurementId}
                onChange={(e) => setMeasurementId(e.target.value)}
                className="bg-transparent border-b border-gray-300 py-1 text-[11px] font-bold text-[#111] uppercase focus:outline-none focus:border-[#111]"
              >
                <option value="m_001">Measurement 001</option>
                <option value="m_002">Measurement 002</option>
                <option value="m_003">Measurement 003</option>
                <option value="m_004">Measurement 004</option>
              </select>
            </div>
          </div>
          
          <SpectralGraph data={data} isLoading={isLoading} viewMode={viewMode} zoom={zoom} />

          {/* Educational Backend Pipeline Algorithm Explanation */}
          {/* <div className="mt-8 bg-gray-50 border border-gray-200 p-6 rounded-sm">
             <h3 className="text-[12px] font-bold tracking-[2px] text-[#111] uppercase mb-4 pb-2 border-b border-gray-200">
               Backend Algorithms & Pipeline Simulation
             </h3>
             <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Layers size={14} className="text-[#111]" />
                    <h4 className="text-[10px] font-bold uppercase tracking-widest text-[#333]">Background Subtraction</h4>
                  </div>
                  <p className="text-[11px] text-gray-600 leading-relaxed font-sans">
                    Computed channel-by-channel via <code>I_clean(λ) = max(0, I_plasma(λ) - I_bg(λ))</code>. Non-informative negative differences are clamped to zero. The baseline suppression factor achieved is approximately 7.1.
                  </p>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Beaker size={14} className="text-[#111]" />
                    <h4 className="text-[10px] font-bold uppercase tracking-widest text-[#333]">SNR Thresholding & Peak Detection</h4>
                  </div>
                  <p className="text-[11px] text-gray-600 leading-relaxed font-sans">
                    Applies a dual-pass detection phase. The local noise <code>σ_local</code> is computed from the suppressed variance over a 50-channel window. Only peaks exhibiting an SNR &gt; 3σ are retained and fitted against the NIST database.
                  </p>
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Cpu size={14} className="text-[#111]" />
                    <h4 className="text-[10px] font-bold uppercase tracking-widest text-[#333]">Adaptive Downsampling</h4>
                  </div>
                  <p className="text-[11px] text-gray-600 leading-relaxed font-sans">
                     Utilizes a zoom-aware Saturation Ratio (ρ). When ρ &gt; 1, multiple data channels are grouped, preserving narrow emission-line features through continuous max/min envelope peak-locking.
                  </p>
                </div>
             </div>
          </div> */}

          {/* Validated Peaks Data Table */}
          <div className="mt-8">
            <h3 className="text-[12px] font-bold tracking-[2px] text-[#111] uppercase mb-4 pb-2 border-b border-gray-200 flex justify-between">
              <span>Validated Elemental Signatures</span>
              <span className="text-[10px] text-gray-400 normal-case tracking-normal font-normal">SNR &gt; 3σ vs NIST</span>
            </h3>
            <div className="w-full overflow-x-auto">
              <table className="w-full text-left text-[11px] border-collapse">
                <thead>
                  <tr className="bg-gray-50 border-y border-gray-200">
                    <th className="py-2 px-4 uppercase tracking-widest text-gray-500 font-bold">Element</th>
                    <th className="py-2 px-4 uppercase tracking-widest text-gray-500 font-bold">Matched Wavelength</th>
                    <th className="py-2 px-4 uppercase tracking-widest text-gray-500 font-bold">Intensity (cts)</th>
                    <th className="py-2 px-4 uppercase tracking-widest text-gray-500 font-bold">Signal-to-Noise</th>
                  </tr>
                </thead>
                <tbody>
                  {peaks.length === 0 && !isLoading && (
                    <tr>
                      <td colSpan={4} className="text-center py-6 text-gray-400">No significant peaks detected in current sequence.</td>
                    </tr>
                  )}
                  {peaks.map((peak, i) => (
                    <tr key={i} className="border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors">
                      <td className="py-2.5 px-4 font-bold text-[#111]">{peak.element}</td>
                      <td className="py-2.5 px-4 text-gray-600">{peak.wavelength.toFixed(2)} nm</td>
                      <td className="py-2.5 px-4 text-gray-600">{peak.intensity}</td>
                      <td className="py-2.5 px-4">
                        <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded-sm font-bold">{peak.snr}σ</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Pipeline Process Indicator Sidebar */}
        <aside className="w-full lg:w-64 flex-shrink-0">
          <div className="border border-gray-200 p-6 bg-[#111] rounded-sm sticky top-6">
            <h2 className="text-[10px] font-bold tracking-[3px] text-white uppercase mb-6 pb-2 border-b border-gray-700">
              Pipeline Flow Status
            </h2>
            <ul className="space-y-6">
              {[
                { label: 'PDS4 XML Extraction', desc: 'Metadata & columns parsed', done: true },
                { label: 'Wide-to-Long', desc: 'Reshaping across 2049 cols', done: true },
                { label: 'Proximity Pairing', desc: 'bg*(p_k) matched |Δt| < 5s', done: true },
                { label: 'Background Subtracted', desc: 'Negative values clamped', done: true },
                { label: 'Isotropic Gaussian Fit', desc: 'NIST ref vs local variance', done: !isLoading },
                { label: 'Min-Max Downsampled', desc: 'Zoom locking active', done: !isLoading }
              ].map((step, idx) => (
                <li key={idx} className="flex items-start gap-3 relative">
                 {idx < 5 && (
                    <div className={`absolute top-5 bottom-[-20px] left-[6px] w-[1px] ${step.done ? 'bg-gray-600' : 'bg-transparent'}`} />
                 )}
                  <div className="relative z-10 bg-[#111] pb-1">
                    {step.done ? (
                      <Check size={14} className="text-white shrink-0 mt-[1px]" />
                    ) : (
                      <CircleDot size={14} className="text-gray-500 shrink-0 mt-[1px] animate-pulse" />
                    )}
                  </div>
                  <div>
                    <div className={`text-[10px] font-bold uppercase tracking-wide leading-tight ${step.done ? 'text-white' : 'text-gray-500'}`}>
                      {step.label}
                    </div>
                    <div className={`text-[9px] mt-1 ${step.done ? 'text-gray-400' : 'text-gray-600'}`}>{step.desc}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>
    </div>
    </div>
  );
}

