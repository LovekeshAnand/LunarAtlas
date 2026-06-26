import { useState, useEffect } from 'react';

// Coordinates for LTTB demonstration
const START_POINT = { x: 30, y: 220 };
const BUCKET_1 = [
  { x: 75, y: 200, label: 'B1a' },
  { x: 110, y: 215, label: 'B1b' },
  { x: 145, y: 160, label: 'B1c' }
];
const BUCKET_2 = [
  { x: 180, y: 180, label: 'B2a' },
  { x: 215, y: 60,  label: 'B2b (Peak)' },
  { x: 250, y: 150, label: 'B2c' }
];
const BUCKET_3 = [
  { x: 285, y: 140, label: 'B3a' },
  { x: 320, y: 200, label: 'B3b' },
  { x: 355, y: 210, label: 'B3c' }
];
const BUCKET_4 = [
  { x: 390, y: 225, label: 'B4a' },
  { x: 425, y: 195, label: 'B4b' },
  { x: 460, y: 220, label: 'B4c' }
];
const END_POINT = { x: 490, y: 225 };

// Average centroids for next buckets
const CENTROID_2 = { x: 215, y: 130 }; // Average of BUCKET_2
const CENTROID_3 = { x: 320, y: 183 }; // Average of BUCKET_3
const CENTROID_4 = { x: 425, y: 213 }; // Average of BUCKET_4
const CENTROID_END = END_POINT;

// Selected points based on maximum triangle area
const SELECTED_1 = BUCKET_1[1]; // B1b
const SELECTED_2 = BUCKET_2[1]; // B2b (Peak)
const SELECTED_3 = BUCKET_3[0]; // B3a
const SELECTED_4 = BUCKET_4[1]; // B4b

