/**
 * @fileoverview MultiSpectralGraph — Full-width overlapping multi-measurement renderer.
 *
 * LTTB + True Peak Guarantee:
 *   Each dataset is independently downsampled using the existing Web Worker
 *   (useDownsampling hook). The worker computes:
 *     P_final = LTTB(data) ∪ LocalMaxima(data)
 *   This guarantees 100% emission-line peak retention per the research paper.
 *
 * Zoom/Pan:
 *   Uses ref-based addEventListener with { passive: false } so e.preventDefault()
 *   works correctly (React's synthetic onWheel is passive by default).
 *
 * Hover isolation:
 *   Hovered/focused curve renders last (topmost z), all others fade to grey.
 */

import { useState, useRef, useMemo, useEffect, useCallback } from 'react';
import { type SpectralDataPoint } from '../../services/apiService';
import { type MeasurementInfo } from '../../services/apiService';
import { useDownsampling } from '../../hooks/useDownsampling';
import { ELEMENT_PEAKS, type ElementalPeak } from '../../utils/spectralUtils';

/* ------------------------------------------------------------------ */
/*  Color palette — muted, astronomy-inspired, no excessive glow       */
/* ------------------------------------------------------------------ */

const MEASUREMENT_COLORS = [
  '#38bdf8', // sky blue
  '#fb923c', // sunset orange
  '#4ade80', // spectral green
  '#c084fc', // nebula violet
  '#facc15', // solar yellow
  '#2dd4bf', // teal
  '#f87171', // red
  '#818cf8', // indigo
  '#fb7185', // rose
  '#a3e635', // lime
  '#60a5fa', // cornflower blue
  '#34d399', // emerald
  '#f472b6', // pink
];

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface SpectralDataset {
  id: string;
  label: string;
  color: string;
  data: SpectralDataPoint[];
  meta?: MeasurementInfo;
}

interface MultiSpectralGraphProps {
  datasets: SpectralDataset[];
  isLoading: boolean;
  lambdaMin: number;
  lambdaMax: number;
  proportion: number;
  onRangeChange?: (min: number, max: number) => void;
  focusedId?: string | null;
  onFocusChange?: (id: string | null) => void;
  targetWavelengths?: number[];
  selectedElement?: string;
}

/* ------------------------------------------------------------------ */
/*  Builder helper                                                     */
/* ------------------------------------------------------------------ */

export function buildDatasets(
  measurementData: Map<string, SpectralDataPoint[]>,
  measurements: MeasurementInfo[]
): SpectralDataset[] {
  return Array.from(measurementData.entries()).map(([id, data]) => {
    const meta = measurements.find((m) => m.measurement_id === id);
    const idx = measurements.findIndex((m) => m.measurement_id === id);
    const stableIdx = idx >= 0 ? idx : 0;
    return {
      id,
      label: meta ? `Measurement #${meta.measurement_index}` : `ID`,
      color: MEASUREMENT_COLORS[stableIdx % MEASUREMENT_COLORS.length],
      data,
      meta,
    };
  });
}

/* ------------------------------------------------------------------ */
/*  Single-dataset lane — applies LTTB independently per measurement  */
/* ------------------------------------------------------------------ */

interface DatasetLaneProps {
  dataset: SpectralDataset;
  proportion: number;
  minX: number;
  domainX: number;
  domainMinY: number;
  domainRangeY: number;
  chartWidth: number;
  chartHeight: number;
  isActive: boolean;
  isInactive: boolean;
  targetWavelengths?: number[];
}

