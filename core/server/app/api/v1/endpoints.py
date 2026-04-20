from fastapi import APIRouter, HTTPException, Query
from typing import List
import numpy as np
import time
import logging

from app.schemas.spectral import (
    SpectralQueryParams,
    SpectralResponse,
    MeasurementInfo,
    HealthResponse,
    NistLine,
    ObservationInfo
)
from app.core.downsampling import adaptive_minmax_downsample, DownsampleConfig
from app.database.connection import db
from app.cache.redis_cache import cache
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns service status and component availability.
    """
    from datetime import datetime
    
    # Check database
    db_healthy = False
    try:
        await db.fetch_one("SELECT 1")
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
        redis=redis_healthy,
        timestamp=datetime.now()
    )


@router.get("/context", response_model=List[ObservationInfo])
async def list_observations():
    """
    List available observation sessions from the database.
    Used to populate mission/date selectors on the frontend.
    """
    query = """
        SELECT 
            file_info_id as observation_id, 
            xml_label_name as target_name, 
            creation_datetime,
            record_count
        FROM observation_file_info
        ORDER BY creation_datetime DESC
        LIMIT 100
    """
    try:
        rows = await db.fetch_all(query)
        return [ObservationInfo(**row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching observations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch observation context")

@router.get("/measurements", response_model=List[MeasurementInfo])
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
    use_cache: bool = Query(True, description="Enable Redis caching"),
    force_raw: bool = Query(False, description="Bypass server downsampling and return raw data")
):
    """
    Retrieve spectral data with adaptive min-max downsampling.
    """
    start_time = time.time()
    
    # Generate cache key
    cache_key = cache.generate_key(
        "spectrum",
        measurement_id,
        lambda_min,
        lambda_max,
        zoom_level
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
            wavelength_nm, 
            intensity
        FROM spectral_data_clean
        WHERE 
            measurement_id = $1
            AND wavelength_nm BETWEEN $2 AND $3
        ORDER BY wavelength_nm
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
            [float(row['wavelength_nm']), float(row['intensity'])]
            for row in rows
        ])
        
        logger.info(
            f"Fetched {len(data)} points for measurement {measurement_id} "
            f"in {db_time:.2f}ms"
        )
        
        if force_raw:
            formatted_data = [
                {"wavelength_nm": float(pt[0]), "intensity": float(pt[1])}
                for pt in data
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
                    "b_final": 0.0
                },
                "cached": False,
                "query_time_ms": db_time
            }
            if use_cache:
                await cache.set(cache_key, result, ttl=settings.CACHE_TTL)
            return result
        
        # Apply downsampling
        downsample_config = DownsampleConfig(
            BASE_BUCKETS=settings.BASE_BUCKETS,
            B_MIN=settings.MIN_BUCKET_SIZE
        )
        
        downsample_result = adaptive_minmax_downsample(
            data=data,
            zoom_level=zoom_level,
            lambda_min=lambda_min,
            lambda_max=lambda_max,
            config=downsample_config
        )
        
        # Format data for Pydantic validation
        raw_data = downsample_result['data']
        if downsample_result['mode'] == 'raw':
            # Convert [[wavelength, intensity], ...] → [{"wavelength_nm": ..., "intensity": ...}, ...]
            formatted_data = [
                {"wavelength_nm": float(pt[0]), "intensity": float(pt[1])}
                for pt in raw_data
            ]
        else:
            # Downsampled buckets are already dicts
            formatted_data = raw_data

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
                "b_final": downsample_result.get('b_final')
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
