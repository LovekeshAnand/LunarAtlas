import React, { useEffect, useRef, useState } from 'react';
import * as am5 from '@amcharts/amcharts5';
import * as am5xy from '@amcharts/amcharts5/xy';
import am5themes_Animated from '@amcharts/amcharts5/themes/Animated';
import axios from 'axios';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const chartRef = useRef(null);
  const [observations, setObservations] = useState([]);
  const [selectedObs, setSelectedObs] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(0);
  const [wavelengthRange, setWavelengthRange] = useState({ min: 164, max: 964 });
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  
  // AmCharts instances
  const rootRef = useRef(null);
  const chartInstanceRef = useRef(null);
  const seriesRef = useRef(null);

  // Fetch available observations on mount
  useEffect(() => {
    fetchObservations();
  }, []);

  const fetchObservations = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/v1/observations`);
      setObservations(response.data.observations);
      if (response.data.observations.length > 0) {
        const firstObs = response.data.observations[0];
        setSelectedObs(firstObs.measurement_id);
        setWavelengthRange({
          min: Math.floor(firstObs.min_wavelength),
          max: Math.ceil(firstObs.max_wavelength)
        });
      }
    } catch (error) {
      console.error('Error fetching observations:', error);
    }
  };

  // Initialize AmCharts
  useEffect(() => {
    if (!chartRef.current) return;

    // Create root
    const root = am5.Root.new(chartRef.current);
    rootRef.current = root;

    // Set themes
    root.setThemes([am5themes_Animated.new(root)]);

    // Create chart
    const chart = root.container.children.push(
      am5xy.XYChart.new(root, {
        panX: true,
        panY: false,
        wheelY: 'zoomX',
        pinchZoomX: true,
        layout: root.verticalLayout
      })
    );
    chartInstanceRef.current = chart;

    // Create X-axis
    const xAxis = chart.xAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererX.new(root, {
          minGridDistance: 50
        }),
        tooltip: am5.Tooltip.new(root, {})
      })
    );
    xAxis.children.moveValue(
      am5.Label.new(root, {
        text: 'Wavelength (nm)',
        x: am5.p50,
        centerX: am5.p50
      }),
      xAxis.children.length - 1
    );

    // Create Y-axis
    const yAxis = chart.yAxes.push(
      am5xy.ValueAxis.new(root, {
        renderer: am5xy.AxisRendererY.new(root, {})
      })
    );
    yAxis.children.moveValue(
      am5.Label.new(root, {
        rotation: -90,
        text: 'Intensity (counts)',
        y: am5.p50,
        centerX: am5.p50
      }),
      0
    );

    // Create series
    const series = chart.series.push(
      am5xy.LineSeries.new(root, {
        name: 'Spectral Data',
        xAxis: xAxis,
        yAxis: yAxis,
        valueYField: 'intensity',
        valueXField: 'wavelength',
        stroke: am5.color(0x0066cc),
        strokeWidth: 1,
        tooltip: am5.Tooltip.new(root, {
          labelText: 'λ: {valueX.formatNumber("#.##")} nm\nI: {valueY.formatNumber("#,###")}'
        })
      })
    );
    seriesRef.current = series;

    // Add cursor
    chart.set('cursor', am5xy.XYCursor.new(root, {
      behavior: 'zoomX'
    }));

    // Add zoom out button
    chart.zoomOutButton.set('forceHidden', false);

    // Cleanup
    return () => {
      root.dispose();
    };
  }, []);

  // Fetch and update data when parameters change
  useEffect(() => {
    if (selectedObs && seriesRef.current) {
      fetchSpectralData();
    }
  }, [selectedObs, zoomLevel, wavelengthRange]);

  const fetchSpectralData = async () => {
    if (!selectedObs) return;

    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/api/v1/spectral`, {
        params: {
          observation_id: selectedObs,
          min_wavelength: wavelengthRange.min,
          max_wavelength: wavelengthRange.max,
          zoom_level: zoomLevel
        }
      });

      const { buckets, metadata, parameters, processing_time_ms } = response.data;
      
      // Convert buckets to data points for AmCharts
      const dataPoints = [];
      buckets.forEach(bucket => {
        if (bucket.data_present) {
          // Add min point
          dataPoints.push({
            wavelength: bucket.min_wavelength,
            intensity: bucket.min_intensity
          });
          // Add max point
          dataPoints.push({
            wavelength: bucket.max_wavelength,
            intensity: bucket.max_intensity
          });
        }
      });

      // Sort by wavelength
      dataPoints.sort((a, b) => a.wavelength - b.wavelength);

      // Update series data
      seriesRef.current.data.setAll(dataPoints);

      // Update stats
      setStats({
        buckets: parameters.bucket_count,
        bucketSize: parameters.bucket_size_nm.toFixed(4),
        dataPoints: dataPoints.length,
        processingTime: processing_time_ms
      });

    } catch (error) {
      console.error('Error fetching spectral data:', error);
      alert('Error loading data: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleZoomIn = () => {
    if (zoomLevel < 10) {
      setZoomLevel(zoomLevel + 1);
    }
  };

  const handleZoomOut = () => {
    if (zoomLevel > 0) {
      setZoomLevel(zoomLevel - 1);
    }
  };

  const handleResetView = () => {
    if (observations.length > 0 && selectedObs) {
      const obs = observations.find(o => o.measurement_id === selectedObs);
      if (obs) {
        setWavelengthRange({
          min: Math.floor(obs.min_wavelength),
          max: Math.ceil(obs.max_wavelength)
        });
        setZoomLevel(0);
      }
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🌙 LunarAtlas Spectral Visualization</h1>
        <p>Chandrayaan-3 LIBS Data Explorer</p>
      </header>

      <div className="controls-panel">
        <div className="control-group">
          <label>Observation:</label>
          <select 
            value={selectedObs || ''} 
            onChange={(e) => setSelectedObs(parseInt(e.target.value))}
          >
            {observations.map(obs => (
              <option key={obs.measurement_id} value={obs.measurement_id}>
                Measurement {obs.measurement_id} ({obs.point_count} points, {obs.min_wavelength.toFixed(1)}-{obs.max_wavelength.toFixed(1)} nm)
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Wavelength Range (nm):</label>
          <input 
            type="number" 
            value={wavelengthRange.min} 
            onChange={(e) => setWavelengthRange({...wavelengthRange, min: parseFloat(e.target.value)})}
            step="1"
          />
          <span> to </span>
          <input 
            type="number" 
            value={wavelengthRange.max} 
            onChange={(e) => setWavelengthRange({...wavelengthRange, max: parseFloat(e.target.value)})}
            step="1"
          />
        </div>

        <div className="control-group">
          <label>Zoom Level: {zoomLevel}</label>
          <div className="zoom-buttons">
            <button onClick={handleZoomOut} disabled={zoomLevel === 0}>
              ➖ Zoom Out
            </button>
            <button onClick={handleZoomIn} disabled={zoomLevel === 10}>
              ➕ Zoom In
            </button>
            <button onClick={handleResetView}>
              🔄 Reset View
            </button>
          </div>
        </div>

        {stats && (
          <div className="stats-panel">
            <div className="stat">
              <strong>Buckets:</strong> {stats.buckets}
            </div>
            <div className="stat">
              <strong>Bucket Size:</strong> {stats.bucketSize} nm
            </div>
            <div className="stat">
              <strong>Data Points:</strong> {stats.dataPoints}
            </div>
            <div className="stat">
              <strong>Processing Time:</strong> {stats.processingTime.toFixed(2)} ms
            </div>
          </div>
        )}
      </div>

      <div className="chart-container">
        {loading && <div className="loading-overlay">Loading spectral data...</div>}
        <div ref={chartRef} style={{ width: '100%', height: '600px' }}></div>
      </div>

      <div className="info-panel">
        <h3>💡 How to Use:</h3>
        <ul>
          <li><strong>Mouse Wheel:</strong> Scroll to zoom in/out on X-axis</li>
          <li><strong>Click & Drag:</strong> Pan across the spectrum</li>
          <li><strong>Zoom Buttons:</strong> Increase zoom level for finer resolution</li>
          <li><strong>Hover:</strong> See wavelength and intensity values</li>
        </ul>
        <div className="algorithm-info">
          <strong>Algorithm:</strong> Min-Max Downsampling with 5% bucket overlap
          <br />
          <strong>Guarantee:</strong> 100% peak preservation at all zoom levels
        </div>
      </div>
    </div>
  );
}

export default App;
