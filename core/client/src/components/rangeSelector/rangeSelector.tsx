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
  'flex items-center bg-slate-50 border border-solid border-slate-200 text-slate-700 font-sans font-medium text-[11px] rounded px-[8px] transition-all duration-150 flex-1 hover:border-slate-350 focus-within:border-black focus-within:ring-1 focus-within:ring-slate-200 outline-none h-7 cursor-pointer';

const SLIDER_CLS =
  'range-track appearance-none w-full h-1 rounded-full outline-none cursor-pointer flex-1 ' +
  '[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-[10px] ' +
  '[&::-webkit-slider-thumb]:h-[10px] [&::-webkit-slider-thumb]:bg-black ' +
  '[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer ' +
  '[&::-webkit-slider-thumb]:border [&::-webkit-slider-thumb]:border-white ' +
  '[&::-webkit-slider-thumb]:shadow [&::-webkit-slider-thumb]:transition-transform ' +
  '[&::-webkit-slider-thumb:hover]:scale-[1.25] ' +
  '[&::-moz-range-thumb]:w-[10px] [&::-moz-range-thumb]:h-[10px] ' +
  '[&::-moz-range-thumb]:bg-black [&::-moz-range-thumb]:rounded-full ' +
  '[&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:border ' +
  '[&::-moz-range-thumb]:border-white [&::-moz-range-thumb]:shadow';

// --- Sub-components ---

function FieldLabel({ text }: { text: string }) {
  return (
    <label className="font-sans text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1 leading-none select-none">
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
      <span className="absolute right-[8px] text-[9px] text-slate-400 pointer-events-none select-none">▾</span>
    </div>
  );
}

