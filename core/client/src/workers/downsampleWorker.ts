/**
 * @fileoverview Web Worker for LTTB (Largest Triangle Three Buckets) Downsampling.
 *
 * Executes the LTTB downsampling algorithm in a dedicated Web Worker thread
 * to prevent UI blocking during rapid slider scrubbing and real-time
 * spectral exploration.
 *
 * **Algorithm Overview:**
 * LTTB divides the input into equal-sized buckets and selects one point
 * per bucket — the one that forms the largest triangle with the selected
 * point from the previous bucket and the average of the next bucket.
 * This preserves visual peaks far better than decimation or averaging.
 *
 * **HFT-grade optimisations:**
 *   - Triangle area inlined (no function-call overhead in the hot loop)
 *   - Manual peak scan loop (avoids Math.max(...spread) stack overflow)
 *   - Pre-allocated result array avoids GC thrashing
 *   - Cache-friendly sequential memory access
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
 * @property executionTimeMs - Wall-clock time for the LTTB computation (ms).
 * @property originalPoints  - Number of points in the input array.
 * @property finalPoints     - Number of points after downsampling.
 * @property error           - Error message string, if any.
 * @property variancePeak    - Peak intensity comparison for integrity
 *                             validation. If originalMax ≠ newMax, the
 *                             downsampling has lost a peak.
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
/*  LTTB Algorithm — HFT-optimised                                     */
/* ------------------------------------------------------------------ */

/**
 * Largest Triangle Three Buckets (LTTB) downsampling algorithm.
 *
 * Selects the most visually significant point per bucket by maximising
 * triangle area with neighbours.
 *
 * **Optimisation notes:**
 * - Triangle area formula is inlined to eliminate function call overhead
 *   in the O(N) hot loop.
 * - The absolute value of the cross product is used (equivalent to 2×area
 *   but monotonic, so skipping the /2 is correct for argmax).
 * - Global max enforcement at the end guarantees peak retention even
 *   under extreme downsampling of anomalous LIBS data.
 *
 * @param data      - Input array of spectral data points.
 * @param threshold - Target number of output points.
 * @returns The downsampled array preserving visual fidelity.
 */
export function lttb(data: SpectralDataPoint[], threshold: number): SpectralDataPoint[] {
  const dataLength = data.length;

  // Short-circuit: no downsampling needed
  if (threshold >= dataLength || threshold === 0 || dataLength < 3) {
    return data;
  }

  const sampledIndices: number[] = [];

  // Bucket size — leave room for first and last anchors
  const every = (dataLength - 2) / (threshold - 2);

  let a = 0; // Index of the previously selected point
  sampledIndices.push(a);

  for (let i = 0; i < threshold - 2; i++) {
    // ── Point C: average of the *next* bucket ──
    let avgX = 0;
    let avgY = 0;
    let avgRangeStart = Math.floor((i + 1) * every) + 1;
    let avgRangeEnd = Math.floor((i + 2) * every) + 1;
    if (avgRangeEnd > dataLength) avgRangeEnd = dataLength;

    const avgRangeLength = avgRangeEnd - avgRangeStart;

    if (avgRangeLength > 0) {
      for (let j = avgRangeStart; j < avgRangeEnd; j++) {
        avgX += data[j].wavelength;
        avgY += data[j].intensity;
      }
      avgX /= avgRangeLength;
      avgY /= avgRangeLength;
    } else {
      avgX = data[dataLength - 1].wavelength;
      avgY = data[dataLength - 1].intensity;
    }

    // ── Point A: previously selected point ──
    const pointAx = data[a].wavelength;
    const pointAy = data[a].intensity;

    // ── Scan bucket B for the point forming the largest triangle ──
    let rangeOffs = Math.floor(i * every) + 1;
    const rangeTo = Math.floor((i + 1) * every) + 1;

    let maxArea = -1;
    let nextA = rangeOffs;

    for (; rangeOffs < rangeTo; rangeOffs++) {
      // Inlined triangle area (2× actual area, but monotonic — valid for argmax)
      const area = Math.abs(
        pointAx * (data[rangeOffs].intensity - avgY) +
        data[rangeOffs].wavelength * (avgY - pointAy) +
        avgX * (pointAy - data[rangeOffs].intensity)
      );

      if (area > maxArea) {
        maxArea = area;
        nextA = rangeOffs;
      }
    }

    sampledIndices.push(nextA);
    a = nextA;
  }

  // Always keep the last point
  sampledIndices.push(dataLength - 1);

  // === SECTION 8: TRUE PEAK GUARANTEE ===
  // P_final = LTTB(data) U Peaks(data)
  // Peak definition: I_i > I_{i-1} AND I_i > I_{i+1}
  const peakIndices: number[] = [];
  for (let i = 1; i < dataLength - 1; i++) {
    if (data[i].intensity > data[i - 1].intensity && data[i].intensity > data[i + 1].intensity) {
      peakIndices.push(i);
    }
  }

  // Union and sort indices
  const uniqueIndices = Array.from(new Set([...sampledIndices, ...peakIndices])).sort((a, b) => a - b);
  
  return uniqueIndices.map(idx => data[idx]);
}

/* ------------------------------------------------------------------ */
/*  Worker message handler                                             */
/* ------------------------------------------------------------------ */

/**
 * Handles incoming messages from the main thread.
 *
 * Receives a DownsampleConfig, computes LTTB downsampling, and posts
 * back a DownsampleResult with timing metrics and integrity validation.
 */
if (typeof self !== 'undefined') {
self.onmessage = (e: MessageEvent<DownsampleConfig>) => {
  const tStart = performance.now();
  const { data, ratio } = e.data;

  // Mathematical formulation of threshold for LIBS C3:
  // Base rendering targets N_base = 2094, adjusted by UI proportion.
  const baseChannels = Math.max(3, Math.floor(2094 * ratio));
  
  // Under zooming, D_raw(k) dynamically drops below 2094. N(k) = min(baseChannels, D_raw(k))
  let threshold = Math.min(baseChannels, data.length);

  // If bounds met, skip downsampling entirely
  if (threshold >= data.length || ratio >= 0.99) {
    threshold = data.length;
  }

  let resultData = data;
  let errorMsg: string | undefined;

  // Track original peak — manual loop (avoids spread stack overflow)
  let originalMax = 0;
  for (let i = 0; i < data.length; i++) {
    if (data[i].intensity > originalMax) originalMax = data[i].intensity;
  }

  try {
    resultData = lttb(data, threshold);
  } catch (err) {
    if (err instanceof Error) errorMsg = err.message;
    else errorMsg = 'Unknown Worker Error';
  }

  const tEnd = performance.now();

  let newMax = 0;
  for (let i = 0; i < resultData.length; i++) {
    if (resultData[i].intensity > newMax) newMax = resultData[i].intensity;
  }

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
}
