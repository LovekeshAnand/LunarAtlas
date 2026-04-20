import { useMemo, useEffect, useRef } from 'react';
import { type MeasurementInfo } from '../../services/apiService';


const ELEMENTS = ['Fe', 'Mg', 'Si', 'Al', 'Ca', 'Ti', 'Na', 'H₂O', 'O'];

// ... ClS constants remain same ...
const SELECT_CLS =
  'flex items-center bg-[#f5f5f5] dark:bg-[#1a1a1a] rounded px-[10px] transition-colors duration-150 flex-1 focus-within:border-[#999] dark:focus-within:border-[#555]';

const NUM_INPUT_CLS =
  'flex-1 min-w-0 bg-transparent border-0 outline-none font-mono text-[12px] font-semibold text-[#222] dark:text-[#d0d0d0] py-[7px] ' +
  '[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none';

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



// --- Sub-components ---

function FieldLabel({ text }: { text: string }) {
  return (
    <label className="font-sans text-[9px] font-bold tracking-[1.3px] text-[#888] dark:text-[#777] uppercase block mb-1">
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
      <span className="absolute right-[10px] text-[10px] text-[#999] dark:text-[#555] pointer-events-none select-none">▾</span>
    </div>
  );
}

function ColDivider() {
  return <div className="w-px bg-border dark:bg-[#222] self-stretch shrink-0" />;
}

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

function ProportionSlider({ proportion, onChange }: { proportion: number; onChange: (v: number) => void }) {
  const pct = Math.max(0, Math.min(100, proportion * 100));
  const sliderRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    sliderRef.current?.style.setProperty('--track-fill', `${pct}%`);
  }, [pct]);

  return (
    <div className="flex flex-col gap-[6px]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
           <FieldLabel text="Data Density (LTTB)" />
           <span className="text-[9px] text-[#999] dark:text-[#555] font-bold tracking-[1px] mb-1">(PROPORTION)</span>
        </div>
        <span className="font-sans text-[11px] font-bold text-[#333] dark:text-[#d0d0d0] tracking-[0.5px] mb-1 font-mono">
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
      />
      <div className="flex justify-between font-sans text-[9px] text-ink-muted dark:text-[#444] tracking-[0.3px]">
        {['0.1%', '25%', '50%', '75%', '100%'].map((l) => <span key={l}>{l}</span>)}
      </div>
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
  measurements, selectedMeasurementId, onMeasurementChange,
}: { 
  mode: 'L1' | 'L2', 
  onModeChange: (m: 'L1' | 'L2') => void,
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
  selectedMeasurementId: string,
  onMeasurementChange: (id: string) => void,
}) {

  const observationOptions = useMemo(() => 
    observations.map(obs => ({
      label: `${obs.target_name} (${new Date(obs.creation_datetime).toLocaleDateString()})`,
      value: obs.observation_id
    })),
    [observations]
  );

  const measurementOptions = useMemo(() => 
    measurements.map(m => ({
      label: `Measurement #${m.measurement_index} (${m.measurement_type})`,
      value: m.measurement_id
    })),
    [measurements]
  );

  return (
    <section className="font-sans border border-border-dark dark:border-[#222] rounded-md bg-canvas dark:bg-[#141414] overflow-hidden transition-colors duration-200 shadow-xl">
      <ModeToggle activeMode={mode} onChange={onModeChange} />
      <div className="flex items-stretch flex-wrap">
        
        {/* Real-time DB Inputs */}
        <div className="flex-[1_1_240px] p-5 px-6 flex flex-col justify-center min-w-0 bg-[#fafafa] dark:bg-[#111]">
          <div className="flex flex-col gap-4">
             <div>
                <FieldLabel text="Observation Session" />
                <StyledSelect
                  value={selectedObservationId}
                  options={observationOptions}
                  onChange={onObservationChange}
                  placeholder="— select observation —"
                />
             </div>
             <div>
                <FieldLabel text="Data Point / Pulse" />
                <StyledSelect
                  value={selectedMeasurementId}
                  options={measurementOptions}
                  onChange={onMeasurementChange}
                  placeholder={selectedObservationId ? "— select measurement —" : "— select observation first —"}
                  disabled={!selectedObservationId}
                />
             </div>
          </div>
        </div>

        <ColDivider />

        {/* Spectral Domain Controls */}
        <div className="flex-[1.4_1_280px] p-5 px-6 flex flex-col justify-center gap-[18px] min-w-0">
          <div className="flex flex-col gap-2">
            <FieldLabel text="Wavelength Range (nm)" />
            <div className="flex items-center gap-2">
                <input 
                  type="number" value={minWavelength} 
                  onChange={(e) => onMinWavelengthChange(parseFloat(e.target.value))}
                  className={NUM_INPUT_CLS + " border border-border-dark dark:border-[#2a2a2a] px-2 rounded bg-white dark:bg-[#1a1a1a]"} 
                />
                <span className="text-gray-400">—</span>
                <input 
                  type="number" value={maxWavelength} 
                  onChange={(e) => onMaxWavelengthChange(parseFloat(e.target.value))}
                  className={NUM_INPUT_CLS + " border border-border-dark dark:border-[#2a2a2a] px-2 rounded bg-white dark:bg-[#1a1a1a]"} 
                />
            </div>
          </div>
          <ProportionSlider proportion={proportion} onChange={onProportionChange} />
        </div>

        <ColDivider />

        {/* Analytics & Export */}
        <div className="flex-[1_1_200px] p-5 px-6 flex flex-col justify-center gap-4 min-w-0 bg-[#fafafa] dark:bg-[#111]">
          <div>
            <FieldLabel text="Elemental Analysis" />
            <StyledSelect value={element} options={ELEMENTS} onChange={onElementChange} placeholder="NIST Peak Matching" />
          </div>
          <div className="pt-2 border-t border-gray-200 dark:border-[#222]">
             <div className="flex justify-between items-center opacity-50 cursor-not-allowed">
                <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Research Export</span>
                <div className="flex gap-1">
                   <div className="w-2 h-2 rounded-full bg-red-400" />
                   <div className="w-2 h-2 rounded-full bg-green-400" />
                   <div className="w-2 h-2 rounded-full bg-blue-400" />
                </div>
             </div>
          </div>
        </div>

      </div>
    </section>
  );
}
