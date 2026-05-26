/**
 * @fileoverview MiniSpectralCard — Individual per-Measurement-ID graph card.
 *
 * Renders a larger, clearly readable single-measurement sparkline card.
 * Also applies LTTB + peak guarantee via useDownsampling independently.
 *
 * Layout: 2 cards per row (lg: 3 per row), each card ~200px tall graph area.
 * Click to focus that curve in the main overlapping graph.
 */

import { useMemo } from 'react';
import { type SpectralDataset } from './MultiSpectralGraph';
import { useDownsampling } from '../../hooks/useDownsampling';

interface MiniSpectralCardProps {
  dataset: SpectralDataset;
  lambdaMin: number;
  lambdaMax: number;
  proportion: number;
  isFocused: boolean;
  onFocus: (id: string | null) => void;
  targetWavelengths?: number[];
}

const MINI_W = 600;
const MINI_H = 160;

export default function MiniSpectralCard({
  dataset,
  lambdaMin,
  lambdaMax,
  proportion,
  isFocused,
  onFocus,
  targetWavelengths,
}: MiniSpectralCardProps) {
  const { id, label, color, data, meta } = dataset;

  // Independent LTTB + peak guarantee for this card
  const { data: lttbData, metrics } = useDownsampling(data, proportion, targetWavelengths);

  const minX = Math.min(lambdaMin, lambdaMax);
  const maxX = Math.max(lambdaMin, lambdaMax);
  const domainX = Math.max(maxX - minX, 0.01);

  const visible = useMemo(
    () => lttbData.filter((p) => p.wavelength >= minX && p.wavelength <= maxX),
    [lttbData, minX, maxX]
  );

  /* ── Stats from raw data (pre-LTTB, for accuracy) ── */
  const stats = useMemo(() => {
    const src = data.filter((p) => p.wavelength >= minX && p.wavelength <= maxX);
    if (src.length === 0) return { min: 0, max: 0, peakWl: 0, pointCount: 0 };
    let min = Infinity, max = -Infinity, peakWl = 0;
    for (const p of src) {
      if (p.intensity < min) min = p.intensity;
      if (p.intensity > max) { max = p.intensity; peakWl = p.wavelength; }
    }
    return { min, max, peakWl, pointCount: src.length };
  }, [data, minX, maxX]);

  /* ── SVG paths from LTTB-downsampled data ── */
  const { linePath, areaPath, domainMinY, domainRangeY } = useMemo(() => {
    if (visible.length < 2) return { linePath: '', areaPath: '', domainMinY: 0, domainRangeY: 1 };
    const ys = visible.map((p) => p.intensity);
    const rawMin = Math.min(...ys);
    const rawMax = Math.max(...ys);
    const range = rawMax - rawMin;
    const pad = range > 0 ? range * 0.1 : 5;
    const dMinY = rawMin - pad;
    const dRangeY = Math.max(rawMax + pad - dMinY, 1);

    const pts = visible.map((p) => {
      const x = ((p.wavelength - minX) / domainX) * MINI_W;
      const y = MINI_H - ((p.intensity - dMinY) / dRangeY) * MINI_H;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    const firstX = ((visible[0].wavelength - minX) / domainX) * MINI_W;
    const lastX = ((visible[visible.length - 1].wavelength - minX) / domainX) * MINI_W;
    const line = `M ${pts.join(' L ')}`;
    const area = `${line} L ${lastX.toFixed(1)},${MINI_H} L ${firstX.toFixed(1)},${MINI_H} Z`;
    return { linePath: line, areaPath: area, domainMinY: dMinY, domainRangeY: dRangeY };
  }, [visible, minX, domainX]);

  /* ── Peak dot position ── */
  const peakDot = useMemo(() => {
    if (!stats.peakWl || visible.length < 2) return null;
    const closest = visible.reduce((best, p) =>
      Math.abs(p.wavelength - stats.peakWl) < Math.abs(best.wavelength - stats.peakWl) ? p : best
    );
    const x = ((closest.wavelength - minX) / domainX) * MINI_W;
    const y = MINI_H - ((closest.intensity - domainMinY) / domainRangeY) * MINI_H;
    return { x, y };
  }, [stats, visible, minX, domainX, domainMinY, domainRangeY]);

  /* ── X axis ticks (3 ticks) ── */
  const xTicks = [minX, minX + domainX / 2, maxX];

  const handleClick = () => onFocus(isFocused ? null : id);

  return (
    <div
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
      className="flex flex-col rounded-lg cursor-pointer select-none transition-all duration-200 overflow-hidden"
      style={{
        border: `2px solid ${isFocused ? color : '#e5e7eb'}`,
        background: isFocused ? color + '0a' : 'white',
        boxShadow: isFocused
          ? `0 0 0 3px ${color}25, 0 4px 12px rgba(0,0,0,0.08)`
          : '0 1px 3px rgba(0,0,0,0.06)',
        transform: isFocused ? 'translateY(-2px)' : 'none',
      }}
    >
      {/* Card header */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{ borderBottom: `1px solid ${isFocused ? color + '25' : '#f3f4f6'}` }}
      >
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full shrink-0" style={{ background: color }} />
          <span className="text-[13px] font-sans font-bold text-gray-800">{label}</span>
          {meta?.measurement_type && (
            <span className="text-[10px] font-sans text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded uppercase tracking-wide">
              {meta.measurement_type}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isFocused && (
            <span
              className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full"
              style={{ background: color + '20', color }}
            >
              Focused
            </span>
          )}
          <span className="text-[10px] font-sans text-gray-400">
            {metrics.finalPoints > 0 ? `${metrics.finalPoints} pts` : ''}
          </span>
        </div>
      </div>

      {/* LTTB badge row */}
      <div className="flex items-center gap-2 px-4 py-1.5 bg-gray-50/50"
        style={{ borderBottom: `1px solid ${isFocused ? color + '18' : '#f3f4f6'}` }}
      >
        <span className="text-[9px] font-sans font-bold text-emerald-600 bg-emerald-50 border border-solid border-emerald-100 px-1.5 py-0.5 rounded uppercase tracking-widest">
          LTTB ✓
        </span>
        <span className="text-[9px] font-sans font-bold text-blue-600 bg-blue-50 border border-solid border-blue-100 px-1.5 py-0.5 rounded uppercase tracking-widest">
          Peak Guarantee ✓
        </span>
        {metrics.executionTimeMs > 0 && (
          <span className="text-[9px] font-sans text-gray-400 ml-auto">
            {metrics.executionTimeMs.toFixed(1)}ms
          </span>
        )}
      </div>

      {/* Graph area — taller, clearly readable */}
      <div className="px-3 pt-3 pb-1 bg-white">
        {visible.length < 2 ? (
          <div className="flex items-center justify-center text-[11px] text-gray-400 italic"
            style={{ height: `${MINI_H}px` }}>
            No data in wavelength range
          </div>
        ) : (
          <svg
            viewBox={`0 0 ${MINI_W} ${MINI_H}`}
            preserveAspectRatio="none"
            className="w-full block"
            style={{ height: `${MINI_H}px` }}
          >
            <defs>
              <linearGradient id={`miniGrad-${id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity="0.28" />
                <stop offset="100%" stopColor={color} stopOpacity="0.02" />
              </linearGradient>
            </defs>
            <path d={areaPath} fill={`url(#miniGrad-${id})`} />
            <path
              d={linePath}
              fill="none"
              stroke={color}
              strokeWidth="1.8"
              strokeLinejoin="round"
            />
            {/* Peak marker dot */}
            {peakDot && (
              <>
                <line
                  x1={peakDot.x} y1={0} x2={peakDot.x} y2={MINI_H}
                  stroke={color} strokeWidth="0.8" strokeDasharray="3,3" opacity="0.5"
                />
                <circle cx={peakDot.x} cy={peakDot.y} r="5" fill={color} stroke="white" strokeWidth="2" />
              </>
            )}
          </svg>
        )}
      </div>

      {/* X axis ticks */}
      <div className="flex items-center justify-between px-3 pb-1">
        {xTicks.map((t) => (
          <span key={t} className="text-[9px] font-sans text-gray-400">{t.toFixed(1)}</span>
        ))}
        <span className="text-[9px] font-sans text-gray-400">nm</span>
      </div>

      {/* Stats footer — 3 columns */}
      <div
        className="px-4 py-3 grid grid-cols-3 gap-2 border-t border-solid"
        style={{ borderColor: isFocused ? color + '20' : '#f3f4f6' }}
      >
        <div className="flex flex-col gap-0.5">
          <span className="text-[9px] font-sans uppercase tracking-widest text-gray-400 font-medium">Peak λ</span>
          <span className="text-[12px] font-sans font-bold text-gray-800">
            {stats.peakWl ? `${stats.peakWl.toFixed(2)} nm` : '—'}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-[9px] font-sans uppercase tracking-widest text-gray-400 font-medium">Max I</span>
          <span className="text-[12px] font-sans font-bold" style={{ color }}>
            {stats.max > 0 ? `${stats.max.toFixed(0)} cts` : '—'}
          </span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-[9px] font-sans uppercase tracking-widest text-gray-400 font-medium">
            {meta?.laser_energy_v ? 'Energy' : 'Raw Pts'}
          </span>
          <span className="text-[12px] font-sans font-bold text-gray-700">
            {meta?.laser_energy_v ? `${meta.laser_energy_v} V` : `${stats.pointCount}`}
          </span>
        </div>
      </div>
    </div>
  );
}
