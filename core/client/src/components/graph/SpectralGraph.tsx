import { useState, useRef, useMemo, useEffect } from 'react';
import { type SpectralDataPoint } from '../../services/apiService';
import { ELEMENT_PEAKS } from '../../utils/spectralUtils';

interface SpectralGraphProps {
  data: SpectralDataPoint[];
  isLoading: boolean;
  viewMode: 'L1' | 'L2';
  proportion: number;
  lambdaMin: number;
  lambdaMax: number;
  selectedElement?: string;
  onRangeChange?: (min: number, max: number) => void;
}

const chartWidth = 1000;
const chartHeight = 320;
const ABS_MIN = 164.35;
const ABS_MAX = 878.26;

const formatTick = (value: number) => value.toFixed(1);

export default function SpectralGraph({
  data,
  isLoading,
  viewMode,
  lambdaMin,
  lambdaMax,
  onRangeChange,
  selectedElement = '',
}: SpectralGraphProps) {
  const [hoveredPoint, setHoveredPoint] = useState<SpectralDataPoint | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);
  const lastMouseX = useRef(0);

  const minX = Math.min(lambdaMin, lambdaMax);
  const maxX = Math.max(lambdaMin, lambdaMax);
  const domainX = Math.max(maxX - minX, 0.01);

  // --- Interaction Handlers ---

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

    // Proportional boundary correction to stay anchored to mouse center
    if (nMin < ABS_MIN) {
      nMin = ABS_MIN;
      nMax = Math.min(ABS_MAX, nMin + targetDomain);
    } else if (nMax > ABS_MAX) {
      nMax = ABS_MAX;
      nMin = Math.max(ABS_MIN, nMax - targetDomain);
    }

    onRangeChange(nMin, nMax);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true;
    lastMouseX.current = e.clientX;
  };

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

    // Clamp but allow pushing against the wall
    if (nMin < ABS_MIN) {
      nMin = ABS_MIN;
      nMax = ABS_MIN + domainX;
    } else if (nMax > ABS_MAX) {
      nMax = ABS_MAX;
      nMin = ABS_MAX - domainX;
    }

    onRangeChange(nMin, nMax);
  };

  const handleMouseUpGlobal = () => {
    isDragging.current = false;
  };

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMoveGlobal);
    window.addEventListener('mouseup', handleMouseUpGlobal);
    return () => {
      window.removeEventListener('mousemove', handleMouseMoveGlobal);
      window.removeEventListener('mouseup', handleMouseUpGlobal);
    };
  }, [minX, maxX, domainX]);

  // --- Data Processors ---

  const visibleData = useMemo(() => 
    data.filter(p => p.wavelength >= minX && p.wavelength <= maxX),
    [data, minX, maxX]
  );



  const allYValues = useMemo(() => {
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

  const xTicks = Array.from({ length: 6 }, (_, i) => minX + (domainX * i) / 5);

  const getYValue = (p: SpectralDataPoint) => {
    if (viewMode === 'L2') return p.intensity;
    return p.rawPlasma; 
  };

  const getCanvasPos = (p: { wavelength: number; intensity: number } | SpectralDataPoint) => {
    const x = ((p.wavelength - minX) / domainX) * chartWidth;
    const val = 'intensity' in p ? p.intensity : getYValue(p as SpectralDataPoint);
    const y = chartHeight - ((val - domainMinY) / domainRangeY) * chartHeight;
    return { x, y };
  };

  const generatePath = (_key: 'intensity' | 'rawPlasma' | 'rawBackground', close = false) => {
    if (visibleData.length < 2) return '';
    const points = visibleData.map((p) => {
      const { x, y } = getCanvasPos(p);
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

  const clearHover = () => setHoveredPoint(null);

  const yAxisLabel = viewMode === 'L2' ? 'Intensity (cts)' : 'Raw Counts';
  // Reduced density threshold for point markers
  const showMarkers = domainX < 5 && visibleData.length < 500;

  // Hover state for any peak line
  const [hoveredPeak, setHoveredPeak] = useState<any | null>(null);

  return (
    <div className="mt-4 border-2 border-dashed border-gray-400 rounded bg-white overflow-hidden shadow-lg select-none relative">
      <div className="absolute top-0 right-0 w-8 h-8 border-l-2 border-b-2 border-dashed border-gray-400 bg-gray-50 pointer-events-none" style={{ transform: 'rotate(10deg) translate(5px, -5px)' }}></div>
      <div className="relative h-[320px] flex">
        <div className="w-10 shrink-0 flex items-center justify-center bg-gray-50 border-r-2 border-dashed border-gray-300">
          <span className="text-[11px] font-caveat font-bold text-gray-500 tracking-widest uppercase -rotate-90 whitespace-nowrap">
            {yAxisLabel}
          </span>
        </div>

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
              <filter id="glow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>

            {!isLoading && visibleData.length > 0 && (
              <>
                {/* Visual Area Gradient */}
                {viewMode === 'L2' && (
                  <path d={generatePath('intensity', true)} fill="url(#areaGradient)" />
                )}

                {/* Spectral Lines (Rendered before peaks) */}
                {viewMode === 'L1' && (
                  <>
                    <path d={generatePath('rawBackground')} fill="none" stroke="#9ca3af" strokeWidth="1" strokeDasharray="4,4" opacity="0.6" />
                    <path d={generatePath('rawPlasma')} fill="none" stroke="#1f2937" strokeWidth="1.5" strokeLinejoin="round" />
                  </>
                )}
                {viewMode === 'L2' && (
                  <path d={generatePath('intensity')} fill="none" stroke="#2563eb" strokeWidth="2" strokeLinejoin="round" style={{ filter: 'drop-shadow(1px 2px 2px rgba(37,99,235,0.2))' }} />
                )}

                {/* ALL ELEMENTAL PEAKS OVERLAY */}
                {Object.entries(ELEMENT_PEAKS).map(([el, peaks]) => {
                  const isActive = selectedElement === el;
                  return peaks.map((peak, idx) => {
                    const x = ((peak.wavelength - minX) / domainX) * chartWidth;
                    if (x < 0 || x > chartWidth) return null;
                    
                    const isHovered = hoveredPeak === peak;
                    const opacity = isHovered ? 1 : (isActive ? 0.6 : 0.15);
                    const strokeWidth = isHovered || isActive ? 1.5 : 1;

                    return (
                      <g 
                        key={`${el}-${peak.label}-${idx}`} 
                        className="cursor-pointer transition-opacity duration-200"
                        onMouseEnter={() => setHoveredPeak(peak)}
                        onMouseLeave={() => setHoveredPeak(null)}
                      >
                        <line 
                          x1={x} y1={0} x2={x} y2={chartHeight} 
                          stroke={isActive ? "#ff3333" : "#999"} 
                          strokeWidth={strokeWidth} 
                          strokeDasharray={isActive ? "none" : "4,4"} 
                          opacity={opacity}
                        />
                        {(isHovered || isActive) && (
                          <text 
                            x={x + 5} y={30 + (idx % 6) * 15} 
                            fill={isActive ? "#ff3333" : "#666"} 
                            fontSize="9" fontWeight="black" 
                            className="font-mono pointer-events-none uppercase tracking-tighter"
                          >
                            {el} {peak.label} ({peak.wavelength}nm)
                          </text>
                        )}
                      </g>
                    );
                  });
                })}

                {/* Individual Data Points */}
                {showMarkers && visibleData.map((p, i) => {
                  const { x, y } = getCanvasPos(p);
                  return (
                    <circle key={i} cx={x} cy={y} r="2" fill="#3b82f6" stroke="white" strokeWidth="0.5" />
                  );
                })}
                
                {/* Crosshair / Tooltip Marker */}
                {hoveredPoint && (
                  <>
                    <line 
                      x1={getCanvasPos(hoveredPoint).x} y1={0} 
                      x2={getCanvasPos(hoveredPoint).x} y2={chartHeight} 
                      stroke="#111" strokeWidth="1" strokeDasharray="2,2" className="dark:stroke-gray-600"
                    />
                    <circle 
                      cx={getCanvasPos(hoveredPoint).x} cy={getCanvasPos(hoveredPoint).y} 
                      r="5" fill="#3b82f6" stroke="white" strokeWidth="2" className="shadow-lg"
                    />
                  </>
                )}
              </>
            )}
          </svg>

          {/* ... Tooltip div remains same ... */}
          {hoveredPoint && (
            <div 
              className="absolute pointer-events-none z-50 sticky-note p-3 text-gray-800 shadow-xl border-t-[8px] border-t-yellow-400 rotate-1"
              style={{ 
                left: Math.min(mousePos.x + 15, containerRef.current?.clientWidth! - 140),
                top: Math.max(mousePos.y - 75, 10)
              }}
            >
              <div className="border-b-2 border-dashed border-gray-400 pb-1 mb-2 font-marker text-blue-700 text-[11px]">
                Spectral Data Snapshot
              </div>
              <div className="flex flex-col gap-1 font-caveat text-[12px]">
                <div className="flex justify-between gap-4">
                  <span className="text-gray-600 font-bold">Wavelength (λ):</span>
                  <span className="font-bold text-red-600">{hoveredPoint.wavelength.toFixed(3)} nm</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span className="text-gray-600 font-bold">Intensity (I):</span>
                  <span className="font-bold text-blue-700">{getYValue(hoveredPoint).toFixed(2)} cts</span>
                </div>
              </div>
            </div>
          )}

          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/40 dark:bg-black/40 backdrop-blur-[2px]">
              <div className="flex flex-col items-center gap-2">
                <div className="w-5 h-5 border-2 border-[#111] dark:border-white border-t-transparent rounded-full animate-spin" />
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="border-t-2 border-dashed border-gray-300 flex items-center py-2 px-12 justify-between bg-gray-50">
        {xTicks.map((tick) => (
          <span key={tick} className="text-[12px] font-caveat font-bold text-gray-600">
            {formatTick(tick)}
          </span>
        ))}
        <span className="text-[12px] font-marker font-bold text-gray-500 ml-2">nm</span>
      </div>

      <div className="border-t-2 border-dashed border-gray-300 px-4 py-3 flex items-center justify-between text-[12px] font-caveat text-gray-600 bg-white">
        <div className="flex gap-4">
          <span>Min: <strong className="text-red-500">{rawMinY.toFixed(1)}</strong></span>
          <span>Max: <strong className="text-blue-600">{rawMaxY.toFixed(1)}</strong></span>
        </div>
        <div className="flex gap-4 items-center">
           {selectedElement && (
             <span className="text-red-600 font-marker text-[13px] animate-pulse -rotate-2">
               Target Base: {selectedElement}
             </span>
           )}
           <span className="font-bold text-gray-800 text-[11px]">Total Pts: {visibleData.length}</span>
           <span className="text-gray-400 text-[11px]">(Scroll to Zoom • Drag to Pan)</span>
        </div>
      </div>
    </div>
  );
}
