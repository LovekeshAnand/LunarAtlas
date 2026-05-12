import { useState, useEffect, useRef } from 'react';
import type { SpectralDataPoint } from '../services/apiService';
import type { DownsampleConfig, DownsampleResult } from '../workers/downsampleWorker';

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

export function useDownsampling(
  rawData: SpectralDataPoint[],
  ratio: number
): DownsamplingState {
  const [state, setState] = useState<DownsamplingState>({
    data: [],
    originalData: [],
    isProcessing: false,
    metrics: { executionTimeMs: 0, originalPoints: 0, finalPoints: 0, variancePeak: null },
    error: null,
  });

  const workerRef = useRef<Worker | null>(null);

  useEffect(() => {
    // Initialize Web Worker
    workerRef.current = new Worker(
      new URL('../workers/downsampleWorker.ts', import.meta.url),
      { type: 'module' }
    );

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

  useEffect(() => {
    // Kick off downsampling whenever rawData or ratio changes
    if (rawData.length === 0) {
      setState(prev => ({ ...prev, data: [], originalData: [], isProcessing: false }));
      return;
    }

    setState(prev => ({ ...prev, originalData: rawData, isProcessing: true, error: null }));
    
    const config: DownsampleConfig = { data: rawData, ratio };
    workerRef.current?.postMessage(config);

  }, [rawData, ratio]);

  return state;
}
