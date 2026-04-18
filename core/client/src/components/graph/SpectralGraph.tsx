const TOP_CLASS:  Record<number, string> = { 20: 'top-[20%]', 40: 'top-[40%]', 60: 'top-[60%]', 80: 'top-[80%]' };
const LEFT_CLASS: Record<number, string> = { 20: 'left-[20%]', 40: 'left-[40%]', 60: 'left-[60%]', 80: 'left-[80%]' };

const NM_TICKS  = ['200', '300', '400', '500', '600', '700', '800', '900', '1000'];
const GRID_PCTS = [20, 40, 60, 80];

export default function SpectralGraph() {
  return (
    <div className="font-sans mt-4 border border-border-dark dark:border-[#222] rounded-md bg-canvas-alt dark:bg-[#141414] overflow-hidden transition-colors duration-200">

      {/* Chart area */}
      <div className="relative h-[320px] flex">

        {/* Y-axis label */}
        <div className="w-10 shrink-0 flex items-center justify-center">
          <span className="text-[10px] font-semibold text-[#999] dark:text-[#555] tracking-[1.5px] uppercase -rotate-90 whitespace-nowrap">
            Intensity
          </span>
        </div>

        {/* Graph body */}
        <div className="flex-1 relative border-l border-border-dark dark:border-[#222]">

          {/* Horizontal grid lines */}
          {GRID_PCTS.map((pct) => (
            <div
              key={`h-${pct}`}
              className={`absolute left-0 right-0 border-t border-dashed border-border dark:border-[#1e1e1e] ${TOP_CLASS[pct]}`}
            />
          ))}

          {/* Vertical grid lines */}
          {GRID_PCTS.map((pct) => (
            <div
              key={`v-${pct}`}
              className={`absolute top-0 bottom-0 border-l border-dashed border-border dark:border-[#1e1e1e] ${LEFT_CLASS[pct]}`}
            />
          ))}

          {/* Placeholder content */}
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
            <svg width="140" height="44" viewBox="0 0 140 44" fill="none">
              <path
                d="M5 38 Q15 38 22 22 Q28 6 34 20 Q40 34 48 30 Q58 22 64 28 Q74 36 84 17 Q90 6 98 20 Q106 34 116 30 Q128 26 135 32"
                stroke="#555"
                strokeWidth="1.6"
                fill="none"
                strokeLinecap="round"
              />
            </svg>
            <span className="text-[12px] text-[#c0c0c0] dark:text-[#333] tracking-[0.5px]">Spectral Graph</span>
            <span className="text-[10px] text-[#d0d0d0] dark:text-[#2a2a2a] tracking-[0.3px]">Select parameters above to load data</span>
          </div>
        </div>
      </div>

      {/* X-axis tick labels */}
      <div className="border-t border-border-dark dark:border-[#222] flex items-center py-2 pl-12 pr-2 justify-between">
        {NM_TICKS.map((nm) => (
          <span key={nm} className="text-[9px] text-ink-muted dark:text-[#444] tracking-[0.3px]">{nm}</span>
        ))}
        <span className="text-[10px] font-semibold text-[#999] dark:text-[#555] tracking-[1.5px] uppercase ml-2">nm</span>
      </div>
    </div>
  );
}