export default function LttbVisualizer() {
  const [step, setStep] = useState(0);
  const [candidateIdx, setCandidateIdx] = useState(0);

  // Animation cycle loop
  useEffect(() => {
    const timer = setInterval(() => {
      setStep((prev) => {
        if (prev === 2 || prev === 3 || prev === 4 || prev === 5) {
          setCandidateIdx((cIdx) => {
            if (cIdx < 2) return cIdx + 1;
            return 0;
          });
          if (candidateIdx === 2) {
            return prev + 1;
          }
          return prev;
        }

        if (prev >= 7) {
          return 0; // Loop back
        }
        return prev + 1;
      });
    }, 2000);

    return () => clearInterval(timer);
  }, [candidateIdx]);

  // Status message based on current step
  const getStatusMessage = () => {
    switch (step) {
      case 0:
        return 'Raw Spectrum: High-frequency data points collected from the sensor.';
      case 1:
        return 'Bucketing: Divide the dataset into equal vertical bins (excluding start/end points).';
      case 2:
        return `Evaluating Bucket 1: Connecting A0 to candidate in Bucket 1 and Centroid of Bucket 2. Largest triangle selects ${SELECTED_1.label}.`;
      case 3:
        return `Evaluating Bucket 2: Connecting B1 to candidate in Bucket 2 and Centroid of Bucket 3. Peak point ${SELECTED_2.label} maximizes the area.`;
      case 4:
        return `Evaluating Bucket 3: Connecting B2 (Peak) to candidate in Bucket 3 and Centroid of Bucket 4. Selects ${SELECTED_3.label}.`;
      case 5:
        return `Evaluating Bucket 4: Connecting B3 to candidate in Bucket 4 and the Final Endpoint. Selects ${SELECTED_4.label}.`;
      case 6:
        return 'Downsampled Output: connects all selected nodes into a simplified, noise-free representation.';
      case 7:
        return 'LTTB Completed: 15 raw spectral channels successfully reduced to 6 points, perfectly preserving the peak intensity!';
      default:
        return '';
    }
  };

  // Helper to calculate triangle points based on current step
  const getTrianglePoints = () => {
    let pA = START_POINT;
    let candidates = BUCKET_1;
    let pC = CENTROID_2;

    if (step === 2) {
      pA = START_POINT;
      candidates = BUCKET_1;
      pC = CENTROID_2;
    } else if (step === 3) {
      pA = SELECTED_1;
      candidates = BUCKET_2;
      pC = CENTROID_3;
    } else if (step === 4) {
      pA = SELECTED_2;
      candidates = BUCKET_3;
      pC = CENTROID_4;
    } else if (step === 5) {
      pA = SELECTED_3;
      candidates = BUCKET_4;
      pC = CENTROID_END;
    } else {
      return null;
    }

    const pB = candidates[candidateIdx];
    return `${pA.x},${pA.y} ${pB.x},${pB.y} ${pC.x},${pC.y}`;
  };

  const currentTriangle = getTrianglePoints();

  // Selected points up to current step
  const getDownsampledPath = () => {
    const points = [START_POINT];
    if (step >= 3) points.push(SELECTED_1);
    if (step >= 4) points.push(SELECTED_2);
    if (step >= 5) points.push(SELECTED_3);
    if (step >= 6) {
      points.push(SELECTED_4);
      points.push(END_POINT);
    }
    return points.map(p => `${p.x},${p.y}`).join(' ');
  };

  return (
    <div className="w-full flex flex-col items-center select-none bg-transparent">
      
      {/* SVG Canvas Area - Transparent, Borderless */}
      <div className="w-full relative overflow-hidden flex justify-center py-2">
        <svg viewBox="0 0 520 270" className="w-full h-auto max-w-[520px] overflow-visible">
          {/* Vertical Grid lines for Buckets (Steps >= 1) */}
          {step >= 1 && (
            <>
              {/* Boundary 1 */}
              <line x1="52.5" y1="10" x2="52.5" y2="250" stroke="#888" strokeWidth="1" strokeDasharray="4,4" className="opacity-30 dark:opacity-40" />
              {/* Boundary 2 */}
              <line x1="162.5" y1="10" x2="162.5" y2="250" stroke="#888" strokeWidth="1" strokeDasharray="4,4" className="opacity-30 dark:opacity-40" />
              {/* Boundary 3 */}
              <line x1="267.5" y1="10" x2="267.5" y2="250" stroke="#888" strokeWidth="1" strokeDasharray="4,4" className="opacity-30 dark:opacity-40" />
              {/* Boundary 4 */}
              <line x1="372.5" y1="10" x2="372.5" y2="250" stroke="#888" strokeWidth="1" strokeDasharray="4,4" className="opacity-30 dark:opacity-40" />
              {/* Boundary 5 */}
              <line x1="477.5" y1="10" x2="477.5" y2="250" stroke="#888" strokeWidth="1" strokeDasharray="4,4" className="opacity-30 dark:opacity-40" />
            </>
          )}

          {/* Bucket Labels */}
          {step >= 1 && (
            <>
              <text x="107.5" y="25" textAnchor="middle" className="text-[8px] font-bold tracking-widest fill-neutral-400 dark:fill-neutral-600">BUCKET 1</text>
              <text x="215" y="25" textAnchor="middle" className="text-[8px] font-bold tracking-widest fill-neutral-400 dark:fill-neutral-600">BUCKET 2</text>
              <text x="320" y="25" textAnchor="middle" className="text-[8px] font-bold tracking-widest fill-neutral-400 dark:fill-neutral-600">BUCKET 3</text>
              <text x="425" y="25" textAnchor="middle" className="text-[8px] font-bold tracking-widest fill-neutral-400 dark:fill-neutral-600">BUCKET 4</text>
            </>
          )}

          {/* Shaded Triangle (Steps 2 to 5) */}
          {currentTriangle && (
            <polygon
              points={currentTriangle}
              fill="rgba(0,0,0,0.04)"
              stroke="rgba(0,0,0,0.25)"
              className="dark:fill-white/[0.03] dark:stroke-white/20"
              strokeWidth="1.5"
              strokeDasharray="4,4"
            />
          )}

          {/* Centroid Labels & Helpers */}
          {(step === 2) && (
            <>
              <circle cx={CENTROID_2.x} cy={CENTROID_2.y} r="5" fill="none" stroke="#888" strokeWidth="2" className="animate-pulse" />
              <circle cx={CENTROID_2.x} cy={CENTROID_2.y} r="3" className="fill-neutral-400" />
              <text x={CENTROID_2.x + 8} y={CENTROID_2.y + 3} className="text-[8px] font-mono font-bold fill-neutral-500 dark:fill-neutral-500">C2 Centroid</text>
            </>
          )}
          {(step === 3) && (
            <>
              <circle cx={CENTROID_3.x} cy={CENTROID_3.y} r="5" fill="none" stroke="#888" strokeWidth="2" className="animate-pulse" />
              <circle cx={CENTROID_3.x} cy={CENTROID_3.y} r="3" className="fill-neutral-400" />
              <text x={CENTROID_3.x + 8} y={CENTROID_3.y + 3} className="text-[8px] font-mono font-bold fill-neutral-500 dark:fill-neutral-500">C3 Centroid</text>
            </>
          )}
          {(step === 4) && (
            <>
              <circle cx={CENTROID_4.x} cy={CENTROID_4.y} r="5" fill="none" stroke="#888" strokeWidth="2" className="animate-pulse" />
              <circle cx={CENTROID_4.x} cy={CENTROID_4.y} r="3" className="fill-neutral-400" />
              <text x={CENTROID_4.x + 8} y={CENTROID_4.y + 3} className="text-[8px] font-mono font-bold fill-neutral-500 dark:fill-neutral-500">C4 Centroid</text>
            </>
          )}

          {/* Raw Spectral Line Connectors (faded) */}
          <polyline
            points={`${START_POINT.x},${START_POINT.y} ${BUCKET_1.map(p => `${p.x},${p.y}`).join(' ')} ${BUCKET_2.map(p => `${p.x},${p.y}`).join(' ')} ${BUCKET_3.map(p => `${p.x},${p.y}`).join(' ')} ${BUCKET_4.map(p => `${p.x},${p.y}`).join(' ')} ${END_POINT.x},${END_POINT.y}`}
            fill="none"
            stroke="#888"
            strokeWidth="1"
            className="opacity-20 dark:opacity-30"
          />

          {/* Thicker Downsampled Line Path */}
          {step >= 2 && (
            <polyline
              points={getDownsampledPath()}
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              className="text-neutral-900 dark:text-neutral-200"
            />
          )}

          {/* Draw Raw Data Circles */}
          {/* Start Point */}
          <circle cx={START_POINT.x} cy={START_POINT.y} r="4.5" className="fill-neutral-900 dark:fill-white" />
          <text x={START_POINT.x} y={START_POINT.y - 12} textAnchor="middle" className="text-[8.5px] font-mono font-bold fill-neutral-800 dark:fill-neutral-300">A0</text>

          {/* Bucket 1 points */}
          {BUCKET_1.map((p, idx) => {
            const isSelected = step >= 3 && p === SELECTED_1;
            const isCurrent = step === 2 && idx === candidateIdx;
            return (
              <g key={p.label}>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={isSelected ? 5 : (isCurrent ? 4.5 : 2.5)}
                  className={`${
                    isSelected ? 'fill-neutral-900 dark:fill-white' : 
                    isCurrent ? 'fill-neutral-700 dark:fill-neutral-300' :
                    'fill-neutral-300 dark:fill-neutral-700'
                  }`}
                />
                {(isSelected || isCurrent) && (
                  <text x={p.x} y={p.y - 12} textAnchor="middle" className="text-[8.5px] font-mono font-bold fill-neutral-800 dark:fill-neutral-300">
                    {p.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* Bucket 2 points */}
          {BUCKET_2.map((p, idx) => {
            const isSelected = step >= 4 && p === SELECTED_2;
            const isCurrent = step === 3 && idx === candidateIdx;
            return (
              <g key={p.label}>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={isSelected ? 5 : (isCurrent ? 4.5 : 2.5)}
                  className={`${
                    isSelected ? 'fill-neutral-900 dark:fill-white' : 
                    isCurrent ? 'fill-neutral-700 dark:fill-neutral-300' :
                    'fill-neutral-300 dark:fill-neutral-700'
                  }`}
                />
                {(isSelected || isCurrent) && (
                  <text x={p.x} y={p.y - 12} textAnchor="middle" className="text-[8.5px] font-mono font-bold fill-neutral-800 dark:fill-neutral-300">
                    {p.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* Bucket 3 points */}
          {BUCKET_3.map((p, idx) => {
            const isSelected = step >= 5 && p === SELECTED_3;
            const isCurrent = step === 4 && idx === candidateIdx;
            return (
              <g key={p.label}>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={isSelected ? 5 : (isCurrent ? 4.5 : 2.5)}
                  className={`${
                    isSelected ? 'fill-neutral-900 dark:fill-white' : 
                    isCurrent ? 'fill-neutral-700 dark:fill-neutral-300' :
                    'fill-neutral-300 dark:fill-neutral-700'
                  }`}
                />
                {(isSelected || isCurrent) && (
                  <text x={p.x} y={p.y - 12} textAnchor="middle" className="text-[8.5px] font-mono font-bold fill-neutral-800 dark:fill-neutral-300">
                    {p.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* Bucket 4 points */}
          {BUCKET_4.map((p, idx) => {
            const isSelected = step >= 6 && p === SELECTED_4;
            const isCurrent = step === 5 && idx === candidateIdx;
            return (
              <g key={p.label}>
                <circle
                  cx={p.x}
                  cy={p.y}
                  r={isSelected ? 5 : (isCurrent ? 4.5 : 2.5)}
                  className={`${
                    isSelected ? 'fill-neutral-900 dark:fill-white' : 
                    isCurrent ? 'fill-neutral-700 dark:fill-neutral-300' :
                    'fill-neutral-300 dark:fill-neutral-700'
                  }`}
                />
                {(isSelected || isCurrent) && (
                  <text x={p.x} y={p.y - 12} textAnchor="middle" className="text-[8.5px] font-mono font-bold fill-neutral-800 dark:fill-neutral-300">
                    {p.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* End Point */}
          <circle cx={END_POINT.x} cy={END_POINT.y} r="4.5" className="fill-neutral-900 dark:fill-white" />
          <text x={END_POINT.x} y={END_POINT.y - 12} textAnchor="middle" className="text-[8.5px] font-mono font-bold fill-neutral-800 dark:fill-neutral-300">An</text>
        </svg>
      </div>

      {/* Description Text Box - Borderless, simple text */}
      <div className="w-full mt-4 text-center">
        <p className="text-[13px] leading-relaxed text-neutral-700 dark:text-neutral-400 font-medium m-0 min-h-[38px] transition-all">
          {getStatusMessage()}
        </p>
      </div>

      {/* Step Progress indicators - Sleek HUD style */}
      <div className="w-full flex justify-between items-center mt-4 px-1 max-w-[480px]">
        <div className="flex gap-2">
          {[0, 1, 2, 3, 4, 5, 6, 7].map((s) => (
            <div
              key={s}
              className={`h-1 rounded-full transition-all duration-300 ${
                s === step
                  ? 'w-6 bg-neutral-900 dark:bg-white'
                  : 'w-2 bg-neutral-200 dark:bg-neutral-800'
              }`}
            />
          ))}
        </div>
        <span className="text-[8.5px] font-bold text-neutral-500 dark:text-neutral-500 tracking-wider uppercase font-mono">
          {step === 6 || step === 7 ? 'Downsampling Done' : 'Processing...'}
        </span>
      </div>

    </div>
  );
}
