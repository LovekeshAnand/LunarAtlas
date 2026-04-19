export interface SpectralData {
  wavelength: number;
  rawPlasma: number;
  rawBackground: number;
  intensity: number; // The cleaned intensity
  measurementId: string;
}

export interface PeakDetection {
  wavelength: number;
  intensity: number;
  snr: number;
  element: string;
}

const NIST_LINES = [
  { wl: 279.55, el: 'Mg II' },
  { wl: 288.16, el: 'Si I' },
  { wl: 334.94, el: 'Ti II' },
  { wl: 393.37, el: 'Ca II' },
  { wl: 396.15, el: 'Al I' },
  { wl: 404.58, el: 'Fe I' },
  { wl: 777.40, el: 'O I' }
];

export function generateMockSpectrum(measurementId: string = 'm_001'): { data: SpectralData[], peaks: PeakDetection[] } {
  const data: SpectralData[] = [];
  const minWavelength = 164.35;
  const maxWavelength = 878.26;
  const numChannels = 2049;
  const step = (maxWavelength - minWavelength) / (numChannels - 1);

  // Background continuum (thermal/solar radiation)
  const bgBaseline = 1000;
  
  // Specific simulated peaks to match NIST lines closely (with some instrument drift)
  const syntheticPeaks = [
    { wl: 279.71, amp: 684, width: 0.2 }, // Mg II matched
    { wl: 288.30, amp: 210, width: 0.2 }, // Si I matched
    { wl: 335.10, amp: 145, width: 0.2 }, // Ti II matched
    { wl: 393.55, amp: 580, width: 0.2 }, // Ca II matched
    { wl: 396.34, amp: 490, width: 0.2 }, // Al I matched
    { wl: 404.75, amp: 205, width: 0.2 }, // Fe I matched
    { wl: 777.62, amp: 240, width: 0.3 }  // O I matched
  ];

  for (let i = 0; i < numChannels; i++) {
    const wavelength = minWavelength + i * step;
    
    // Independent poisson-like noise for background and plasma
    const bgNoise = (Math.random() - 0.5) * 80;
    const plasmaNoise = (Math.random() - 0.5) * 80;
    
    const rawBackground = bgBaseline + bgNoise;
    let plasmaEmission = 0;
    
    // Add peak emissions to plasma
    for (const peak of syntheticPeaks) {
      plasmaEmission += peak.amp * Math.exp(-Math.pow(wavelength - peak.wl, 2) / (2 * Math.pow(peak.width, 2)));
    }
    
    const rawPlasma = bgBaseline + plasmaEmission + plasmaNoise;

    // ALGORITHM: Background Subtraction and Negative-Value Clamping
    // I_clean(lambda) = max(0, I_plasma(lambda) - I_bg(lambda))
    const cleanedIntensity = Math.max(0, rawPlasma - rawBackground);

    data.push({
      wavelength: Number(wavelength.toFixed(2)),
      rawPlasma: Number(Math.round(rawPlasma)),
      rawBackground: Number(Math.round(rawBackground)),
      intensity: Number(Math.round(cleanedIntensity)),
      measurementId
    });
  }

  // ALGORITHM: SNR Thresholding and Peak Detection
  // Using a local window of 50 channels where SNR > 3 sigma local
  const peakDetections: PeakDetection[] = [];
  const windowSize = 50;
  
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
    
    // Check if it's a local maximum
    if (currentPoint.intensity > data[i - 1].intensity && currentPoint.intensity > data[i + 1].intensity) {
      const snr = currentPoint.intensity / localSigma;
      if (snr > 3) {
        // Find best match in NIST database (if within 0.5 nm)
        let bestMatch = null;
        let minDiff = 0.5;
        for (const nist of NIST_LINES) {
          const diff = Math.abs(currentPoint.wavelength - nist.wl);
          if (diff < minDiff) {
            minDiff = diff;
            bestMatch = nist.el;
          }
        }
        
        if (bestMatch && currentPoint.intensity > 50) {
            // we found a valid peak
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

  // Filter overlapping detections
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

export const mockDataService = {
  fetchSpectrum: (measurementId: string): Promise<{ data: SpectralData[], peaks: PeakDetection[] }> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(generateMockSpectrum(measurementId));
      }, 400);
    });
  }
};
