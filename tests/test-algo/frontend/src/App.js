import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';
import axios from 'axios';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// ── element colour palette ────────────────────────────────────────────────────
const ELEMENT_COLORS = {
  Mg: '#34d399', Ca: '#f472b6', Al: '#a78bfa',
  Fe: '#fb923c', Si: '#38bdf8', O:  '#fbbf24',
  Ti: '#e879f9', Na: '#4ade80', K:  '#f87171',
  Mn: '#67e8f9', Cr: '#c084fc', H:  '#e2e8f0',
};
const elementColor = (el) => ELEMENT_COLORS[el] ?? '#94a3b8';

const fmt = (n, dec = 2) =>
  n == null ? '—' : Number(n).toLocaleString(undefined, { maximumFractionDigits: dec });

// ── same formula as backend Eq. 6 ────────────────────────────────────────────
function computeZmax(span) {
  const ratio = span / (1000 * 0.01); // BASE_BUCKETS=1000, MIN_BUCKET_SIZE=0.01
  if (ratio <= 1) return 0;
  return Math.floor(Math.log2(ratio));
}

/** Derive logical zoom level from visible vs full wavelength span. */
function spanToZoom(visibleSpan, fullSpan) {
  if (visibleSpan <= 0 || fullSpan <= 0) return 0;
  return Math.max(0, Math.min(10, Math.floor(Math.log2(fullSpan / visibleSpan))));
}

// ── sub-components ────────────────────────────────────────────────────────────

function StatusBadge({ mode, saturated, zmax, zoomLevel }) {
  if (mode === 'raw' || saturated) {
    return (
      <span className="badge badge-raw">
        ⚡ RAW MODE · zoom {zoomLevel} &gt; z<sub>max</sub> {zmax}
      </span>
    );
  }
  return (
    <span className="badge badge-ds">
      〰 DOWNSAMPLED · zoom {zoomLevel} / z<sub>max</sub> {zmax}
    </span>
  );
}

function StatCard({ label, value, unit, highlight }) {
  return (
    <div className={`stat-card ${highlight ? 'stat-highlight' : ''}`}>
      <span className="stat-label">{label}</span>
      <span className="stat-value">
        {value}{unit && <span className="stat-unit"> {unit}</span>}
      </span>
    </div>
  );
}

function ZoomBar({ zoom, zmax, maxZoom, onZoomIn, onZoomOut, onReset }) {
  const pct  = zmax > 0 ? Math.min((zoom / zmax) * 100, 100) : 100;
  const over = zoom > zmax;
  return (
    <div className="zoom-bar-wrap">
      <div className="zoom-track">
        <div className={`zoom-fill ${over ? 'zoom-fill-over' : ''}`} style={{ width: `${pct}%` }} />
        {zmax > 0 && (
          <div className="zmax-marker" style={{ left: `${(zmax / maxZoom) * 100}%` }}>
            <span className="zmax-label">z<sub>max</sub></span>
          </div>
        )}
      </div>
      <div className="zoom-controls">
        <button className="btn-icon" onClick={onZoomOut} disabled={zoom === 0}>−</button>
        <span className="zoom-value">{zoom}</span>
        <button className="btn-icon" onClick={onZoomIn} disabled={zoom === maxZoom}>+</button>
        <button className="btn-ghost" onClick={onReset}>↺ Reset</button>
      </div>
    </div>
  );
}

function ElementLegend({ visibleElements }) {
  if (!visibleElements.length) return null;
  return (
    <div className="el-legend">
      {visibleElements.map(el => (
        <span key={el} className="el-chip" style={{ '--ec': elementColor(el) }}>
          <span className="el-dot" />{el}
        </span>
      ))}
    </div>
  );
}

// ── main ──────────────────────────────────────────────────────────────────────
const ABS_MAX_ZOOM = 10;

