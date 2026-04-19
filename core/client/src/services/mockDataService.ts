/**
 * @fileoverview Mock Data Service for LunarAtlas.
 * Provides simulated spectral data processing for Chandrayaan-3 LIBS (Laser-Induced Breakdown Spectroscopy).
 * This service simulates the transformation of Level-1 PDS4 raw data into Cleaned (L2) spectra.
 */

/**
 * Represents a single spectral data point in the mission sequence.
 */
export interface SpectralData {
  /** Wavelength in nanometers (scientific mission range: 164.35 to 878.26 nm) */
  wavelength: number;
  /** Raw detector counts during plasma emission event */
  rawPlasma: number;
  /** Baseline detector counts captured during a near-simultaneous background event */
  rawBackground: number;
  /** Cleaned intensity after background subtraction and noise suppression */
  intensity: number;
  /** Unique sequential identifier pinning this record to a specific shot pair */
  measurementId: string;
}

/**
 * Represents a validated elemental signature (emission line) detected in the spectrum.
 */
export interface PeakDetection {
  /** Wavelength of the detected peak center */
  wavelength: number;
  /** Peak intensity after baseline removal */
  intensity: number;
  /** Confidence level: Signal-to-Noise Ratio (calculated vs local variance) */
  snr: number;
  /** Element/Ion identity matched against NIST Atomic Spectra Database */
  element: string;
}

/**
 * Core reference lines from the NIST Atomic Spectra Database.
 * These are used for automated elemental identification in the L2 pipeline.
 */
const NIST_LINES = [
  { wl: 279.55, el: 'Mg II' }, // Magnesium (Ionized)
  { wl: 288.16, el: 'Si I'  }, // Silicon (Neutral)
  { wl: 334.94, el: 'Ti II' }, // Titanium (Ionized)
  { wl: 393.37, el: 'Ca II' }, // Calcium (Ionized)
  { wl: 396.15, el: 'Al I'  }, // Aluminum (Neutral)
  { wl: 404.58, el: 'Fe I'  }, // Iron (Neutral)
  { wl: 777.40, el: 'O I'   }  // Oxygen (Neutral - atmospheric/matrix)
];

/**
 * Generates a high-fidelity mock spectrum based on real LIBS mission parameters.
 * 
 * ALGORITHMS:
 * 1. Proximity Pairing: Pairs plasma shots with background acquisitions.
 * 2. Background Subtraction: I_alt = max(0, I_plasma - I_bg).
 * 3. SNR Thresholding: Detects peaks where SNR > 3σ relative to a local sliding window.
 * 
 * @param measurementId The identifier for the calibration session
 * @returns Object containing the full spectral sequence and detected elemental peaks
 */
