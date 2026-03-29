"""
LunarAtlas Spectral Visualization API
FastAPI backend with adaptive min-max downsampling
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import math

app = FastAPI(
    title="LunarAtlas Spectral API",
    description="Adaptive min-max downsampling for LIBS spectroscopy data",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "spectroscopy_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "lovekesh"),
    "port": os.getenv("DB_PORT", "5432")
}

# Algorithm constants
BASE_BUCKETS = 1000
MIN_BUCKET_SIZE = 0.01  # nm
OVERLAP_PCT = 0.05
MAX_ZOOM = 10


# Response Models
class BucketData(BaseModel):
    bucket_id: int
    start_wl: float
    end_wl: float
    min_intensity: float
    max_intensity: float
    min_wavelength: float
    max_wavelength: float
    point_count: int
    data_present: bool = True


class SpectralResponse(BaseModel):
    status: str
    metadata: Dict[str, Any]
    parameters: Dict[str, Any]
    buckets: List[BucketData]
    processing_time_ms: float


class RawDataPoint(BaseModel):
    wavelength: float
    intensity: float


class RawDataResponse(BaseModel):
    status: str
    metadata: Dict[str, Any]
    data_points: List[RawDataPoint]
    processing_time_ms: float


# Database helper
def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


# Core algorithm functions
def calculate_bucket_size(wavelength_span: float, zoom_level: int) -> float:
    """
    Calculate bucket size based on zoom level
    Formula: bucket_size = wavelength_span / (BASE_BUCKETS * 2^zoom_level)
    """
    if zoom_level >= MAX_ZOOM:
        return 0  # Trigger raw data mode
    
    bucket_size = wavelength_span / (BASE_BUCKETS * (2 ** zoom_level))
    
    # Apply floor constraint
    if bucket_size < MIN_BUCKET_SIZE:
        return MIN_BUCKET_SIZE
    
    return bucket_size


def calculate_bucket_count(wavelength_span: float, bucket_size: float) -> int:
    """Calculate number of buckets needed"""
    return math.ceil(wavelength_span / bucket_size)


def generate_bucket_boundaries(
    min_wl: float, 
    max_wl: float, 
    bucket_size: float
) -> List[tuple]:
    """
    Generate bucket boundaries with overlap
    Returns: List of (start_wl, end_wl) tuples
    """
    wavelength_span = max_wl - min_wl
    bucket_count = calculate_bucket_count(wavelength_span, bucket_size)
    overlap = bucket_size * OVERLAP_PCT
    
    boundaries = []
    for i in range(bucket_count):
        # First bucket has no left overlap
        start = min_wl + (i * bucket_size) - (overlap if i > 0 else 0)
        end = start + bucket_size + overlap
        
        # Ensure we don't go below min_wl
        start = max(start, min_wl)
        
        boundaries.append((start, end))
    
    return boundaries


def perform_minmax_downsampling(
    observation_id: int,
    min_wl: float,
    max_wl: float,
    bucket_size: float
) -> List[BucketData]:
    """
    Perform min-max downsampling on spectral data
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    boundaries = generate_bucket_boundaries(min_wl, max_wl, bucket_size)
    buckets = []
    
    try:
        for idx, (start, end) in enumerate(boundaries):
            # Query for points in this bucket
            query = """
                SELECT 
                    wavelength_nm,
                    cleaned_intensity
                FROM spectroscopy_measurements
                WHERE measurement_id = %s
                  AND wavelength_nm >= %s
                  AND wavelength_nm < %s
                ORDER BY wavelength_nm
            """
            
            cursor.execute(query, (observation_id, start, end))
            points = cursor.fetchall()
            
            if not points:
                # Empty bucket
                buckets.append(BucketData(
                    bucket_id=idx,
                    start_wl=start,
                    end_wl=end,
                    min_intensity=0,
                    max_intensity=0,
                    min_wavelength=start,
                    max_wavelength=end,
                    point_count=0,
                    data_present=False
                ))
                continue
            
            # Find min and max
            intensities = [p['cleaned_intensity'] for p in points]
            wavelengths = [p['wavelength_nm'] for p in points]
            
            min_idx = intensities.index(min(intensities))
            max_idx = intensities.index(max(intensities))
            
            buckets.append(BucketData(
                bucket_id=idx,
                start_wl=start,
                end_wl=end,
                min_intensity=intensities[min_idx],
                max_intensity=intensities[max_idx],
                min_wavelength=wavelengths[min_idx],
                max_wavelength=wavelengths[max_idx],
                point_count=len(points),
                data_present=True
            ))
    
    finally:
        cursor.close()
        conn.close()
    
    return buckets


def get_raw_data(observation_id: int, min_wl: float, max_wl: float) -> List[RawDataPoint]:
    """Get raw data points without downsampling"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                wavelength_nm as wavelength,
                cleaned_intensity as intensity
            FROM spectroscopy_measurements
            WHERE measurement_id = %s
              AND wavelength_nm >= %s
              AND wavelength_nm <= %s
            ORDER BY wavelength_nm
        """
        
        cursor.execute(query, (observation_id, min_wl, max_wl))
        points = cursor.fetchall()
        
        return [RawDataPoint(**p) for p in points]
    
    finally:
        cursor.close()
        conn.close()


