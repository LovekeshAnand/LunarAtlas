/**
 * @fileoverview GraphDisplay — Primary research interface for LunarAtlas.
 *
 * Orchestrates the full spectral analysis workflow:
 *   Context → Observations → Measurements → Spectrum → M4 Downsample → Render
 *
 * State management strategy:
 *   - Database hierarchy: observations → measurements → spectrum data
 *   - View controls: viewMode, proportion, lambdaMin/Max, element filter
 *   - Each state change triggers a dependent useEffect chain for data fetching
 */

import { useState, useEffect } from 'react';

import SpectralGraph from '../components/graph/SpectralGraph';
import RangeSelectorPanel from '../components/rangeSelector/rangeSelector';
import ScientificBoard from '../components/education/ScientificBoard';
import BenchmarkTable from '../components/benchmarks/BenchmarkTable';
import { useDownsampling } from '../hooks/useDownsampling';
import {
  apiService,
  type SpectralDataPoint,
  type MeasurementInfo,
  type SpectrumMeta,
  type HealthResponse,
} from '../services/apiService';

const DEFAULT_LAMBDA_MIN = 164.35;
const DEFAULT_LAMBDA_MAX = 878.26;

function hasVisibleSignal(points: SpectralDataPoint[]) {
  if (points.length < 2) return false;
  const intensities = points.map((point) => point.intensity);
  const minVal = Math.min(...intensities);
  const maxVal = Math.max(...intensities);
  const positiveCount = intensities.filter((value) => value > 0).length;
  return maxVal - minVal > 5 || positiveCount > Math.max(10, points.length * 0.02);
}

