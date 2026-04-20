from fastapi import APIRouter, HTTPException, Query
from typing import List
import numpy as np
import time
import logging

from app.schemas.spectral import (
    SpectralQueryParams,
    SpectralResponse,
    MeasurementInfo,
    HealthResponse
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
    
    status = "healthy" if (db_healthy and redis_healthy) else "degraded"
    
    return HealthResponse(
        status=status,
        version=settings.APP_VERSION,
        database=db_healthy,
        redis=redis_healthy,
        timestamp=datetime.now()
    )


@router.get("/measurements", response_model=List[MeasurementInfo])
async def list_measurements(
    limit: int = Query(10, ge=1, le=100, description="Number of measurements to return")
):
    """
    List available measurements.
    Returns metadata for the most recent measurements.
    """
    query = """
        SELECT 
            id, 
            measurement_id, 
            time_utc, 
            laser_energy_v, 
            integration_time_us, 
            num_pulses, 
            operation_mode
        FROM measurement
        ORDER BY time_utc DESC
        LIMIT $1
    """
    
    try:
        rows = await db.fetch_all(query, limit)
        
        measurements = [
            MeasurementInfo(
                id=row['id'],
                measurement_id=row['measurement_id'],
                time_utc=row['time_utc'],
                laser_energy_v=row['laser_energy_v'],
                integration_time_us=row['integration_time_us'],
                num_pulses=row['num_pulses'],
                operation_mode=row['operation_mode']
            )
            for row in rows
        ]
        
        return measurements
    
    except Exception as e:
        logger.error(f"Error fetching measurements: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")


@router.get("/spectrum", response_model=SpectralResponse)
async def get_spectrum(
    measurement_id: int = Query(..., description="Measurement ID"),
    lambda_min: float = Query(200.0, description="Minimum wavelength (nm)"),
    lambda_max: float = Query(800.0, description="Maximum wavelength (nm)"),
    zoom_level: int = Query(0, ge=0, le=10, description="Zoom level"),
    use_cache: bool = Query(True, description="Use cache")
):
    """
    Retrieve spectral data with adaptive min-max downsampling.
    
    This endpoint implements the LunarAtlas downsampling algorithm:
    1. Query spectral data from PostgreSQL
    2. Apply min-max downsampling based on zoom level
    3. Cache results in Redis
    4. Return optimized dataset for visualization
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
            cleaned_intensity
        FROM spectral_data
        WHERE 
            measurement_id = $1
            AND wavelength_nm >= $2
            AND wavelength_nm <= $3
        ORDER BY wavelength_nm ASC
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
                "data": [],
                "metadata": {
                    "message": "No data in specified range"
                },
                "cached": False,
                "query_time_ms": db_time
            }
            return SpectralResponse(**result)
        
        # Convert to NumPy array
        data = np.array([
            [float(row['wavelength_nm']), float(row['cleaned_intensity'])]
            for row in rows
        ])
        
        logger.info(
            f"Fetched {len(data)} points for measurement {measurement_id} "
            f"in {db_time:.2f}ms"
        )
        
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
        
        # Build response
        result = {
            "mode": downsample_result['mode'],
            "measurement_id": measurement_id,
            "lambda_min": lambda_min,
            "lambda_max": lambda_max,
            "zoom_level": zoom_level,
            "z_max": downsample_result.get('z_max'),
            "data": downsample_result['data'],
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
        
        return SpectralResponse(**result)
    
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
