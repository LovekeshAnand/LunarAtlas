import { useState, useMemo, useEffect, useRef } from 'react';
import {
  mockObservationData,
  getUniqueDates,
  getTimesForDate,
  getUniqueMeasurementTypes,
  ELEMENTS,
} from '../../utils/mockData';

const ABS_MIN  = 0;
const ABS_MAX  = 2000;
const ZOOM_MIN = 1;
const ZOOM_MAX = 5;

// ─────────────────────────────────────────────────────────────
// Shared Tailwind class strings — complete strings so JIT scans them.
// Dark mode colours use CSS custom properties defined in index.css
// where possible (slider). Static surfaces use dark: variants.
// ─────────────────────────────────────────────────────────────
const SELECT_CLS =
  'w-full appearance-none bg-[#f5f5f5] dark:bg-[#1a1a1a] border border-border-dark dark:border-[#2a2a2a] rounded px-[10px] pr-8 py-[7px] ' +
  'font-sans text-[12px] font-medium text-[#222] dark:text-[#d0d0d0] cursor-pointer outline-none transition-colors duration-150 ' +
  'leading-[1.4] focus:border-[#999] dark:focus:border-[#555] disabled:text-ink-muted dark:disabled:text-[#444] disabled:cursor-not-allowed disabled:bg-canvas-alt dark:disabled:bg-[#111]';

const NUM_WRAP_BASE =
  'flex items-center bg-[#f5f5f5] dark:bg-[#1a1a1a] rounded px-[10px] transition-colors duration-150 flex-1 focus-within:border-[#999] dark:focus-within:border-[#555]';

const NUM_INPUT_CLS =
  'flex-1 min-w-0 bg-transparent border-0 outline-none font-mono text-[12px] font-semibold text-[#222] dark:text-[#d0d0d0] py-[7px] ' +
  '[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none';

// Slider thumb colour comes from --slider-thumb CSS var (switches on .dark).
// Border ring uses --slider-thumb-ring. Both are defined in index.css :root/.dark.
const SLIDER_CLS =
  'range-track appearance-none w-full h-1 rounded-sm outline-none cursor-pointer ' +
  '[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-[14px] ' +
  '[&::-webkit-slider-thumb]:h-[14px] [&::-webkit-slider-thumb]:bg-[var(--slider-thumb)] ' +
  '[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer ' +
  '[&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-[var(--slider-thumb-ring)] ' +
  '[&::-webkit-slider-thumb]:shadow [&::-webkit-slider-thumb]:transition-transform ' +
  '[&::-webkit-slider-thumb:hover]:scale-[1.15] ' +
  '[&::-moz-range-thumb]:w-[14px] [&::-moz-range-thumb]:h-[14px] ' +
  '[&::-moz-range-thumb]:bg-[var(--slider-thumb)] [&::-moz-range-thumb]:rounded-full ' +
  '[&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:border-2 ' +
  '[&::-moz-range-thumb]:border-[var(--slider-thumb-ring)] [&::-moz-range-thumb]:shadow';

// Per-format export button colours — same in both modes (intentionally coloured)
const EXPORT_BG: Record<string, string> = {
  pdf:  'bg-[#8b4444] hover:bg-[#a05050]',
  csv:  'bg-[#3a6b3a] hover:bg-[#4a7d4a]',
  json: 'bg-[#3a4d6b] hover:bg-[#4a5e80]',
};

// ─────────────────────────────────────────────────────────────
// SHARED: FieldLabel
// ─────────────────────────────────────────────────────────────
function FieldLabel({ text }: { text: string }) {
  return (
    <label className="font-sans text-[9px] font-bold tracking-[1.3px] text-[#888] dark:text-[#777] uppercase block mb-1">
      {text}
    </label>
  );
}


