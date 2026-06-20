/**
 * @fileoverview Spectral Analysis Utilities for Chandrayaan-3 LIBS Data.
 *
 * Single source of truth for elemental emission lines (wavelengths in nm)
 * derived from NIST Atomic Spectra Database (ASD).
 *
 * Both the graph overlay (MultiSpectralGraph) and the downsampling target list
 * (SpectralAnalyzerPage) import from this file to stay in sync.
 *
 * Total peaks: 32
 */

export interface ElementalPeak {
  wavelength: number;
  label: string;
  intensity?: 'high' | 'medium' | 'low';
}

/**
 * Map of common lunar-surface elements to their primary LIBS emission lines (nm).
 *
 * Wavelengths are given to 3 decimal places matching NIST ASD values.
 * Labels follow the convention "Element IonStage" (e.g. "Fe I", "Ca II").
 *
 * Peak count per element:
 *   Fe: 4  |  Mg: 3  |  Si: 3  |  Al: 4  |  Ca: 6
 *   Ti: 4  |  O:  4  |  Na: 2  |  H₂O: 2
 *   ─────────────────────────────────────────────
 *   Total:  32
 */
export const ELEMENT_PEAKS: Record<string, ElementalPeak[]> = {
  'Fe': [
    { wavelength: 373.486, label: 'Fe I',  intensity: 'high'   },
    { wavelength: 385.991, label: 'Fe I',  intensity: 'medium' },
    { wavelength: 404.581, label: 'Fe I',  intensity: 'medium' },
    { wavelength: 438.355, label: 'Fe I',  intensity: 'medium' },
  ],
  'Mg': [
    { wavelength: 279.553, label: 'Mg II', intensity: 'high'   },
    { wavelength: 280.271, label: 'Mg II', intensity: 'high'   },
    { wavelength: 285.213, label: 'Mg I',  intensity: 'high'   },
  ],
  'Si': [
    { wavelength: 288.158, label: 'Si I',  intensity: 'high'   },
    { wavelength: 390.553, label: 'Si I',  intensity: 'medium' },
    { wavelength: 413.089, label: 'Si I',  intensity: 'medium' },
  ],
  'Al': [
    { wavelength: 308.215, label: 'Al I',  intensity: 'high'   },
    { wavelength: 309.271, label: 'Al I',  intensity: 'high'   },
    { wavelength: 394.401, label: 'Al I',  intensity: 'high'   },
    { wavelength: 396.152, label: 'Al I',  intensity: 'high'   },
  ],
  'Ca': [
    { wavelength: 393.366, label: 'Ca II', intensity: 'high'   },
    { wavelength: 396.847, label: 'Ca II', intensity: 'high'   },
    { wavelength: 422.673, label: 'Ca I',  intensity: 'high'   },
    { wavelength: 849.802, label: 'Ca II', intensity: 'medium' },
    { wavelength: 854.209, label: 'Ca II', intensity: 'medium' },
    { wavelength: 866.214, label: 'Ca II', intensity: 'medium' },
  ],
  'Ti': [
    { wavelength: 334.941, label: 'Ti II', intensity: 'high'   },
    { wavelength: 336.121, label: 'Ti I',  intensity: 'medium' },
    { wavelength: 337.280, label: 'Ti I',  intensity: 'medium' },
    { wavelength: 368.520, label: 'Ti I',  intensity: 'medium' },
  ],
  'O': [
    { wavelength: 777.194, label: 'O I',   intensity: 'high'   },
    { wavelength: 777.417, label: 'O I',   intensity: 'high'   },
    { wavelength: 777.539, label: 'O I',   intensity: 'high'   },
    { wavelength: 844.636, label: 'O I',   intensity: 'medium' },
  ],
  'Na': [
    { wavelength: 588.995, label: 'Na I',  intensity: 'high'   },
    { wavelength: 589.592, label: 'Na I',  intensity: 'high'   },
  ],
  'H₂O': [
    { wavelength: 486.133, label: 'Hβ (H I)', intensity: 'medium' },
    { wavelength: 656.281, label: 'Hα (H I)', intensity: 'high'   },
  ],
};

/**
 * Flat array of all target wavelengths (numbers only).
 * Useful for downsampling peak-preservation without needing the full objects.
 */
export const ALL_PEAK_WAVELENGTHS: number[] = Object.values(ELEMENT_PEAKS)
  .flat()
  .map((p) => p.wavelength);

/**
 * Returns all peaks for a given element key.
 */
export function getPeaksForElement(element: string): ElementalPeak[] {
  return ELEMENT_PEAKS[element] || [];
}

/**
 * Returns all peak wavelengths (numbers) for a given element key.
 */
export function getWavelengthsForElement(element: string): number[] {
  return (ELEMENT_PEAKS[element] || []).map((p) => p.wavelength);
}