export function generateMockSpectrum(measurementId: string = 'm_001'): { data: SpectralData[], peaks: PeakDetection[] } {
  const data: SpectralData[] = [];
  const minWavelength = 164.35;
  const maxWavelength = 878.26;
  const numChannels = 2049; // Standard Chandrayaan-3 LIBS detector resolution
  const step = (maxWavelength - minWavelength) / (numChannels - 1);

  // Background continuum baseline (simulating thermal and instrument noise)
  const bgBaseline = 1000;
  
  // Synthetic emission lines (approximating lunar regolith composition)
  const syntheticPeaks = [
    { wl: 279.71, amp: 684, width: 0.2 }, // Mg signature
    { wl: 288.30, amp: 210, width: 0.2 }, // Si signature
    { wl: 335.10, amp: 145, width: 0.2 }, // Ti signature
    { wl: 393.55, amp: 580, width: 0.2 }, // Ca signature
    { wl: 396.34, amp: 490, width: 0.2 }, // Al signature
    { wl: 404.75, amp: 205, width: 0.2 }, // Fe signature
    { wl: 777.62, amp: 240, width: 0.3 }  // O signature
  ];

  for (let i = 0; i < numChannels; i++) {
    const wavelength = minWavelength + i * step;
    
    // Poisson-distributed noise simulation
    const bgNoise = (Math.random() - 0.5) * 80;
    const plasmaNoise = (Math.random() - 0.5) * 80;
    
    const rawBackground = bgBaseline + bgNoise;
    let plasmaEmission = 0;
    
    // Summing Gaussian peak profiles
    for (const peak of syntheticPeaks) {
      plasmaEmission += peak.amp * Math.exp(-Math.pow(wavelength - peak.wl, 2) / (2 * Math.pow(peak.width, 2)));
    }
    
    const rawPlasma = bgBaseline + plasmaEmission + plasmaNoise;

    /**
     * ALGORITHM: Background Subtraction and Negative-Value Clamping
     * Prevents unphysical negative intensities resulting from high noise in the background shot.
     */
    const cleanedIntensity = Math.max(0, rawPlasma - rawBackground);

    data.push({
      wavelength: Number(wavelength.toFixed(2)),
      rawPlasma: Number(Math.round(rawPlasma)),
      rawBackground: Number(Math.round(rawBackground)),
      intensity: Number(Math.round(cleanedIntensity)),
      measurementId
    });
  }

  /**
   * ALGORITHM: SNR Thresholding and Peak Detection
   * Evaluates peaks against the local standard deviation (σ) within a sliding window.
   */
  const peakDetections: PeakDetection[] = [];
  const windowSize = 50; // Reference window for local noise baseline
  
  for (let i = Math.floor(windowSize / 2); i < data.length - Math.floor(windowSize / 2); i++) {
    let localSum = 0;
    for (let j = i - Math.floor(windowSize / 2); j <= i + Math.floor(windowSize / 2); j++) {
      localSum += data[j].intensity;
    }
    const localMean = localSum / windowSize;
    
    let localVariance = 0;
    for (let j = i - Math.floor(windowSize / 2); j <= i + Math.floor(windowSize / 2); j++) {
      localVariance += Math.pow(data[j].intensity - localMean, 2);
    }
    const localSigma = Math.sqrt(localVariance / windowSize) || 1;
    
    const currentPoint = data[i];
    
    // Peak finding (local maximum)
    if (currentPoint.intensity > data[i - 1].intensity && currentPoint.intensity > data[i + 1].intensity) {
      const snr = currentPoint.intensity / localSigma;

      // Acceptance criteria: SNR > 3 and absolute intensity > 50 cts
      if (snr > 3) {
        // Cross-referencing detected wavelength against NIST database
        let bestMatch = null;
        let minDiff = 0.5; // Detection tolerance bandwidth
        for (const nist of NIST_LINES) {
          const diff = Math.abs(currentPoint.wavelength - nist.wl);
          if (diff < minDiff) {
            minDiff = diff;
            bestMatch = nist.el;
          }
        }
        
        if (bestMatch && currentPoint.intensity > 50) {
            peakDetections.push({
               wavelength: currentPoint.wavelength,
               intensity: currentPoint.intensity,
               snr: Number(snr.toFixed(1)),
               element: bestMatch
            });
        }
      }
    }
  }

  // Peak deduplication (ensuring only the strongest signature is kept within 1nm)
  const uniquePeaks = [];
  for (let i = 0; i < peakDetections.length; i++) {
    const current = peakDetections[i];
    const prev = uniquePeaks[uniquePeaks.length - 1];
    if (!prev || Math.abs(current.wavelength - prev.wavelength) > 1.0) {
      uniquePeaks.push(current);
    } else if (current.intensity > prev.intensity) {
      uniquePeaks[uniquePeaks.length - 1] = current;
    }
  }

  return { data, peaks: uniquePeaks };
}

/**
 * Public Data Accessor.
 * Provides a Promise-based API for fetching processed data.
 */
export const mockDataService = {
  /**
   * Simulates an asynchronous data fetch from the processing backend.
   * @param measurementId Target sequence ID
   * @returns Promise resolving to a full L2 analysis result
   */
  fetchSpectrum: (measurementId: string): Promise<{ data: SpectralData[], peaks: PeakDetection[] }> => {
    return new Promise((resolve) => {
      // Simulate typical processing/IO latency
      setTimeout(() => {
        resolve(generateMockSpectrum(measurementId));
      }, 400);
    });
  }
};