export default function App() {
  // chart DOM + amCharts refs
  const chartRef      = useRef(null);
  const rootRef       = useRef(null);
  const chartObjRef   = useRef(null);
  const seriesRef     = useRef(null);
  const xAxisRef      = useRef(null);
  const yAxisRef      = useRef(null);
  const nistSeriesMap = useRef({});   // element -> ColumnSeries

  // state
  const [observations,    setObservations]    = useState([]);
  const [selectedObs,     setSelectedObs]     = useState(null);
  const [zoomLevel,       setZoomLevel]       = useState(0);
  const [wavelengthRange, setWavelengthRange] = useState({ min: 164, max: 964 });
  const [fullRange,       setFullRange]       = useState({ min: 164, max: 964 });
  const [loading,         setLoading]         = useState(false);
  const [error,           setError]           = useState(null);
  const [stats,           setStats]           = useState(null);
  const [showNist,        setShowNist]        = useState(true);
  const [nistPeaks,       setNistPeaks]       = useState([]);
  const [visibleElements, setVisibleElements] = useState([]);
  const [minConf,         setMinConf]         = useState(0.5);

  // debounce + dedup guards
  const viewportTimer = useRef(null);
  const fetchingRef   = useRef(false);
  const lastFetch     = useRef({ min: null, max: null, zoom: null, obs: null });
  const updatingData  = useRef(false);  // prevents feedback loop during data updates

  // keep latest state accessible inside amCharts callbacks without re-subscribing
  const liveRef = useRef({});
  useEffect(() => {
    liveRef.current = { selectedObs, fullRange, showNist, minConf, wavelengthRange, zoomLevel };
  }, [selectedObs, fullRange, showNist, minConf, wavelengthRange, zoomLevel]);

  // ── fetch observations ──────────────────────────────────────────────────────
  useEffect(() => {
    axios.get(`${API_BASE}/api/v1/observations`)
      .then(r => {
        const obs = r.data.observations;
        setObservations(obs);
        if (obs.length > 0) {
          const o = obs[0];
          const rng = { min: Math.floor(o.min_wavelength), max: Math.ceil(o.max_wavelength) };
          setSelectedObs(o.measurement_id);
          setWavelengthRange(rng);
          setFullRange(rng);
        }
      })
      .catch(() => setError('Could not reach API — is the backend running?'));
  }, []);

  // ── init amCharts (once) ────────────────────────────────────────────────────
  useEffect(() => {
    if (!chartRef.current) return;

    const root = am5.Root.new(chartRef.current);
    rootRef.current = root;
    root.setThemes([am5themes_Animated.new(root)]);

    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: true, panY: false,
        wheelY: 'zoomX', pinchZoomX: true,
        layout: root.verticalLayout,
      })
    );
    chartObjRef.current = chart;

    // X axis
    const xAxis = chart.xAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererX.new(root, { minGridDistance: 60 }),
        tooltip: am5.Tooltip.new(root, {}),
      })
    );
    xAxisRef.current = xAxis;
    xAxis.get('renderer').labels.template.setAll({ fill: am5.color(0x8899bb), fontSize: 11 });
    xAxis.get('renderer').grid.template.setAll({ stroke: am5.color(0x1e2d4a), strokeWidth: 1 });
    xAxis.children.moveValue(
      am5.Label.new(root, {
        text: 'Wavelength (nm)', fill: am5.color(0x5577aa), fontSize: 12,
        x: am5.p50, centerX: am5.p50,
      }),
      xAxis.children.length - 1
    );

    // Y axis
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, { renderer: am5xy.AxisRendererY.new(root, {}) })
    );
    yAxisRef.current = yAxis;
    yAxis.get('renderer').labels.template.setAll({ fill: am5.color(0x8899bb), fontSize: 11 });
    yAxis.get('renderer').grid.template.setAll({ stroke: am5.color(0x1e2d4a), strokeWidth: 1 });
    yAxis.children.moveValue(
      am5.Label.new(root, {
        rotation: -90, text: 'Intensity (a.u.)', fill: am5.color(0x5577aa), fontSize: 12,
        y: am5.p50, centerX: am5.p50,
      }),
      0
    );

    // Spectrum line series
    const series = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: 'Spectrum', xAxis, yAxis,
        valueYField: 'intensity', valueXField: 'wavelength',
        stroke: am5.color(0x38bdf8), strokeWidth: 1.5,
        tooltip: am5.Tooltip.new(root, {
          labelText: 'λ {valueX.formatNumber("#.##")} nm\nI {valueY.formatNumber("#,###")}',
          getFillFromSprite: false,
          background: am5.RoundedRectangle.new(root, {
            fill: am5.color(0x0a1628), stroke: am5.color(0x38bdf8), strokeWidth: 1,
            cornerRadiusTL: 6, cornerRadiusTR: 6, cornerRadiusBL: 6, cornerRadiusBR: 6,
          }),
        }),
      })
    );
    seriesRef.current = series;

    // Cursor
    const cursor = am5xy.XYCursor.new(root, { behavior: 'zoomX', lineY: { visible: false } });
    chart.set('cursor', cursor);
    cursor.lineX.setAll({ stroke: am5.color(0x38bdf8), strokeWidth: 1, strokeDasharray: [4, 4] });

    // Chart plot background
    chart.plotContainer.set('background', am5.Rectangle.new(root, {
      fill: am5.color(0x060e1f), fillOpacity: 1,
    }));
    chart.zoomOutButton.setAll({
      background: am5.RoundedRectangle.new(root, { fill: am5.color(0x1e3a5f) }),
    });

    // ── KEY: listen for viewport changes driven by scroll/pan/drag ──────────
    // selectionMin / selectionMax are the data-space values of the visible window
    xAxis.onPrivate('selectionMin', onViewportChange);
    xAxis.onPrivate('selectionMax', onViewportChange);

    return () => root.dispose();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── viewport change handler ─────────────────────────────────────────────────
  // Called by amCharts whenever the user scrolls/pans — computes the new
  // wavelength window and logical zoom level, then re-fetches.
  function onViewportChange() {
    // Ignore viewport changes triggered by data updates to prevent feedback loop
    if (updatingData.current) return;
    
    const xAxis = xAxisRef.current;
    if (!xAxis) return;

    const visMin = xAxis.getPrivate('selectionMin');
    const visMax = xAxis.getPrivate('selectionMax');
    if (visMin == null || visMax == null) return;

    const { fullRange: fr } = liveRef.current;
    const visSpan  = visMax - visMin;
    const fullSpan = fr.max - fr.min;
    if (visSpan <= 0 || fullSpan <= 0) return;

    const newZoom = spanToZoom(visSpan, fullSpan);
    const newMin  = Math.max(fr.min, Math.round(visMin * 100) / 100);
    const newMax  = Math.min(fr.max, Math.round(visMax * 100) / 100);

    // debounce: collapse rapid scroll events into one state update + fetch
    clearTimeout(viewportTimer.current);
    viewportTimer.current = setTimeout(() => {
      setZoomLevel(newZoom);
      setWavelengthRange({ min: newMin, max: newMax });
      // fetch is triggered by the useEffect below watching these two
    }, 150);
  }

  // ── fetch spectral data ─────────────────────────────────────────────────────
  const doFetchSpectral = useCallback(async (obsId, minWl, maxWl, zoom) => {
    if (!obsId || minWl >= maxWl) return;
    if (fetchingRef.current) return;

    // dedup identical consecutive requests
    const lf = lastFetch.current;
    if (lf.obs === obsId && lf.min === minWl && lf.max === maxWl && lf.zoom === zoom) return;
    lastFetch.current = { obs: obsId, min: minWl, max: maxWl, zoom };

    fetchingRef.current = true;
    setLoading(true);
    setError(null);

    try {
      const r = await axios.get(`${API_BASE}/api/v1/spectral`, {
        params: {
          observation_id: obsId,
          min_wavelength: minWl,
          max_wavelength: maxWl,
          zoom_level: zoom,
        },
      });

      const { buckets, parameters, metadata, processing_time_ms, mode } = r.data;

      const pts = [];
      buckets.forEach(b => {
        if (!b.data_present) return;
        pts.push({ wavelength: b.min_wavelength, intensity: b.min_intensity });
        if (b.min_wavelength !== b.max_wavelength)
          pts.push({ wavelength: b.max_wavelength, intensity: b.max_intensity });
      });
      pts.sort((a, b) => a.wavelength - b.wavelength);

      // Prevent viewport change handler from triggering during data update
      updatingData.current = true;
      seriesRef.current?.data.setAll(pts);
      
      // Re-enable viewport change handling after amCharts settles
      setTimeout(() => {
        updatingData.current = false;
      }, 200);

      setStats({
        mode, saturated: parameters.saturated,
        buckets: parameters.bucket_count,
        bucketSize: parameters.bucket_size_nm,
        dataPoints: pts.length,
        processingTime: processing_time_ms,
        zmax: metadata.zmax_for_window,
      });
    } catch (e) {
      const detail = e?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : e.message || 'Unknown error');
    } finally {
      setLoading(false);
      fetchingRef.current = false;
    }
  }, []);

  useEffect(() => {
    doFetchSpectral(selectedObs, wavelengthRange.min, wavelengthRange.max, zoomLevel);
  }, [selectedObs, wavelengthRange.min, wavelengthRange.max, zoomLevel, doFetchSpectral]);

  // ── fetch + render NIST peaks ───────────────────────────────────────────────
  const doFetchNist = useCallback(async (minWl, maxWl, conf, visible) => {
    if (!visible || minWl >= maxWl) {
      clearNistSeries();
      return;
    }
    try {
      const r = await axios.get(`${API_BASE}/api/v1/nist_peaks`, {
        params: { min_wavelength: minWl, max_wavelength: maxWl, min_confidence: conf },
      });
      const peaks = r.data.peaks ?? [];
      setNistPeaks(peaks);
      renderNistLines(peaks);
    } catch (_) {
      // NIST is non-critical — don't surface errors to the user
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    doFetchNist(wavelengthRange.min, wavelengthRange.max, minConf, showNist);
  }, [wavelengthRange.min, wavelengthRange.max, minConf, showNist, doFetchNist]);

  function clearNistSeries() {
    Object.values(nistSeriesMap.current).forEach(s => { try { s.dispose(); } catch (_) {} });
    nistSeriesMap.current = {};
    setVisibleElements([]);
    setNistPeaks([]);
  }

  function renderNistLines(peaks) {
    const root  = rootRef.current;
    const chart = chartObjRef.current;
    const xAxis = xAxisRef.current;
    const yAxis = yAxisRef.current;
    if (!root || !chart || !xAxis || !yAxis) return;

    // dispose previous NIST series
    clearNistSeries();

    // group by element
    const byEl = {};
    peaks.forEach(p => { (byEl[p.element] = byEl[p.element] ?? []).push(p); });

    const elements = Object.keys(byEl);
    setVisibleElements(elements);

    elements.forEach(el => {
      const color = am5.color(elementColor(el));

      // ColumnSeries renders vertical bars — we make them 1px wide = reference lines
      const s = chart.series.push(
        am5xy.ColumnSeries.new(root, {
          name: el, xAxis, yAxis,
          valueXField: 'wavelength',
          valueYField: 'lineHeight',
          openValueYField: 'zero',
          clustered: false,
          tooltip: am5.Tooltip.new(root, {
            labelText: `{element} {ionStage}\nλ {valueX.formatNumber("#.###")} nm\nconf {confidence.formatNumber("0.00")}`,
            getFillFromSprite: false,
            background: am5.RoundedRectangle.new(root, {
              fill: am5.color(0x0a1628), stroke: color, strokeWidth: 1,
              cornerRadiusTL: 6, cornerRadiusTR: 6, cornerRadiusBL: 6, cornerRadiusBR: 6,
            }),
          }),
        })
      );

      // 1 px wide lines; dashed appearance via strokeDasharray is not available on
      // columns, but setting width=1 + full fill opacity gives a clean line look
      s.columns.template.setAll({
        width: 1,
        strokeOpacity: 0,
        fill: color,
        fillOpacity: 0.75,
        tooltipY: 0,
      });

      // Use Y = confidence-weighted large value so lines span the plot height
      // The actual Y axis auto-scales to spectrum data, so we pick a very tall value
      // and let amCharts clip at the plot boundary.
      const data = byEl[el].map(p => ({
        wavelength: p.wavelength,
        lineHeight: 1e9,   // effectively "top of chart"
        zero: 0,
        element: el,
        ionStage: p.ion_stage ?? '',
        confidence: p.confidence ?? 0,
      }));

      s.data.setAll(data);
      nistSeriesMap.current[el] = s;
    });
  }

  // show/hide NIST series when toggle changes
  useEffect(() => {
    Object.values(nistSeriesMap.current).forEach(s => {
      try { showNist ? s.show() : s.hide(); } catch (_) {}
    });
  }, [showNist]);

  // ── manual controls ─────────────────────────────────────────────────────────
  const handleObsChange = (id) => {
    const obs = observations.find(o => o.measurement_id === id);
    setSelectedObs(id);
    if (obs) {
      const rng = { min: Math.floor(obs.min_wavelength), max: Math.ceil(obs.max_wavelength) };
      setWavelengthRange(rng);
      setFullRange(rng);
      setZoomLevel(0);
      xAxisRef.current?.zoom(0, 1);
    }
  };

  const handleReset = () => {
    const obs = observations.find(o => o.measurement_id === selectedObs);
    if (obs) {
      const rng = { min: Math.floor(obs.min_wavelength), max: Math.ceil(obs.max_wavelength) };
      setWavelengthRange(rng);
      setFullRange(rng);
      setZoomLevel(0);
      xAxisRef.current?.zoom(0, 1);
    }
  };

  const zmax = stats?.zmax ?? computeZmax(wavelengthRange.max - wavelengthRange.min);

  // ── render ──────────────────────────────────────────────────────────────────
  return (
    <div className="la-app">
      {/* starfield */}
      <div className="starfield" aria-hidden="true">
        {Array.from({ length: 60 }).map((_, i) => (
          <div key={i} className="star" style={{
            left: `${(i * 17.3 + 3) % 100}%`,
            top:  `${(i * 23.7 + 7) % 100}%`,
            animationDelay: `${(i * 0.23) % 4}s`,
            width: i % 7 === 0 ? '2px' : '1px',
            height: i % 7 === 0 ? '2px' : '1px',
            opacity: 0.2 + (i % 5) * 0.08,
          }} />
        ))}
      </div>

      {/* header */}
      <header className="la-header">
        <div className="la-logo">
          <span className="la-moon">☽</span>
          <div>
            <h1 className="la-title">LunarAtlas</h1>
            <p className="la-subtitle">Chandrayaan-3 · LIBS Spectral Explorer</p>
          </div>
        </div>
        {stats && (
          <StatusBadge
            mode={stats.mode} saturated={stats.saturated}
            zmax={stats.zmax} zoomLevel={zoomLevel}
          />
        )}
      </header>

      <main className="la-main">

        {/* sidebar */}
        <aside className="la-sidebar">

          <section className="la-panel">
            <h2 className="panel-title">Observation</h2>
            <select className="la-select" value={selectedObs || ''}
              onChange={e => handleObsChange(parseInt(e.target.value))}>
              {observations.map(o => (
                <option key={o.measurement_id} value={o.measurement_id}>
                  #{o.measurement_id} · {o.min_wavelength?.toFixed(0)}–{o.max_wavelength?.toFixed(0)} nm
                  · {o.point_count?.toLocaleString()} pts
                </option>
              ))}
            </select>
          </section>

          <section className="la-panel">
            <h2 className="panel-title">Wavelength Range</h2>
            <div className="range-row">
              <label>
                <span className="range-label">min</span>
                <input type="number" className="la-input" value={wavelengthRange.min} step={1}
                  onChange={e => setWavelengthRange(r => ({ ...r, min: parseFloat(e.target.value) }))} />
              </label>
              <span className="range-sep">→</span>
              <label>
                <span className="range-label">max</span>
                <input type="number" className="la-input" value={wavelengthRange.max} step={1}
                  onChange={e => setWavelengthRange(r => ({ ...r, max: parseFloat(e.target.value) }))} />
              </label>
              <span className="range-unit">nm</span>
            </div>
          </section>

          <section className="la-panel">
            <h2 className="panel-title">
              Zoom Level
              <span className={`zmax-chip ${zoomLevel > zmax ? 'zmax-chip-warn' : ''}`}>
                z<sub>max</sub> = {zmax}
              </span>
            </h2>
            <ZoomBar
              zoom={zoomLevel} zmax={zmax} maxZoom={ABS_MAX_ZOOM}
              onZoomIn={() => setZoomLevel(z => Math.min(z + 1, ABS_MAX_ZOOM))}
              onZoomOut={() => setZoomLevel(z => Math.max(z - 1, 0))}
              onReset={handleReset}
            />
            {stats?.saturated && (
              <p className="saturation-warn">
                ⚡ Beyond z<sub>max</sub> — switched to raw data mode automatically.
              </p>
            )}
          </section>

          {/* NIST controls */}
          <section className="la-panel">
            <h2 className="panel-title">
              NIST Peak Lines
              <label className="toggle-wrap">
                <input type="checkbox" checked={showNist}
                  onChange={e => setShowNist(e.target.checked)} />
                <span className="toggle-track"><span className="toggle-thumb" /></span>
              </label>
            </h2>

            {showNist && (
              <>
                <div className="conf-row">
                  <span className="range-label">Min confidence</span>
                  <input type="range" min="0" max="1" step="0.05"
                    value={minConf} onChange={e => setMinConf(parseFloat(e.target.value))}
                    className="conf-slider" />
                  <span className="conf-val">{minConf.toFixed(2)}</span>
                </div>
                <ElementLegend visibleElements={visibleElements} />
                {nistPeaks.length === 0
                  ? <p className="nist-empty">No NIST lines in this window at this confidence.</p>
                  : <p className="nist-count">{nistPeaks.length} reference line{nistPeaks.length !== 1 ? 's' : ''}</p>
                }
              </>
            )}
          </section>

          {/* stats */}
          {stats && (
            <section className="la-panel stats-grid">
              <StatCard label="Mode"        value={stats.mode.toUpperCase()} highlight={stats.saturated} />
              <StatCard label="Data Points"  value={fmt(stats.dataPoints, 0)} />
              <StatCard label="Bucket Size"  value={fmt(stats.bucketSize, 4)} unit="nm" />
              <StatCard label="Buckets"      value={fmt(stats.buckets, 0)} />
              <StatCard label="Response"     value={fmt(stats.processingTime)} unit="ms" />
              <StatCard label="z_max"        value={stats.zmax} />
            </section>
          )}

          {error && (
            <div className="la-error">
              <strong>⚠ Error</strong>
              <p>{error}</p>
            </div>
          )}

          <section className="la-panel la-info">
            <h2 className="panel-title">Controls</h2>
            <div className="shortcut-list">
              <kbd>Scroll</kbd> zoom · auto re-fetches
              <kbd>Drag</kbd> pan · auto re-fetches
              <kbd>±</kbd> manual zoom level
            </div>
            <p style={{ marginTop: 10, fontSize: '0.78rem', color: 'var(--text-dim)', lineHeight: 1.6 }}>
              Scroll or drag on the chart — the zoom level and wavelength
              range update automatically and new data is fetched from the backend.
              NIST lines are colour-coded per element with confidence filtering.
            </p>
          </section>

        </aside>

        {/* chart */}
        <div className="la-chart-wrap">
          {loading && (
            <div className="la-loading">
              <span className="spinner" />
              <span>Fetching spectral data…</span>
            </div>
          )}
          <div ref={chartRef} className="la-chart" />
        </div>

      </main>
    </div>
  );
}