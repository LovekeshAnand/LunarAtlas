import type { SpectralDataPoint } from '../services/apiService';

/**
 * @fileoverview Web Worker for M4 Algorithm Downsampling.
 * Runs in a separate thread to prevent UI freezing during rapid slider scrubbing.
 */

// Define the incoming message format
export interface DownsampleConfig {
  data: SpectralDataPoint[];
  ratio: number; // e.g. 0.5 for 50%, 0.1 for 10%
}

export interface DownsampleResult {
  downsampled: SpectralDataPoint[];
  executionTimeMs: number;
  originalPoints: number;
  finalPoints: number;
  error?: string;
  variancePeak: {
    originalMax: number;
    newMax: number;
  };
}

/**
 * M4 Algorithm (MinMaxMinMax).
 * Downsamples data while explicitly preserving exactly up to 4 extreme points per bucket: First, Min, Max, Last.
 * This guarantees visual envelope preservation while massively reducing data size.
 */
export function m4(data: SpectralDataPoint[], threshold: number): SpectralDataPoint[] {
  const dataLength = data.length;
  // If threshold is large enough, or too few points, return data
  if (threshold >= dataLength || threshold === 0 || dataLength < 4) {
    return data;
  }

  // threshold is the target number of downsampled points.
  // M4 yields up to 4 points per bucket. So we divide data into (threshold / 4) buckets.
  const numBuckets = Math.max(1, Math.floor(threshold / 4));
  const pointsPerBucket = dataLength / numBuckets;
  
  const sampled: SpectralDataPoint[] = [];

  for (let i = 0; i < numBuckets; i++) {
    const startIdx = Math.floor(i * pointsPerBucket);
    const endIdx = i === numBuckets - 1 ? dataLength : Math.floor((i + 1) * pointsPerBucket);
    const bucketLength = endIdx - startIdx;
    
    if (bucketLength === 0) continue;

    let minIdx = startIdx;
    let maxIdx = startIdx;
    let minVal = data[startIdx].intensity;
    let maxVal = data[startIdx].intensity;

    for (let j = startIdx + 1; j < endIdx; j++) {
      const val = data[j].intensity;
      if (val < minVal) {
        minVal = val;
        minIdx = j;
      }
      if (val > maxVal) {
        maxVal = val;
        maxIdx = j;
      }
    }

    const firstIdx = startIdx;
    const lastIdx = endIdx - 1;

    // Deduplicate and sort
    const uniqueIndices = Array.from(new Set([firstIdx, minIdx, maxIdx, lastIdx])).sort((a, b) => a - b);
    
    for (const idx of uniqueIndices) {
      sampled.push(data[idx]);
    }
  }

  return sampled;
}

// Worker message handler
self.onmessage = (e: MessageEvent<DownsampleConfig>) => {
  const tStart = performance.now();
  const { data, ratio } = e.data;

  // Calculate target threshold (e.g. 0.5 * 2000 = 1000 points)
  let threshold = Math.max(4, Math.floor(data.length * ratio));
  
  // If the desired threshold is 100%, skip downsampling
  if (ratio >= 0.99) {
     threshold = data.length;
  }

  let resultData = data;
  let errorMsg;

  const originalMax = data.length > 0 ? Math.max(...data.map(d => d.intensity)) : 0;

  try {
    resultData = m4(data, threshold);
  } catch (err) {
    if (err instanceof Error) errorMsg = err.message;
    else errorMsg = 'Unknown Worker Error';
  }

  const tEnd = performance.now();
  const newMax = resultData.length > 0 ? Math.max(...resultData.map(d => d.intensity)) : 0;

  const result: DownsampleResult = {
    downsampled: resultData,
    executionTimeMs: tEnd - tStart,
    originalPoints: data.length,
    finalPoints: resultData.length,
    error: errorMsg,
    variancePeak: {
      originalMax,
      newMax
    }
  };

  self.postMessage(result);
};