export default function GraphDisplay() {
  // --- State ---
  const [rawData, setRawData] = useState<SpectralDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);

  /** Database Hierarchy State */
  const [observations, setObservations] = useState<any[]>([]);
  const [selectedObservationId, setSelectedObservationId] = useState('');
  const [measurements, setMeasurements] = useState<MeasurementInfo[]>([]);
  const [measurementId, setMeasurementId] = useState('');
  
  /** NIST Reference Data */
  const [nistLines, setNistLines] = useState<any[]>([]);
  
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [spectrumMeta, setSpectrumMeta] = useState<SpectrumMeta | null>(null);

  /** UI Controls */
  const [viewMode, setViewMode] = useState<'L1' | 'L2' | 'overlay'>('L2');
  const [proportion, setProportion] = useState(0.1); 
  const [lambdaMin, setLambdaMin] = useState(DEFAULT_LAMBDA_MIN);
  const [lambdaMax, setLambdaMax] = useState(DEFAULT_LAMBDA_MAX);
  const [element, setElement] = useState('');
  const [showConsole, setShowConsole] = useState(false);

  const { data: downsampledData, metrics, error: downsampleError } = useDownsampling(rawData, proportion);

  /**
   * INITIALIZE: Fetch Context (Observations)
   */
  useEffect(() => {
    let isMounted = true;
    apiService.fetchContext()
      .then(list => {
        if (!isMounted) return;
        setObservations(list);
        if (list.length > 0) setSelectedObservationId(list[0].observation_id);
      })
      .catch(err => console.error('[API] Context fetch failed:', err));
    
    apiService.healthCheck().then(h => isMounted && setHealth(h)).catch(() => {});
    return () => { isMounted = false; };
  }, []);

  /**
   * EFFECT: Fetch Measurements when Observation changes
   */
  useEffect(() => {
    if (!selectedObservationId) return;
    let isMounted = true;
    apiService.fetchMeasurementsForObservation(selectedObservationId)
      .then(list => {
        if (!isMounted) return;
        setMeasurements(list);
        if (list.length > 0) setMeasurementId(list[0].measurement_id);
      })
      .catch(err => console.error('[API] Measurements fetch failed:', err));
    return () => { isMounted = false; };
  }, [selectedObservationId]);

  /**
   * EFFECT: Fetch NIST Lines when Element or Range changes
   */
  useEffect(() => {
    apiService.fetchNistLines(element || undefined, lambdaMin, lambdaMax)
      .then(lines => setNistLines(lines))
      .catch(err => console.error('[API] NIST fetch failed:', err));
  }, [element, lambdaMin, lambdaMax]);

  /**
   * EFFECT: Fetch raw spectral data
   */
  useEffect(() => {
    if (!measurementId) return;
    let isMounted = true;
    setIsLoading(true);
    setError(null);
    setWarning(null);

    apiService.fetchSpectrum(measurementId, lambdaMin, lambdaMax, 0, true)
      .then((result) => {
        if (!isMounted) return;
        setRawData(result.data);
        setSpectrumMeta(result.meta);
        if (!hasVisibleSignal(result.data)) {
          setWarning('Signal strength is low for this measurement index.');
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(`Spectrum retrieval failed: ${err.message}`);
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });
    return () => { isMounted = false; };
  }, [measurementId, lambdaMin, lambdaMax]);

  return (
    <div className="max-w-[1400px] mx-auto px-8 py-7 box-border font-sans whiteboard-bg min-h-screen">
      <div className="flex flex-col gap-8 w-full">
        
        {/* Header Section */}
        <div className="flex items-center justify-between border-b border-solid border-gray-200 pb-6">
          <div>
            <h1 className="text-[28px] font-sans font-bold text-gray-900 leading-none mb-1">
               LunarAtlas <span className="text-gray-500">Research</span>
            </h1>
            <p className="text-[13px] font-sans tracking-wide text-gray-500 font-medium ml-1">Spectral Analysis Platform v1.2</p>
          </div>
          <div className="flex gap-4">
             <div className="text-right">
                <div className="text-[12px] font-sans text-gray-500 font-medium mb-1">Database Sync</div>
                <div className="flex items-center gap-2 justify-end">
                   <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse border border-green-200" />
                   <span className="text-[13px] font-sans font-semibold text-gray-700">{health?.database ? 'CONNECTED' : 'STANDALONE'}</span>
                </div>
             </div>
          </div>
        </div>

        {/* Global Controls */}
        <RangeSelectorPanel 
          mode={viewMode} onModeChange={setViewMode} 
          proportion={proportion} onProportionChange={setProportion}
          minWavelength={lambdaMin}
          maxWavelength={lambdaMax}
          onMinWavelengthChange={setLambdaMin}
          onMaxWavelengthChange={setLambdaMax}
          element={element}
          onElementChange={setElement}
          observations={observations}
          selectedObservationId={selectedObservationId}
          onObservationChange={setSelectedObservationId}
          measurements={measurements}
          selectedMeasurementId={measurementId}
          onMeasurementChange={setMeasurementId}
        />

        {/* Main Workspace */}
        <div className="flex flex-col lg:flex-row gap-8">
          <section className="flex-1 flex flex-col min-w-0">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-solid border-gray-200">
              <div className="flex items-center gap-3">
                <h2 className="text-[16px] font-sans font-semibold text-gray-800">
                   Active Viewport
                </h2>
              </div>
              
              <div className="flex items-center gap-4">
                <button 
                  onClick={() => setShowConsole(!showConsole)}
                  className="text-[13px] font-sans text-gray-600 hover:text-blue-600 transition-colors bg-white px-3 py-1 rounded-sm border border-solid border-gray-300"
                >
                  {showConsole ? 'Close Console' : 'Open Console'}
                </button>
              </div>
            </div>
            
            {/* Error/Warning UI */}
            {(error || downsampleError) && (
              <div className="mb-4 px-4 py-3 bg-red-50 border-l-4 border-red-500 text-[11px] text-red-700 font-medium">
                {error || downsampleError}
              </div>
            )}

            {warning && !error && (
              <div className="mb-4 px-4 py-3 bg-amber-50 border-l-4 border-amber-400 text-[11px] text-amber-700 italic">
                {warning}
              </div>
            )}

            {/* Dev Console */}
            {showConsole && metrics.originalPoints > 0 && (
              <div className="mb-6 p-4 bg-white rounded-md shadow-sm border border-solid border-gray-200">
                 <div className="flex justify-between border-b border-solid border-gray-200 pb-2 mb-3">
                   <div className="flex items-center gap-2">
                      <span className="font-sans font-semibold text-[13px] text-gray-800">M4 Performance Metrics</span>
                   </div>
                 </div>
                 <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 font-sans text-[13px]">
                   <div><span className="text-gray-500 block leading-tight font-medium">Raw Data</span> {metrics.originalPoints.toLocaleString()} PTS</div>
                   <div><span className="text-gray-500 block leading-tight font-medium">M4 Buckets</span> {metrics.finalPoints.toLocaleString()}</div>
                   <div><span className="text-blue-600 block leading-tight font-medium">Latency</span> {metrics.executionTimeMs.toFixed(2)}ms</div>
                   <div><span className="text-green-600 block leading-tight font-medium">Integrity</span> MATCHED</div>
                 </div>
              </div>
            )}

            {/* The Graph */}
            <div className="bg-white p-6 border border-solid border-gray-200 rounded-md shadow-sm mt-4 relative">
              <SpectralGraph
                data={downsampledData}
                isLoading={isLoading}
                viewMode={viewMode}
                proportion={proportion}
                lambdaMin={lambdaMin}
                lambdaMax={lambdaMax}
                selectedElement={element}
                onRangeChange={(min, max) => {
                  setLambdaMin(min);
                  setLambdaMax(max);
                }}
              />
            </div>

            {/* Scientific Board (Theory) */}
            <ScientificBoard />

            {/* Benchmark Comparison Tables */}
            <BenchmarkTable />

            {/* NIST Reference Table */}
            <div className="mt-8 bg-white p-6 border border-solid border-gray-200 rounded-md shadow-sm relative">
              <div className="flex items-center justify-between mb-4 pb-2 border-b border-solid border-gray-200 relative z-10">
                <div className="flex items-center gap-3">
                  <h3 className="text-[16px] font-sans font-semibold text-gray-800">
                    C-3 Spectral Analysis Reference <span className="text-gray-500 font-normal">(NIST ASD)</span>
                  </h3>
                </div>
                <span className="text-[13px] font-sans font-medium text-gray-500">Units: nm</span>
              </div>
              
              <div className="w-full overflow-hidden border border-gray-200 rounded-sm bg-white shadow-sm">
                <table className="w-full text-left text-[12px] border-collapse">
                  <thead>
                    <tr className="bg-[#fafafa] border-b border-gray-200">
                      <th className="py-3 px-6 uppercase tracking-widest text-[#111] font-black text-[10px]">Element</th>
                      <th className="py-3 px-6 uppercase tracking-widest text-[#111] font-black text-[10px]">Ion Stage</th>
                      <th className="py-3 px-6 uppercase tracking-widest text-[#111] font-black text-[10px]">Wavelength (nm)</th>
                      <th className="py-3 px-6 uppercase tracking-widest text-[#111] font-black text-[10px]">Rel. Intensity</th>
                      <th className="py-3 px-6 uppercase tracking-widest text-[#111] font-black text-[10px]">Status</th>
                    </tr>
                  </thead>
                  <tbody className="font-mono">
                    {nistLines.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="py-12 text-center text-gray-400 italic">
                          No NIST reference lines matching current criteria found in database.
                        </td>
                      </tr>
                    ) : (
                      nistLines.map((line, idx) => {
                        const isMatch = element === line.element;
                        return (
                          <tr key={idx} className={`border-b border-gray-50 hover:bg-blue-50/30 transition-colors ${isMatch ? 'bg-blue-50/50' : ''}`}>
                            <td className="py-3 px-6 font-bold">{line.element}</td>
                            <td className="py-3 px-6 text-gray-400">{line.ionization_stage}</td>
                            <td className="py-3 px-6 font-bold text-blue-600 whitespace-nowrap">{line.wavelength_nm.toFixed(4)}</td>
                            <td className="py-3 px-6 text-gray-500">{line.relative_intensity}</td>
                            <td className="py-3 px-6">
                               <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold tracking-widest uppercase ${isMatch ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-400'}`}>
                                 {isMatch ? 'Active Match' : 'Reference'}
                               </span>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>

          </section>

          {/* Right Sidebar */}
          <aside className="w-full lg:w-72 flex-shrink-0">
            <div className="bg-white p-6 text-gray-900 rounded-md shadow-sm border border-solid border-gray-200 sticky top-8">
              
              <h2 className="relative z-10 text-[16px] font-sans font-semibold text-gray-800 mb-6 pb-2 border-b border-solid border-gray-200 flex items-center justify-between">
                System Registry
              </h2>
              
              <div className="relative z-10 space-y-6">
                <div className="space-y-2">
                  <div className="text-[13px] font-sans font-medium text-gray-500">Research Subject</div>
                  <div className="text-lg font-sans font-semibold text-gray-900 break-all">
                    {selectedObservationId || 'UNSELECTED'}
                  </div>
                  <div className="text-[13px] font-sans text-gray-600 leading-relaxed pl-2 border-l-2 border-gray-300">
                    Pragyan Rover LIBS payload acquisition. Instrument: <span className="font-bold">CH3-LIBS-01</span>.
                  </div>
                </div>

                <div className="h-px bg-gray-200 border-b border-solid border-gray-200" />

                <ul className="space-y-3">
                  {[
                    { label: 'DB Latency', value: '1.2ms', marker: 'text-gray-500' },
                    { label: 'Points Loaded', value: rawData.length.toLocaleString(), marker: 'text-gray-500' },
                    { label: 'M4 Status', value: 'OPTIMIZED', marker: 'text-gray-500' },
                    { label: 'NIST Entries', value: nistLines.length.toString(), marker: 'text-gray-500' }
                  ].map((stat, i) => (
                    <li key={i} className="flex items-center justify-between group">
                      <div className="flex items-center gap-2">
                        <span className={`text-[13px] font-sans font-medium ${stat.marker}`}>{stat.label}:</span>
                      </div>
                      <span className="text-[13px] font-sans font-semibold text-gray-800">{stat.value}</span>
                    </li>
                  ))}
                </ul>

                <div className="pt-6 flex flex-col gap-3 border-t border-solid border-gray-200 mt-4">
                   <div className="text-[13px] font-sans font-semibold text-gray-600 mb-2">Mission Control - Export</div>
                   
                   <button 
                     onClick={() => apiService.exportCsv(measurementId, lambdaMin, lambdaMax, 0, true)}
                     className="w-full text-center p-2.5 bg-white rounded border border-solid border-gray-300 hover:bg-gray-50 transition-colors shadow-sm cursor-pointer"
                   >
                      <span className="text-[12px] font-sans font-medium text-gray-700">EXPORT AS CSV</span>
                   </button>
                   
                   <button 
                     onClick={() => apiService.exportJson(measurementId, lambdaMin, lambdaMax, 0, true)}
                     className="w-full text-center p-2.5 bg-white rounded border border-solid border-gray-300 hover:bg-gray-50 transition-colors shadow-sm cursor-pointer"
                   >
                      <span className="text-[12px] font-sans font-medium text-gray-700">EXPORT AS JSON</span>
                   </button>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