function DatasetLane({
  dataset,
  proportion,
  minX,
  domainX,
  domainMinY,
  domainRangeY,
  chartWidth,
  chartHeight,
  isActive,
  isInactive,
  targetWavelengths,
}: DatasetLaneProps) {
  // LTTB + peak guarantee via Web Worker for THIS dataset independently
  const { data: lttbData } = useDownsampling(dataset.data, proportion, targetWavelengths);

  const visible = useMemo(
    () => lttbData.filter((p) => p.wavelength >= minX && p.wavelength <= minX + domainX),
    [lttbData, minX, domainX]
  );

  const linePath = useMemo(() => {
    if (visible.length < 2) return '';
    const pts = visible.map((p) => {
      const x = ((p.wavelength - minX) / domainX) * chartWidth;
      const y = chartHeight - ((p.intensity - domainMinY) / domainRangeY) * chartHeight;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    });
    return `M ${pts.join(' L ')}`;
  }, [visible, minX, domainX, domainMinY, domainRangeY, chartWidth, chartHeight]);

  const areaPath = useMemo(() => {
    if (visible.length < 2) return '';
    const pts = visible.map((p) => {
      const x = ((p.wavelength - minX) / domainX) * chartWidth;
      const y = chartHeight - ((p.intensity - domainMinY) / domainRangeY) * chartHeight;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    });
    const firstX = ((visible[0].wavelength - minX) / domainX) * chartWidth;
    const lastX = ((visible[visible.length - 1].wavelength - minX) / domainX) * chartWidth;
    return `M ${pts.join(' L ')} L ${lastX.toFixed(2)},${chartHeight} L ${firstX.toFixed(2)},${chartHeight} Z`;
  }, [visible, minX, domainX, domainMinY, domainRangeY, chartWidth, chartHeight]);

  const stroke = isInactive ? '#9ca3af' : dataset.color;
  const strokeWidth = isActive ? 2.0 : isInactive ? 0.7 : 1.3;
  const opacity = isInactive ? 0.18 : isActive ? 1.0 : 0.75;

  return (
    <g style={{ transition: 'opacity 200ms ease' }}>
      {!isInactive && (
        <path
          d={areaPath}
          fill={`url(#areaGrad-${dataset.id})`}
          opacity={isActive ? 0.6 : 0.3}
        />
      )}
      <path
        d={linePath}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinejoin="round"
        opacity={opacity}
        style={{ transition: 'stroke 200ms, stroke-width 150ms, opacity 200ms' }}
      />
    </g>
  );
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

const CHART_W = 1200;
const CHART_H = 400;
const ABS_MIN = 164.35;
const ABS_MAX = 878.26;

export default function MultiSpectralGraph({
  datasets,
  isLoading,
  lambdaMin,
  lambdaMax,
  proportion,
  onRangeChange,
  focusedId,
  onFocusChange,
  targetWavelengths,
  selectedElement,
}: MultiSpectralGraphProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [hiddenIds, setHiddenIds] = useState<Set<string>>(new Set());
  const [hoveredPoint, setHoveredPoint] = useState<{ wavelength: number; intensity: number; id: string } | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [hoveredPeak, setHoveredPeak] = useState<ElementalPeak | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);
  const lastMouseX = useRef(0);

  const minX = Math.min(lambdaMin, lambdaMax);
  const maxX = Math.max(lambdaMin, lambdaMax);
  const domainX = Math.max(maxX - minX, 0.01);

  const activeId = focusedId ?? hoveredId;

  /* ── Global Y domain across all visible datasets (raw data for scale) ── */
  const { domainMinY, domainMaxY } = useMemo(() => {
    let gMin = Infinity, gMax = -Infinity;
    for (const ds of datasets) {
      if (hiddenIds.has(ds.id)) continue;
      for (const p of ds.data) {
        if (p.wavelength < minX || p.wavelength > maxX) continue;
        if (p.intensity < gMin) gMin = p.intensity;
        if (p.intensity > gMax) gMax = p.intensity;
      }
    }
    if (!isFinite(gMin)) { gMin = 0; gMax = 1; }
    const range = gMax - gMin;
    const pad = range > 0 ? range * 0.12 : 10;
    return { domainMinY: gMin - pad, domainMaxY: gMax + pad };
  }, [datasets, hiddenIds, minX, maxX]);

  const domainRangeY = Math.max(domainMaxY - domainMinY, 1);

  /* ── Wheel zoom — MUST use passive:false addEventListener, not React onWheel ── */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      if (!onRangeChange) return;
      const factor = 1 + (e.deltaY > 0 ? 1 : -1) * 0.10;
      const rect = el.getBoundingClientRect();
      const pct = (e.clientX - rect.left) / rect.width;
      const anchor = minX + pct * domainX;
      const newDomain = Math.max(0.5, domainX * factor);
      let nMin = anchor - pct * newDomain;
      let nMax = nMin + newDomain;
      if (nMin < ABS_MIN) { nMin = ABS_MIN; nMax = Math.min(ABS_MAX, nMin + newDomain); }
      if (nMax > ABS_MAX) { nMax = ABS_MAX; nMin = Math.max(ABS_MIN, nMax - newDomain); }
      onRangeChange(nMin, nMax);
    };

    el.addEventListener('wheel', handleWheel, { passive: false });
    return () => el.removeEventListener('wheel', handleWheel);
  }, [onRangeChange, minX, domainX]);

  /* ── Drag pan ── */
  const handleMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true;
    lastMouseX.current = e.clientX;
  };

  const handleMouseMoveGlobal = useCallback((e: MouseEvent) => {
    if (!isDragging.current || !onRangeChange) return;
    const dx = e.clientX - lastMouseX.current;
    if (Math.abs(dx) < 1) return;
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    lastMouseX.current = e.clientX;
    const shift = (dx / rect.width) * domainX;
    let nMin = minX - shift, nMax = maxX - shift;
    if (nMin < ABS_MIN) { nMin = ABS_MIN; nMax = ABS_MIN + domainX; }
    if (nMax > ABS_MAX) { nMax = ABS_MAX; nMin = ABS_MAX - domainX; }
    onRangeChange(nMin, nMax);
  }, [onRangeChange, minX, maxX, domainX]);

  useEffect(() => {
    const up = () => { isDragging.current = false; };
    window.addEventListener('mousemove', handleMouseMoveGlobal);
    window.addEventListener('mouseup', up);
    return () => {
      window.removeEventListener('mousemove', handleMouseMoveGlobal);
      window.removeEventListener('mouseup', up);
    };
  }, [handleMouseMoveGlobal]);

  /* ── Hover: find nearest dataset curve ── */
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    let bestDist = Infinity;
    let bestPoint: typeof hoveredPoint = null;
    let bestId: string | null = null;

    for (const ds of datasets) {
      if (hiddenIds.has(ds.id)) continue;
      for (const p of ds.data) {
        if (p.wavelength < minX || p.wavelength > maxX) continue;
        const px = ((p.wavelength - minX) / domainX) * rect.width;
        const py = (1 - (p.intensity - domainMinY) / domainRangeY) * rect.height;
        const dist = Math.hypot(px - mx, py - my);
        if (dist < bestDist) {
          bestDist = dist;
          bestPoint = { wavelength: p.wavelength, intensity: p.intensity, id: ds.id };
          bestId = ds.id;
        }
      }
    }

    if (bestDist < 45) {
      setHoveredId(bestId);
      setHoveredPoint(bestPoint);
    } else {
      setHoveredId(null);
      setHoveredPoint(null);
    }
    setMousePos({ x: mx, y: my });
  };

  const toggleVisibility = (id: string) => {
    setHiddenIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  /* ── X ticks ── */
  const xTicks = Array.from({ length: 7 }, (_, i) => minX + (domainX * i) / 6);

  /* ── Render order: active last = topmost ── */
  const orderedDatasets = useMemo(() => {
    if (!activeId) return datasets;
    return [
      ...datasets.filter((d) => d.id !== activeId),
      ...datasets.filter((d) => d.id === activeId),
    ];
  }, [datasets, activeId]);

  const loadedCount = datasets.filter((d) => d.data.length > 0).length;
  const totalPoints = datasets.reduce((s, d) => s + d.data.length, 0);

  return (
    <div className="w-full flex flex-col bg-white border border-solid border-gray-200 rounded-lg shadow-sm overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3.5 border-b border-solid border-gray-100 bg-gray-50/70">
        <div className="flex items-center gap-3">
          <span className="text-[13px] font-sans font-bold text-gray-700">
            Overlapping Spectral View
          </span>
          <span className="text-[11px] font-sans text-gray-400 px-2 py-0.5 bg-white border border-solid border-gray-200 rounded-full">
            {loadedCount} measurement{loadedCount !== 1 ? 's' : ''} · {totalPoints.toLocaleString()} pts (raw)
          </span>
          {/* LTTB badge */}
          <span className="text-[10px] font-sans font-bold text-emerald-700 px-2 py-0.5 bg-emerald-50 border border-solid border-emerald-200 rounded-full uppercase tracking-wide">
            LTTB + Peak Guarantee ✓
          </span>
        </div>
        <div className="text-[11px] font-sans text-gray-400">
          Scroll to Zoom · Drag to Pan · Hover to Isolate
        </div>
      </div>

      {/* Legend chips */}
      {datasets.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap px-6 py-2.5 border-b border-solid border-gray-100 bg-white">
          {datasets.map((ds) => {
            const hidden = hiddenIds.has(ds.id);
            const isActive = activeId === ds.id;
            return (
              <button
                key={ds.id}
                onClick={() => {
                  toggleVisibility(ds.id);
                  if (onFocusChange) onFocusChange(isActive ? null : null);
                }}
                onMouseEnter={() => !focusedId && setHoveredId(ds.id)}
                onMouseLeave={() => !focusedId && setHoveredId(null)}
                style={{
                  borderColor: hidden ? '#e5e7eb' : ds.color,
                  color: hidden ? '#9ca3af' : '#374151',
                  background: hidden ? '#f9fafb' : isActive ? ds.color + '20' : ds.color + '12',
                }}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-sans font-semibold
                           border border-solid transition-all duration-150 cursor-pointer select-none"
              >
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: hidden ? '#d1d5db' : ds.color }} />
                {ds.label}
                {ds.meta?.laser_energy_v && (
                  <span className="opacity-50 font-normal text-[10px]">· {ds.meta.laser_energy_v}V</span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Chart area */}
      <div className="relative flex" style={{ height: '440px' }}>

        {/* Y-axis label */}
        <div className="w-10 shrink-0 flex items-center justify-center border-r border-solid border-gray-100 bg-gray-50/40">
          <span className="text-[10px] font-sans font-medium text-gray-400 tracking-widest uppercase -rotate-90 whitespace-nowrap">
            Intensity (cts)
          </span>
        </div>

        {/* SVG container */}
        <div
          ref={containerRef}
          className="flex-1 relative cursor-crosshair overflow-hidden"
          style={{ height: '440px' }}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => { setHoveredId(null); setHoveredPoint(null); }}
          onMouseDown={handleMouseDown}
        >
          {/* Subtle grid */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage:
                'linear-gradient(to right, #f1f5f9 1px, transparent 1px), linear-gradient(to bottom, #f1f5f9 1px, transparent 1px)',
              backgroundSize: '100px 66px',
            }}
          />

          <svg
            className="absolute inset-0 w-full h-full"
            viewBox={`0 0 ${CHART_W} ${CHART_H}`}
            preserveAspectRatio="none"
          >
            <defs>
              {datasets.map((ds) => (
                <linearGradient key={ds.id} id={`areaGrad-${ds.id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={ds.color} stopOpacity="0.22" />
                  <stop offset="100%" stopColor={ds.color} stopOpacity="0" />
                </linearGradient>
              ))}
            </defs>

            {/* Render each dataset through its own LTTB lane */}
            {!isLoading && orderedDatasets.map((ds) => {
              if (hiddenIds.has(ds.id)) return null;
              const isActive = activeId === ds.id;
              const isInactive = activeId !== null && !isActive;
              return (
                <DatasetLane
                  key={ds.id}
                  dataset={ds}
                  proportion={proportion}
                  minX={minX}
                  domainX={domainX}
                  domainMinY={domainMinY}
                  domainRangeY={domainRangeY}
                  chartWidth={CHART_W}
                  chartHeight={CHART_H}
                  isActive={isActive}
                  isInactive={isInactive}
                  targetWavelengths={targetWavelengths}
                />
              );
            })}

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
                    const x = ((peak.wavelength - minX) / domainX) * CHART_W;
                    if (x < 0 || x > CHART_W) return null;
                    return (
                      <line
                        key={`bg-${el}-${idx}`}
                        x1={x} y1={0} x2={x} y2={CHART_H}
                        stroke="#d1d5db" strokeWidth="0.5" strokeDasharray="6,6"
                        opacity="0.3"
                      />
                    );
                  });
                }

                const color = ELEMENT_COLORS[el] || '#6b7280';

                return peaks.map((peak, idx) => {
                  const x = ((peak.wavelength - minX) / domainX) * CHART_W;
                  if (x < 0 || x > CHART_W) return null;

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
                        x1={x} y1={0} x2={x} y2={CHART_H}
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

            {/* Hover crosshair + dot (no glow filter) */}
            {hoveredPoint && (() => {
              const ds = datasets.find((d) => d.id === hoveredPoint.id);
              if (!ds) return null;
              const px = ((hoveredPoint.wavelength - minX) / domainX) * CHART_W;
              const py = CHART_H - ((hoveredPoint.intensity - domainMinY) / domainRangeY) * CHART_H;
              return (
                <>
                  <line x1={px} y1={0} x2={px} y2={CHART_H}
                    stroke={ds.color} strokeWidth="1" strokeDasharray="4,3" opacity="0.6" />
                  <circle cx={px} cy={py} r="5" fill={ds.color} stroke="white" strokeWidth="2" />
                </>
              );
            })()}
          </svg>

          {/* Hover tooltip */}
          {hoveredPoint && (() => {
            const ds = datasets.find((d) => d.id === hoveredPoint.id);
            if (!ds) return null;
            const left = Math.min(mousePos.x + 14, (containerRef.current?.clientWidth ?? 400) - 190);
            const top = Math.max(mousePos.y - 85, 8);
            return (
              <div
                className="absolute pointer-events-none z-50 bg-white p-3 rounded-lg shadow-lg border border-solid border-gray-200"
                style={{ left, top, minWidth: '175px' }}
              >
                <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-gray-100">
                  <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: ds.color }} />
                  <span className="text-[11px] font-sans font-bold text-gray-800">{ds.label}</span>
                </div>
                <div className="flex flex-col gap-1 text-[12px] font-sans">
                  <div className="flex justify-between gap-4">
                    <span className="text-gray-400">λ</span>
                    <span className="font-semibold text-gray-900">{hoveredPoint.wavelength.toFixed(3)} nm</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-gray-400">Intensity</span>
                    <span className="font-semibold" style={{ color: ds.color }}>
                      {hoveredPoint.intensity.toFixed(1)} cts
                    </span>
                  </div>
                  {ds.meta?.laser_energy_v && (
                    <div className="flex justify-between gap-4">
                      <span className="text-gray-400">Energy</span>
                      <span className="font-semibold text-gray-600">{ds.meta.laser_energy_v} V</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })()}

          {/* Loading spinner */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/70 backdrop-blur-sm">
              <div className="flex flex-col items-center gap-3">
                <div className="w-7 h-7 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                <span className="text-[12px] font-sans text-gray-500">Loading measurements…</span>
              </div>
            </div>
          )}

          {!isLoading && datasets.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-4xl mb-3 opacity-20">🔭</div>
                <div className="text-[13px] font-sans text-gray-400">Select an observation to load all measurements</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* X-axis */}
      <div className="flex items-center justify-between px-12 py-2 bg-gray-50/60 border-t border-solid border-gray-100">
        {xTicks.map((t) => (
          <span key={t} className="text-[11px] font-sans font-medium text-gray-500">{t.toFixed(1)}</span>
        ))}
        <span className="text-[11px] font-sans text-gray-400">nm</span>
      </div>

      {/* Footer */}
      <div className="px-6 py-2.5 flex items-center justify-between border-t border-solid border-gray-100 bg-white text-[11px] font-sans text-gray-500">
        <div className="flex items-center gap-4">
          <span>λ range: <strong className="text-gray-700">{minX.toFixed(2)}–{maxX.toFixed(2)} nm</strong></span>
          <span>Span: <strong className="text-gray-700">{domainX.toFixed(2)} nm</strong></span>
        </div>
        <div className="flex items-center gap-3">
          {activeId && (
            <span
              className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide"
              style={{
                background: (datasets.find(d => d.id === activeId)?.color ?? '#888') + '18',
                color: datasets.find(d => d.id === activeId)?.color ?? '#888',
              }}
            >
              Isolating: {datasets.find(d => d.id === activeId)?.label}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
