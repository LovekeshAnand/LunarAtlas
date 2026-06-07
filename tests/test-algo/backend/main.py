"""
LunarAtlas Spectral Visualization API
FastAPI backend with adaptive min-max downsampling
Fixed: dynamic zmax computation, proper raw-mode switching, connection pooling
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import math
import logging
import threading

# Load .env file if present (no dependency on python-dotenv required)
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LunarAtlas Spectral API",
    description="Adaptive min-max downsampling for LIBS spectroscopy data",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Database ──────────────────────────────────────────────────────────────────

def _build_db_config() -> dict:
    """Build DB config at call-time so env vars set after import are picked up."""
    return {
        "host":     os.getenv("DB_HOST",     "localhost"),
        "database": os.getenv("DB_NAME",     "spectroscopy_db"),
        "user":     os.getenv("DB_USER",     "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),   # set DB_PASSWORD in .env
        "port":     os.getenv("DB_PORT",     "5432"),
    }

_pool: Optional[ThreadedConnectionPool] = None
_pool_lock = threading.Lock()

def get_pool() -> ThreadedConnectionPool:
    """
    Lazily creates the connection pool on first use.
    Raises HTTP 503 with a clear message when the DB is unreachable,
    instead of crashing the whole process at startup.
    """
    global _pool
    if _pool is not None:
        return _pool
    with _pool_lock:
        if _pool is not None:          # double-checked inside lock
            return _pool
        cfg = _build_db_config()
        if not cfg["password"]:
            logger.warning(
                "DB_PASSWORD is empty. Set it in a .env file or as an environment variable."
            )
        try:
            _pool = ThreadedConnectionPool(minconn=2, maxconn=10, **cfg)
            logger.info("Database connection pool created (host=%s db=%s user=%s)",
                        cfg["host"], cfg["database"], cfg["user"])
        except psycopg2.OperationalError as exc:
            logger.error("Cannot connect to database: %s", exc)
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Database unavailable: {exc}. "
                    "Check DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT in your .env file."
                ),
            ) from exc
    return _pool


class DBConn:
    """Context manager that checks out / returns a pooled connection."""
    def __enter__(self):
        try:
            self.conn = get_pool().getconn()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"DB pool error: {exc}") from exc
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If the connection broke mid-request, close it instead of returning it
        try:
            if exc_type is not None and self.conn.closed == 0:
                self.conn.rollback()
            get_pool().putconn(self.conn, close=self.conn.closed != 0)
        except Exception:
            pass  # never raise inside __exit__


# ── Algorithm constants ───────────────────────────────────────────────────────

BASE_BUCKETS:    int   = 1000
MIN_BUCKET_SIZE: float = 0.01   # nm  (≈ instrument resolution floor)
ABS_MAX_ZOOM:    int   = 10     # hard cap so UI slider stays sane


# ── Pydantic models ───────────────────────────────────────────────────────────

class BucketData(BaseModel):
    bucket_id:     int
    start_wl:      float
    end_wl:        float
    min_intensity: float
    max_intensity: float
    min_wavelength: float
    max_wavelength: float
    point_count:   int
    data_present:  bool = True


class SpectralResponse(BaseModel):
    status:             str
    mode:               str          # "downsampled" | "raw"
    metadata:           Dict[str, Any]
    parameters:         Dict[str, Any]
    buckets:            List[BucketData]
    processing_time_ms: float


class RawDataPoint(BaseModel):
    wavelength: float
    intensity:  float


class RawDataResponse(BaseModel):
    status:             str
    metadata:           Dict[str, Any]
    data_points:        List[RawDataPoint]
    processing_time_ms: float


class ZoomInfo(BaseModel):
    wavelength_span:   float
    zmax:              int
    bucket_size_at_zmax: float
    saturated:         bool
    message:           str


# ── Core algorithm ────────────────────────────────────────────────────────────

def compute_zmax(wavelength_span: float) -> int:
    """
    Maximum unsaturated zoom level per Eq. (6) of the paper:
        zmax = floor( log2( Δλ / (BASE_BUCKETS × MIN_BUCKET_SIZE) ) )
    Returns 0 when Δλ is already at or below the saturation floor.
    """
    ratio = wavelength_span / (BASE_BUCKETS * MIN_BUCKET_SIZE)
    if ratio <= 1.0:
        return 0
    return int(math.floor(math.log2(ratio)))


def compute_bucket_size(wavelength_span: float, zoom_level: int) -> float:
    """
    Effective bucket size after applying the MIN_BUCKET_SIZE floor.
    Returns MIN_BUCKET_SIZE when zoom is at or beyond zmax (saturated regime).
    """
    raw = wavelength_span / (BASE_BUCKETS * (2 ** zoom_level))
    return max(raw, MIN_BUCKET_SIZE)


def is_saturated(wavelength_span: float, zoom_level: int) -> bool:
    """True when zoom_level > zmax(wavelength_span)."""
    return zoom_level > compute_zmax(wavelength_span)


def generate_bucket_boundaries(
    min_wl: float,
    max_wl: float,
    bucket_size: float,
) -> List[tuple]:
    wavelength_span = max_wl - min_wl
    n_buckets = math.ceil(wavelength_span / bucket_size)
    boundaries = []
    for i in range(n_buckets):
        start = min_wl + i * bucket_size
        start = max(start, min_wl)
        end   = start + bucket_size
        boundaries.append((start, end))
    return boundaries


def _minmax_buckets(
    conn,
    observation_id: int,
    min_wl: float,
    max_wl: float,
    bucket_size: float,
) -> List[BucketData]:
    boundaries = generate_bucket_boundaries(min_wl, max_wl, bucket_size)
    buckets: List[BucketData] = []

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        for idx, (start, end) in enumerate(boundaries):
            cur.execute(
                """
                SELECT wavelength_nm, cleaned_intensity
                FROM   spectroscopy_measurements
                WHERE  measurement_id = %s
                  AND  wavelength_nm >= %s
                  AND  wavelength_nm <  %s
                ORDER  BY wavelength_nm
                """,
                (observation_id, start, end),
            )
            rows = cur.fetchall()

            if not rows:
                buckets.append(BucketData(
                    bucket_id=idx, start_wl=start, end_wl=end,
                    min_intensity=0, max_intensity=0,
                    min_wavelength=start, max_wavelength=end,
                    point_count=0, data_present=False,
                ))
                continue

            intensities = [r["cleaned_intensity"] for r in rows]
            wavelengths = [r["wavelength_nm"]      for r in rows]
            lo = intensities.index(min(intensities))
            hi = intensities.index(max(intensities))

            buckets.append(BucketData(
                bucket_id=idx, start_wl=start, end_wl=end,
                min_intensity=intensities[lo], max_intensity=intensities[hi],
                min_wavelength=wavelengths[lo], max_wavelength=wavelengths[hi],
                point_count=len(rows), data_present=True,
            ))

    return buckets


def _raw_points(
    conn,
    observation_id: int,
    min_wl: float,
    max_wl: float,
) -> List[RawDataPoint]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT wavelength_nm AS wavelength,
                   cleaned_intensity AS intensity
            FROM   spectroscopy_measurements
            WHERE  measurement_id = %s
              AND  wavelength_nm BETWEEN %s AND %s
            ORDER  BY wavelength_nm
            """,
            (observation_id, min_wl, max_wl),
        )
        return [RawDataPoint(**r) for r in cur.fetchall()]


