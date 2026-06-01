/**
 * @fileoverview GraphDisplay — Primary research interface for LunarAtlas.
 *
 * Orchestrates the full multi-measurement spectral analysis workflow:
 *   Context → Observations → All Measurements (parallel fetch) → Overlap Render → Mini Cards
 *
 * Layout:
 *   1. Controls bar (observation selector, wavelength range, element filter)
 *   2. Full-width MultiSpectralGraph — all Measurement IDs overlaid simultaneously
 *   3. Responsive mini-card grid — one card per Measurement ID
 *   4. NIST reference table
 *
 * State management:
 *   - `measurementData` — Map<measurementId, SpectralDataPoint[]> populated in parallel
 *   - `focusedId` — the currently "isolated" measurement (from legend click or mini card)
 *   - `lambdaMin/Max` — shared viewport range, passed to BOTH graph and all API calls
 */

import { useState, useEffect, useRef, useMemo } from 'react';

import MultiSpectralGraph, { buildDatasets } from '../components/graph/MultiSpectralGraph';
import type { SpectralDataset } from '../components/graph/MultiSpectralGraph';
import MiniSpectralCard from '../components/graph/MiniSpectralCard';
import RangeSelectorPanel from '../components/rangeSelector/rangeSelector';
import ScientificBoard from '../components/education/ScientificBoard';
import BenchmarkTable from '../components/benchmarks/BenchmarkTable';
import NistValidationPanel from '../components/benchmarks/NistValidationPanel';
import {
  apiService,
  type SpectralDataPoint,
  type MeasurementInfo,
  type HealthResponse,
} from '../services/apiService';

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

const DEFAULT_LAMBDA_MIN = 164.35;
const DEFAULT_LAMBDA_MAX = 878.26;

const ELEMENT_PEAKS: Record<string, number[]> = {
  Mg: [279.553, 280.271, 285.213],
  Si: [288.158, 390.553, 413.089],
  Ti: [334.941, 336.121, 337.280, 368.520],
  Ca: [393.366, 396.847, 422.673, 849.802, 854.209, 866.214],
  Al: [394.401, 396.152, 308.215, 309.271],
  Fe: [404.581, 438.355, 373.486, 385.991],
  O: [777.194, 777.417, 777.539, 844.636],
  Na: [588.995, 589.592],
  'H₂O': [656.281, 486.133],
};

/* ------------------------------------------------------------------ */
/*  GraphDisplay                                                        */
/* ------------------------------------------------------------------ */

