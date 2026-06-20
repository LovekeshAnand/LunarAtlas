/**
 * @fileoverview SpectralGraph — High-performance SVG spectral line renderer.
 *
 * Renders Chandrayaan-3 LIBS spectral data as an interactive SVG chart
 * with support for three view modes:
 *   - L2: Background-subtracted cleaned intensity
 *   - L1: Raw plasma / background counts
 *   - overlay: Both L1 and L2 rendered simultaneously for comparison
 *
 * Interaction features:
 *   - Mouse-wheel zoom anchored to cursor position
 *   - Click-and-drag pan across the wavelength axis
 *   - Hover crosshair with nearest-point snapping
 *   - NIST elemental peak overlay with hover labels
 *   - Adaptive point-marker rendering at high zoom levels
 *
 * @see {@link ../../services/apiService.ts} for SpectralDataPoint shape
 * @see {@link ../../utils/spectralUtils.ts} for ELEMENT_PEAKS reference data
 */

import { useState, useRef, useMemo, useEffect } from 'react';
import { type SpectralDataPoint } from '../../services/apiService';
import { ELEMENT_PEAKS } from '../../utils/spectralUtils';

/* ------------------------------------------------------------------ */
/*  Component props                                                    */
/* ------------------------------------------------------------------ */

interface SpectralGraphProps {
  /** Array of spectral data points to render. */
  data: SpectralDataPoint[];
  /** Whether the parent is still fetching data. */
  isLoading: boolean;
  /** Active view mode: L2 cleaned, L1 raw, or overlay (both). */
  viewMode: 'L1' | 'L2' | 'overlay';
  /** Current downsampling proportion (0–1). */
  proportion: number;
  /** Current viewport minimum wavelength in nm. */
  lambdaMin: number;
  /** Current viewport maximum wavelength in nm. */
  lambdaMax: number;
  /** Currently selected element for peak highlighting (e.g. "Fe"). */
  selectedElement?: string;
  /** Callback invoked when the user zooms or pans the viewport. */
  onRangeChange?: (min: number, max: number) => void;
}

/* ------------------------------------------------------------------ */
/*  Constants                                                          */
/* ------------------------------------------------------------------ */

/** Internal SVG coordinate system width. */
const chartWidth = 1000;
/** Internal SVG coordinate system height. */
const chartHeight = 320;
/** Absolute minimum wavelength boundary (Chandrayaan-3 LIBS). */
const ABS_MIN = 164.35;
/** Absolute maximum wavelength boundary (Chandrayaan-3 LIBS). */
const ABS_MAX = 878.26;

/**
 * Formats a numeric wavelength tick for axis display.
 * @param value - Wavelength in nm
 * @returns Formatted string with one decimal place
 */
const formatTick = (value: number) => value.toFixed(1);

/* ------------------------------------------------------------------ */
/*  SpectralGraph component                                            */
/* ------------------------------------------------------------------ */

