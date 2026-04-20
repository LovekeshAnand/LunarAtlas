import { useState, useEffect } from 'react';
import { Activity, Zap, Table as TableIcon } from 'lucide-react';

import SpectralGraph from '../components/graph/SpectralGraph';
import RangeSelectorPanel from '../components/rangeSelector/rangeSelector';
import ScientificBoard from '../components/education/ScientificBoard';
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
  const [viewMode, setViewMode] = useState<'L1' | 'L2'>('L2');
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
    <div className="max-w-[1400px] mx-auto px-8 py-7 box-border font-sans bg-[#fcfcfc] min-h-screen">
      <div className="flex flex-col gap-8 w-full">
        
        {/* Header Section */}
        <div className="flex items-center justify-between border-b-[2px] border-[#111] pb-6">
          <div>
            <h1 className="text-[28px] font-black tracking-[-1px] text-[#111] uppercase leading-none mb-1">
               LunarAtlas <span className="text-blue-600">Research</span>
            </h1>
            <p className="text-[10px] uppercase tracking-[3px] text-gray-400 font-bold">Spectral Analysis Platform v1.2</p>
          </div>
          <div className="flex gap-4">
             <div className="text-right">
                <div className="text-[9px] uppercase tracking-widest text-gray-400 font-bold mb-1">Database Sync</div>
                <div className="flex items-center gap-2 justify-end">
                   <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                   <span className="text-xs font-mono font-bold text-[#111]">{health?.database ? 'CONNECTED' : 'STANDALONE'}</span>
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
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <Activity size={18} className="text-blue-600" />
                <h2 className="text-[14px] font-black tracking-[1.5px] text-[#111] uppercase italic">
                   Active Viewport
                </h2>
              </div>
              
              <div className="flex items-center gap-4">
                <button 
                  onClick={() => setShowConsole(!showConsole)}
                  className="text-[9px] font-black tracking-[1.5px] text-gray-400 hover:text-blue-600 uppercase transition-colors"
                >
                  {showConsole ? '[ Close Console ]' : '[ Open Console ]'}
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
              <div className="mb-6 p-4 bg-[#111] rounded-sm font-mono text-[10px] text-blue-400 shadow-2xl border border-blue-900/30">
                 <div className="flex justify-between border-b border-gray-800 pb-2 mb-3">
                   <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                      <span className="font-bold uppercase tracking-widest text-gray-400">LTTB Performance Metrics</span>
                   </div>
                   <span className="text-gray-600">CLIENT-SIDE THREAD: ACTIVE</span>
                 </div>
                 <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                   <div><span className="text-gray-500 block mb-1 uppercase tracking-tighter">Raw Data</span> {metrics.originalPoints.toLocaleString()} PTS</div>
                   <div><span className="text-gray-500 block mb-1 uppercase tracking-tighter">LTTB Buckets</span> {metrics.finalPoints.toLocaleString()}</div>
                   <div><span className="text-gray-500 block mb-1 uppercase tracking-tighter">Latency</span> {metrics.executionTimeMs.toFixed(2)}ms</div>
                   <div><span className="text-gray-500 block mb-1 uppercase tracking-tighter">Integrity</span> MATCHED</div>
                 </div>
              </div>
            )}

            {/* The Graph */}
            <div className="bg-white p-4 border border-gray-100 rounded-sm shadow-sm ring-1 ring-black/5">
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

            {/* NIST Reference Table */}
            <div className="mt-8">
              <div className="flex items-center justify-between mb-4 pb-2 border-b-2 border-[#111]">
                <div className="flex items-center gap-3">
                  <TableIcon size={18} className="text-blue-600" />
                  <h3 className="text-[14px] font-black tracking-[1.5px] text-[#111] uppercase">
                    C-3 Spectral Analysis Reference <span className="text-gray-400 font-normal ml-2">(NIST ASD)</span>
                  </h3>
                </div>
                <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Wavelength Units: Nanometers (nm)</span>
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
            <div className="bg-[#111] p-6 text-white rounded-sm sticky top-8 shadow-2xl overflow-hidden">
              {/* Decorative background element */}
              <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-600/10 rounded-full blur-3xl" />
              
              <h2 className="relative z-10 text-[10px] font-black tracking-[3px] text-white uppercase mb-8 pb-3 border-b border-white/10 flex items-center justify-between">
                System Registry
                <div className="w-2 h-2 rounded-full bg-green-500" />
              </h2>
              
              <div className="relative z-10 space-y-8">
                <div className="space-y-4">
                  <div className="text-[9px] uppercase tracking-widest text-gray-500 font-bold">Research Subject</div>
                  <div className="text-xl font-black italic tracking-tighter text-blue-400 truncate" title={selectedObservationId}>
                    {selectedObservationId || 'UNSELECTED'}
                  </div>
                  <div className="text-[11px] text-white/60 leading-relaxed border-l-2 border-blue-500 pl-3">
                    Pragyan Rover LIBS payload acquisition. Instrument: <span className="text-white font-bold">CH3-LIBS-01</span>.
                  </div>
                </div>

                <div className="h-px bg-white/5" />

                <ul className="space-y-4 overflow-hidden">
                  {[
                    { label: 'DB Latency', value: '1.2ms', color: 'bg-green-500' },
                    { label: 'Points Loaded', value: rawData.length.toLocaleString(), color: 'bg-blue-500' },
                    { label: 'LTTB Status', value: 'OPTIMIZED', color: 'bg-blue-400' },
                    { label: 'NIST Entries', value: nistLines.length.toString(), color: 'bg-yellow-400' }
                  ].map((stat, i) => (
                    <li key={i} className="flex items-center justify-between group">
                      <div className="flex items-center gap-3">
                        <span className={`w-1.5 h-1.5 rounded-full ${stat.color} group-hover:scale-125 transition-transform`} />
                        <span className="text-[10px] text-gray-400 uppercase tracking-widest font-bold">{stat.label}</span>
                      </div>
                      <span className="text-[10px] font-mono font-bold text-white group-hover:text-blue-400 transition-colors">{stat.value}</span>
                    </li>
                  ))}
                </ul>

                <div className="pt-4">
                   <div className="p-4 bg-white/5 rounded-sm border border-white/10 hover:bg-white/10 transition-colors cursor-pointer group">
                      <div className="text-[8px] uppercase tracking-[3px] text-gray-500 mb-2 font-black">Mission Control</div>
                      <div className="text-xs font-bold flex items-center justify-between">
                         DOWNLOAD DATA
                         <Zap size={12} className="text-yellow-500 group-hover:animate-pulse" />
                      </div>
                   </div>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
