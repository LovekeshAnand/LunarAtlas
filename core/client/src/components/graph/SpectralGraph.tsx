import { type SpectralData } from '../../services/mockDataService';

const NM_TICKS  = ['200', '300', '400', '500', '600', '700', '800', '900', '1000'];

/**
 * @fileoverview High-performance SVG-based spectral graph component.

 * Optimized for rendering 2,000+ data points without external library overhead.
 */

/**
 * Properties for the SpectralGraph component.
 */
interface SpectralGraphProps {
  /** Array of processed spectral data points */
  data: SpectralData[];
  /** Loading state flag */
  isLoading: boolean;
  /** Current display mode (L1 Raw or L2 Cleaned) */
  viewMode: 'L1' | 'L2';
  /** Discrete zoom multiplier (1x to 5x) controlled by the parent */
  zoom: number;
}

// SVG Viewbox dimensions (fixed aspect ratio)
const chartWidth  = 1000;
const chartHeight = 320;

/**
 * Renders a scientifically accurate spectral plot using SVG paths.
 * Implements centered-zoom logic by recalculating the visible wavelength range.
 */
export default function SpectralGraph({ data, isLoading, viewMode, zoom }: SpectralGraphProps) {

  /**
   * Generates an SVG Path string for a specific data series.
   * 
   * MATH:
   * 1. Define Absolute Mission Range (ABS_MIN to ABS_MAX).
   * 2. Calculate Viewport Range based on zoom: Range / Zoom.
   * 3. Center the Viewport around the middle of the spectrum.
   * 4. Map the physical wavelengths (nm) to local SVG coordinates (0 to 1000).
   * 
   * @param key The data key to plot (intensity, rawPlasma, or rawBackground)
   * @returns A valid SVG 'd' attribute string
   */
  const generatePath = (key: 'intensity' | 'rawPlasma' | 'rawBackground') => {
    if (!data.length) return '';
    
    // Mission instrument range parameters
    const ABS_MIN = 164.35;
    const ABS_MAX = 878.26;
    const ABS_CENTER = (ABS_MIN + ABS_MAX) / 2;
    const ABS_RANGE = ABS_MAX - ABS_MIN;

    // Viewport calculation: narrows the range as zoom increases
    const viewRange = ABS_RANGE / zoom;
    const minX = ABS_CENTER - (viewRange / 2);
    const maxX = ABS_CENTER + (viewRange / 2);

    const minY = 0;
    // L1 counts (raw) are magnitudes higher than L2 intensity (subtracted)
    const maxY = viewMode === 'L2' ? 1000 : 2500;

    const points = data
      .filter(d => d.wavelength >= minX && d.wavelength <= maxX) // Viewport clipping
      .map((d) => {
        // Horizontal mapping (wavelength -> x coordinate)
        const x = ((d.wavelength - minX) / (maxX - minX)) * chartWidth;
        // Vertical mapping (counts/intensity -> y coordinate)
        const val = d[key] as number;
        const y = chartHeight - ((val - minY) / (maxY - minY)) * chartHeight;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      });

    if (points.length < 2) return '';
    return `M ${points.join(' L ')}`;
  };

  return (
    <div className="font-sans mt-4 border border-border-dark dark:border-[#222] rounded-md bg-canvas-alt dark:bg-[#141414] overflow-hidden transition-colors duration-200">

      {/* Primary Plot Area */}
      <div className="relative h-[320px] flex">

        {/* Vertical Axis (Y) Label */}
        <div className="w-10 shrink-0 flex items-center justify-center">
          <span className="text-[10px] font-semibold text-[#999] dark:text-[#555] tracking-[1.5px] uppercase -rotate-90 whitespace-nowrap">
            {viewMode === 'L2' ? 'Cleaned Intensity' : 'Raw Counts'}
          </span>
        </div>

        {/* SVG Drawing Canvas */}
        <div className="flex-1 relative border-l border-border-dark dark:border-[#222] bg-white dark:bg-[#0a0a0a] overflow-hidden">
          
          {/* Scientific Grid (Subtle 40px default mesh) */}
          <div className="absolute inset-0 grid-mesh opacity-20 pointer-events-none" />

          <svg 
            className="absolute inset-0 w-full h-full" 
            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
            preserveAspectRatio="none"
          >
            {!isLoading && data.length > 0 && (
              <>
                {/* Level-1 Visualization: Composite showing background vs plasma */}
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
                {/* Level-2 Visualization: Single cleaned intensity stream */}
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

          {/* Loading and Selection Overlays */}
          {(isLoading || !data.length) && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/50 dark:bg-black/50 backdrop-blur-[1px]">
              {isLoading ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-5 h-5 border-2 border-[#111] dark:border-white border-t-transparent rounded-full animate-spin" />
                  <span className="text-[10px] font-bold tracking-[1px] uppercase text-[#111] dark:text-white">Executing Processing Pipeline</span>
                </div>
              ) : (
                <span className="text-[10px] font-bold tracking-[1px] uppercase text-gray-400">Select parameters to load spectra</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Horizontal Axis (X) Labels (Wavelength nm) */}
      <div className="border-t border-border-dark dark:border-[#222] flex items-center py-2 pl-12 pr-2 justify-between">
        {NM_TICKS.map((nm) => (
          <span key={nm} className="text-[9px] text-ink-muted dark:text-gray-400 tracking-[0.3px] font-mono">{nm}</span>
        ))}
        <span className="text-[10px] font-semibold text-[#999] dark:text-[#555] tracking-[1.5px] uppercase ml-2">nm</span>
      </div>
    </div>
  );
}

