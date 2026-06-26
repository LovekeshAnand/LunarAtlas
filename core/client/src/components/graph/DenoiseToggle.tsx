import { useState } from 'react';
import { type DenoiseMode } from '../../services/apiService';

interface DenoiseToggleProps {
  value: DenoiseMode;
  onChange: (mode: DenoiseMode) => void;
  disabled?: boolean;
}

export default function DenoiseToggle({
  value,
  onChange,
  disabled = false,
}: DenoiseToggleProps) {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  const modes: {
    key: DenoiseMode;
    label: string;
    description: string;
    tooltip: string;
  }[] = [
    {
      key: 'none',
      label: 'None (L2 Clean)',
      description: 'Standard paired background-subtracted spectrum.',
      tooltip: 'Show original baseline-retaining clean measurements.',
    },
    {
      key: 'als',
      label: 'ALS Correction',
      description: 'Asymmetric Least Squares removes slowly-varying baseline/continuum.',
      tooltip: 'Filter out thermal radiation and substrate glow using Whittaker smoothing (λ=1e5, p=0.01).',
    },
    {
      key: 'savgol',
      label: 'Savitzky-Golay',
      description: 'Local polynomial smoothing to reduce high-frequency noise.',
      tooltip: 'Suppress detector shot noise while preserving peak intensity and position (Window=11, Poly=3).',
    },
  ];

  return (
    <div className={`flex flex-col gap-1 font-sans ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
      <div className="flex items-center justify-between">
        <span className="font-sans text-[9px] font-black text-slate-400 uppercase tracking-widest block leading-none select-none">
          Spectral Denoising Layer
        </span>
        <div className="relative flex items-center">
          <button
            type="button"
            onMouseEnter={() => setActiveTooltip('info')}
            onMouseLeave={() => setActiveTooltip(null)}
            className="text-[10px] text-slate-400 hover:text-slate-600 transition-colors border-0 bg-transparent cursor-pointer p-0 select-none outline-none leading-none"
          >
            ⓘ
          </button>
          {activeTooltip === 'info' && (
            <div className="absolute right-0 bottom-full mb-1.5 z-50 w-52 bg-slate-900 text-white text-[9px] p-2 rounded shadow-md leading-relaxed animate-in fade-in duration-100 font-normal">
              Apply real-time mathematical denoising in the visualization layer without altering database records.
            </div>
          )}
        </div>
      </div>

      {/* Pill Selector */}
      <div className="flex bg-slate-50 border border-solid border-slate-200 p-0.5 rounded items-center gap-0.5 shadow-inner h-7 relative">
        {modes.map(({ key, label, tooltip, description }) => {
          const active = key === value;
          return (
            <div
              key={key}
              className="relative flex-1 h-full flex"
              onMouseEnter={() => setActiveTooltip(key)}
              onMouseLeave={() => setActiveTooltip(null)}
            >
              <button
                type="button"
                onClick={() => {
                  if (active) {
                    onChange('none'); // Clicking active returns to none
                  } else {
                    onChange(key);
                  }
                }}
                className={`w-full py-0 px-2 border-0 font-sans font-black text-[9px] uppercase tracking-wider rounded cursor-pointer transition-all duration-150 outline-none h-full flex items-center justify-center select-none ${
                  active
                    ? 'bg-black text-white shadow-sm border border-black/10'
                    : 'bg-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                {key === 'none' ? 'None' : key === 'als' ? 'ALS' : 'SG'}
              </button>

              {/* Tooltip on Hover */}
              {activeTooltip === key && (
                <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 z-50 w-56 bg-slate-900 text-white p-2.5 rounded shadow-lg animate-in fade-in slide-in-from-bottom-1 duration-150">
                  <div className="text-[9px] font-black uppercase tracking-wider text-white mb-0.5">
                    {label}
                  </div>
                  <div className="text-[9px] leading-relaxed text-slate-200 font-medium">
                    {description}
                  </div>
                  <div className="text-[8px] italic text-slate-400 mt-1 border-t border-slate-800 pt-1 leading-normal font-light">
                    {tooltip}
                  </div>
                  <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-[4px] border-solid border-transparent border-t-slate-900" />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
