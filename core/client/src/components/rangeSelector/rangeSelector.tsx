import { useState, useMemo, useEffect } from 'react';
import {
  mockObservationData,
  getUniqueDates,
  getTimesForDate,
  getUniqueMeasurementTypes,
  ELEMENTS,
} from '../../utils/mockData';

const F = "'Helvetica', 'Helvetica Neue', Arial, sans-serif";
const ABS_MIN = 0;
const ABS_MAX = 2000;
const ZOOM_MIN = 1;
const ZOOM_MAX = 5;

// ─────────────────────────────────────────────────────────
// Inject pseudo-selector styles once (slider thumb, spinner,
// select appearance — things that can't be done with inline styles)
// ─────────────────────────────────────────────────────────
const INJECTED_ID = 'rs-pseudo-styles';
const PSEUDO_CSS = `
  .rs-select {
    width: 100%;
    appearance: none;
    -webkit-appearance: none;
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 7px 32px 7px 10px;
    font-family: 'Helvetica', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px;
    font-weight: 500;
    color: #222;
    cursor: pointer;
    outline: none;
    transition: border-color 0.15s ease;
    line-height: 1.4;
  }
  .rs-select:focus { border-color: #999; }
  .rs-select:disabled { color: #bbb; cursor: not-allowed; background: #fafafa; }
  .rs-select option {
    font-family: 'Helvetica', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px; color: #222; background: #fff;
  }
  .rs-num-wrap:focus-within { border-color: #999; }
  .rs-num-input {
    flex: 1; min-width: 0; background: transparent; border: none; outline: none;
    font-family: 'Helvetica', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px; font-weight: 600; color: #222; padding: 7px 0;
    -moz-appearance: textfield;
  }
  .rs-num-input::-webkit-outer-spin-button,
  .rs-num-input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
  .rs-slider {
    -webkit-appearance: none; appearance: none;
    width: 100%; height: 4px; border-radius: 2px;
    outline: none; cursor: pointer; transition: background 0.15s ease;
  }
  .rs-slider::-webkit-slider-thumb {
    -webkit-appearance: none; width: 14px; height: 14px;
    background: #333; border-radius: 50%; cursor: pointer;
    border: 2px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.25);
    transition: transform 0.12s ease, box-shadow 0.12s ease;
  }
  .rs-slider::-webkit-slider-thumb:hover {
    transform: scale(1.15); box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  }
  .rs-slider::-moz-range-thumb {
    width: 14px; height: 14px; background: #333; border-radius: 50%;
    cursor: pointer; border: 2px solid #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.25);
  }
  .rs-export-btn:hover { transform: scale(1.06); box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
  .rs-export-btn:active { transform: scale(0.96); }
  @media (max-width: 768px) {
    .rs-select, .rs-num-input { font-size: 13px; padding: 9px 10px; }
  }
  @media (max-width: 480px) { .rs-select { font-size: 14px; } }
`;

function usePseudoStyles() {
  useEffect(() => {
    if (document.getElementById(INJECTED_ID)) return;
    const tag = document.createElement('style');
    tag.id = INJECTED_ID;
    tag.textContent = PSEUDO_CSS;
    document.head.appendChild(tag);
    return () => { /* leave mounted — shared across instances */ };
  }, []);
}

// ─────────────────────────────────────────────────────────
// SHARED: FieldLabel
// ─────────────────────────────────────────────────────────
function FieldLabel({ text }: { text: string }) {
  return (
    <label
      style={{
        fontFamily: F, fontSize: '9px', fontWeight: '700',
        letterSpacing: '1.3px', color: '#888', textTransform: 'uppercase',
        display: 'block', marginBottom: '4px',
      }}
    >
      {text}
    </label>
  );
}