// ─────────────────────────────────────────────────────────────
// SHARED: StyledSelect
// ─────────────────────────────────────────────────────────────
function StyledSelect({
  value, options, onChange, placeholder = '— select —', disabled = false,
}: {
  value: string; options: string[];
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
        {options.map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
      <span className="absolute right-[10px] text-[10px] text-[#999] dark:text-[#555] pointer-events-none select-none">▾</span>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// SHARED: Column divider
// ─────────────────────────────────────────────────────────────
function ColDivider() {
  return <div className="w-px bg-border dark:bg-[#222] self-stretch shrink-0" />;
}

// ─────────────────────────────────────────────────────────────
// 1. MODE TOGGLE — L1 / L2
// ─────────────────────────────────────────────────────────────
function ModeToggle({ activeMode, onChange }: { activeMode: 'L1' | 'L2'; onChange: (m: 'L1' | 'L2') => void }) {
  const modes: { key: 'L1' | 'L2'; label: string }[] = [
    { key: 'L2', label: 'L2 (CLEAN)' },
    { key: 'L1', label: 'L1 (CALIBRATED)' },
  ];


  return (
    <div className="flex border-b border-border-dark dark:border-[#222] font-sans">
      {modes.map(({ key, label }) => {
        const active = key === activeMode;
        return (
          <button
            key={key}
            onClick={() => onChange(key)}
            className={`flex-1 py-[10px] border-0 border-r border-border-dark dark:border-[#222] font-sans text-[11px] tracking-[1.4px] uppercase cursor-pointer transition-all duration-150 outline-none border-b-2 ${
              active
                ? 'bg-canvas dark:bg-[#141414] text-ink dark:text-[#f0f0f0] font-bold border-b-ink dark:border-b-[#f0f0f0]'
                : 'bg-[#f7f7f7] dark:bg-[#1a1a1a] text-[#888] dark:text-[#555] font-normal border-b-transparent'
            }`}
          >
            {label}
          </button>
        );
      })}
      <div className="flex-[2] border-b-2 border-b-transparent bg-[#f7f7f7] dark:bg-[#1a1a1a] border-l border-border-dark dark:border-[#222]" />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// 2. OBSERVATION INPUTS
// ─────────────────────────────────────────────────────────────
function ObservationInputs({
  dates, timesForDate, measurementTypes,
  selectedDate, selectedTime, selectedMeasurementType,
  onDateChange, onTimeChange, onMeasurementTypeChange,
}: {
  dates: string[]; timesForDate: string[]; measurementTypes: string[];
  selectedDate: string; selectedTime: string; selectedMeasurementType: string;
  onDateChange: (v: string) => void; onTimeChange: (v: string) => void;
  onMeasurementTypeChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-[10px]">
      <div>
        <FieldLabel text="Observation Date" />
        <StyledSelect
          value={selectedDate}
          options={dates}
          onChange={(v) => { onDateChange(v); onTimeChange(''); }}
          placeholder="— select date —"
        />
      </div>
      <div>
        <FieldLabel text="Observation Time" />
        <StyledSelect
          value={selectedTime}
          options={timesForDate}
          onChange={onTimeChange}
          placeholder={selectedDate ? '— select time —' : '— select date first —'}
          disabled={!selectedDate}
        />
      </div>
      <div>
        <FieldLabel text="Measurement Type" />
        <StyledSelect
          value={selectedMeasurementType}
          options={measurementTypes}
          onChange={onMeasurementTypeChange}
          placeholder="— select type —"
        />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// 3. WAVELENGTH RANGE INPUTS
// ─────────────────────────────────────────────────────────────
function WavelengthRangeInputs({ min, max, onMinChange, onMaxChange }: {
  min: number; max: number; onMinChange: (v: number) => void; onMaxChange: (v: number) => void;
}) {
  const [minErr, setMinErr] = useState(false);
  const [maxErr, setMaxErr] = useState(false);

  const handleMin = (raw: string) => {
    const v = parseInt(raw);
    if (isNaN(v)) return;
    if (v >= max) { setMinErr(true); return; }
    setMinErr(false);
    onMinChange(Math.max(ABS_MIN, v));
  };

  const handleMax = (raw: string) => {
    const v = parseInt(raw);
    if (isNaN(v)) return;
    if (v <= min) { setMaxErr(true); return; }
    setMaxErr(false);
    onMaxChange(Math.min(ABS_MAX, v));
  };

  const wrapClass = (err: boolean) =>
    `${NUM_WRAP_BASE} border ${err ? 'border-[#c44]' : 'border-border-dark dark:border-[#2a2a2a]'}`;

  return (
    <div className="flex flex-col gap-[6px]">
      <FieldLabel text="Wavelength Range (nm)" />
      <div className="flex items-center gap-2">
        <div className={wrapClass(minErr)}>
          <input
            type="number"
            value={min}
            onChange={(e) => handleMin(e.target.value)}
            className={NUM_INPUT_CLS}
            min={ABS_MIN}
            max={max - 1}
          />
          <span className="font-sans text-[9px] text-ink-muted dark:text-[#444] ml-1 shrink-0 tracking-[0.2px]">(min)</span>
        </div>
        <span className="font-sans text-[13px] text-ink-muted dark:text-[#444] shrink-0">—</span>
        <div className={wrapClass(maxErr)}>
          <input
            type="number"
            value={max}
            onChange={(e) => handleMax(e.target.value)}
            className={NUM_INPUT_CLS}
            min={min + 1}
            max={ABS_MAX}
          />
          <span className="font-sans text-[9px] text-ink-muted dark:text-[#444] ml-1 shrink-0 tracking-[0.2px]">(max)</span>
        </div>
      </div>
      {(minErr || maxErr) && (
        <span className="font-sans text-[9px] text-[#c44] tracking-[0.3px]">Min must be less than Max</span>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// 4. ZOOM SLIDER
// Track fill driven by --track-fill CSS var (set via useEffect).
// Track and thumb colours adapt to dark mode via --slider-* vars.
// ─────────────────────────────────────────────────────────────
function ZoomSlider({ zoom, onChange }: { zoom: number; onChange: (v: number) => void }) {
  const pct       = ((zoom - ZOOM_MIN) / (ZOOM_MAX - ZOOM_MIN)) * 100;
  const sliderRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    sliderRef.current?.style.setProperty('--track-fill', `${pct}%`);
  }, [pct]);

  return (
    <div className="flex flex-col gap-[6px]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
           <FieldLabel text="Spectral Zoom" />
           <span className="text-[9px] text-[#999] dark:text-[#555] font-bold tracking-[1px] mb-1">(X-Axis SCALE)</span>
        </div>
        <span className="font-sans text-[11px] font-bold text-[#333] dark:text-[#d0d0d0] tracking-[0.5px] mb-1 font-mono">
          {zoom === 1 ? 'FULL SCAN' : `${zoom.toFixed(0)}x`}
        </span>
      </div>
      <input
        ref={sliderRef}
        type="range"
        min={ZOOM_MIN}
        max={ZOOM_MAX}
        step={1}
        value={zoom}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className={SLIDER_CLS}
      />

      <div className="flex justify-between font-sans text-[9px] text-ink-muted dark:text-[#444] tracking-[0.3px]">
        {['×1', '×2', '×3', '×4', '×5'].map((l) => <span key={l}>{l}</span>)}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// 5. ELEMENT DROPDOWN
// ─────────────────────────────────────────────────────────────
function ElementDropdown({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <FieldLabel text="Elemental Analysis" />
      <StyledSelect value={value} options={ELEMENTS} onChange={onChange} placeholder="— select element —" />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// 6. EXPORT BUTTONS
// ─────────────────────────────────────────────────────────────
const EXPORT_OPTIONS = [
  {
    format: 'pdf' as const,
    tooltip: 'Export as PDF',
    icon: (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <rect x="2" y="1" width="8" height="11" rx="1" stroke="white" strokeWidth="1.2" />
        <line x1="4" y1="4.5" x2="8" y2="4.5" stroke="white" strokeWidth="1" />
        <line x1="4" y1="6.5" x2="8" y2="6.5" stroke="white" strokeWidth="1" />
        <line x1="4" y1="8.5" x2="7" y2="8.5" stroke="white" strokeWidth="1" />
      </svg>
    ),
  },
  {
    format: 'csv' as const,
    tooltip: 'Export as CSV',
    icon: (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <rect x="1.5" y="1.5" width="11" height="11" rx="1" stroke="white" strokeWidth="1.2" />
        <line x1="1.5" y1="5"   x2="12.5" y2="5"   stroke="white" strokeWidth="0.8" />
        <line x1="1.5" y1="8.5" x2="12.5" y2="8.5" stroke="white" strokeWidth="0.8" />
        <line x1="5"   y1="5"   x2="5"    y2="13"   stroke="white" strokeWidth="0.8" />
        <line x1="9"   y1="5"   x2="9"    y2="13"   stroke="white" strokeWidth="0.8" />
      </svg>
    ),
  },
  {
    format: 'json' as const,
    tooltip: 'Export as JSON',
    icon: (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M4 2 Q2 2 2 4 L2 10 Q2 12 4 12"  stroke="white" strokeWidth="1.2" fill="none" strokeLinecap="round" />
        <path d="M10 2 Q12 2 12 4 L12 10 Q12 12 10 12" stroke="white" strokeWidth="1.2" fill="none" strokeLinecap="round" />
        <circle cx="7"   cy="7" r="1" fill="white" />
        <circle cx="4.5" cy="7" r="1" fill="white" />
        <circle cx="9.5" cy="7" r="1" fill="white" />
      </svg>
    ),
  },
];

function ExportButtons({ onExport }: { onExport: (f: 'pdf' | 'csv' | 'json') => void }) {
  return (
    <div>
      <FieldLabel text="Export Analysis" />
      <div className="flex gap-2">
        {EXPORT_OPTIONS.map(({ format, tooltip, icon }) => (
          <button
            key={format}
            onClick={() => onExport(format)}
            title={tooltip}
            className={`w-9 h-9 border-0 rounded-[5px] cursor-pointer flex items-center justify-center transition-all duration-[120ms] shrink-0 hover:scale-[1.06] hover:shadow-md active:scale-[0.96] ${EXPORT_BG[format]}`}
          >
            {icon}
          </button>
        ))}
      </div>
    </div>
  );
}

// ═════════════════════════════════════════════════════════════
// DEFAULT EXPORT: RangeSelectorPanel
// ═════════════════════════════════════════════════════════════
export default function RangeSelectorPanel({ 
  mode, onModeChange, 
  zoom, onZoomChange 
}: { 
  mode: 'L1' | 'L2', onModeChange: (m: 'L1' | 'L2') => void,
  zoom: number, onZoomChange: (z: number) => void
}) {
  const [selectedDate,            setSelectedDate]            = useState('');
  const [selectedTime,            setSelectedTime]            = useState('');
  const [selectedMeasurementType, setSelectedMeasurementType] = useState('');
  const [minWl,                   setMinWl]                   = useState(200);
  const [maxWl,                   setMaxWl]                   = useState(900);
  const [element,                 setElement]                 = useState('');



  const allDates         = useMemo(() => getUniqueDates(mockObservationData), []);
  const timesForDate     = useMemo(
    () => (selectedDate ? getTimesForDate(mockObservationData, selectedDate) : []),
    [selectedDate]
  );
  const measurementTypes = useMemo(() => getUniqueMeasurementTypes(mockObservationData), []);

  const handleExport = (format: 'pdf' | 'csv' | 'json') => {
    console.log('[Export]', format, { mode, selectedDate, selectedTime, selectedMeasurementType, minWl, maxWl, zoom, element });
  };

  return (
    <section className="font-sans border border-border-dark dark:border-[#222] rounded-md bg-canvas dark:bg-[#141414] overflow-hidden transition-colors duration-200">
      <ModeToggle activeMode={mode} onChange={onModeChange} />


      <div className="flex items-stretch flex-wrap">

        {/* COL 1 — Observation Metadata */}
        <div className="flex-[1_1_240px] p-5 px-6 flex flex-col justify-center min-w-0">
          <ObservationInputs
            dates={allDates}
            timesForDate={timesForDate}
            measurementTypes={measurementTypes}
            selectedDate={selectedDate}
            selectedTime={selectedTime}
            selectedMeasurementType={selectedMeasurementType}
            onDateChange={setSelectedDate}
            onTimeChange={setSelectedTime}
            onMeasurementTypeChange={setSelectedMeasurementType}
          />
        </div>

        <ColDivider />

        {/* COL 2 — Wavelength Range + Zoom */}
        <div className="flex-[1.4_1_280px] p-5 px-6 flex flex-col justify-center gap-[18px] min-w-0">
          <WavelengthRangeInputs min={minWl} max={maxWl} onMinChange={setMinWl} onMaxChange={setMaxWl} />
          <ZoomSlider zoom={zoom} onChange={onZoomChange} />
        </div>


        <ColDivider />

        {/* COL 3 — Elemental Analysis + Export */}
        <div className="flex-[1_1_200px] p-5 px-6 flex flex-col justify-center gap-4 min-w-0">
          <ElementDropdown value={element} onChange={setElement} />
          <ExportButtons onExport={handleExport} />
        </div>

      </div>
    </section>
  );
}