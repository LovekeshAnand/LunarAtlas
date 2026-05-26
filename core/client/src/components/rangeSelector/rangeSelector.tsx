import { useMemo, useEffect, useRef, useState } from 'react';
import { type MeasurementInfo } from '../../services/apiService';

const ELEMENTS = ['All', 'Fe', 'Mg', 'Si', 'Al', 'Ca', 'Ti', 'Na', 'H₂O', 'O'];

const MEASUREMENT_COLORS = [
  '#38bdf8', // sky blue
  '#fb923c', // sunset orange
  '#4ade80', // spectral green
  '#c084fc', // nebula violet
  '#facc15', // solar yellow
  '#2dd4bf', // teal
  '#f87171', // red
  '#818cf8', // indigo
  '#fb7185', // rose
  '#a3e635', // lime
  '#60a5fa', // cornflower blue
  '#34d399', // emerald
  '#f472b6', // pink
];

const SELECT_CLS =
  'flex items-center bg-white border border-solid border-gray-300 text-gray-700 font-sans text-[13px] rounded px-[10px] transition-colors duration-150 flex-1 focus-within:border-blue-400 focus-within:ring-1 focus-within:ring-blue-100';

const NUM_INPUT_CLS =
  'flex-[0.5] min-w-0 bg-transparent border-0 outline-none font-sans font-medium text-[13px] text-blue-700 py-[4px] ' +
  '[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none text-center';

const SLIDER_CLS =
  'range-track appearance-none w-full h-1 rounded-sm outline-none cursor-pointer ' +
  '[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-[14px] ' +
  '[&::-webkit-slider-thumb]:h-[14px] [&::-webkit-slider-thumb]:bg-blue-600 ' +
  '[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer ' +
  '[&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white ' +
  '[&::-webkit-slider-thumb]:shadow [&::-webkit-slider-thumb]:transition-transform ' +
  '[&::-webkit-slider-thumb:hover]:scale-[1.15] ' +
  '[&::-moz-range-thumb]:w-[14px] [&::-moz-range-thumb]:h-[14px] ' +
  '[&::-moz-range-thumb]:bg-blue-600 [&::-moz-range-thumb]:rounded-full ' +
  '[&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:border-2 ' +
  '[&::-moz-range-thumb]:border-white [&::-moz-range-thumb]:shadow';

// --- Sub-components ---

function FieldLabel({ text }: { text: string }) {
  return (
    <label className="font-sans text-[12px] font-bold text-gray-600 block mb-1">
      {text}
    </label>
  );
}

function StyledSelect({
  value, options, onChange, placeholder = '— select —', disabled = false,
}: {
  value: string; options: { label: string; value: string }[] | string[];
  onChange: (v: string) => void; placeholder?: string; disabled?: boolean;
}) {
  return (
    <div className="relative flex items-center">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={SELECT_CLS}
      >
        <option value="">{placeholder}</option>
        {options.map((opt) => {
          const label = typeof opt === 'string' ? opt : opt.label;
          const val = typeof opt === 'string' ? opt : opt.value;
          return <option key={val} value={val}>{label}</option>;
        })}
      </select>
      <span className="absolute right-[10px] text-[10px] text-[#999] pointer-events-none select-none">▾</span>
    </div>
  );
}

function ModeToggle({ activeMode, onChange }: { activeMode: 'L1' | 'L2' | 'overlay'; onChange: (m: 'L1' | 'L2' | 'overlay') => void }) {
  const modes: { key: 'L1' | 'L2' | 'overlay'; label: string }[] = [
    { key: 'L2', label: 'L2 Cleaned' },
    { key: 'L1', label: 'L1 Raw' },
    { key: 'overlay', label: 'L1 vs L2 Overlay' },
  ];

  return (
    <div className="flex border-b border-solid border-gray-200 bg-gray-50">
      {modes.map(({ key, label }) => {
        const active = key === activeMode;
        return (
          <button
            key={key}
            onClick={() => onChange(key)}
            className={`flex-1 py-[10px] border-0 border-r border-solid border-gray-200 font-sans font-medium text-[13px] cursor-pointer transition-all duration-150 outline-none ${
              active
                ? 'bg-blue-50 text-blue-700 font-semibold border-b-2 border-b-blue-600'
                : 'bg-transparent text-gray-500 font-normal border-b-2 border-b-transparent'
            }`}
          >
            {label}
          </button>
        );
      })}
      <div className="flex-1 bg-gray-50" />
    </div>
  );
}