export default function SpectralGraph({
  data,
  isLoading,
  viewMode,
  lambdaMin,
  lambdaMax,
  onRangeChange,
  selectedElement = '',
}: SpectralGraphProps) {
  /* ── Local state ── */
  const [hoveredPoint, setHoveredPoint] = useState<SpectralDataPoint | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);
  const lastMouseX = useRef(0);

  /* ── Derived domain values ── */
  const minX = Math.min(lambdaMin, lambdaMax);
  const maxX = Math.max(lambdaMin, lambdaMax);
  const domainX = Math.max(maxX - minX, 0.01);

  /* ================================================================ */
  /*  Interaction handlers                                             */
  /* ================================================================ */

  /**
   * Handles mouse-wheel zoom. The zoom is anchored to the cursor's
   * wavelength position so the point under the mouse stays fixed.
   */
  const handleWheel = (e: React.WheelEvent) => {
    if (!onRangeChange) return;
    e.preventDefault();
    const zoomSpeed = 0.12;
    const direction = e.deltaY > 0 ? 1 : -1;
    const factor = 1 + direction * zoomSpeed;

    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const mouseX = e.clientX - rect.left;
    const mousePct = mouseX / rect.width;
    const mouseWavelength = minX + mousePct * domainX;

    const targetDomain = Math.max(0.1, domainX * factor);
    let nMin = mouseWavelength - mousePct * targetDomain;
    let nMax = nMin + targetDomain;

    /* Boundary clamping — keep the viewport within instrument range */
    if (nMin < ABS_MIN) {
      nMin = ABS_MIN;
      nMax = Math.min(ABS_MAX, nMin + targetDomain);
    } else if (nMax > ABS_MAX) {
      nMax = ABS_MAX;
      nMin = Math.max(ABS_MIN, nMax - targetDomain);
    }

    onRangeChange(nMin, nMax);
  };

  /**
   * Initiates a click-and-drag pan operation.
   */
  const handleMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true;
    lastMouseX.current = e.clientX;
  };

  /**
   * Processes mouse movement during a drag pan, translating pixel
   * delta into wavelength shift and clamping to boundaries.
   */
  const handleMouseMoveGlobal = (e: MouseEvent) => {
    if (!isDragging.current || !onRangeChange) return;
    const dx = e.clientX - lastMouseX.current;
    if (Math.abs(dx) < 1) return;
    
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    lastMouseX.current = e.clientX;
    const wavelengthShift = (dx / rect.width) * domainX;
    
    let nMin = minX - wavelengthShift;
    let nMax = maxX - wavelengthShift;

    if (nMin < ABS_MIN) {
      nMin = ABS_MIN;
      nMax = ABS_MIN + domainX;
    } else if (nMax > ABS_MAX) {
      nMax = ABS_MAX;
      nMin = ABS_MAX - domainX;
    }

    onRangeChange(nMin, nMax);
  };

  /** Ends the drag pan operation. */
  const handleMouseUpGlobal = () => {
    isDragging.current = false;
  };

  /* Register and clean up global mouse listeners for drag panning */
  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMoveGlobal);
    window.addEventListener('mouseup', handleMouseUpGlobal);
    return () => {
      window.removeEventListener('mousemove', handleMouseMoveGlobal);
      window.removeEventListener('mouseup', handleMouseUpGlobal);
    };
  }, [minX, maxX, domainX]);

  /* ================================================================ */
  /*  Data processing + memoized computations                          */
  /* ================================================================ */

  /** Filter data to only points within the current viewport. */
  const visibleData = useMemo(() => 
    data.filter(p => p.wavelength >= minX && p.wavelength <= maxX),
    [data, minX, maxX]
  );

  /** Compute the Y-axis domain from visible data points. */
  const allYValues = useMemo(() => {
    if (viewMode === 'overlay') {
      return visibleData.flatMap((point) => [point.intensity, point.rawPlasma]);
    }
    return visibleData.flatMap((point) =>
      viewMode === 'L2' ? [point.intensity] : [point.rawPlasma, point.rawBackground]
    );
  }, [visibleData, viewMode]);

  const rawMinY = allYValues.length ? Math.min(...allYValues) : 0;
  const rawMaxY = allYValues.length ? Math.max(...allYValues) : 1;
  const rangeY = rawMaxY - rawMinY;
  const paddingY = rangeY > 0 ? rangeY * 0.15 : 10;
  
  const domainMinY = rawMinY - paddingY;
  const domainMaxY = rawMaxY + paddingY;
  const domainRangeY = Math.max(domainMaxY - domainMinY, 1);

  /** Generate evenly-spaced X-axis tick positions. */
  const xTicks = Array.from({ length: 6 }, (_, i) => minX + (domainX * i) / 5);

  /**
   * Returns the Y value for a data point based on current view mode.
   */
  const getYValue = (p: SpectralDataPoint) => {
    if (viewMode === 'L2') return p.intensity;
    return p.rawPlasma; 
  };

  /**
   * Converts a data point to SVG canvas coordinates.
   */
  const getCanvasPos = (p: { wavelength: number; intensity: number } | SpectralDataPoint) => {
    const x = ((p.wavelength - minX) / domainX) * chartWidth;
    const val = 'intensity' in p ? p.intensity : getYValue(p as SpectralDataPoint);
    const y = chartHeight - ((val - domainMinY) / domainRangeY) * chartHeight;
    return { x, y };
  };

  /**
   * Generates an SVG path string for a given data key.
   * @param _key - Which intensity field to map
   * @param close - Whether to close the path for area fill
   */
  const generatePath = (_key: 'intensity' | 'rawPlasma' | 'rawBackground', close = false) => {
    if (visibleData.length < 2) return '';
    const getter = (p: SpectralDataPoint) => {
      if (_key === 'intensity') return p.intensity;
      if (_key === 'rawPlasma') return p.rawPlasma;
      return p.rawBackground;
    };
    const points = visibleData.map((p) => {
      const x = ((p.wavelength - minX) / domainX) * chartWidth;
      const val = getter(p);
      const y = chartHeight - ((val - domainMinY) / domainRangeY) * chartHeight;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    });
    let d = `M ${points.join(' L ')}`;
    if (close) {
      const lastX = ((visibleData[visibleData.length - 1].wavelength - minX) / domainX) * chartWidth;
      const firstX = ((visibleData[0].wavelength - minX) / domainX) * chartWidth;
      d += ` L ${lastX},${chartHeight} L ${firstX},${chartHeight} Z`;
    }
    return d;
  };

  /**
   * Hover handler: finds the nearest data point to the cursor
   * using a linear scan (fast for downsampled datasets).
   */
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!containerRef.current || visibleData.length === 0) return;
    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    const svgX = (mouseX / rect.width) * chartWidth;
    const targetWavelength = minX + (svgX / chartWidth) * domainX;
    
    let closest = visibleData[0];
    let minDiff = Math.abs(closest.wavelength - targetWavelength);

    for (const p of visibleData) {
      const diff = Math.abs(p.wavelength - targetWavelength);
      if (diff < minDiff) {
        minDiff = diff;
        closest = p;
      }
    }

    setHoveredPoint(closest);
    setMousePos({ x: mouseX, y: mouseY });
  };

  /** Clears the hover state when the mouse leaves the chart area. */
  const clearHover = () => setHoveredPoint(null);

  const yAxisLabel = viewMode === 'L2' ? 'Intensity (cts)' : viewMode === 'overlay' ? 'Intensity' : 'Raw Counts';
  /** Show individual point markers only when zoomed in enough. */
  const showMarkers = domainX < 5 && visibleData.length < 500;

  /** Hover state for NIST elemental peak overlays. */
  const [hoveredPeak, setHoveredPeak] = useState<any | null>(null);

  /* ================================================================ */
  /*  Render                                                           */
  /* ================================================================ */

  return (
    <div className="mt-4 border border-solid border-gray-200 rounded-md bg-white overflow-hidden shadow-sm select-none relative">
      <div className="relative h-[320px] flex">
        {/* ── Y-axis label ── */}
        <div className="w-10 shrink-0 flex items-center justify-center bg-gray-50 border-r border-solid border-gray-200">
          <span className="text-[11px] font-sans font-medium text-gray-500 tracking-widest uppercase -rotate-90 whitespace-nowrap">
            {yAxisLabel}
          </span>
        </div>

        {/* ── Chart area ── */}
        <div 
          ref={containerRef}
          className="flex-1 relative bg-transparent cursor-crosshair overflow-hidden"
          onMouseMove={handleMouseMove}
          onMouseLeave={clearHover}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
        >
          <div className="absolute inset-0 grid-mesh opacity-10 pointer-events-none" />

          <svg
            className="absolute inset-0 w-full h-full"
            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
              </linearGradient>
              <linearGradient id="areaGradientL1" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.10" />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
              <filter id="peakGlow">
                <feGaussianBlur stdDeviation="4" result="blur"/>
                <feMerge>
                  <feMergeNode in="blur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>

            {!isLoading && visibleData.length > 0 && (
              <>
                {/* ── Area gradient fills ── */}
                {(viewMode === 'L2' || viewMode === 'overlay') && (
                  <path d={generatePath('intensity', true)} fill="url(#areaGradient)" />
                )}
                {viewMode === 'overlay' && (
                  <path d={generatePath('rawPlasma', true)} fill="url(#areaGradientL1)" />
                )}

                {/* ── Spectral lines ── */}
                {viewMode === 'L1' && (
                  <>
                    <path d={generatePath('rawBackground')} fill="none" stroke="#9ca3af" strokeWidth="0.8" strokeDasharray="4,4" opacity="0.6" />
                    <path d={generatePath('rawPlasma')} fill="none" stroke="#1f2937" strokeWidth="1" strokeLinejoin="round" />
                  </>
                )}
                {viewMode === 'L2' && (
                  <path d={generatePath('intensity')} fill="none" stroke="#2563eb" strokeWidth="1.2" strokeLinejoin="round" />
                )}
                {viewMode === 'overlay' && (
                  <>
                    {/* L2 Cleaned — blue (rendered first, behind) */}
                    <path d={generatePath('intensity')} fill="none" stroke="#2563eb" strokeWidth="1" strokeLinejoin="round" opacity="0.85" />
                    {/* L1 Raw Plasma — amber (rendered second, on top) */}
                    <path d={generatePath('rawPlasma')} fill="none" stroke="#d97706" strokeWidth="1" strokeLinejoin="round" opacity="0.85" />
                  </>
                )}

                {/* ── NIST elemental peak overlays ── */}
                {(() => {
                  /** Per-element color palette for visual distinction */
                  const ELEMENT_COLORS: Record<string, string> = {
                    'Fe': '#ef4444', 'Mg': '#22c55e', 'Si': '#8b5cf6',
                    'Al': '#f97316', 'Ca': '#06b6d4', 'Ti': '#ec4899',
                    'Na': '#eab308', 'H₂O': '#14b8a6', 'O': '#6366f1',
                  };

                  const showAll = selectedElement === 'All';
                  let labelSlot = 0; // stagger labels vertically to prevent overlap

                  return Object.entries(ELEMENT_PEAKS).map(([el, peaks]) => {
                    const isActive = showAll || selectedElement === el;
                    if (!isActive && !showAll) {
                      // Still render faintly for context when nothing selected
                      return peaks.map((peak, idx) => {
                        const x = ((peak.wavelength - minX) / domainX) * chartWidth;
                        if (x < 0 || x > chartWidth) return null;
                        return (
                          <line
                            key={`bg-${el}-${idx}`}
                            x1={x} y1={0} x2={x} y2={chartHeight}
                            stroke="#d1d5db" strokeWidth="0.5" strokeDasharray="6,6"
                            opacity="0.3"
                          />
                        );
                      });
                    }

                    const color = ELEMENT_COLORS[el] || '#6b7280';

                    return peaks.map((peak, idx) => {
                      const x = ((peak.wavelength - minX) / domainX) * chartWidth;
                      if (x < 0 || x > chartWidth) return null;

                      const isHovered = hoveredPeak === peak;
                      const currentSlot = labelSlot++;
                      const labelY = 18 + (currentSlot % 10) * 22;
                      const lineOpacity = isHovered ? 1.0 : 0.65;
                      const labelText = `${el} ${peak.label}  ${peak.wavelength}`;

                      return (
                        <g
                          key={`${el}-${peak.label}-${idx}`}
                          className="cursor-pointer"
                          onMouseEnter={() => setHoveredPeak(peak)}
                          onMouseLeave={() => setHoveredPeak(null)}
                        >
                          {/* Solid vertical reference line */}
                          <line
                            x1={x} y1={0} x2={x} y2={chartHeight}
                            stroke={color}
                            strokeWidth={isHovered ? 2 : 1.2}
                            opacity={lineOpacity}
                          />

                          {/* Label pill */}
                          <rect
                            x={x + 5} y={labelY - 8}
                            width={labelText.length * 5.5 + 10} height={16}
                            rx="3" fill={color}
                            opacity={isHovered ? 0.95 : 0.75}
                          />
                          <text
                            x={x + 10} y={labelY + 3}
                            fill="white"
                            fontSize="8" fontWeight="600"
                            className="font-sans pointer-events-none select-none"
                          >
                            {labelText}
                          </text>
                        </g>
                      );
                    });
                  });
                })()}

                {/* ── Individual data point markers (high zoom) ── */}
                {showMarkers && visibleData.map((p, i) => {
                  const { x, y } = getCanvasPos(p);
                  return (
                    <circle key={i} cx={x} cy={y} r="2" fill="#3b82f6" stroke="white" strokeWidth="0.5" />
                  );
                })}
                
                {/* ── Hover crosshair + point highlight ── */}
                {hoveredPoint && (
                  <>
                    <line 
                      x1={getCanvasPos(hoveredPoint).x} y1={0} 
                      x2={getCanvasPos(hoveredPoint).x} y2={chartHeight} 
                      stroke="#6b7280" strokeWidth="1" strokeDasharray="2,2"
                    />
                    <circle 
                      cx={getCanvasPos(hoveredPoint).x} cy={getCanvasPos(hoveredPoint).y} 
                      r="6" fill="#3b82f6" stroke="white" strokeWidth="2" 
                      filter="url(#peakGlow)"
                    />
                  </>
                )}
              </>
            )}
          </svg>

          {/* ── Hover tooltip ── */}
          {hoveredPoint && (
            <div 
              className="absolute pointer-events-none z-50 bg-white p-3 rounded-md shadow-lg border border-solid border-gray-200 text-gray-800"
              style={{ 
                left: Math.min(mousePos.x + 15, containerRef.current?.clientWidth! - 160),
                top: Math.max(mousePos.y - 80, 10)
              }}
            >
              <div className="border-b border-solid border-gray-200 pb-1 mb-2 font-sans font-semibold text-gray-700 text-[11px]">
                Spectral Data Point
              </div>
              <div className="flex flex-col gap-1 font-sans text-[12px]">
                <div className="flex justify-between gap-4">
                  <span className="text-gray-500 font-medium">Wavelength (λ):</span>
                  <span className="font-semibold text-gray-900">{hoveredPoint.wavelength.toFixed(3)} nm</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-gray-500 font-medium">Intensity (I):</span>
                  <span className="font-semibold text-blue-600">{getYValue(hoveredPoint).toFixed(2)} cts</span>
                </div>
                {viewMode === 'overlay' && (
                  <div className="flex justify-between gap-4">
                    <span className="text-gray-500 font-medium">Raw Plasma:</span>
                    <span className="font-semibold text-amber-600">{hoveredPoint.rawPlasma.toFixed(2)} cts</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── Loading spinner ── */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/40 backdrop-blur-[2px]">
              <div className="flex flex-col items-center gap-2">
                <div className="w-5 h-5 border-2 border-gray-800 border-t-transparent rounded-full animate-spin" />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── X-axis tick labels ── */}
      <div className="border-t border-solid border-gray-200 flex items-center py-2 px-12 justify-between bg-gray-50">
        {xTicks.map((tick) => (
          <span key={tick} className="text-[12px] font-sans font-medium text-gray-600">
            {formatTick(tick)}
          </span>
        ))}
        <span className="text-[12px] font-sans font-medium text-gray-500 ml-2">nm</span>
      </div>

      {/* ── Footer status bar ── */}
      <div className="border-t border-solid border-gray-200 px-4 py-3 flex items-center justify-between text-[12px] font-sans text-gray-600 bg-white">
        <div className="flex gap-4">
          <span>Min: <strong className="text-gray-800">{rawMinY.toFixed(1)}</strong></span>
          <span>Max: <strong className="text-blue-600">{rawMaxY.toFixed(1)}</strong></span>
        </div>
        <div className="flex gap-4 items-center">
           {selectedElement && (
             <span className="text-red-500 font-sans font-semibold text-[12px]">
               Target: {selectedElement}
             </span>
           )}
           {viewMode === 'overlay' && (
            <div className="flex items-center gap-3 border-l border-gray-200 pl-3 ml-1">
              <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-blue-600 inline-block rounded" /> L1-Processed</span>
              <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-amber-500 inline-block rounded" /> L1-Raw</span>
            </div>
           )}
           <span className="font-semibold text-gray-800 text-[11px]">Pts: {visibleData.length}</span>
           <span className="text-gray-400 text-[11px]">(Scroll to Zoom · Drag to Pan)</span>
        </div>
      </div>
    </div>
  );
}