export default function GraphDisplay() {
  /* ── Database hierarchy ── */
  const [observations, setObservations] = useState<any[]>([]);
  const [selectedObservationId, setSelectedObservationId] = useState('');
  const [measurements, setMeasurements] = useState<MeasurementInfo[]>([]);

  /* ── Multi-measurement data: Map<measurement_id, SpectralDataPoint[]> ── */
  const [measurementData, setMeasurementData] = useState<Map<string, SpectralDataPoint[]>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* ── Active subset selector to prevent client and database overload ── */
  const [activeMeasurementIds, setActiveMeasurementIds] = useState<Set<string>>(new Set());
  const [lttbEnabled, setLttbEnabled] = useState(true);

  /* ── Viewport ── */
  const [lambdaMin, setLambdaMin] = useState(DEFAULT_LAMBDA_MIN);
  const [lambdaMax, setLambdaMax] = useState(DEFAULT_LAMBDA_MAX);

  /* ── UI controls ── */
  const [viewMode, setViewMode] = useState<'L1' | 'L2' | 'overlay'>('L2');
  const [proportion, setProportion] = useState(0.1);
  const [element, setElement] = useState('');
  const [focusedId, setFocusedId] = useState<string | null>(null);
  const [showConsole, setShowConsole] = useState(false);

  /* ── NIST reference ── */
  const [nistLines, setNistLines] = useState<any[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  /* ── Scroll-to ref for mini cards section ── */
  const miniCardsRef = useRef<HTMLDivElement>(null);
  const mainGraphRef = useRef<HTMLDivElement>(null);

  /* ================================================================ */
  /*  INIT: Fetch Context (Observations) + Health                     */
  /* ================================================================ */

  useEffect(() => {
    let isMounted = true;
    apiService.fetchContext()
      .then((list) => {
        if (!isMounted) return;
        setObservations(list);
        if (list.length > 0) setSelectedObservationId(list[0].observation_id);
      })
      .catch((err) => console.error('[API] Context fetch failed:', err));

    apiService.healthCheck()
      .then((h) => isMounted && setHealth(h))
      .catch(() => {});

    return () => { isMounted = false; };
  }, []);

  /* ================================================================ */
  /*  EFFECT: Fetch Measurements when Observation changes             */
  /* ================================================================ */

  useEffect(() => {
    if (!selectedObservationId) return;
    let isMounted = true;
    setMeasurements([]);
    setMeasurementData(new Map());
    setFocusedId(null);
    setError(null);

    apiService.fetchMeasurementsForObservation(selectedObservationId)
      .then((list) => {
        if (!isMounted) return;
        setMeasurements(list);
        if (list.length > 0) {
          setActiveMeasurementIds(new Set([list[0].measurement_id]));
        } else {
          setActiveMeasurementIds(new Set());
        }
      })
      .catch((err) => console.error('[API] Measurements fetch failed:', err));

    return () => { isMounted = false; };
  }, [selectedObservationId]);

  /* ================================================================ */
  /*  EFFECT: Parallel-fetch active measurement spectra only          */
  /* ================================================================ */

  useEffect(() => {
    if (measurements.length === 0 || activeMeasurementIds.size === 0) {
      setMeasurementData(new Map());
      return;
    }
    let isMounted = true;

    const ids = Array.from(activeMeasurementIds);
    setIsLoading(true);
    setError(null);

    // Fetch raw spectral data for active measurements in the full wavelength range
    apiService.fetchMultipleSpectra(ids, DEFAULT_LAMBDA_MIN, DEFAULT_LAMBDA_MAX)
      .then((dataMap) => {
        if (!isMounted) return;
        setMeasurementData(dataMap);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(`Failed to load spectral data: ${err.message}`);
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => { isMounted = false; };
  }, [measurements, activeMeasurementIds]);

  /* ================================================================ */
  /*  EFFECT: Fetch NIST lines for the full range on element change   */
  /* ================================================================ */

  useEffect(() => {
    apiService.fetchNistLines(element || undefined, DEFAULT_LAMBDA_MIN, DEFAULT_LAMBDA_MAX)
      .then((lines) => setNistLines(lines))
      .catch((err) => console.error('[API] NIST fetch failed:', err));
  }, [element]);

  // Client-side viewport filter for NIST lines
  const visibleNistLines = useMemo(() => {
    return nistLines.filter(
      (line) => line.wavelength_nm >= lambdaMin && line.wavelength_nm <= lambdaMax
    );
  }, [nistLines, lambdaMin, lambdaMax]);

  /* ================================================================ */
  /*  Derived Peak Preservation Wavelengths                           */
  /* ================================================================ */

  const ALL_TARGET_WAVELENGTHS = useMemo(() => {
    return Object.values(ELEMENT_PEAKS).flat();
  }, []);

  const targetWavelengths = useMemo(() => {
    if (!lttbEnabled) return [];
    if (!element || element === 'All') return ALL_TARGET_WAVELENGTHS;
    return ELEMENT_PEAKS[element] || [];
  }, [element, lttbEnabled, ALL_TARGET_WAVELENGTHS]);

  const currentProportion = lttbEnabled ? proportion : 1.0;

  /* ================================================================ */
  /*  Derived: build SpectralDataset[] for both components           */
  /* ================================================================ */

  const datasets: SpectralDataset[] = useMemo(
    () => buildDatasets(measurementData, measurements),
    [measurementData, measurements]
  );

  const totalPoints = useMemo(
    () => datasets.reduce((s, d) => s + d.data.length, 0),
    [datasets]
  );

  /* ── Handle focus from mini card → scroll main graph into view ── */
  const handleFocus = (id: string | null) => {
    setFocusedId(id);
    if (id && mainGraphRef.current) {
      mainGraphRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  /* ================================================================ */
  /*  Render                                                           */
  /* ================================================================ */

  return (
    <div className="w-full px-6 py-4 box-border font-sans min-h-screen bg-[#f8f9fb]">
      <div className="max-w-[1600px] mx-auto flex flex-col gap-4">

        {/* ── Controls Panel ── */}
        <RangeSelectorPanel
          mode={viewMode}
          onModeChange={setViewMode}
          proportion={proportion}
          onProportionChange={setProportion}
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
          lttbEnabled={lttbEnabled}
          onLttbEnabledChange={setLttbEnabled}
          activeMeasurementIds={activeMeasurementIds}
          onActiveMeasurementIdsChange={setActiveMeasurementIds}
          showConsole={showConsole}
          setShowConsole={setShowConsole}
          health={health}
        />

        {/* ── Dev Console ── */}
        {showConsole && (
          <div className="bg-white p-4 border border-solid border-gray-200 rounded-lg shadow-sm text-[12px] font-mono">
            <div className="text-gray-500 font-sans font-semibold text-[11px] uppercase tracking-widest mb-2 pb-1 border-b border-gray-100">
              System Console
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-sans text-[12px]">
              <div><span className="text-gray-400 block text-[10px] uppercase tracking-wide">Observation</span>{selectedObservationId ? selectedObservationId.slice(0, 16) + '…' : '—'}</div>
              <div><span className="text-gray-400 block text-[10px] uppercase tracking-wide">Measurements</span>{measurements.length}</div>
              <div><span className="text-gray-400 block text-[10px] uppercase tracking-wide">Total Points</span>{totalPoints.toLocaleString()}</div>
              <div><span className="text-gray-400 block text-[10px] uppercase tracking-wide">NIST Entries</span>{visibleNistLines.length}</div>
            </div>
          </div>
        )}

        {/* ── Error Banner ── */}
        {error && (
          <div className="px-5 py-3 bg-red-50 border-l-4 border-red-400 text-[12px] text-red-700 font-medium rounded-r-lg">
            {error}
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════ */}
        {/* SECTION 1: Full-width Overlapping Multi-Measurement Graph */}
        {/* ══════════════════════════════════════════════════════════ */}
        <div ref={mainGraphRef}>
          {/* Full-width graph — no sidebar */}
          <MultiSpectralGraph
            datasets={datasets}
            isLoading={isLoading}
            lambdaMin={lambdaMin}
            lambdaMax={lambdaMax}
            proportion={currentProportion}
            onRangeChange={(min, max) => {
              setLambdaMin(Math.round(min * 100) / 100);
              setLambdaMax(Math.round(max * 100) / 100);
            }}
            focusedId={focusedId}
            onFocusChange={setFocusedId}
            targetWavelengths={targetWavelengths}
            selectedElement={element}
          />
        </div>

        {/* ══════════════════════════════════════════════════════════ */}
        {/* SECTION 2: Individual Measurement Mini-Cards Grid         */}
        {/* ══════════════════════════════════════════════════════════ */}
        {datasets.length > 0 && (
          <div ref={miniCardsRef}>
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-[15px] font-sans font-bold text-gray-800">
                  Individual Measurements
                </h2>
                <p className="text-[11px] font-sans text-gray-400 mt-0.5">
                  Click a card to isolate and highlight that curve in the main graph
                </p>
              </div>
              <span className="text-[11px] font-sans text-gray-400 bg-white px-3 py-1 rounded-full border border-solid border-gray-200">
                {datasets.length} active measurement{datasets.length !== 1 ? 's' : ''}
              </span>
            </div>

            {/* Responsive grid: 2 cols → 3 on larger screens */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-5">
              {datasets.map((ds) => (
                <MiniSpectralCard
                  key={ds.id}
                  dataset={ds}
                  lambdaMin={lambdaMin}
                  lambdaMax={lambdaMax}
                  proportion={currentProportion}
                  isFocused={focusedId === ds.id}
                  onFocus={handleFocus}
                  targetWavelengths={targetWavelengths}
                />
              ))}
            </div>
          </div>
        )}

        {/* ══════════════════════════════════════════════════════════ */}
        {/* SECTION 3: Scientific Board + Benchmarks                  */}
        {/* ══════════════════════════════════════════════════════════ */}
        <NistValidationPanel
          lambdaMin={lambdaMin}
          lambdaMax={lambdaMax}
          measurementData={measurementData}
          element={element}
          activeMeasurementIds={activeMeasurementIds}
        />
        <ScientificBoard />
        <BenchmarkTable />

        {/* ══════════════════════════════════════════════════════════ */}
        {/* SECTION 4: NIST Reference Table                           */}
        {/* ══════════════════════════════════════════════════════════ */}
        <div className="bg-white p-6 border border-solid border-gray-200 rounded-lg shadow-sm">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-solid border-gray-100">
            <h3 className="text-[15px] font-sans font-bold text-gray-800">
              C-3 Spectral Reference{' '}
              <span className="text-gray-400 font-normal text-[13px]">(NIST ASD)</span>
            </h3>
            <span className="text-[12px] font-sans font-medium text-gray-400">Units: nm</span>
          </div>
          <div className="w-full overflow-hidden border border-gray-100 rounded-md bg-white">
            <table className="w-full text-left text-[12px] border-collapse">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  {['Element', 'Ion Stage', 'Wavelength (nm)', 'Rel. Intensity', 'Status'].map((h) => (
                    <th key={h} className="py-3 px-5 uppercase tracking-widest text-[10px] font-black text-gray-600">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="font-mono">
                {visibleNistLines.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-gray-400 italic text-[12px] font-sans">
                      No NIST reference lines matching current criteria found in database.
                    </td>
                  </tr>
                ) : (
                  visibleNistLines.map((line, idx) => {
                    const isMatch = element === line.element;
                    return (
                      <tr
                        key={idx}
                        className={`border-b border-gray-50 hover:bg-blue-50/30 transition-colors ${isMatch ? 'bg-blue-50/50' : ''}`}
                      >
                        <td className="py-3 px-5 font-bold">{line.element}</td>
                        <td className="py-3 px-5 text-gray-400">{line.ionization_stage}</td>
                        <td className="py-3 px-5 font-bold text-blue-600">{line.wavelength_nm?.toFixed(4)}</td>
                        <td className="py-3 px-5 text-gray-500">{line.relative_intensity}</td>
                        <td className="py-3 px-5">
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

      </div>
    </div>
  );
}
