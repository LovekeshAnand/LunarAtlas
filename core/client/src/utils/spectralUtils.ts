/**
 * @fileoverview Spectral Analysis Utilities for Chandrayaan-3 LIBS Data.
 * Contains elemental emission lines (wavelengths in nm) derived from NIST database.
 */

export interface ElementalPeak {
  wavelength: number;
  label: string;
  intensity?: 'high' | 'medium' | 'low';
}

/** 
 * Map of common elements to their primary LIBS emission lines (nm).
 */
export const ELEMENT_PEAKS: Record<string, ElementalPeak[]> = {
  'Fe': [
    { wavelength: 238.2, label: 'Fe II' },
    { wavelength: 239.5, label: 'Fe II' },
    { wavelength: 248.3, label: 'Fe I' },
    { wavelength: 259.9, label: 'Fe II' },
    { wavelength: 373.5, label: 'Fe I' },
  ],
  'Mg': [
    { wavelength: 279.5, label: 'Mg II' },
    { wavelength: 280.2, label: 'Mg II' },
    { wavelength: 285.2, label: 'Mg I' },
  ],
  'Si': [
    { wavelength: 251.6, label: 'Si I' },
    { wavelength: 288.2, label: 'Si I' },
    { wavelength: 390.5, label: 'Si I' },
  ],
  'Al': [
    { wavelength: 308.2, label: 'Al I' },
    { wavelength: 309.3, label: 'Al I' },
    { wavelength: 394.4, label: 'Al I' },
    { wavelength: 396.1, label: 'Al I' },
  ],
  'Ca': [
    { wavelength: 393.3, label: 'Ca II' },
    { wavelength: 396.8, label: 'Ca II' },
    { wavelength: 422.7, label: 'Ca I' },
  ],
  'Ti': [
    { wavelength: 334.9, label: 'Ti I' },
    { wavelength: 336.1, label: 'Ti I' },
    { wavelength: 337.2, label: 'Ti I' },
    { wavelength: 498.1, label: 'Ti I' },
  ],
  'O': [
    { wavelength: 777.2, label: 'O I' },
    { wavelength: 777.4, label: 'O I' },
    { wavelength: 777.5, label: 'O I' },
  ],
  'Na': [
    { wavelength: 589.0, label: 'Na I' },
    { wavelength: 589.6, label: 'Na I' },
  ],
  'H₂O': [
    { wavelength: 656.3, label: 'Hα (H I)' },
  ],
};

/**
 * Returns all peaks for a given element key.
 */
export function getPeaksForElement(element: string): ElementalPeak[] {
  return ELEMENT_PEAKS[element] || [];
}
