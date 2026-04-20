import { describe, it, expect } from 'vitest';
import { lttb } from '../workers/downsampleWorker';

describe('LTTB Downsampling Algorithm', () => {
  // Generate a synthetic dataset with 1000 points and a sharp peak
  const mockData = Array.from({ length: 1000 }, (_, i) => ({
    wavelength: i,
    intensity: Math.sin(i / 10) * 100 + (i === 452 ? 999 : 0), // Sharp peak at index 452
    rawPlasma: 0,
    rawBackground: 0,
    measurementId: 'test'
  }));

  it('should return original data if threshold >= length', () => {
    const result = lttb(mockData, 1500);
    expect(result.length).toBe(1000);
    expect(result).toEqual(mockData);
  });

  it('should downsample to the exact threshold requested', () => {
    const threshold = 100;
    const result = lttb(mockData, threshold);
    expect(result.length).toBe(threshold);
  });

  it('should preserve the first and last points', () => {
    const threshold = 50;
    const result = lttb(mockData, threshold);
    expect(result[0].wavelength).toBe(mockData[0].wavelength);
    expect(result[result.length - 1].wavelength).toBe(mockData[mockData.length - 1].wavelength);
  });

  it('should retain the global maximum (Peak Retention Check)', () => {
    // Even with heavy downsampling (1000 -> 20 pts), the peak at 999 should survive
    const threshold = 20;
    const result = lttb(mockData, threshold);
    const maxVal = Math.max(...result.map(p => p.intensity));
    expect(maxVal).toBe(999);
  });

  it('should handle empty or near-empty arrays gracefully', () => {
    expect(lttb([], 10)).toEqual([]);
    const onePoint = [mockData[0]];
    expect(lttb(onePoint, 10)).toEqual(onePoint);
  });

  it('should maintain monotonicity of the x-axis (wavelength)', () => {
    const result = lttb(mockData, 100);
    for (let i = 1; i < result.length; i++) {
      expect(result[i].wavelength).toBeGreaterThan(result[i-1].wavelength);
    }
  });

  it('should perform under the 16ms benchmark for 10k points', () => {
    const largeData = Array.from({ length: 10000 }, (_, i) => ({
      wavelength: i,
      intensity: Math.random() * 100,
      rawPlasma: 0,
      rawBackground: 0,
      measurementId: 'test'
    }));
    
    const start = performance.now();
    lttb(largeData, 1000);
    const end = performance.now();
    
    const duration = end - start;
    console.log(`LTTB Execution Time (10k pts): ${duration.toFixed(3)}ms`);
    expect(duration).toBeLessThan(16); // 60FPS frame budget
  });
});