// ─────────────────────────────────────────────────────────
// SHARED: StyledSelect
// ─────────────────────────────────────────────────────────
function StyledSelect({
  value, options, onChange, placeholder = '— select —', disabled = false,
}: {
  value: string; options: string[];
  onChange: (v: string) => void; placeholder?: string; disabled?: boolean;
}) {
  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="rs-select"
      >
        <option value="">{placeholder}</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
      <span style={{ position: 'absolute', right: '10px', fontSize: '10px', color: '#999', pointerEvents: 'none', userSelect: 'none' }}>▾</span>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// SHARED: Column divider
// ─────────────────────────────────────────────────────────
function ColDivider() {
  return <div style={{ width: '1px', background: '#e8e8e8', alignSelf: 'stretch', flexShrink: 0 }} />;
}

// ─────────────────────────────────────────────────────────
// 1. MODE TOGGLE — L1 / L2
// ─────────────────────────────────────────────────────────
function ModeToggle({ activeMode, onChange }: { activeMode: 'L1' | 'L2'; onChange: (m: 'L1' | 'L2') => void }) {
  const modes: { key: 'L1' | 'L2'; label: string }[] = [
    { key: 'L1', label: 'L1 (CALIBRATED)' },
    { key: 'L2', label: 'L2 (CLEAN)' },
  ];

  return (
    <div style={{ display: 'flex', borderBottom: '1px solid #ddd', fontFamily: F }}>
      {modes.map(({ key, label }) => {
        const active = key === activeMode;
        return (
          <button
            key={key}
            onClick={() => onChange(key)}
            style={{
              flex: 1, padding: '10px 0',
              background: active ? '#fff' : '#f7f7f7',
              border: 'none',
              borderBottom: active ? '2px solid #111' : '2px solid transparent',
              borderRight: '1px solid #ddd',
              color: active ? '#111' : '#888',
              fontFamily: F, fontSize: '11px',
              fontWeight: active ? '700' : '400',
              letterSpacing: '1.4px', textTransform: 'uppercase',
              cursor: 'pointer', transition: 'all 0.15s ease', outline: 'none',
            }}
          >
            {label}
          </button>
        );
      })}
      <div style={{ flex: 2, borderBottom: '2px solid transparent', background: '#f7f7f7', borderLeft: '1px solid #ddd' }} />
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// 2. OBSERVATION INPUTS — Date / Time / Measurement Type
// ─────────────────────────────────────────────────────────
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <div>
        <FieldLabel text="Observation Date" />
        <StyledSelect value={selectedDate} options={dates} onChange={(v) => { onDateChange(v); onTimeChange(''); }} placeholder="— select date —" />
      </div>
      <div>
        <FieldLabel text="Observation Time" />
        <StyledSelect value={selectedTime} options={timesForDate} onChange={onTimeChange} placeholder={selectedDate ? '— select time —' : '— select date first —'} disabled={!selectedDate} />
      </div>
      <div>
        <FieldLabel text="Measurement Type" />
        <StyledSelect value={selectedMeasurementType} options={measurementTypes} onChange={onMeasurementTypeChange} placeholder="— select type —" />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// 3. WAVELENGTH RANGE INPUTS — min / max numeric fields
// ─────────────────────────────────────────────────────────
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

  const wrapStyle = (err: boolean): React.CSSProperties => ({
    display: 'flex', alignItems: 'center',
    background: '#f5f5f5',
    border: `1px solid ${err ? '#c44' : '#ddd'}`,
    borderRadius: '4px', padding: '0 10px',
    transition: 'border-color 0.15s ease',
    flex: 1,
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      <FieldLabel text="Wavelength Range (nm)" />
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={wrapStyle(minErr)} className="rs-num-wrap">
          <input type="number" value={min} onChange={(e) => handleMin(e.target.value)} className="rs-num-input" min={ABS_MIN} max={max - 1} />
          <span style={{ fontFamily: F, fontSize: '9px', color: '#bbb', marginLeft: '4px', flexShrink: 0, letterSpacing: '0.2px' }}>(min)</span>
        </div>
        <span style={{ fontFamily: F, fontSize: '13px', color: '#bbb', flexShrink: 0 }}>—</span>
        <div style={wrapStyle(maxErr)} className="rs-num-wrap">
          <input type="number" value={max} onChange={(e) => handleMax(e.target.value)} className="rs-num-input" min={min + 1} max={ABS_MAX} />
          <span style={{ fontFamily: F, fontSize: '9px', color: '#bbb', marginLeft: '4px', flexShrink: 0, letterSpacing: '0.2px' }}>(max)</span>
        </div>
      </div>
      {(minErr || maxErr) && (
        <span style={{ fontFamily: F, fontSize: '9px', color: '#c44', letterSpacing: '0.3px' }}>Min must be less than Max</span>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// 4. ZOOM SLIDER — 1x to 5x
// ─────────────────────────────────────────────────────────
function ZoomSlider({ zoom, onChange }: { zoom: number; onChange: (v: number) => void }) {
  const pct = ((zoom - ZOOM_MIN) / (ZOOM_MAX - ZOOM_MIN)) * 100;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <FieldLabel text="Zoom Level" />
        <span style={{ fontFamily: F, fontSize: '11px', fontWeight: '700', color: '#333', letterSpacing: '0.5px', marginBottom: '4px' }}>
          ×{zoom.toFixed(1)}
        </span>
      </div>
      <input
        type="range" min={ZOOM_MIN} max={ZOOM_MAX} step={0.1} value={zoom}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="rs-slider"
        style={{ background: `linear-gradient(to right, #333 0%, #333 ${pct}%, #ddd ${pct}%, #ddd 100%)` }}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: F, fontSize: '9px', color: '#bbb', letterSpacing: '0.3px' }}>
        {['×1', '×2', '×3', '×4', '×5'].map((l) => <span key={l}>{l}</span>)}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// 5. ELEMENT DROPDOWN
// ─────────────────────────────────────────────────────────
function ElementDropdown({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <FieldLabel text="Elemental Analysis" />
      <StyledSelect value={value} options={ELEMENTS} onChange={onChange} placeholder="— select element —" />
    </div>
  );
}

// ─────────────────────────────────────────────────────────
// 6. EXPORT BUTTONS — PDF / CSV / JSON
// ─────────────────────────────────────────────────────────
const EXPORT_OPTIONS = [
  {
    format: 'pdf' as const, color: '#8b4444', hover: '#a05050', tooltip: 'Export as PDF',
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
    format: 'csv' as const, color: '#3a6b3a', hover: '#4a7d4a', tooltip: 'Export as CSV',
    icon: (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <rect x="1.5" y="1.5" width="11" height="11" rx="1" stroke="white" strokeWidth="1.2" />
        <line x1="1.5" y1="5" x2="12.5" y2="5" stroke="white" strokeWidth="0.8" />
        <line x1="1.5" y1="8.5" x2="12.5" y2="8.5" stroke="white" strokeWidth="0.8" />
        <line x1="5" y1="5" x2="5" y2="13" stroke="white" strokeWidth="0.8" />
        <line x1="9" y1="5" x2="9" y2="13" stroke="white" strokeWidth="0.8" />
      </svg>
    ),
  },
  {
    format: 'json' as const, color: '#3a4d6b', hover: '#4a5e80', tooltip: 'Export as JSON',
    icon: (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M4 2 Q2 2 2 4 L2 10 Q2 12 4 12" stroke="white" strokeWidth="1.2" fill="none" strokeLinecap="round" />
        <path d="M10 2 Q12 2 12 4 L12 10 Q12 12 10 12" stroke="white" strokeWidth="1.2" fill="none" strokeLinecap="round" />
        <circle cx="7" cy="7" r="1" fill="white" />
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
      <div style={{ display: 'flex', gap: '8px' }}>
        {EXPORT_OPTIONS.map(({ format, color, hover, tooltip, icon }) => (
          <button
            key={format}
            onClick={() => onExport(format)}
            title={tooltip}
            className="rs-export-btn"
            style={{
              width: '36px', height: '36px', border: 'none', borderRadius: '5px',
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'transform 0.12s ease, box-shadow 0.12s ease', flexShrink: 0,
              background: color,
            }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = hover)}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = color)}
          >
            {icon}
          </button>
        ))}
      </div>
    </div>
  );
}

// ═════════════════════════════════════════════════════════
// DEFAULT EXPORT: RangeSelectorPanel
// ═════════════════════════════════════════════════════════
export default function RangeSelectorPanel() {
  usePseudoStyles();

  const [mode, setMode] = useState<'L1' | 'L2'>('L1');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [selectedMeasurementType, setSelectedMeasurementType] = useState('');
  const [minWl, setMinWl] = useState(200);
  const [maxWl, setMaxWl] = useState(900);
  const [zoom, setZoom] = useState(3);
  const [element, setElement] = useState('');

  const allDates = useMemo(() => getUniqueDates(mockObservationData), []);
  const timesForDate = useMemo(
    () => (selectedDate ? getTimesForDate(mockObservationData, selectedDate) : []),
    [selectedDate]
  );
  const measurementTypes = useMemo(() => getUniqueMeasurementTypes(mockObservationData), []);

  const handleExport = (format: 'pdf' | 'csv' | 'json') => {
    console.log('[Export]', format, { mode, selectedDate, selectedTime, selectedMeasurementType, minWl, maxWl, zoom, element });
  };

  return (
    <section
      style={{
        fontFamily: F, border: '1px solid #ddd',
        borderRadius: '6px', background: '#fff', overflow: 'hidden',
      }}
    >
      <ModeToggle activeMode={mode} onChange={setMode} />

      <div style={{ display: 'flex', alignItems: 'stretch', flexWrap: 'wrap' }}>

        {/* COL 1 — Observation Metadata */}
        <div style={{ flex: '1 1 240px', padding: '20px 24px', display: 'flex', flexDirection: 'column', justifyContent: 'center', minWidth: 0 }}>
          <ObservationInputs
            dates={allDates} timesForDate={timesForDate} measurementTypes={measurementTypes}
            selectedDate={selectedDate} selectedTime={selectedTime} selectedMeasurementType={selectedMeasurementType}
            onDateChange={setSelectedDate} onTimeChange={setSelectedTime} onMeasurementTypeChange={setSelectedMeasurementType}
          />
        </div>

        <ColDivider />

        {/* COL 2 — Wavelength Range + Zoom */}
        <div style={{ flex: '1.4 1 280px', padding: '20px 24px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '18px', minWidth: 0 }}>
          <WavelengthRangeInputs min={minWl} max={maxWl} onMinChange={setMinWl} onMaxChange={setMaxWl} />
          <ZoomSlider zoom={zoom} onChange={setZoom} />
        </div>

        <ColDivider />

        {/* COL 3 — Elemental Analysis + Export */}
        <div style={{ flex: '1 1 200px', padding: '20px 24px', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '16px', minWidth: 0 }}>
          <ElementDropdown value={element} onChange={setElement} />
          <ExportButtons onExport={handleExport} />
        </div>

      </div>
    </section>
  );
}