# ── API endpoints ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "LunarAtlas Spectral Visualization API v2",
        "endpoints": {
            "spectral":     "/api/v1/spectral",
            "raw":          "/api/v1/spectral/raw",
            "zoom_info":    "/api/v1/zoom_info",
            "observations": "/api/v1/observations",
            "health":       "/health",
        },
    }


@app.get("/health")
def health_check():
    try:
        with DBConn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}


@app.get("/api/v1/zoom_info", response_model=ZoomInfo)
def zoom_info(
    min_wavelength: float = Query(..., ge=0, le=2000),
    max_wavelength: float = Query(..., ge=0, le=2000),
    zoom_level:     int   = Query(0,   ge=0, le=ABS_MAX_ZOOM),
):
    """
    Returns zmax for a given wavelength window so the frontend can
    warn the user before they hit raw-data mode.
    """
    if min_wavelength >= max_wavelength:
        raise HTTPException(400, "min_wavelength must be < max_wavelength")
    span  = max_wavelength - min_wavelength
    zmax  = compute_zmax(span)
    bsize = compute_bucket_size(span, min(zoom_level, zmax))
    sat   = is_saturated(span, zoom_level)
    return ZoomInfo(
        wavelength_span=span,
        zmax=zmax,
        bucket_size_at_zmax=round(bsize, 6),
        saturated=sat,
        message=(
            f"Zoom {zoom_level} is beyond zmax={zmax} for this window — "
            "use /api/v1/spectral/raw for full-resolution data."
            if sat else
            f"Zoom {zoom_level} is within unsaturated range (zmax={zmax})."
        ),
    )


