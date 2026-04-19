import { type SpectralData } from '../../services/mockDataService';

const NM_TICKS  = ['200', '300', '400', '500', '600', '700', '800', '900', '1000'];

interface SpectralGraphProps {
  data: SpectralData[];
  isLoading: boolean;
  viewMode: 'L1' | 'L2';
  zoom: number;
}

// SVG Chart calculation
const chartWidth  = 1000;
const chartHeight = 320;

export default function SpectralGraph({ data, isLoading, viewMode, zoom }: SpectralGraphProps) {

  
  const generatePath = (key: 'intensity' | 'rawPlasma' | 'rawBackground') => {
    if (!data.length) return '';
    
    // Mission range
    const ABS_MIN = 164.35;
    const ABS_MAX = 878.26;
    const ABS_CENTER = (ABS_MIN + ABS_MAX) / 2;
    const ABS_RANGE = ABS_MAX - ABS_MIN;

    // Viewport calculation based on zoom (centered on current range)
    const viewRange = ABS_RANGE / zoom;
    const minX = ABS_CENTER - (viewRange / 2);
    const maxX = ABS_CENTER + (viewRange / 2);

    const minY = 0;
    const maxY = viewMode === 'L2' ? 1000 : 2500;

    const points = data
      .filter(d => d.wavelength >= minX && d.wavelength <= maxX) // Clip data points outside viewport
      .map((d) => {
        const x = ((d.wavelength - minX) / (maxX - minX)) * chartWidth;
        const val = d[key] as number;
        const y = chartHeight - ((val - minY) / (maxY - minY)) * chartHeight;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      });

    if (points.length < 2) return '';
    return `M ${points.join(' L ')}`;
  };


  return (
    <div className="font-sans mt-4 border border-border-dark dark:border-[#222] rounded-md bg-canvas-alt dark:bg-[#141414] overflow-hidden transition-colors duration-200">

      {/* Chart area */}
      <div className="relative h-[320px] flex">

        {/* Y-axis label */}
        <div className="w-10 shrink-0 flex items-center justify-center">
          <span className="text-[10px] font-semibold text-[#999] dark:text-[#555] tracking-[1.5px] uppercase -rotate-90 whitespace-nowrap">
            {viewMode === 'L2' ? 'Cleaned Intensity' : 'Raw Counts'}
          </span>
        </div>

        {/* Graph body */}
        <div className="flex-1 relative border-l border-border-dark dark:border-[#222] bg-white dark:bg-[#0a0a0a] overflow-hidden">
          
          {/* Grid implementation */}
          <div className="absolute inset-0 grid-mesh opacity-20 pointer-events-none" />

          {/* SVG Data Layer */}
          <svg 
            className="absolute inset-0 w-full h-full" 
            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
            preserveAspectRatio="none"
          >
            {!isLoading && data.length > 0 && (
              <>
                {viewMode === 'L1' && (
                  <>
                    <path
                      d={generatePath('rawBackground')}
                      fill="none"
                      stroke="#888"
                      strokeWidth="1"
                      strokeDasharray="4 2"
                      opacity="0.4"
                    />
                    <path
                      d={generatePath('rawPlasma')}
                      fill="none"
                      stroke="#111"
                      strokeWidth="1.2"
                      className="dark:stroke-[#f0f0f0]"
                    />
                  </>
                )}
                {viewMode === 'L2' && (
                  <path
                    d={generatePath('intensity')}
                    fill="none"
                    stroke="#111"
                    strokeWidth="1.5"
                    className="dark:stroke-[#f0f0f0]"
                  />
                )}
              </>
            )}
          </svg>

          {/* Overlay for loading/empty */}
          {(isLoading || !data.length) && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/50 dark:bg-black/50 backdrop-blur-[1px]">
              {isLoading ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-5 h-5 border-2 border-[#111] dark:border-white border-t-transparent rounded-full animate-spin" />
                  <span className="text-[10px] font-bold tracking-[1px] uppercase text-[#111] dark:text-white">Processing L1/L2 Sequence</span>
                </div>
              ) : (
                <span className="text-[10px] font-bold tracking-[1px] uppercase text-gray-400">Select parameters to load spectra</span>
              )}
            </div>
          )}
        </div>
      </div>


      {/* X-axis tick labels */}
      <div className="border-t border-border-dark dark:border-[#222] flex items-center py-2 pl-12 pr-2 justify-between">
        {NM_TICKS.map((nm) => (
          <span key={nm} className="text-[9px] text-ink-muted dark:text-gray-400 tracking-[0.3px]">{nm}</span>
        ))}
        <span className="text-[10px] font-semibold text-[#999] dark:text-[#555] tracking-[1.5px] uppercase ml-2">nm</span>
      </div>
    </div>
  );
}
