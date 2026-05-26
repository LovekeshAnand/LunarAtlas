/**
 * @fileoverview useDownsampling — React hook for off-thread LTTB downsampling.
 *
 * Manages the lifecycle of a dedicated Web Worker that runs the LTTB
 * (Largest Triangle Three Buckets) downsampling algorithm. This ensures
 * that heavy computation (scanning thousands of data points) never
 * blocks the main UI thread, maintaining 60 FPS responsiveness during
 * rapid slider scrubbing.
 *
 * **Usage:**
 * ```tsx
 * const { data, metrics, error } = useDownsampling(rawData, proportion);
 * // `data` contains the LTTB-downsampled points ready for rendering.
 * // `metrics` provides execution time and point counts for the dev console.
 * ```
 *
 * @see {@link ../workers/downsampleWorker.ts} for the LTTB algorithm implementation.
 */

import { useState, useEffect, useRef } from 'react';
import type { SpectralDataPoint } from '../services/apiService';
import type { DownsampleConfig, DownsampleResult } from '../workers/downsampleWorker';

/* ------------------------------------------------------------------ */
/*  State interface                                                    */
/* ------------------------------------------------------------------ */

/**
 * Shape of the state returned by the useDownsampling hook.
 *
 * @property data         - The downsampled data points (ready to render).
 * @property originalData - Reference to the unmodified raw input data.
 * @property isProcessing - True while the worker is computing.
 * @property metrics      - Performance and integrity metrics from the worker.
 * @property error        - Error message from the worker, or null.
 */
export interface DownsamplingState {
  data: SpectralDataPoint[];
  originalData: SpectralDataPoint[];
  isProcessing: boolean;
  metrics: {
    executionTimeMs: number;
    originalPoints: number;
    finalPoints: number;
    variancePeak: { originalMax: number; newMax: number; } | null;
  };
  error: string | null;
}

/* ------------------------------------------------------------------ */
/*  Hook implementation                                                */
/* ------------------------------------------------------------------ */

/**
 * React hook that manages an LTTB downsampling Web Worker.
 *
 * Spawns a Web Worker on mount, posts data whenever `rawData` or `ratio`
 * changes, and cleans up (terminates) the worker on unmount.
 *
 * @param rawData - Full spectral data array from the API.
 * @param ratio   - Downsampling ratio (0.0–1.0). E.g., 0.1 = keep 10%.
 * @returns DownsamplingState with the downsampled data, metrics, and status.
 */
export function useDownsampling(
  rawData: SpectralDataPoint[],
  ratio: number,
  targetWavelengths?: number[]
): DownsamplingState {
  const [state, setState] = useState<DownsamplingState>({
    data: [],
    originalData: [],
    isProcessing: false,
    metrics: { executionTimeMs: 0, originalPoints: 0, finalPoints: 0, variancePeak: null },
    error: null,
  });

  const workerRef = useRef<Worker | null>(null);

  /* ── Spawn worker on mount, terminate on unmount ── */
  useEffect(() => {
    workerRef.current = new Worker(
      new URL('../workers/downsampleWorker.ts', import.meta.url),
      { type: 'module' }
    );

    /* Handle results from the worker */
    workerRef.current.onmessage = (e: MessageEvent<DownsampleResult>) => {
      const { downsampled, executionTimeMs, originalPoints, finalPoints, error, variancePeak } = e.data;
      
      setState(prev => ({
        ...prev,
        data: downsampled,
        isProcessing: false,
        error: error || null,
        metrics: { executionTimeMs, originalPoints, finalPoints, variancePeak }
      }));
    };

    return () => {
      workerRef.current?.terminate();
    };
  }, []);

  const targetWavelengthsStr = JSON.stringify(targetWavelengths);

  /* ── Post data to worker whenever inputs change ── */
  useEffect(() => {
    if (rawData.length === 0) {
      setState(prev => ({ ...prev, data: [], originalData: [], isProcessing: false }));
      return;
    }

    setState(prev => ({ ...prev, originalData: rawData, isProcessing: true, error: null }));
    
    const config: DownsampleConfig = { data: rawData, ratio, targetWavelengths };
    workerRef.current?.postMessage(config);

  }, [rawData, ratio, targetWavelengthsStr]);

  return state;
}