# API Endpoints
@app.get("/")
def root():
    """API root endpoint"""
    return {
        "message": "LunarAtlas Spectral Visualization API",
        "version": "1.0.0",
        "endpoints": {
            "spectral": "/api/v1/spectral",
            "raw": "/api/v1/spectral/raw",
            "observations": "/api/v1/observations",
            "health": "/health"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}


@app.get("/api/v1/observations")
def list_observations():
    """List all available observations"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                measurement_id,
                time_utc,
                measurement_count,
                MIN(wavelength_nm) as min_wavelength,
                MAX(wavelength_nm) as max_wavelength,
                COUNT(*) as point_count
            FROM spectroscopy_measurements
            GROUP BY measurement_id, time_utc, measurement_count
            ORDER BY measurement_id
        """
        
        cursor.execute(query)
        observations = cursor.fetchall()
        
        return {
            "status": "success",
            "count": len(observations),
            "observations": observations
        }
    
    finally:
        cursor.close()
        conn.close()


@app.get("/api/v1/spectral", response_model=SpectralResponse)
def get_spectral_data(
    observation_id: int = Query(..., description="Observation/Measurement ID"),
    min_wavelength: float = Query(..., ge=0, le=1000, description="Minimum wavelength (nm)"),
    max_wavelength: float = Query(..., ge=0, le=1000, description="Maximum wavelength (nm)"),
    zoom_level: int = Query(0, ge=0, le=MAX_ZOOM, description="Zoom level (0-10)")
):
    """
    Get downsampled spectral data with min-max bucketing
    
    - **observation_id**: Measurement ID from database
    - **min_wavelength**: Start of wavelength range (nm)
    - **max_wavelength**: End of wavelength range (nm)
    - **zoom_level**: Zoom level (0=overview, 10=raw data)
    """
    start_time = datetime.now()
    
    # Validation
    if min_wavelength >= max_wavelength:
        raise HTTPException(status_code=400, detail="min_wavelength must be < max_wavelength")
    
    wavelength_span = max_wavelength - min_wavelength
    
    if wavelength_span < 1.0:
        raise HTTPException(status_code=400, detail="Wavelength span must be at least 1.0 nm")
    
    # Calculate bucket parameters
    bucket_size = calculate_bucket_size(wavelength_span, zoom_level)
    
    # Check if raw data mode
    if bucket_size == 0 or zoom_level >= MAX_ZOOM:
        raise HTTPException(
            status_code=400, 
            detail=f"Use /api/v1/spectral/raw endpoint for zoom level {MAX_ZOOM}"
        )
    
    bucket_count = calculate_bucket_count(wavelength_span, bucket_size)
    
    # Perform downsampling
    buckets = perform_minmax_downsampling(
        observation_id, 
        min_wavelength, 
        max_wavelength, 
        bucket_size
    )
    
    # Calculate processing time
    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    
    # Build response
    return SpectralResponse(
        status="success",
        metadata={
            "observation_id": observation_id,
            "algorithm_version": "minmax_v1.0.0",
            "processing_timestamp": datetime.now().isoformat(),
            "returned_bucket_count": len(buckets)
        },
        parameters={
            "wavelength_range": [min_wavelength, max_wavelength],
            "wavelength_span": wavelength_span,
            "zoom_level": zoom_level,
            "bucket_size_nm": bucket_size,
            "bucket_count": bucket_count,
            "overlap_percentage": OVERLAP_PCT * 100
        },
        buckets=buckets,
        processing_time_ms=round(processing_time, 2)
    )


@app.get("/api/v1/spectral/raw", response_model=RawDataResponse)
def get_raw_spectral_data(
    observation_id: int = Query(..., description="Observation/Measurement ID"),
    min_wavelength: float = Query(..., ge=0, le=1000, description="Minimum wavelength (nm)"),
    max_wavelength: float = Query(..., ge=0, le=1000, description="Maximum wavelength (nm)")
):
    """
    Get raw spectral data without downsampling
    Use this for very narrow wavelength ranges or maximum zoom
    """
    start_time = datetime.now()
    
    # Validation
    if min_wavelength >= max_wavelength:
        raise HTTPException(status_code=400, detail="min_wavelength must be < max_wavelength")
    
    # Get raw data
    data_points = get_raw_data(observation_id, min_wavelength, max_wavelength)
    
    # Calculate processing time
    processing_time = (datetime.now() - start_time).total_seconds() * 1000
    
    return RawDataResponse(
        status="success",
        metadata={
            "observation_id": observation_id,
            "processing_timestamp": datetime.now().isoformat(),
            "point_count": len(data_points)
        },
        data_points=data_points,
        processing_time_ms=round(processing_time, 2)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
