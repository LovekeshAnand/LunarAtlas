import type { SpectralDataPoint } from '../services/apiService';

/**
 * @fileoverview Web Worker for Largest Triangle Three Buckets (LTTB) Downsampling.
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
 * Calculates the area of a triangle given three points.
 */
function calculateTriangleArea(
  p1x: number, p1y: number,
  p2x: number, p2y: number,
  p3x: number, p3y: number
): number {
  return Math.abs(
    (p1x * (p2y - p3y) +
     p2x * (p3y - p1y) +
     p3x * (p1y - p2y)) / 2.0
  );
}

/**
 * Largest Triangle Three Buckets (LTTB) Algorithm.
 * Downsamples data while explicitly preserving extreme visual points (peaks/valleys).
 */
export function lttb(data: SpectralDataPoint[], threshold: number): SpectralDataPoint[] {
  const dataLength = data.length;
  if (threshold >= dataLength || threshold === 0 || dataLength < 3) {
    return data;
  }

  const sampled: SpectralDataPoint[] = [];
  let sampledIndex = 0;

  // Bucket size. Leave room for start and end data points
  const every = (dataLength - 2) / (threshold - 2);

  let a = 0; // Initially a is the first point in the triangle
  let maxAreaPoint = { ...data[a] };
  sampled[sampledIndex++] = maxAreaPoint;

  for (let i = 0; i < threshold - 2; i++) {
    // Calculate point average for next bucket (the 'C' in the triangle ABC)
    let avgX = 0;
    let avgY = 0;
    let avgRangeStart = Math.floor((i + 1) * every) + 1;
    let avgRangeEnd = Math.floor((i + 2) * every) + 1;
    avgRangeEnd = avgRangeEnd < dataLength ? avgRangeEnd : dataLength;

    const avgRangeLength = avgRangeEnd - avgRangeStart;

    for (; avgRangeStart < avgRangeEnd; avgRangeStart++) {
      avgX += data[avgRangeStart].wavelength;
      avgY += data[avgRangeStart].intensity;
    }
    avgX /= avgRangeLength;
    avgY /= avgRangeLength;

    // Get the range for the current bucket (the 'B' in the triangle ABC)
    let rangeOffs = Math.floor(i * every) + 1;
    const rangeTo = Math.floor((i + 1) * every) + 1;

    // Point A
    const pointAx = data[a].wavelength;
    const pointAy = data[a].intensity;

    let maxArea = -1;
    let nextA = rangeOffs;
    let maxAreaPointRef = data[rangeOffs];

    // Find the point in bucket B that creates the largest triangle
    for (; rangeOffs < rangeTo; rangeOffs++) {
      const area = calculateTriangleArea(
        pointAx, pointAy, // Point A
        data[rangeOffs].wavelength, data[rangeOffs].intensity, // Point B
        avgX, avgY // Point C (Average of next bucket)
      );

      if (area > maxArea) {
        maxArea = area;
        maxAreaPointRef = data[rangeOffs];
        nextA = rangeOffs;
      }
    }

    sampled[sampledIndex++] = { ...maxAreaPointRef }; // Clone the chosen point
    a = nextA; // Set the chosen point as the 'A' for the next iteration
  }

  // Always add the last point
  sampled[sampledIndex++] = { ...data[dataLength - 1] };

  // Quick sanity check - enforce global max/min if they somehow missed 
  // (LTTB generally catches them because peaks create the largest triangles, 
  // but LIBS data can be highly anomalous).
  const originalMax = Math.max(...data.map(d => d.intensity));
  const newMax = Math.max(...sampled.map(d => d.intensity));
  
  if (originalMax !== newMax) {
       // Find the real peak and enforce it near its location
       const peakObj = data.find(d => d.intensity === originalMax);
       if(peakObj) {
           sampled.push({...peakObj});
           sampled.sort((x, y) => x.wavelength - y.wavelength); // Maintain X-axis order
       }
  }

  return sampled;
}

// Worker message handler
self.onmessage = (e: MessageEvent<DownsampleConfig>) => {
  const tStart = performance.now();
  const { data, ratio } = e.data;

  // Calculate target threshold (e.g. 0.5 * 2000 = 1000 points)
  let threshold = Math.max(3, Math.floor(data.length * ratio));
  
  // If the desired threshold is 100%, skip downsampling
  if (ratio >= 0.99) {
     threshold = data.length;
  }

  let resultData = data;
  let errorMsg;

  const originalMax = data.length > 0 ? Math.max(...data.map(d => d.intensity)) : 0;

  try {
    resultData = lttb(data, threshold);
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
