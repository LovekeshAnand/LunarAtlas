/**
 * @fileoverview Live API Service for LunarAtlas.
 *
 * Centralises all HTTP communication with the FastAPI backend.
 * Provides typed methods for:
 *   - Authentication (register, login, session validation)
 *   - Spectral data retrieval with LTTB downsampling
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

export type DenoiseMode = 'none' | 'als' | 'savgol';

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
    denoising?: {
      als_applied: boolean;
      savgol_applied: boolean;
    };
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
  denoising?: {
    als_applied: boolean;
    savgol_applied: boolean;
  };
}

export const apiService = {
  // === Helpers ===
  getAuthHeader(): Record<string, string> {
    const token = localStorage.getItem('access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  },

  // === Authentication & User ===
  async register(data: { email: string; username: string; role: string; institution: string; interest: string; password: string }) {
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

  async updateProfile(data: { role?: string; institution?: string; interest?: string }) {
    const res = await fetch(`${API_BASE}/auth/profile`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeader()
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to update profile: ${res.status}`);
    }
    return res.json();
  },

  async fetchApiKeys(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/auth/api-keys`, {
      headers: this.getAuthHeader()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch API keys: ${res.status}`);
    }
    return res.json();
  },

  async createApiKey(label = 'Default'): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/api-keys`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeader()
      },
      body: JSON.stringify({ label }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to create API key: ${res.status}`);
    }
    return res.json();
  },

  async revokeApiKey(keyId: number): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/api-keys/${keyId}`, {
      method: 'DELETE',
      headers: this.getAuthHeader()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to revoke API key: ${res.status}`);
    }
    return res.json();
  },

  async fetchUsageSummary(): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/usage/summary`, {
      headers: this.getAuthHeader()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch usage summary: ${res.status}`);
    }
    return res.json();
  },

  async fetchUsageLog(limit = 50, offset = 0): Promise<any[]> {
    const res = await fetch(`${API_BASE}/auth/usage/log?limit=${limit}&offset=${offset}`, {
      headers: this.getAuthHeader()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch usage log: ${res.status}`);
    }
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
    forceRaw = false,
    als = false,
    savgol = false
  ): Promise<{ data: SpectralDataPoint[]; meta: SpectrumMeta }> {
    const params = new URLSearchParams({
      measurement_id: measurementId,
      lambda_min: String(lambdaMin),
      lambda_max: String(lambdaMax),
      zoom_level: String(zoomLevel),
      use_cache: 'true',
      force_raw: String(forceRaw),
      als: String(als),
      savgol: String(savgol),
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
    const points: SpectralDataPoint[] = body.data.map((point) => {
      const rawPlasma = point.raw_plasma ?? point.intensity;
      return {
        wavelength: point.wavelength_nm,
        intensity: point.intensity,
        rawPlasma,
        rawBackground: Math.max(0, rawPlasma - point.intensity),
        measurementId: body.measurement_id,
      };
    });

    return {
      data: points,
      meta: {
        mode: body.mode,
        z_max: body.z_max,
        original_points: body.metadata.original_points ?? points.length,
        n_buckets: body.metadata.n_buckets ?? null,
        reduction_factor: body.metadata.reduction_factor ?? null,
        b_final: body.metadata.b_final ?? null,
        denoising: body.metadata.denoising,
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
  },

  /**
   * Fetches spectral data for multiple Measurement IDs simultaneously.
   * All requests run in parallel via Promise.all.
   *
   * @param measurementIds - Array of measurement_id strings to fetch
   * @param lambdaMin - Wavelength lower bound (nm)
   * @param lambdaMax - Wavelength upper bound (nm)
   * @returns Map from measurement_id → SpectralDataPoint[]
   */
  async fetchMultipleSpectra(
    measurementIds: string[],
    lambdaMin: number,
    lambdaMax: number,
    als = false,
    savgol = false
  ): Promise<Map<string, SpectralDataPoint[]>> {
    const results = await Promise.allSettled(
      measurementIds.map((id) =>
        this.fetchSpectrum(id, lambdaMin, lambdaMax, 0, true, als, savgol)
      )
    );

    const map = new Map<string, SpectralDataPoint[]>();
    results.forEach((result, index) => {
      const id = measurementIds[index];
      if (result.status === 'fulfilled') {
        map.set(id, result.value.data);
      } else {
        console.warn(`[API] fetchMultipleSpectra: Failed for ID ${id}:`, result.reason);
        map.set(id, []);
      }
    });
    return map;
  },

  // === Public Developer APIs ===
  async fetchPublicMissions(apiKey: string, limit = 10, offset = 0): Promise<any> {
    const res = await fetch(`${API_BASE}/public/missions?api_key=${encodeURIComponent(apiKey)}&limit=${limit}&offset=${offset}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch public missions: ${res.status}`);
    }
    return res.json();
  },

  async fetchPublicMissionByCode(apiKey: string, missionCode: string): Promise<any> {
    const res = await fetch(`${API_BASE}/public/missions/${encodeURIComponent(missionCode)}?api_key=${encodeURIComponent(apiKey)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch public mission by code: ${res.status}`);
    }
    return res.json();
  },

  async fetchPublicInstruments(apiKey: string, missionCode?: string): Promise<any> {
    const params = new URLSearchParams();
    params.append('api_key', apiKey);
    if (missionCode) params.append('mission_code', missionCode);
    const res = await fetch(`${API_BASE}/public/instruments?${params}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch public instruments: ${res.status}`);
    }
    return res.json();
  },

  async fetchPublicObservations(apiKey: string, filters: { mission?: string; instrument?: string; targetName?: string; date?: string; limit?: number; offset?: number }): Promise<any> {
    const params = new URLSearchParams({ api_key: apiKey });
    if (filters.mission) params.append('mission', filters.mission);
    if (filters.instrument) params.append('instrument', filters.instrument);
    if (filters.targetName) params.append('target_name', filters.targetName);
    if (filters.date) params.append('date', filters.date);
    if (filters.limit) params.append('limit', String(filters.limit));
    if (filters.offset) params.append('offset', String(filters.offset));
    
    const res = await fetch(`${API_BASE}/public/observations?${params}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch public observations: ${res.status}`);
    }
    return res.json();
  },

  async fetchPublicMeasurements(apiKey: string, filters: { observationId?: string; mission?: string; instrument?: string; date?: string; isBackground?: boolean; limit?: number; offset?: number }): Promise<any> {
    const params = new URLSearchParams({ api_key: apiKey });
    if (filters.observationId) params.append('observation_id', filters.observationId);
    if (filters.mission) params.append('mission', filters.mission);
    if (filters.instrument) params.append('instrument', filters.instrument);
    if (filters.date) params.append('date', filters.date);
    if (filters.isBackground !== undefined) params.append('is_background', String(filters.isBackground));
    if (filters.limit) params.append('limit', String(filters.limit));
    if (filters.offset) params.append('offset', String(filters.offset));

    const res = await fetch(`${API_BASE}/public/measurements?${params}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch public measurements: ${res.status}`);
    }
    return res.json();
  },

  async fetchPublicSpectrum(
    apiKey: string,
    measurementId: string,
    params: { lambdaMin?: number; lambdaMax?: number; downsample?: boolean; zoomLevel?: number; targetWavelengths?: string } = {}
  ): Promise<any> {
    const q = new URLSearchParams({ api_key: apiKey });
    if (params.lambdaMin !== undefined) q.append('lambda_min', String(params.lambdaMin));
    if (params.lambdaMax !== undefined) q.append('lambda_max', String(params.lambdaMax));
    if (params.downsample !== undefined) q.append('downsample', String(params.downsample));
    if (params.zoomLevel !== undefined) q.append('zoom_level', String(params.zoomLevel));
    if (params.targetWavelengths) q.append('target_wavelengths', params.targetWavelengths);

    const res = await fetch(`${API_BASE}/public/spectra/${measurementId}?${q}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch public spectrum: ${res.status}`);
    }
    return res.json();
  },

  async fetchPublicBulkSpectra(
    apiKey: string,
    params: {
      observationId?: string;
      date?: string;
      mission?: string;
      measurementIds?: string;
      lambdaMin?: number;
      lambdaMax?: number;
      downsample?: boolean;
      zoomLevel?: number;
      targetWavelengths?: string;
      limit?: number;
      offset?: number;
    } = {}
  ): Promise<any> {
    const q = new URLSearchParams({ api_key: apiKey });
    if (params.observationId) q.append('observation_id', params.observationId);
    if (params.date) q.append('date', params.date);
    if (params.mission) q.append('mission', params.mission);
    if (params.measurementIds) q.append('measurement_ids', params.measurementIds);
    if (params.lambdaMin !== undefined) q.append('lambda_min', String(params.lambdaMin));
    if (params.lambdaMax !== undefined) q.append('lambda_max', String(params.lambdaMax));
    if (params.downsample !== undefined) q.append('downsample', String(params.downsample));
    if (params.zoomLevel !== undefined) q.append('zoom_level', String(params.zoomLevel));
    if (params.targetWavelengths) q.append('target_wavelengths', params.targetWavelengths);
    if (params.limit !== undefined) q.append('limit', String(params.limit));
    if (params.offset !== undefined) q.append('offset', String(params.offset));

    const res = await fetch(`${API_BASE}/public/spectra?${q}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch public bulk spectra: ${res.status}`);
    }
    return res.json();
  },
};