function ModeToggle({
  activeMode,
  onChange,
  showConsole,
  setShowConsole,
  health,
}: {
  activeMode: 'L1' | 'L2' | 'overlay';
  onChange: (m: 'L1' | 'L2' | 'overlay') => void;
  showConsole?: boolean;
  setShowConsole?: (v: boolean) => void;
  health?: any;
}) {
  const modes: { key: 'L1' | 'L2' | 'overlay'; label: string }[] = [
    { key: 'L2', label: 'L2 Cleaned' },
    { key: 'L1', label: 'L1 Raw' },
    { key: 'overlay', label: 'L1 vs L2 Overlay' },
  ];

  return (
    <div className="flex flex-row bg-slate-50 border-b border-solid border-slate-200 px-3 py-1.5 items-center justify-between gap-3 text-slate-700 select-none rounded-t-lg">
      {/* Segmented Pill Selector (Light Theme) */}
      <div className="flex bg-slate-200/50 p-0.5 rounded items-center gap-0.5 shadow-inner border border-slate-200/40">
        {modes.map(({ key, label }) => {
          const active = key === activeMode;
          return (
            <button
              key={key}
              onClick={() => onChange(key)}
              className={`py-0.5 px-2.5 border-0 font-sans font-black text-[9px] uppercase tracking-wider rounded cursor-pointer transition-all duration-150 outline-none ${
                active
                  ? 'bg-white text-black shadow-sm border border-slate-350/10'
                  : 'bg-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>
      
      {/* Branding + Indicators */}
      <div className="flex items-center gap-3">
        {/* Title */}
        <span className="text-[9px] font-sans font-black text-slate-700 tracking-widest leading-none">
          LUNARATLAS <span className="text-black font-bold text-[8px] px-1 py-0.5 bg-slate-100 border border-slate-200 rounded ml-1 tracking-normal">TELEMETRY</span>
        </span>
        
        {/* DB Connection Indicator */}
        <div className="flex items-center gap-1 bg-white border border-slate-200 shadow-sm rounded-full py-0.5 px-2">
          <span className={`w-1 h-1 rounded-full ${health?.database ? 'bg-emerald-500 animate-pulse ring-2 ring-emerald-100' : 'bg-slate-300'}`} />
          <span className="text-[8px] font-sans font-black text-slate-500 uppercase tracking-widest leading-none">
            {health?.database ? 'CONNECTED' : 'STANDALONE'}
          </span>
        </div>

        {/* Dev Console Toggle */}
        {setShowConsole && (
          <button
            onClick={() => setShowConsole(!showConsole)}
            className={`text-[8px] font-sans transition-all px-2 py-0.5 rounded border border-solid font-black tracking-wider uppercase shrink-0 cursor-pointer ${
              showConsole 
                ? 'bg-black border-black text-white hover:bg-slate-900 hover:border-black' 
                : 'bg-white border-slate-200 hover:border-slate-300 text-slate-550 hover:text-slate-900'
            }`}
          >
            {showConsole ? 'Console On' : 'Console'}
          </button>
        )}
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
    <div className="flex items-center justify-between px-2 bg-slate-50 border border-solid border-slate-200 rounded hover:border-slate-350 transition-colors duration-150 select-none h-7">
      <span className="font-sans text-[10px] font-bold text-slate-600 uppercase tracking-wide leading-none font-sans">
        {enabled ? 'LTTB ON' : 'LTTB OFF'}
      </span>
      <button
        type="button"
        onClick={() => onChange(!enabled)}
        className={`w-7 h-4 flex items-center rounded-full p-0.5 cursor-pointer transition-colors duration-200 outline-none border-0 ${
          enabled ? 'bg-black' : 'bg-slate-300'
        }`}
      >
        <div
          className={`bg-white w-3 h-3 rounded-full shadow-sm transform transition-transform duration-200 ${
            enabled ? 'translate-x-3' : 'translate-x-0'
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
      month: 'short',
      day: 'numeric',
    });
  };

  const getLocalTimeString = (dateTimeStr: string) => {
    if (!dateTimeStr) return 'Unknown Time';
    return new Date(dateTimeStr).toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  // Pre-sort all observations chronologically ascending by creation_datetime
  const sortedObservations = useMemo(() => {
    return [...observations].sort((a, b) => {
      const timeA = a.creation_datetime ? new Date(a.creation_datetime).getTime() : 0;
      const timeB = b.creation_datetime ? new Date(b.creation_datetime).getTime() : 0;
      return timeA - timeB; // ascending order
    });
  }, [observations]);

  // Group sorted observations by Date
  const groupedObservations = useMemo(() => {
    const groups: Record<string, any[]> = {};
    sortedObservations.forEach((obs) => {
      const dateStr = getLocalDateString(obs.creation_datetime);
      if (!groups[dateStr]) {
        groups[dateStr] = [];
      }
      groups[dateStr].push(obs);
    });
    return groups;
  }, [sortedObservations]);

  // Sort grouped entries by date ascending
  const sortedGroupedEntries = useMemo(() => {
    return Object.entries(groupedObservations).sort((a, b) => {
      const firstA = a[1][0]?.creation_datetime ? new Date(a[1][0].creation_datetime).getTime() : 0;
      const firstB = b[1][0]?.creation_datetime ? new Date(b[1][0].creation_datetime).getTime() : 0;
      return firstA - firstB; // ascending
    });
  }, [groupedObservations]);

  // Selected details
  const selectedObs = useMemo(() => {
    return observations.find((o) => o.observation_id === selectedObservationId);
  }, [observations, selectedObservationId]);

  const selectedLabel = useMemo(() => {
    if (!selectedObs) return '— Select Observation —';
    const dateStr = getLocalDateString(selectedObs.creation_datetime);
    const timeStr = selectedObs.creation_datetime 
      ? new Date(selectedObs.creation_datetime).toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit',
        })
      : 'Unknown Time';
    return `${dateStr} @ ${timeStr} (${selectedObs.record_count} curves)`;
  }, [selectedObs]);

  return (
    <div className="relative font-sans" ref={containerRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between bg-slate-50 hover:bg-slate-100 border border-solid border-slate-200 text-slate-700 font-sans font-bold text-[11px] rounded px-[8px] py-[4px] transition-all duration-150 cursor-pointer shadow-sm outline-none focus:border-black focus:ring-1 focus:ring-slate-200 h-7"
      >
        <span className="truncate text-slate-700 font-semibold">{selectedLabel}</span>
        <span className="text-[8px] text-slate-400 select-none ml-1 shrink-0">▼</span>
      </button>

      {/* Main Dropdown Panel */}
      {isOpen && (
        <div className="absolute left-0 mt-1 bg-white border border-solid border-slate-200 rounded shadow-xl py-1 w-56 z-50 animate-in fade-in duration-100">
          <div className="px-2.5 py-1 text-[8px] font-black text-slate-400 uppercase tracking-widest border-b border-solid border-slate-100 mb-0.5">
            Select Date (Ascending)
          </div>
          <div className="flex flex-col gap-0.2 pr-0.5">
            {sortedGroupedEntries.length === 0 ? (
              <div className="px-2.5 py-3 text-center text-slate-400 italic text-[11px]">
                No observations found
              </div>
            ) : (
              sortedGroupedEntries.map(([dateStr, files]) => (
                <div
                  key={dateStr}
                  className="relative"
                  onMouseEnter={() => setHoveredDate(dateStr)}
                  onMouseLeave={() => setHoveredDate(null)}
                >
                  {/* Date Option Row */}
                  <div
                    className={`flex items-center justify-between px-2.5 py-1.5 rounded mx-1 text-[11px] font-semibold transition-colors cursor-pointer ${
                      hoveredDate === dateStr
                        ? 'bg-slate-100 text-black'
                        : 'text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <span>{dateStr}</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[8px] font-bold px-1.5 py-0.2 bg-slate-100 rounded-full text-slate-500">
                        {files.length}
                      </span>
                      <span className="text-[8px] text-slate-400 font-bold">›</span>
                    </div>
                  </div>

                  {/* Sub-menu containing files for this Date */}
                  {hoveredDate === dateStr && (
                    <div
                      className="absolute left-full top-0 ml-1 bg-white border border-solid border-slate-200 rounded shadow-xl p-1.5 w-64 z-50 animate-in fade-in duration-100"
                      style={{ marginTop: '-4px' }}
                    >
                      <div className="px-2 py-1 text-[8px] font-black text-slate-400 uppercase tracking-widest border-b border-solid border-slate-100 mb-1 flex items-center justify-between">
                        <span>Capture Time</span>
                        <span className="bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded-full text-[8px] font-bold">
                          {files.length} sessions
                        </span>
                      </div>
                      <div className="flex flex-col gap-0.5 max-h-[200px] overflow-y-auto pr-0.5">
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
                              className={`w-full text-left px-2.5 py-1.5 rounded text-[10px] font-mono transition-colors break-all cursor-pointer border-0 ${
                                isSelected
                                  ? 'bg-black text-white font-semibold shadow-sm'
                                  : 'text-slate-600 hover:bg-slate-100 hover:text-black'
                              }`}
                            >
                              {getLocalTimeString(obs.creation_datetime)} ({obs.record_count} curves)
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
  showConsole, setShowConsole, health,
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
  showConsole?: boolean,
  setShowConsole?: (v: boolean) => void,
  health?: any,
}) {
  const ABS_MIN = 164.35;
  const ABS_MAX = 878.26;
  const MIN_SPAN = 2.0;
  const MAX_SPAN = ABS_MAX - ABS_MIN; // 713.91
  const currentW = maxWavelength - minWavelength;

  // Invert slider value for Zoom slider calculations
  const zoomSliderVal = MAX_SPAN - (currentW - MIN_SPAN);

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

  // Data density slider calculation
  const densityPct = Math.max(0, Math.min(100, proportion * 100));
  const densitySliderRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    densitySliderRef.current?.style.setProperty('--track-fill', `${densityPct}%`);
  }, [densityPct]);

  return (
    <section className="border border-solid border-slate-200 bg-white rounded-lg shadow-sm relative z-30">
      <ModeToggle 
        activeMode={mode} 
        onChange={onModeChange} 
        showConsole={showConsole} 
        setShowConsole={setShowConsole} 
        health={health} 
      />
      <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-slate-100 bg-white">
        
        {/* Column 1: Observation Session, Overlay pills & Focus select */}
        <div className="p-3 px-4 flex flex-col gap-3 min-w-0 bg-white h-full justify-start">
          <div className="text-[9px] font-black tracking-widest text-slate-800 uppercase flex items-center gap-1 font-sans">
            <span>1. Session & Overlay</span>
          </div>
          
          <div className="flex flex-col gap-2.5">
            {/* Row 1: Session select */}
            <div>
              <FieldLabel text="Observation Session" />
              <DateObservationDropdown
                observations={observations}
                selectedObservationId={selectedObservationId}
                onObservationChange={onObservationChange}
              />
            </div>

            {/* Row 2: Overlay measurements pills */}
            <div>
              <FieldLabel text="Overlay Measurements" />
              <div className="flex items-center gap-1 overflow-x-auto pr-1 p-1 h-7 border border-solid border-slate-200 rounded bg-slate-50/50 scrollbar-none">
                {measurements.length === 0 ? (
                  <div className="text-[9px] font-sans text-slate-400 italic w-full text-center">No measurements</div>
                ) : (
                  measurements.map((m, idx) => {
                    const active = activeMeasurementIds.has(m.measurement_id);
                    const color = MEASUREMENT_COLORS[idx % MEASUREMENT_COLORS.length];
                    return (
                      <button
                        key={m.measurement_id}
                        type="button"
                        onClick={() => {
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
                        className={`flex items-center gap-1.5 px-2 py-0.5 rounded border border-solid text-[9px] font-bold cursor-pointer select-none transition-all duration-150 shrink-0 leading-none h-5 ${
                          active
                            ? 'bg-white border-slate-350 text-slate-800 shadow-sm font-extrabold'
                            : 'bg-transparent border-transparent hover:bg-slate-200/40 text-slate-500 hover:text-slate-700'
                        }`}
                      >
                        <span
                          className="w-1.5 h-1.5 rounded-full shrink-0"
                          style={{ 
                            backgroundColor: color,
                            boxShadow: active ? `0 0 5px 1px ${color}80` : 'none'
                          }}
                        />
                        <span>#{m.measurement_index}</span>
                        <span className="text-[8px] font-normal opacity-70 scale-[0.9] origin-right shrink-0">
                          {m.laser_energy_v ? `${m.laser_energy_v}V` : 'clean'}
                        </span>
                      </button>
                    );
                  })
                )}
              </div>
            </div>

            {/* Row 3: Focus Dropdown select */}
            <div>
              <FieldLabel text="Elemental Focus Tool" />
              <StyledSelect value={element} options={ELEMENTS} onChange={onElementChange} placeholder="None active" />
            </div>
          </div>
        </div>

        {/* Column 2: Wavelength Bounds Input, Zoom Slider & Pan Slider */}
        <div className="p-3 px-4 flex flex-col gap-3 min-w-0 bg-white h-full justify-start">
          <div className="text-[9px] font-black tracking-widest text-slate-800 uppercase flex items-center gap-1 font-sans">
            <span>2. Wavelength Viewport</span>
          </div>
          
          <div className="flex flex-col gap-2.5">
            {/* Row 1: Connected Wavelength Bounds */}
            <div>
              <FieldLabel text="Wavelength Range Bound (nm)" />
              <div className="flex items-center bg-slate-50 hover:bg-white focus-within:bg-white border border-solid border-slate-200 focus-within:border-black focus-within:ring-1 focus-within:ring-slate-200 rounded p-0.5 transition-all duration-150 h-7">
                <div className="flex items-center gap-0.5 px-1.5 text-slate-400 font-sans text-[8px] font-black tracking-wider select-none shrink-0 leading-none">
                  <span className="text-[10px] text-slate-500 font-bold">λ</span>
                  <span>MIN</span>
                </div>
                <input
                  type="number" 
                  value={minWavelength}
                  step={0.1}
                  onChange={(e) => onMinWavelengthChange(parseFloat(e.target.value) || ABS_MIN)}
                  className="w-full bg-transparent border-0 outline-none font-mono font-bold text-[11px] text-slate-900 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none p-0 h-full"
                />
                <div className="h-3 w-px bg-slate-200 mx-1 shrink-0" />
                <div className="flex items-center gap-0.5 px-1.5 text-slate-400 font-sans text-[8px] font-black tracking-wider select-none shrink-0 leading-none">
                  <span className="text-[10px] text-slate-500 font-bold">λ</span>
                  <span>MAX</span>
                </div>
                <input
                  type="number" 
                  value={maxWavelength}
                  step={0.1}
                  onChange={(e) => onMaxWavelengthChange(parseFloat(e.target.value) || ABS_MAX)}
                  className="w-full bg-transparent border-0 outline-none font-mono font-bold text-[11px] text-slate-900 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none p-0 h-full"
                />
              </div>
            </div>

            {/* Row 2: Zoom Slider */}
            <div>
              <div className="flex justify-between items-center mb-1 leading-none select-none">
                <FieldLabel text="Viewport Zoom Span" />
                <span className="font-mono text-[9px] text-slate-700 font-bold bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded leading-none shrink-0">
                  {currentW.toFixed(1)} nm
                </span>
              </div>
              <div className="flex items-center h-7">
                <input
                  type="range"
                  min={MIN_SPAN}
                  max={MAX_SPAN}
                  step={0.1}
                  value={zoomSliderVal}
                  onChange={handleZoomChange}
                  className={SLIDER_CLS}
                />
              </div>
            </div>

            {/* Row 3: Pan Slider */}
            <div>
              <div className="flex justify-between items-center mb-1 leading-none select-none">
                <FieldLabel text="Viewport Pan Scroll" />
                <span className="font-mono text-[9px] text-slate-700 font-bold bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded leading-none shrink-0">
                  {((minWavelength + maxWavelength) / 2).toFixed(1)} nm
                </span>
              </div>
              <div className="flex items-center h-7">
                <input
                  type="range"
                  min={ABS_MIN}
                  max={Math.max(ABS_MIN, ABS_MAX - currentW)}
                  step={0.1}
                  value={minWavelength}
                  onChange={handlePanChange}
                  className={SLIDER_CLS}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Column 3: Processing switches, density dials & Active diagnostics */}
        <div className="p-3 px-4 flex flex-col gap-3 min-w-0 bg-white h-full justify-start">
          <div className="text-[9px] font-black tracking-widest text-slate-800 uppercase flex items-center gap-1 font-sans">
            <span>3. Processing & Stats</span>
          </div>
          
          <div className="flex flex-col gap-2.5">
            {/* Row 1: LTTB Downsampling Toggle switch */}
            <div>
              <FieldLabel text="Downsample Toggle" />
              <LttbToggle enabled={lttbEnabled} onChange={onLttbEnabledChange} />
            </div>

            {/* Row 2: Data Density Slider */}
            <div className={!lttbEnabled ? 'opacity-40 pointer-events-none' : ''}>
              <div className="flex justify-between items-center mb-1 leading-none select-none">
                <FieldLabel text="LTTB Data Density" />
                <span className="font-mono text-[9px] text-slate-700 font-bold bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded leading-none shrink-0">
                  {densityPct === 100 ? 'RAW' : `${densityPct.toFixed(0)}%`}
                </span>
              </div>
              <div className="flex items-center h-7">
                <input
                  ref={densitySliderRef}
                  type="range"
                  min={0.001}
                  max={1.0}
                  step={0.001}
                  value={proportion}
                  onChange={(e) => onProportionChange(parseFloat(e.target.value))}
                  className={SLIDER_CLS}
                  disabled={!lttbEnabled}
                />
              </div>
            </div>

            {/* Row 3: Diagnostics Badge Strip */}
            <div>
              <FieldLabel text="Active Diagnostics" />
              <div className="flex items-center justify-between px-2 bg-slate-50 border border-solid border-slate-200 rounded h-7 select-none">
                <span className="text-[8px] font-sans font-black text-slate-400 uppercase tracking-widest leading-none">Status</span>
                <div className="flex items-center gap-1">
                  <span className="text-[8px] font-mono font-black uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200 rounded px-1.5 py-0.5 leading-none">
                    {activeMeasurementIds.size} Active
                  </span>
                  <span className="text-[8px] font-mono font-black uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-100 rounded px-1.5 py-0.5 leading-none">
                    {lttbEnabled ? 'LTTB ON' : 'RAW ON'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
