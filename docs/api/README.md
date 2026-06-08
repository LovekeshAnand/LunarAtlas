# LunarAtlas API Reference

This document describes all REST API endpoints exposed by the LunarAtlas
FastAPI server (`core/server/`).

**Base URL:** `http://localhost:8000/api/v1`  
**Interactive docs:** `http://localhost:8000/docs` (Swagger UI, auto-generated)  
**OpenAPI spec:** `http://localhost:8000/openapi.json`

---

## Authentication

All API endpoints require a Bearer token in the `Authorization` header
(JWT-based, configured via `core/server/.env`):

```
Authorization: Bearer <your-token>
```

---

## Endpoints

### `GET /health`

Returns the operational status of the backend.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": true,
  "redis": true,
  "timestamp": "2025-08-23T10:42:11.000Z"
}
```

| Field | Type | Description |
|---|---|---|
| `status` | string | `"healthy"` or `"degraded"` |
| `database` | bool | PostgreSQL connectivity |
| `redis` | bool | Redis connectivity |

---

### `GET /context`

Lists all available observation sessions.

**Response:** Array of observation records, ordered by date (newest first).

```json
[
  {
    "observation_id": "FI-20230825-104221-00",
    "target_name": "ch3_lib_002_20230825T104221_00_l1.xml",
    "creation_datetime": "2023-08-25",
    "record_count": 14658
  }
]
```

---

### `GET /measurements`

Lists measurements for a given observation.

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `observation_id` | string | — | Filter by `file_info_id` |
| `limit` | int | 50 | Max results (1–500) |

---

### `GET /spectrum` ⭐ Core Endpoint

Returns downsampled spectral data for a single measurement.

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `measurement_id` | string | **required** | Measurement identifier |
| `lambda_min` | float | `200.0` | Wavelength range start (nm) |
| `lambda_max` | float | `800.0` | Wavelength range end (nm) |
| `zoom_level` | int | `0` | Discrete zoom level (0–5) |
| `proportion` | float | — | Density ratio 0.0–1.0 (overrides zoom) |
| `target_wavelengths` | string | — | Comma-separated NIST targets (nm) |
| `use_cache` | bool | `true` | Enable Redis caching |
| `force_raw` | bool | `false` | Bypass downsampling |

**Zoom level → output points:**

| `zoom_level` | Output Points | Reduction |
|---|---|---|
| 0 | 2094 (raw) | 1× |
| 1 | 1047 | 2× |
| 2 | 523 | 4× |
| 3 | 261 | 8× |
| 4 | 130 | 16× |

**Example request:**
```
GET /api/v1/spectrum?measurement_id=FI-20230825-104221-00-1
  &lambda_min=270&lambda_max=420
  &zoom_level=2
  &target_wavelengths=279.55,288.16,393.37
```

**Response:**
```json
{
  "mode": "downsampled",
  "measurement_id": "FI-20230825-104221-00-1",
  "lambda_min": 270.0,
  "lambda_max": 420.0,
  "zoom_level": 2,
  "z_max": 5,
  "data": [
    {"wavelength_nm": 270.1, "intensity": 48.2, "raw_plasma": 312.7},
    {"wavelength_nm": 279.55, "intensity": 4821.3, "raw_plasma": 5102.1},
    ...
  ],
  "metadata": {
    "original_points": 347,
    "n_buckets": 130,
    "reduction_factor": 2.67,
    "b_final": 0.0
  },
  "cached": false,
  "query_time_ms": 18.4
}
```

---

### `GET /nist/lines`

Returns NIST atomic emission line references.

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `element` | string | Filter by element (e.g. `"Fe"`, `"Mg"`) |
| `lambda_min` | float | Wavelength range start |
| `lambda_max` | float | Wavelength range end |

---

### `POST /cache/clear`

Clears the Redis cache.

**Query parameters:**

| Parameter | Default | Description |
|---|---|---|
| `pattern` | `"*"` | Key pattern to clear |

---

## Data Flow Diagram

```
Browser Request
     │
     ▼
GET /spectrum?measurement_id=X&zoom_level=2
     │
     ├── Redis cache HIT → return cached JSON (< 2 ms)
     │
     └── Redis cache MISS
              │
              ▼
         PostgreSQL query
         spectral_data_clean JOIN spectral_data_calibrated
              │
              ▼
         lttb_downsample(data, zoom_level=2)
         │
         ├── N(k) = min(2094, 2094 × 2^(-2)) = 523 target points
         ├── LTTB triangle-area selection
         └── NIST Peak-Union Lock: P_final = LTTB ∪ NIST_set
              │
              ▼
         Cache result in Redis (TTL = 3600s)
              │
              ▼
         Return SpectralResponse JSON
```
