import { useEffect, useState, useMemo } from 'react';
import { apiService, type SpectralDataPoint } from '../../services/apiService';

interface NistValidationPanelProps {
  lambdaMin: number;
  lambdaMax: number;
  measurementData: Map<string, SpectralDataPoint[]>;
  element: string;
  activeMeasurementIds: Set<string>;
}

interface ValidationResult {
  nistWavelength: number;
  element: string;
  ionStage: string;
  relIntensity: number;
  measuredWavelength: number | null;
  intensity: number | null;
  offset: number | null;
  status: 'Validated' | 'Tentative' | 'No Peak';
  measurementLabel: string;
}

export default function NistValidationPanel({
  lambdaMin,
  lambdaMax,
  measurementData,
  element,
  activeMeasurementIds,
}: NistValidationPanelProps) {
  const [nistLines, setNistLines] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch NIST lines for the full range and element
  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    apiService.fetchNistLines(element || undefined, 164.35, 878.26)
      .then((lines) => {
        if (isMounted) {
          setNistLines(lines);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        console.error('[NistValidationPanel] Fetch lines failed:', err);
        if (isMounted) setIsLoading(false);
      });

    return () => { isMounted = false; };
  }, [element]);

  // Perform peak fitting / alignment calculations
  const validationResults = useMemo((): ValidationResult[] => {
    const results: ValidationResult[] = [];
    if (nistLines.length === 0 || measurementData.size === 0) return [];

    // Filter NIST reference lines to the current viewport client-side
    const viewportLines = nistLines.filter(
      (line) => line.wavelength_nm >= lambdaMin && line.wavelength_nm <= lambdaMax
    );

    Array.from(measurementData.entries()).forEach(([id, points]) => {
      if (!activeMeasurementIds.has(id)) return;
      if (points.length === 0) return;

      const label = `Measurement #${id.slice(0, 4)}…`;

      viewportLines.forEach((line) => {
        const targetWl = line.wavelength_nm;
        if (!targetWl) return;

        // Search window: +/- 0.5 nm
        const windowSize = 0.5;
        const candidates = points.filter(
          (p) => Math.abs(p.wavelength - targetWl) <= windowSize
        );

        if (candidates.length === 0) {
          results.push({
            nistWavelength: targetWl,
            element: line.element,
            ionStage: line.ionization_stage || 'I',
            relIntensity: line.relative_intensity || 0,
            measuredWavelength: null,
            intensity: null,
            offset: null,
            status: 'No Peak',
            measurementLabel: label,
          });
          return;
        }

        // Find peak (local max intensity) in candidates
        let peak = candidates[0];
        for (let i = 1; i < candidates.length; i++) {
          if (candidates[i].intensity > peak.intensity) {
            peak = candidates[i];
          }
        }

        // Calculate offset
        const offset = peak.wavelength - targetWl;
        const absOffset = Math.abs(offset);
        
        let status: 'Validated' | 'Tentative' = 'Tentative';
        // Validation criterion: offset < 0.2 nm
        if (absOffset < 0.20) {
          status = 'Validated';
        }

        results.push({
          nistWavelength: targetWl,
          element: line.element,
          ionStage: line.ionization_stage || 'I',
          relIntensity: line.relative_intensity || 0,
          measuredWavelength: peak.wavelength,
          intensity: peak.intensity,
          offset: offset,
          status: status,
          measurementLabel: label,
        });
      });
    });

    // Sort by NIST wavelength ascending
    return results.sort((a, b) => a.nistWavelength - b.nistWavelength);
  }, [nistLines, measurementData, activeMeasurementIds]);

  return (
    <div className="bg-white p-6 border border-solid border-gray-200 rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-solid border-gray-100">
        <div>
          <h3 className="text-[15px] font-sans font-bold text-gray-800">
            NIST Validation & Peak Alignment
          </h3>
          <p className="text-[11px] font-sans text-gray-400 mt-0.5">
            Compares theoretical emission lines against Gaussian-fitted/local intensity peaks in current viewport
          </p>
        </div>
        <span className="text-[12px] font-sans font-medium text-gray-400">Units: nm / counts</span>
      </div>

      {isLoading ? (
        <div className="py-12 flex justify-center items-center">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2" />
          <span className="text-[12px] font-sans text-gray-500">Calculating peak alignment…</span>
        </div>
      ) : validationResults.length === 0 ? (
        <div className="py-8 text-center text-gray-400 italic text-[12px] font-sans">
          No active measurements or reference lines in current viewport range.
        </div>
      ) : (
        <div className="w-full overflow-x-auto border border-gray-100 rounded-md bg-white">
          <table className="w-full text-left text-[12px] border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                {['Measurement', 'Element', 'Ion', 'NIST λ (nm)', 'Measured λ (nm)', 'Offset (nm)', 'Intensity (cts)', 'Status'].map((h) => (
                  <th key={h} className="py-3 px-5 uppercase tracking-widest text-[9px] font-black text-gray-600">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="font-mono text-gray-700">
              {validationResults.map((res, idx) => {
                const isValid = res.status === 'Validated';
                const isNoPeak = res.status === 'No Peak';
                return (
                  <tr key={idx} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
                    <td className="py-3 px-5 font-sans font-semibold text-gray-600">{res.measurementLabel}</td>
                    <td className="py-3 px-5 font-sans font-bold text-gray-800">{res.element}</td>
                    <td className="py-3 px-5 text-gray-400 font-sans">{res.ionStage}</td>
                    <td className="py-3 px-5 font-bold text-blue-600">{res.nistWavelength.toFixed(3)}</td>
                    <td className="py-3 px-5">
                      {res.measuredWavelength ? (
                        <span className="font-bold">{res.measuredWavelength.toFixed(3)}</span>
                      ) : (
                        <span className="text-gray-400 italic font-sans">not resolved</span>
                      )}
                    </td>
                    <td className="py-3 px-5">
                      {res.offset !== null ? (
                        <span className={Math.abs(res.offset) < 0.20 ? 'text-emerald-600' : 'text-amber-600'}>
                          {res.offset > 0 ? '+' : ''}{res.offset.toFixed(3)}
                        </span>
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="py-3 px-5">
                      {res.intensity ? res.intensity.toFixed(1) : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="py-3 px-5 font-sans">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider ${
                          isValid
                            ? 'bg-emerald-50 text-emerald-700 border border-solid border-emerald-200'
                            : isNoPeak
                            ? 'bg-gray-100 text-gray-400'
                            : 'bg-amber-50 text-amber-700 border border-solid border-amber-200'
                        }`}
                      >
                        {res.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