@app.get("/api/v1/observations")
def list_observations():
    with DBConn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT measurement_id,
                       time_utc,
                       measurement_count,
                       MIN(wavelength_nm) AS min_wavelength,
                       MAX(wavelength_nm) AS max_wavelength,
                       COUNT(*)           AS point_count
                FROM   spectroscopy_measurements
                GROUP  BY measurement_id, time_utc, measurement_count
                ORDER  BY measurement_id
                """
            )
            rows = cur.fetchall()
    return {"status": "success", "count": len(rows), "observations": rows}


@app.get("/api/v1/spectral", response_model=SpectralResponse)
def get_spectral_data(
    observation_id: int   = Query(..., description="Measurement ID"),
    min_wavelength: float = Query(..., ge=0, le=2000, description="Min wavelength (nm)"),
    max_wavelength: float = Query(..., ge=0, le=2000, description="Max wavelength (nm)"),
    zoom_level:     int   = Query(0,   ge=0, le=ABS_MAX_ZOOM, description="Zoom level 0-10"),
):
    """
    Returns min-max downsampled OR raw spectral data depending on
    whether zoom_level exceeds zmax(Δλ).

    The endpoint never returns misleading saturated buckets — if the
    requested zoom is beyond zmax the backend automatically switches
    to raw mode and sets `mode = "raw"` in the response so the
    frontend can show appropriate UI cues.
    """
    t0 = datetime.now()

    if min_wavelength >= max_wavelength:
        raise HTTPException(400, "min_wavelength must be < max_wavelength")
    span = max_wavelength - min_wavelength
    if span < 1.0:
        raise HTTPException(400, "Wavelength span must be at least 1.0 nm")

    zmax       = compute_zmax(span)
    saturated  = is_saturated(span, zoom_level)
    eff_zoom   = min(zoom_level, zmax)          # clamp for bucket computation
    bsize      = compute_bucket_size(span, eff_zoom)
    n_buckets  = math.ceil(span / bsize)

    with DBConn() as conn:
        if saturated:
            # Auto-switch to raw mode — no misleading saturated buckets
            raw_pts = _raw_points(conn, observation_id, min_wavelength, max_wavelength)
            # Wrap raw points as single-point buckets for a uniform response shape
            buckets = [
                BucketData(
                    bucket_id=i,
                    start_wl=p.wavelength, end_wl=p.wavelength,
                    min_intensity=p.intensity, max_intensity=p.intensity,
                    min_wavelength=p.wavelength, max_wavelength=p.wavelength,
                    point_count=1, data_present=True,
                )
                for i, p in enumerate(raw_pts)
            ]
            mode = "raw"
        else:
            buckets = _minmax_buckets(conn, observation_id, min_wavelength, max_wavelength, bsize)
            mode    = "downsampled"

    ms = (datetime.now() - t0).total_seconds() * 1000

    return SpectralResponse(
        status="success",
        mode=mode,
        metadata={
            "observation_id":       observation_id,
            "algorithm_version":    "minmax_v2.0.0",
            "processing_timestamp": datetime.now().isoformat(),
            "returned_bucket_count": len(buckets),
            "zmax_for_window":      zmax,
            "auto_switched_to_raw": saturated,
        },
        parameters={
            "wavelength_range":   [min_wavelength, max_wavelength],
            "wavelength_span":    span,
            "zoom_level":         zoom_level,
            "effective_zoom":     eff_zoom,
            "bucket_size_nm":     bsize,
            "bucket_count":       n_buckets,
            "overlap_percentage": 0.0,
            "saturated":          saturated,
        },
        buckets=buckets,
        processing_time_ms=round(ms, 2),
    )


@app.get("/api/v1/spectral/raw", response_model=RawDataResponse)
def get_raw_spectral_data(
    observation_id: int   = Query(..., description="Measurement ID"),
    min_wavelength: float = Query(..., ge=0, le=2000),
    max_wavelength: float = Query(..., ge=0, le=2000),
):
    """Raw data without any downsampling — use for narrow windows or max zoom."""
    t0 = datetime.now()
    if min_wavelength >= max_wavelength:
        raise HTTPException(400, "min_wavelength must be < max_wavelength")

    with DBConn() as conn:
        pts = _raw_points(conn, observation_id, min_wavelength, max_wavelength)

    ms = (datetime.now() - t0).total_seconds() * 1000
    return RawDataResponse(
        status="success",
        metadata={
            "observation_id":       observation_id,
            "processing_timestamp": datetime.now().isoformat(),
            "point_count":          len(pts),
        },
        data_points=pts,
        processing_time_ms=round(ms, 2),
    )



@app.get("/api/v1/nist_peaks")
def get_nist_peaks(
    min_wavelength: float = Query(..., ge=0, le=2000, description="Min wavelength (nm)"),
    max_wavelength: float = Query(..., ge=0, le=2000, description="Max wavelength (nm)"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Min confidence filter"),
):
    """
    Return NIST reference emission lines within the wavelength window.

    Expects a nist_peaks table with columns:
        wavelength_nm FLOAT, element TEXT, ion_stage TEXT,
        relative_intensity FLOAT, confidence_score FLOAT
    """
    if min_wavelength >= max_wavelength:
        raise HTTPException(400, "min_wavelength must be < max_wavelength")

    with DBConn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT  wavelength_nm      AS wavelength,
                        element,
                        ion_stage,
                        relative_intensity AS rel_intensity,
                        confidence_score   AS confidence
                FROM    nist_peaks
                WHERE   wavelength_nm BETWEEN %s AND %s
                  AND   confidence_score   >= %s
                ORDER   BY wavelength_nm
                """,
                (min_wavelength, max_wavelength, min_confidence),
            )
            rows = cur.fetchall()

    return {
        "status": "success",
        "count":  len(rows),
        "peaks":  rows,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)