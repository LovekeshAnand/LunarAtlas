/**
 * @fileoverview Web Worker for M4 (MinMaxMinMax) Downsampling.
 *
 * Executes the M4 downsampling algorithm in a dedicated Web Worker thread
 * to prevent UI blocking during rapid slider scrubbing and real-time
 * spectral exploration.
 *
 * **Algorithm Overview:**
 * The M4 algorithm divides the input data into N/4 non-overlapping buckets
 * (where N is the target point count) and extracts exactly four extreme
 * points per bucket:
 *   1. First — the first data point (left boundary)
 *   2. Min   — the point with minimum intensity
 *   3. Max   — the point with maximum intensity
 *   4. Last  — the last data point (right boundary)
 *
 * These four points are deduplicated and sorted by wavelength index,
 * guaranteeing that the visual envelope of the downsampled data is
 * identical to the original — with zero peak clipping.
 *
 * **Complexity:** O(N) time, O(N) space.
 *
 * @see {@link ../hooks/useDownsampling.ts} for the React hook that manages
 *      the worker lifecycle and state propagation.
 */

import type { SpectralDataPoint } from '../services/apiService';

/* ------------------------------------------------------------------ */
/*  Message interfaces                                                 */
/* ------------------------------------------------------------------ */

/**
 * Configuration payload sent to the worker via `postMessage`.
 *
 * @property data  - Full array of spectral data points from the API.
 * @property ratio - Downsampling ratio (0.0–1.0). For example, 0.1 means
 *                   reduce to 10% of the original point count.
 */
export interface DownsampleConfig {
  data: SpectralDataPoint[];
  ratio: number;
}

/**
 * Result payload returned by the worker via `postMessage`.
 *
 * @property downsampled     - The downsampled data point array.
 * @property executionTimeMs - Wall-clock time for the M4 computation (ms).
 * @property originalPoints  - Number of points in the input array.
 * @property finalPoints     - Number of points after downsampling.
 * @property error           - Error message string, if any.
 * @property variancePeak    - Peak intensity comparison for integrity
 *                             validation. If originalMax ≠ newMax, the
 *                             downsampling has lost a peak (should not
 *                             happen with M4).
 */
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

/* ------------------------------------------------------------------ */
/*  M4 Algorithm                                                       */
/* ------------------------------------------------------------------ */

/**
 * M4 (MinMaxMinMax) downsampling algorithm.
 *
 * Divides the input array into `threshold / 4` non-overlapping buckets
 * and extracts up to 4 extreme points per bucket: First, Min, Max, Last.
 *
 * **Step-by-step flow:**
 * 1. Calculate the number of buckets: `numBuckets = floor(threshold / 4)`.
 * 2. For each bucket, compute the start/end index range.
 * 3. Scan the bucket to find the indices of min and max intensity.
 * 4. Collect [firstIdx, minIdx, maxIdx, lastIdx], deduplicate via Set.
 * 5. Sort by index to preserve wavelength ordering, then emit points.
 *
 * **Guarantees:**
 * - Every global maximum within any bucket is explicitly preserved.
 * - The first and last points of every bucket maintain boundary continuity.
 * - Total output size ≤ 4 × numBuckets (exactly 4 when all indices differ).
 *
 * @param data      - Input array of spectral data points.
 * @param threshold - Target number of output points (will be rounded to
 *                    a multiple of 4 internally).
 * @returns The downsampled array preserving the visual envelope.
 */
export function m4(data: SpectralDataPoint[], threshold: number): SpectralDataPoint[] {
  const dataLength = data.length;

  // If threshold is large enough, or too few points, return as-is
  if (threshold >= dataLength || threshold === 0 || dataLength < 4) {
    return data;
  }

  // M4 yields up to 4 points per bucket, so we need threshold/4 buckets
  const numBuckets = Math.max(1, Math.floor(threshold / 4));
  const pointsPerBucket = dataLength / numBuckets;
  
  const sampled: SpectralDataPoint[] = [];

  for (let i = 0; i < numBuckets; i++) {
    // Calculate inclusive start and exclusive end indices for this bucket
    const startIdx = Math.floor(i * pointsPerBucket);
    const endIdx = i === numBuckets - 1 ? dataLength : Math.floor((i + 1) * pointsPerBucket);
    const bucketLength = endIdx - startIdx;
    
    if (bucketLength === 0) continue;

    // ── Scan for min and max intensity within this bucket ──
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

    // ── Boundary indices ──
    const firstIdx = startIdx;
    const lastIdx = endIdx - 1;

    // ── Deduplicate and sort by index (preserves wavelength order) ──
    const uniqueIndices = Array.from(new Set([firstIdx, minIdx, maxIdx, lastIdx])).sort((a, b) => a - b);
    
    for (const idx of uniqueIndices) {
      sampled.push(data[idx]);
    }
  }

  return sampled;
}

/* ------------------------------------------------------------------ */
/*  Worker message handler                                             */
/* ------------------------------------------------------------------ */

/**
 * Handles incoming messages from the main thread.
 *
 * Receives a DownsampleConfig, computes the M4 downsampling, and posts
 * back a DownsampleResult with timing metrics and integrity validation.
 */
self.onmessage = (e: MessageEvent<DownsampleConfig>) => {
  const tStart = performance.now();
  const { data, ratio } = e.data;

  // Calculate target threshold from ratio (e.g., 0.5 × 2000 = 1000 points)
  let threshold = Math.max(4, Math.floor(data.length * ratio));
  
  // If the desired threshold is ≥100%, skip downsampling entirely
  if (ratio >= 0.99) {
     threshold = data.length;
  }

  let resultData = data;
  let errorMsg;

  // Track original peak for integrity validation
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
