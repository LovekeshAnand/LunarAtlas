// ─────────────────────────────────────────────────────────────────
// mockData.ts  –  Simulates CSV-loaded observation records
// All values loaded in full; no filtering applied at source level.
// Replace parseCSV() with a real fetch + Papa.parse() when ready.
// ─────────────────────────────────────────────────────────────────

export interface ObservationRecord {
  date: string;
  time: string;
  measurementType: string;
}

/** Raw simulated CSV dataset – 9 observation dates, multiple passes per date */
export const mockObservationData: ObservationRecord[] = [
  // 2024-03-01
  { date: '2024-03-01', time: '00:12:45', measurementType: 'REFLECTANCE' },
  { date: '2024-03-01', time: '02:34:10', measurementType: 'RADIANCE' },
  { date: '2024-03-01', time: '06:18:22', measurementType: 'REFLECTANCE' },

  // 2024-03-15
  { date: '2024-03-15', time: '01:05:33', measurementType: 'CALIBRATED_RADIANCE' },
  { date: '2024-03-15', time: '03:47:09', measurementType: 'REFLECTANCE' },
  { date: '2024-03-15', time: '08:22:54', measurementType: 'EMISSION' },

  // 2024-04-02
  { date: '2024-04-02', time: '00:30:00', measurementType: 'RADIANCE' },
  { date: '2024-04-02', time: '04:15:17', measurementType: 'REFLECTANCE' },
  { date: '2024-04-02', time: '09:00:45', measurementType: 'ABSORPTION' },

  // 2024-04-18
  { date: '2024-04-18', time: '02:10:55', measurementType: 'REFLECTANCE' },
  { date: '2024-04-18', time: '05:44:30', measurementType: 'CALIBRATED_RADIANCE' },
  { date: '2024-04-18', time: '10:30:11', measurementType: 'RADIANCE' },

  // 2024-05-06
  { date: '2024-05-06', time: '00:58:11', measurementType: 'EMISSION' },
  { date: '2024-05-06', time: '03:20:48', measurementType: 'RADIANCE' },
  { date: '2024-05-06', time: '07:35:22', measurementType: 'REFLECTANCE' },
  { date: '2024-05-06', time: '11:01:09', measurementType: 'ABSORPTION' },

  // 2024-05-20
  { date: '2024-05-20', time: '01:22:44', measurementType: 'REFLECTANCE' },
  { date: '2024-05-20', time: '04:55:18', measurementType: 'RADIANCE' },
  { date: '2024-05-20', time: '09:30:00', measurementType: 'CALIBRATED_RADIANCE' },

  // 2024-06-04
  { date: '2024-06-04', time: '00:14:55', measurementType: 'ABSORPTION' },
  { date: '2024-06-04', time: '03:48:20', measurementType: 'REFLECTANCE' },
  { date: '2024-06-04', time: '08:05:37', measurementType: 'EMISSION' },

  // 2024-06-19
  { date: '2024-06-19', time: '02:33:10', measurementType: 'RADIANCE' },
  { date: '2024-06-19', time: '06:12:44', measurementType: 'REFLECTANCE' },
  { date: '2024-06-19', time: '10:45:29', measurementType: 'CALIBRATED_RADIANCE' },

  // 2024-07-03
  { date: '2024-07-03', time: '01:05:00', measurementType: 'REFLECTANCE' },
  { date: '2024-07-03', time: '04:30:15', measurementType: 'RADIANCE' },
  { date: '2024-07-03', time: '07:55:42', measurementType: 'EMISSION' },
  { date: '2024-07-03', time: '12:20:08', measurementType: 'ABSORPTION' },
];

/** All unique dates from the dataset – no filtering */
export function getUniqueDates(data: ObservationRecord[]): string[] {
  return [...new Set(data.map((r) => r.date))].sort();
}

/** All timestamps recorded on a specific date */
export function getTimesForDate(data: ObservationRecord[], date: string): string[] {
  return [...new Set(data.filter((r) => r.date === date).map((r) => r.time))].sort();
}

/** All unique measurement types across the dataset */
export function getUniqueMeasurementTypes(data: ObservationRecord[]): string[] {
  return [...new Set(data.map((r) => r.measurementType))].sort();
}

/** Elements available for elemental analysis */
export const ELEMENTS = ['Fe', 'Mg', 'Si', 'Al', 'Ca', 'Ti', 'O', 'Na', 'H₂O'];
