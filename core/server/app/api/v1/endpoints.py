from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import numpy as np
import time
import logging
import json

from app.schemas.spectral import (
    SpectralQueryParams,
    SpectralResponse,
    MeasurementInfo,
    HealthResponse,
    NistLine,
    ObservationInfo
)
from app.core.downsampling import lttb_downsample
from app.core.denoising import apply_denoising_pipeline
from app.database.connection import db
from app.cache.redis_cache import cache, cached
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns the operational status of all backend components:
    - **Database:** PostgreSQL connectivity (verified via ``SELECT 1``).
    - **Redis:** Cache layer connectivity (verified via ``PING``).
    - **Status:** ``healthy`` if the database is reachable, ``degraded`` otherwise.

    Returns
    -------
    HealthResponse
        JSON with status, version, database, redis, and timestamp fields.
    """
    import time
    from datetime import datetime
    
    # Check database
    db_healthy = False
    db_latency = 0.0
    try:
        start_time = time.perf_counter()
        await db.fetch_one("SELECT 1")
        db_latency = (time.perf_counter() - start_time) * 1000.0
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis
    redis_healthy = False
    try:
        if cache.redis:
            await cache.redis.ping()
            redis_healthy = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
    
    status = "healthy" if db_healthy else "degraded"
    
    return HealthResponse(
        status=status,
        version=settings.APP_VERSION,
        database=db_healthy,
        db_latency_ms=round(db_latency, 2),
        redis=redis_healthy,
        timestamp=datetime.now()
    )


@router.get("/context", response_model=List[ObservationInfo])
@cached(ttl=3600)
async def list_observations():
    """
    List available observation sessions from the database.

    Queries the ``observation_file_info`` table joined with ``observation``
    and returns observation metadata ordered by data capture date (most recent first).
    Used by the frontend to populate the mission/date selector dropdowns.

    Returns
    -------
    List[ObservationInfo]
        Up to 100 observation records with ID, target name, date, and count.
    """
    query = """
        SELECT 
            i.file_info_id as observation_id, 
            o.xml_label_name as target_name, 
            s.observation_date as creation_datetime,
            i.record_count
        FROM observation_file_info i
        JOIN observation o ON i.observation_id = o.observation_id
        JOIN observation_session s ON o.session_id = s.session_id
        ORDER BY s.observation_date DESC, o.start_time DESC
        LIMIT 500
    """
    try:
        rows = await db.fetch_all(query)
        return [ObservationInfo(**row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching observations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch observation context")

@router.get("/measurements", response_model=List[MeasurementInfo])
@cached(ttl=3600)
async def list_measurements(
    observation_id: str = Query(None, description="Filter by observation id (file_info_id)"),
    limit: int = Query(50, ge=1, le=500)
):
    """
    List available measurements, optionally filtered by observation.
    """
    query = """
        SELECT 
            measurement_id, 
            file_info_id,
            measurement_index,
            time_utc, 
            measurement_count,
            operation_mode,
            measurement_type,
            is_background,
            integration_time_us, 
            number_of_pulses, 
            laser_energy_v
        FROM measurement_clean
    """
    if observation_id:
        query += " WHERE file_info_id = $1 "
        query += " ORDER BY measurement_index ASC LIMIT $2"
        params = [observation_id, limit]
    else:
        query += " ORDER BY time_utc DESC LIMIT $1"
        params = [limit]
    
    try:
        rows = await db.fetch_all(query, *params)
        return [MeasurementInfo(**row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching measurements: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")

@router.get("/nist/lines", response_model=List[NistLine])
@cached(ttl=3600)
async def get_nist_lines(
    element: str = Query(None, description="Filter by element (e.g. Fe, Mg)"),
    lambda_min: float = Query(None),
    lambda_max: float = Query(None)
):
    """
    Fetch NIST reference atomic spectra data.
    Backs our spectral claims with solid atomic physics data.
    """
    query = "SELECT * FROM nist_lines WHERE 1=1"
    params = []
    
    if element:
        params.append(element)
        query += f" AND element = ${len(params)}"
    
    if lambda_min is not None and lambda_max is not None:
        params.extend([lambda_min, lambda_max])
        query += f" AND wavelength_nm BETWEEN ${len(params)-1} AND ${len(params)}"
        
    query += " ORDER BY wavelength_nm ASC"
    
    try:
        rows = await db.fetch_all(query, *params)
        return [NistLine(**row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching NIST lines: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch NIST data")


@router.get("/spectrum", response_model=SpectralResponse)
async def get_spectrum(
    measurement_id: str = Query(..., description="Measurement ID"),
    lambda_min: float = Query(200.0, description="Minimum wavelength (nm)"),
    lambda_max: float = Query(800.0, description="Maximum wavelength (nm)"),
    zoom_level: int = Query(0, description="Discrete zoom level (0-5)"),
    proportion: Optional[float] = Query(None, description="LTTB density ratio (0.0–1.0). Overrides zoom_level when set."),
    target_wavelengths: Optional[str] = Query(None, description="Comma-separated target wavelengths (nm) for Targeted Peak Preservation."),
    use_cache: bool = Query(True, description="Enable Redis caching"),
    force_raw: bool = Query(False, description="Bypass server downsampling and return raw data"),
    als: bool = Query(False, description="Apply ALS baseline correction (visualization only — does not modify stored data)"),
    savgol: bool = Query(False, description="Apply Savitzky-Golay smoothing (visualization only — does not modify stored data)")
):
    """
    Retrieve spectral data with LTTB downsampling.

    Fetches raw wavelength-intensity pairs from ``spectral_data_clean``,
    applies the LTTB (Largest Triangle Three Buckets) downsampling
    algorithm based on zoom level, and returns the result with metadata.
    Supports Redis caching and a ``force_raw`` bypass.

    Query Flow
    ----------
    1. Generate cache key from (measurement_id, λ_min, λ_max, zoom).
    2. Check Redis cache (if enabled).
    3. Query PostgreSQL for raw spectral data.
    4. Apply ``lttb_downsample()`` (or return raw if ``force_raw=True``).
    5. Cache the result and return.

    Parameters
    ----------
    measurement_id : str
        Unique measurement identifier from the measurement_clean table.
    lambda_min : float
        Minimum wavelength boundary in nm.
    lambda_max : float
        Maximum wavelength boundary in nm.
    zoom_level : int
        Discrete zoom level (0 = most zoomed out, higher = more buckets).
    use_cache : bool
        Whether to check and store results in Redis.
    force_raw : bool
        If True, bypass server-side downsampling and return all raw points.

    Returns
    -------
    SpectralResponse
        JSON containing mode, data array, metadata, and timing info.
    """
    start_time = time.time()
    
    # Parse target_wavelengths from comma-separated string
    parsed_target_wavelengths: List[float] = []
    if target_wavelengths:
        try:
            parsed_target_wavelengths = [float(w.strip()) for w in target_wavelengths.split(',') if w.strip()]
        except ValueError:
            logger.warning(f"Invalid target_wavelengths format: {target_wavelengths}")

    # Generate cache key — als/savgol flags are included so each of the four
    # denoising combinations gets its own isolated Redis entry.
    cache_key = cache.generate_key(
        "spectrum",
        measurement_id,
        lambda_min,
        lambda_max,
        zoom_level,
        proportion,
        target_wavelengths or "",
        als,
        savgol
    )
    
    # Try cache first
    if use_cache:
        cached_result = await cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache HIT for measurement {measurement_id}")
            cached_result['cached'] = True
            return SpectralResponse(**cached_result)
    
    # Query database
    query = """
        SELECT 
            c.wavelength_nm, 
            c.intensity,
            COALESCE(cal.response_count, c.intensity) AS raw_plasma
        FROM spectral_data_clean c
        LEFT JOIN spectral_data_raw cal 
          ON c.measurement_id = cal.measurement_id 
          AND c.wavelength_nm = cal.wavelength_nm
        WHERE 
            c.measurement_id = $1
            AND c.wavelength_nm BETWEEN $2 AND $3
        ORDER BY c.wavelength_nm
    """
    
    try:
        # Fetch data
        db_start = time.time()
        rows = await db.fetch_all(query, measurement_id, lambda_min, lambda_max)
        db_time = (time.time() - db_start) * 1000  # Convert to ms
        
        if not rows:
            # No data found
            result = {
                "mode": "empty",
                "measurement_id": measurement_id,
                "lambda_min": lambda_min,
                "lambda_max": lambda_max,
                "zoom_level": zoom_level,
                "z_max": None,
                "data": [],
                "metadata": {
                    "original_points": 0,
                    "n_buckets": None,
                    "reduction_factor": None,
                    "b_final": None,
                    "message": "No data in specified range",
                },
                "cached": False,
                "query_time_ms": db_time
            }
            return SpectralResponse(**result)
        
        # Convert to NumPy array
        data = np.array([
            [float(row['wavelength_nm']), float(row['intensity']), float(row['raw_plasma'])]
            for row in rows
        ])

        # --- Optional denoising pipeline (ALS → Savitzky-Golay) ---
        # Operates exclusively in the visualization layer.
        # The database (spectral_data_clean) is never modified.
        als_applied = False
        savgol_applied = False
        if als or savgol:
            raw_intensities = data[:, 1]
            denoised, als_applied, savgol_applied = apply_denoising_pipeline(
                raw_intensities, als=als, savgol=savgol
            )
            data = data.copy()
            data[:, 1] = denoised
            logger.info(
                "Denoising applied for measurement %s: als=%s savgol=%s",
                measurement_id, als_applied, savgol_applied
            )
        
        logger.info(
            f"Fetched {len(data)} points for measurement {measurement_id} "
            f"in {db_time:.2f}ms"
        )
        
        if force_raw:
            formatted_data = [
                {
                    "wavelength_nm": float(data[i, 0]),
                    "intensity": float(data[i, 1]),
                    "raw_plasma": float(data[i, 2])
                }
                for i in range(len(data))
            ]
            result = {
                "mode": "raw",
                "measurement_id": measurement_id,
                "lambda_min": lambda_min,
                "lambda_max": lambda_max,
                "zoom_level": zoom_level,
                "z_max": 0,
                "data": formatted_data,
                "metadata": {
                    "original_points": len(data),
                    "n_buckets": len(data),
                    "reduction_factor": 1.0,
                    "b_final": 0.0,
                    "denoising": {
                        "als_applied": als_applied,
                        "savgol_applied": savgol_applied
                    }
                },
                "cached": False,
                "query_time_ms": db_time
            }
            if use_cache:
                await cache.set(cache_key, result, ttl=settings.CACHE_TTL)
            return result
        
        # Apply downsampling (index-based for LIBS data)
        downsample_result = lttb_downsample(
            data=data,
            zoom_level=zoom_level,
            lambda_min=lambda_min,
            lambda_max=lambda_max,
            target_wavelengths=parsed_target_wavelengths if parsed_target_wavelengths else None,
            proportion=proportion
        )
        
        # LTTB returns flat dicts for both raw and downsampled modes
        formatted_data = downsample_result['data']

        # Build response
        result = {
            "mode": downsample_result['mode'],
            "measurement_id": measurement_id,
            "lambda_min": lambda_min,
            "lambda_max": lambda_max,
            "zoom_level": zoom_level,
            "z_max": downsample_result.get('z_max'),
            "data": formatted_data,
            "metadata": {
                "original_points": downsample_result.get('original_points', len(data)),
                "n_buckets": downsample_result.get('n_buckets'),
                "reduction_factor": downsample_result.get('reduction_factor'),
                "b_final": downsample_result.get('b_final'),
                "denoising": {
                    "als_applied": als_applied,
                    "savgol_applied": savgol_applied
                }
            },
            "cached": False,
            "query_time_ms": db_time
        }
        
        # Cache result
        if use_cache:
            await cache.set(cache_key, result, ttl=settings.CACHE_TTL)
        
        return result
    
    except Exception as e:
        logger.error(f"Error fetching spectrum: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve spectral data: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache(
    pattern: str = Query("*", description="Cache key pattern to clear")
):
    """
    Clear Redis cache.
    """
    try:
        await cache.clear_pattern(pattern)
        return {
            "status": "success",
            "message": f"Cache cleared for pattern: {pattern}"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Cache clear failed")
