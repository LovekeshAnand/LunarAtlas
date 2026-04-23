import { useMemo, useEffect, useRef } from 'react';
import { type MeasurementInfo } from '../../services/apiService';


const ELEMENTS = ['All', 'Fe', 'Mg', 'Si', 'Al', 'Ca', 'Ti', 'Na', 'H₂O', 'O'];

// ... ClS constants remain same ...
const SELECT_CLS =
  'flex items-center bg-white border border-solid border-gray-300 text-gray-700 font-sans text-[13px] rounded px-[10px] transition-colors duration-150 flex-1 focus-within:border-blue-400 focus-within:ring-1 focus-within:ring-blue-100';

const NUM_INPUT_CLS =
  'flex-[0.5] min-w-0 bg-transparent border-0 outline-none font-sans font-medium text-[13px] text-blue-700 py-[4px] ' +
  '[appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none text-center';

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
      <span className="absolute right-[10px] text-[10px] text-[#999] dark:text-[#555] pointer-events-none select-none">▾</span>
    </div>
  );
}

function ColDivider() {
  return <div className="w-px bg-border dark:bg-[#222] self-stretch shrink-0" />;
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
           <FieldLabel text="Data Density (M4)" />
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
      />
      <div className="flex justify-between font-sans text-[11px] text-gray-400 font-medium">
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
    <section className="border border-solid border-gray-200 bg-white rounded-md shadow-sm overflow-hidden relative">
      <ModeToggle activeMode={mode} onChange={onModeChange} />
      <div className="flex items-stretch flex-wrap">
        
        {/* Real-time DB Inputs */}
        <div className="flex-[1_1_240px] p-5 px-6 flex flex-col justify-center min-w-0 bg-white border-r border-solid border-gray-200">
          <div className="flex flex-col gap-4">
             <div>
                <FieldLabel text="Observation Session" />
                <StyledSelect
                  value={selectedObservationId}
                  options={observationOptions}
                  onChange={onObservationChange}
                  placeholder="— Pick one —"
                />
             </div>
             <div>
                <FieldLabel text="Data Point / Pulse" />
                <StyledSelect
                  value={selectedMeasurementId}
                  options={measurementOptions}
                  onChange={onMeasurementChange}
                  placeholder={selectedObservationId ? "— Pick Measurement —" : "— Select above first —"}
                  disabled={!selectedObservationId}
                />
             </div>
          </div>
        </div>

        {/* Spectral Domain Controls */}
        <div className="flex-[1.4_1_280px] p-5 px-6 flex flex-col justify-center gap-[18px] min-w-0 border-r border-solid border-gray-200 bg-white relative">
          <div className="flex flex-col gap-2">
            <FieldLabel text="Wavelength Zoom Range (nm)" />
            <div className="flex items-center gap-2">
                <input 
                  type="number" value={minWavelength} 
                  onChange={(e) => onMinWavelengthChange(parseFloat(e.target.value))}
                  className={NUM_INPUT_CLS + " border border-solid border-gray-200 rounded-sm bg-gray-50 hover:bg-white focus:bg-white transition-colors"} 
                />
                <span className="font-sans font-medium text-gray-400 px-2">to</span>
                <input 
                  type="number" value={maxWavelength} 
                  onChange={(e) => onMaxWavelengthChange(parseFloat(e.target.value))}
                  className={NUM_INPUT_CLS + " border border-solid border-gray-200 rounded-sm bg-gray-50 hover:bg-white focus:bg-white transition-colors"} 
                />
            </div>
          </div>
          <ProportionSlider proportion={proportion} onChange={onProportionChange} />
        </div>

        {/* Analytics & Export */}
        <div className="flex-[1_1_200px] p-5 px-6 flex flex-col justify-center gap-4 min-w-0 bg-white">
          <div>
             <FieldLabel text="Elemental Focus Tool" />
             <StyledSelect value={element} options={ELEMENTS} onChange={onElementChange} placeholder="None active" />
          </div>
          <div className="pt-2 border-t border-solid border-gray-200">
             <div className="flex flex-col gap-1 opacity-80">
                <span className="font-sans text-[12px] text-gray-500 font-medium inline-block">Analysis Status:</span>
                <span className="font-sans text-[13px] text-blue-600 font-semibold inline-block">Monitoring...</span>
             </div>
          </div>
        </div>

      </div>
    </section>
  );
}
