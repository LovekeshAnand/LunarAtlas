/**
 * @fileoverview Live API Service for LunarAtlas.
 *
 * Centralises all HTTP communication with the FastAPI backend.
 * Provides typed methods for:
 *   - Authentication (register, login, session validation)
 *   - Spectral data retrieval with M4 downsampling
 *   - NIST reference line queries
 *   - Data export (CSV / JSON)
 *   - Observation and measurement hierarchy navigation
 *
 * All methods return typed Promises and throw on HTTP errors.
 * The base URL is configured via `VITE_API_BASE_URL` env variable,
 * with a fallback to `/api/v1` for same-origin deployments.
 */

const API_BASE =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') || '/api/v1';

/** Measurement metadata from /measurements */
export interface MeasurementInfo {
  measurement_id: string;
  file_info_id: string;
  measurement_index: number;
  time_utc: string | null;
  measurement_count: number | null;
  operation_mode: string | null;
  measurement_type: string | null;
  is_background: boolean;
  integration_time_us: number | null;
  number_of_pulses: number | null;
  laser_energy_v: number | null;
}

interface SpectralApiPoint {
  wavelength_nm: number;
  intensity: number;
  raw_plasma: number;
}

interface SpectrumResponse {
  mode: 'downsampled' | 'raw' | 'empty';
  measurement_id: string;
  lambda_min: number;
  lambda_max: number;
  zoom_level: number;
  z_max: number | null;
  data: SpectralApiPoint[];
  metadata: {
    original_points?: number;
    n_buckets?: number | null;
    reduction_factor?: number | null;
    b_final?: number | null;
  };
  cached: boolean;
  query_time_ms: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  database: boolean;
  redis: boolean;
  timestamp: string;
}

/**
 * A single spectral data point as consumed by the frontend graph.
 *
 * This is the unified shape used across the rendering pipeline:
 * API response → apiService mapping → useDownsampling hook → SpectralGraph.
 *
 * @property wavelength    - Wavelength in nm (X-axis).
 * @property intensity     - Cleaned (L2) intensity in counts (primary Y-axis).
 * @property rawPlasma     - Uncleaned plasma counts (for L1 / overlay mode).
 * @property rawBackground - Background counts (for L1 mode).
 * @property measurementId - Foreign key linking back to the measurement record.
 */
export interface SpectralDataPoint {
  wavelength: number;
  intensity: number;
  rawPlasma: number;
  rawBackground: number;
  measurementId: string;
}

export interface SpectrumMeta {
  mode: SpectrumResponse['mode'];
  z_max: number | null;
  original_points: number;
  n_buckets: number | null;
  reduction_factor: number | null;
  b_final: number | null;
}

export const apiService = {
  // === Helpers ===
  getAuthHeader() {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  },

  // === Authentication & User ===
  async register(data: { email: string; institution: string; interest: string; password: string }) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json().catch(()=>({}));
        throw new Error(err.detail || `Registration failed: ${res.status}`);
    }
    return res.json();
  },

  async login(email: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params,
    });
    if (!res.ok) {
        const err = await res.json().catch(()=>({}));
        throw new Error(err.detail || `Login failed: ${res.status}`);
    }
    return res.json();
  },

  async fetchMe() {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: this.getAuthHeader()
    });
    if (!res.ok) throw new Error('Not authenticated');
    return res.json();
  },

  // === Spectral Data ===
  async fetchMeasurements(limit = 50): Promise<MeasurementInfo[]> {
    const res = await fetch(`${API_BASE}/measurements?limit=${limit}`, {
        headers: this.getAuthHeader()
    });
    if (!res.ok) {
      throw new Error(`Measurements fetch failed: ${res.status}`);
    }
    return res.json();
  },

  async fetchSpectrum(
    measurementId: string,
    lambdaMin = 164.35,
    lambdaMax = 878.26,
    zoomLevel = 0,
    forceRaw = false
  ): Promise<{ data: SpectralDataPoint[]; meta: SpectrumMeta }> {
    const params = new URLSearchParams({
      measurement_id: measurementId,
      lambda_min: String(lambdaMin),
      lambda_max: String(lambdaMax),
      zoom_level: String(zoomLevel),
      use_cache: 'true',
      force_raw: String(forceRaw),
    });

    const res = await fetch(`${API_BASE}/spectrum?${params}`, {
        headers: this.getAuthHeader()
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Spectrum fetch failed (${res.status}): ${err.slice(0, 200)}`);
    }

    const body: SpectrumResponse = await res.json();
    
    // Both 'downsampled' and 'raw' modes now return flat SpectralApiPoint objects
    const points: SpectralDataPoint[] = body.data.map((point) => ({
      wavelength: point.wavelength_nm,
      intensity: point.intensity,
      rawPlasma: point.raw_plasma ?? point.intensity, // fallback just in case
      rawBackground: 0,
      measurementId: body.measurement_id,
    }));

    return {
      data: points,
      meta: {
        mode: body.mode,
        z_max: body.z_max,
        original_points: body.metadata.original_points ?? points.length,
        n_buckets: body.metadata.n_buckets ?? null,
        reduction_factor: body.metadata.reduction_factor ?? null,
        b_final: body.metadata.b_final ?? null,
      },
    };
  },

  async healthCheck(): Promise<HealthResponse> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) {
      throw new Error(`Health check failed: ${res.status}`);
    }
    return res.json();
  },

  async fetchContext(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/context`);
    if (!res.ok) {
      throw new Error(`Context fetch failed: ${res.status}`);
    }
    return res.json();
  },

  async fetchMeasurementsForObservation(observationId: string): Promise<MeasurementInfo[]> {
    const res = await fetch(`${API_BASE}/measurements?observation_id=${observationId}`);
    if (!res.ok) {
      throw new Error(`Measurements for observation failed: ${res.status}`);
    }
    return res.json();
  },

  async fetchNistLines(element?: string, min?: number, max?: number): Promise<any[]> {
    const params = new URLSearchParams();
    if (element) params.append('element', element);
    if (min !== undefined) params.append('lambda_min', String(min));
    if (max !== undefined) params.append('lambda_max', String(max));
    
    const res = await fetch(`${API_BASE}/nist/lines?${params}`, {
        headers: this.getAuthHeader()
    });
    if (!res.ok) {
      throw new Error(`NIST lines fetch failed: ${res.status}`);
    }
    return res.json();
  },

  // === Export API ===
  exportJson(measurementId: string, lambdaMin: number, lambdaMax: number, zoomLevel: number, forceRaw: boolean) {
    const params = new URLSearchParams({
      measurement_id: measurementId,
      lambda_min: String(lambdaMin),
      lambda_max: String(lambdaMax),
      zoom_level: String(zoomLevel),
      force_raw: String(forceRaw),
    });
    window.open(`${API_BASE}/export/json?${params}`, '_blank');
  },

  exportCsv(measurementId: string, lambdaMin: number, lambdaMax: number, zoomLevel: number, forceRaw: boolean) {
    const params = new URLSearchParams({
      measurement_id: measurementId,
      lambda_min: String(lambdaMin),
      lambda_max: String(lambdaMax),
      zoom_level: String(zoomLevel),
      force_raw: String(forceRaw),
    });
    window.open(`${API_BASE}/export/csv?${params}`, '_blank');
  }
};