function ProportionSlider({ proportion, onChange, disabled }: { proportion: number; onChange: (v: number) => void; disabled?: boolean }) {
  const pct = Math.max(0, Math.min(100, proportion * 100));
  const sliderRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    sliderRef.current?.style.setProperty('--track-fill', `${pct}%`);
  }, [pct]);

  return (
    <div className={`flex flex-col gap-[6px] ${disabled ? 'opacity-40 pointer-events-none' : ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
           <FieldLabel text="Data Density (LTTB)" />
        </div>
        <span className="font-sans text-[13px] font-semibold text-gray-600">
          {pct === 100 ? 'RAW 100%' : `${pct.toFixed(1)}%`}
        </span>
      </div>
      <input
        ref={sliderRef}
        type="range"
        min={0.001}
        max={1.0}
        step={0.001}
        value={proportion}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className={SLIDER_CLS}
        disabled={disabled}
      />
      <div className="flex justify-between font-sans text-[11px] text-gray-400 font-medium">
        {['0.1%', '25%', '50%', '75%', '100%'].map((l) => <span key={l}>{l}</span>)}
      </div>
    </div>
  );
}

function PanZoomSliders({
  minWavelength,
  maxWavelength,
  onMinWavelengthChange,
  onMaxWavelengthChange,
}: {
  minWavelength: number;
  maxWavelength: number;
  onMinWavelengthChange: (v: number) => void;
  onMaxWavelengthChange: (v: number) => void;
}) {
  const ABS_MIN = 164.35;
  const ABS_MAX = 878.26;
  const MIN_SPAN = 2.0;
  const MAX_SPAN = ABS_MAX - ABS_MIN; // 713.91
  const currentW = maxWavelength - minWavelength;

  // Invert slider value: when slider is at MIN_SPAN (left), span is MAX_SPAN (Full).
  // When slider is at MAX_SPAN (right), span is MIN_SPAN (Detail).
  const sliderVal = MAX_SPAN - (currentW - MIN_SPAN);

  const handleZoomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const x = parseFloat(e.target.value);
    const newW = MAX_SPAN - (x - MIN_SPAN);
    const center = (minWavelength + maxWavelength) / 2;
    let newMin = center - newW / 2;
    let newMax = center + newW / 2;

    if (newMin < ABS_MIN) {
      newMin = ABS_MIN;
      newMax = ABS_MIN + newW;
    }
    if (newMax > ABS_MAX) {
      newMax = ABS_MAX;
      newMin = ABS_MAX - newW;
    }

    onMinWavelengthChange(Math.round(newMin * 100) / 100);
    onMaxWavelengthChange(Math.round(newMax * 100) / 100);
  };

  const handlePanChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newMin = parseFloat(e.target.value);
    const newMax = newMin + currentW;

    onMinWavelengthChange(Math.round(newMin * 100) / 100);
    onMaxWavelengthChange(Math.round(newMax * 100) / 100);
  };

  return (
    <div className="flex flex-col gap-3 pt-3 border-t border-dashed border-gray-150">
      {/* Zoom Slider */}
      <div className="flex flex-col gap-1">
        <div className="flex justify-between text-[11px] font-sans font-bold text-gray-500">
          <span>Zoom (Wavelength Span)</span>
          <span className="font-mono text-[10px]">{currentW.toFixed(2)} nm</span>
        </div>
        <input
          type="range"
          min={MIN_SPAN}
          max={MAX_SPAN}
          step={0.1}
          value={sliderVal}
          onChange={handleZoomChange}
          className={SLIDER_CLS}
        />
        <div className="flex justify-between text-[9px] font-sans text-gray-400">
          <span>Full (713.9 nm)</span>
          <span>Detail (2 nm)</span>
        </div>
      </div>

      {/* Pan Slider */}
      <div className="flex flex-col gap-1">
        <div className="flex justify-between text-[11px] font-sans font-bold text-gray-500">
          <span>Pan (Scroll Viewport)</span>
          <span className="font-mono text-[10px]">{((minWavelength + maxWavelength) / 2).toFixed(2)} nm</span>
        </div>
        <input
          type="range"
          min={ABS_MIN}
          max={Math.max(ABS_MIN, ABS_MAX - currentW)}
          step={0.1}
          value={minWavelength}
          onChange={handlePanChange}
          className={SLIDER_CLS}
        />
        <div className="flex justify-between text-[9px] font-sans text-gray-400">
          <span>{ABS_MIN} nm</span>
          <span>{ABS_MAX} nm</span>
        </div>
      </div>
    </div>
  );
}

function LttbToggle({
  enabled,
  onChange,
}: {
  enabled: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between py-1.5 px-3 bg-gray-50 border border-solid border-gray-200 rounded-sm">
      <span className="font-sans text-[12px] font-bold text-gray-600">LTTB Downsampling</span>
      <button
        type="button"
        onClick={() => onChange(!enabled)}
        className={`w-9 h-5 flex items-center rounded-full p-0.5 cursor-pointer transition-colors outline-none border-0 ${
          enabled ? 'bg-blue-600' : 'bg-gray-300'
        }`}
      >
        <div
          className={`bg-white w-4 h-4 rounded-full shadow-sm transform transition-transform ${
            enabled ? 'translate-x-4' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Custom Nested Dropdown Component for Observations
// ─────────────────────────────────────────────────────────────

function DateObservationDropdown({
  observations,
  selectedObservationId,
  onObservationChange,
}: {
  observations: any[];
  selectedObservationId: string;
  onObservationChange: (id: string) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [hoveredDate, setHoveredDate] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setHoveredDate(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getLocalDateString = (dateTimeStr: string) => {
    if (!dateTimeStr) return 'Unknown Date';
    return new Date(dateTimeStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Group observations by Date
  const groupedObservations = useMemo(() => {
    const groups: Record<string, any[]> = {};
    observations.forEach((obs) => {
      const dateStr = getLocalDateString(obs.creation_datetime);
      if (!groups[dateStr]) {
        groups[dateStr] = [];
      }
      groups[dateStr].push(obs);
    });
    return groups;
  }, [observations]);

  // Selected details
  const selectedObs = useMemo(() => {
    return observations.find((o) => o.observation_id === selectedObservationId);
  }, [observations, selectedObservationId]);

  const selectedLabel = useMemo(() => {
    if (!selectedObs) return '— Select Observation —';
    const dateStr = getLocalDateString(selectedObs.creation_datetime);
    const fileNameClean = selectedObs.target_name.replace(/\.xml$/i, '');
    return `${dateStr} (${fileNameClean})`;
  }, [selectedObs]);

  return (
    <div className="relative font-sans" ref={containerRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between bg-white hover:bg-gray-50 border border-solid border-gray-300 active:border-blue-400 text-gray-700 font-sans text-[13px] rounded px-[12px] py-[7px] transition-all duration-150 cursor-pointer shadow-sm focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-100"
      >
        <div className="flex items-center gap-2 truncate">
          <span className="text-[14px]">📅</span>
          <span className="truncate font-semibold text-gray-700">{selectedLabel}</span>
        </div>
        <span className="text-[10px] text-gray-400 select-none">▾</span>
      </button>

      {/* Main Dropdown Panel */}
      {isOpen && (
        <div className="absolute left-0 mt-1 bg-white border border-solid border-gray-200 rounded-lg shadow-xl py-1.5 w-64 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
          <div className="px-3 py-1.5 text-[10px] font-bold text-gray-400 uppercase tracking-wider border-b border-solid border-gray-100 mb-1">
            Select Observation Date
          </div>
          <div className="flex flex-col gap-0.5 pr-0.5">
            {Object.keys(groupedObservations).length === 0 ? (
              <div className="px-3 py-4 text-center text-gray-400 italic text-[12px]">
                No observations found
              </div>
            ) : (
              Object.entries(groupedObservations).map(([dateStr, files]) => (
                <div
                  key={dateStr}
                  className="relative"
                  onMouseEnter={() => setHoveredDate(dateStr)}
                  onMouseLeave={() => setHoveredDate(null)}
                >
                  {/* Date Option Row */}
                  <div
                    className={`flex items-center justify-between px-3 py-2 rounded text-[13px] font-medium transition-colors cursor-pointer ${
                      hoveredDate === dateStr
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <span>{dateStr}</span>
                    <div className="flex items-center gap-1.5">
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
                        hoveredDate === dateStr
                          ? 'bg-blue-200 text-blue-800'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {files.length}
                      </span>
                      <span className="text-[10px] text-gray-400 font-bold">›</span>
                    </div>
                  </div>

                  {/* Sub-menu containing files for this Date */}
                  {hoveredDate === dateStr && (
                    <div
                      className="absolute left-full top-0 ml-1.5 bg-white border border-solid border-gray-200 rounded-lg shadow-xl p-1.5 w-80 z-50 animate-in fade-in slide-in-from-left-2 duration-150"
                      style={{ marginTop: '-4px' }}
                    >
                      <div className="px-3 py-1.5 text-[10px] font-bold text-gray-400 uppercase tracking-wider border-b border-solid border-gray-100 mb-1 flex items-center justify-between">
                        <span>Observation Files</span>
                        <span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full text-[9px] font-bold">
                          {files.length} file{files.length !== 1 ? 's' : ''}
                        </span>
                      </div>
                      <div className="flex flex-col gap-1 max-h-[260px] overflow-y-auto pr-1">
                        {files.map((obs) => {
                          const isSelected = selectedObservationId === obs.observation_id;
                          return (
                            <button
                              key={obs.observation_id}
                              type="button"
                              onClick={() => {
                                onObservationChange(obs.observation_id);
                                setIsOpen(false);
                                setHoveredDate(null);
                              }}
                              className={`w-full text-left px-3 py-2 rounded text-[11px] font-mono transition-colors break-all ${
                                isSelected
                                  ? 'bg-blue-600 text-white font-semibold shadow-sm'
                                  : 'text-gray-700 hover:bg-blue-50 hover:text-blue-700'
                              }`}
                            >
                              {obs.target_name.replace(/\.xml$/i, '')}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Main Panel Component
// ─────────────────────────────────────────────────────────────

export default function RangeSelectorPanel({ 
  mode, onModeChange, 
  proportion, onProportionChange,
  minWavelength, maxWavelength,
  onMinWavelengthChange, onMaxWavelengthChange,
  element, onElementChange,
  observations, selectedObservationId, onObservationChange,
  measurements,
  lttbEnabled, onLttbEnabledChange,
  activeMeasurementIds, onActiveMeasurementIdsChange,
}: { 
  mode: 'L1' | 'L2' | 'overlay', 
  onModeChange: (m: 'L1' | 'L2' | 'overlay') => void,
  proportion: number, 
  onProportionChange: (p: number) => void,
  minWavelength: number,
  maxWavelength: number,
  onMinWavelengthChange: (v: number) => void,
  onMaxWavelengthChange: (v: number) => void,
  element: string,
  onElementChange: (e: string) => void,
  observations: any[],
  selectedObservationId: string,
  onObservationChange: (id: string) => void,
  measurements: MeasurementInfo[],
  lttbEnabled: boolean,
  onLttbEnabledChange: (v: boolean) => void,
  activeMeasurementIds: Set<string>,
  onActiveMeasurementIdsChange: (ids: Set<string>) => void,
}) {
  return (
    <section className="border border-solid border-gray-200 bg-white rounded-md shadow-sm relative z-30">
      <ModeToggle activeMode={mode} onChange={onModeChange} />
      <div className="flex items-stretch flex-wrap">
        {/* Column 1: Observation Session & Selected Measurements Checklist */}
        <div className="flex-[1_1_280px] p-5 px-6 flex flex-col gap-4 min-w-0 bg-white border-r border-solid border-gray-200">
          <div>
            <FieldLabel text="Observation Session" />
            <DateObservationDropdown
              observations={observations}
              selectedObservationId={selectedObservationId}
              onObservationChange={onObservationChange}
            />
          </div>

          <div className="flex flex-col gap-2">
            <FieldLabel text="Select Measurements to Overlay" />
            <div className="flex flex-col gap-1.5 max-h-[140px] overflow-y-auto pr-1 border border-solid border-gray-150 rounded p-2 bg-gray-50/50">
              {measurements.length === 0 ? (
                <div className="text-[11px] font-sans text-gray-400 italic py-2 text-center">
                  No measurements
                </div>
              ) : (
                measurements.map((m, idx) => {
                  const active = activeMeasurementIds.has(m.measurement_id);
                  const color = MEASUREMENT_COLORS[idx % MEASUREMENT_COLORS.length];
                  return (
                    <label
                      key={m.measurement_id}
                      className={`flex items-center gap-2 px-2 py-1.5 rounded border border-solid cursor-pointer select-none transition-all ${
                        active
                          ? 'bg-white border-blue-200 shadow-sm'
                          : 'bg-transparent border-transparent hover:bg-gray-100'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={active}
                        onChange={() => {
                          const newSet = new Set(activeMeasurementIds);
                          if (active) {
                            if (newSet.size > 1) {
                              newSet.delete(m.measurement_id);
                            }
                          } else {
                            newSet.add(m.measurement_id);
                          }
                          onActiveMeasurementIdsChange(newSet);
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-3.5 h-3.5"
                      />
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: color }}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between text-[11px] font-sans font-bold text-gray-700">
                          <span>Measurement #{m.measurement_index}</span>
                          <span className="text-[10px] font-normal text-gray-400">
                            {m.laser_energy_v ? `${m.laser_energy_v}V` : 'clean'}
                          </span>
                        </div>
                        <div className="text-[9px] font-sans text-gray-400 truncate">
                          {m.time_utc ? new Date(m.time_utc).toLocaleTimeString() : '—'}
                        </div>
                      </div>
                    </label>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Column 2: Spectral Domain Zoom & Pan Sliders */}
        <div className="flex-[1.4_1_300px] p-5 px-6 flex flex-col justify-center gap-3 min-w-0 border-r border-solid border-gray-200 bg-white relative">
          <div className="flex flex-col gap-2">
            <FieldLabel text="Wavelength Range Bound (nm)" />
            <div className="flex items-center gap-2">
              <input
                type="number" value={minWavelength}
                onChange={(e) => onMinWavelengthChange(parseFloat(e.target.value) || 164.35)}
                className={NUM_INPUT_CLS + " border border-solid border-gray-200 rounded-sm bg-gray-50 hover:bg-white focus:bg-white transition-colors"}
              />
              <span className="font-sans font-medium text-gray-400 px-2">to</span>
              <input
                type="number" value={maxWavelength}
                onChange={(e) => onMaxWavelengthChange(parseFloat(e.target.value) || 878.26)}
                className={NUM_INPUT_CLS + " border border-solid border-gray-200 rounded-sm bg-gray-50 hover:bg-white focus:bg-white transition-colors"}
              />
            </div>
          </div>
          <PanZoomSliders
            minWavelength={minWavelength}
            maxWavelength={maxWavelength}
            onMinWavelengthChange={onMinWavelengthChange}
            onMaxWavelengthChange={onMaxWavelengthChange}
          />
        </div>

        {/* Column 3: Downsampling, Data Density & Elemental Focus */}
        <div className="flex-[1_1_240px] p-5 px-6 flex flex-col justify-center gap-4 min-w-0 bg-white">
          <LttbToggle enabled={lttbEnabled} onChange={onLttbEnabledChange} />
          
          <ProportionSlider
            proportion={proportion}
            onChange={onProportionChange}
            disabled={!lttbEnabled}
          />

          <div className="pt-2 border-t border-solid border-gray-200">
            <FieldLabel text="Elemental Focus Tool" />
            <StyledSelect value={element} options={ELEMENTS} onChange={onElementChange} placeholder="None active" />
          </div>
        </div>

      </div>
    </section>
  );
}
