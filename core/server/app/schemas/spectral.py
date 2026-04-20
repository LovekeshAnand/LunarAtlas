from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime

class SpectralDataPoint(BaseModel):
    """Single spectral data point"""
    wavelength_nm: float
    intensity: float

class DownsampledBucket(BaseModel):
    """Min-max downsampled bucket"""
    bucket_id: int
    lambda_min: float
    intensity_min: float
    lambda_max: float
    intensity_max: float
    n_points: int
    lambda_center: float

class SpectralQueryParams(BaseModel):
    """Query parameters for spectral data"""
    measurement_id: str = Field(..., description="Measurement ID to query")
    lambda_min: float = Field(200.0, description="Minimum wavelength (nm)")
    lambda_max: float = Field(800.0, description="Maximum wavelength (nm)")
    zoom_level: int = Field(0, ge=0, le=10, description="Zoom level (0-10)")
    use_cache: bool = Field(True, description="Use Redis cache")

class SpectralResponse(BaseModel):
    """Response model for spectral data query"""
    mode: str = Field(..., description="Response mode: 'downsampled', 'raw', or 'empty'")
    measurement_id: str
    lambda_min: float
    lambda_max: float
    zoom_level: int
    z_max: Optional[int] = None
    data: Union[List[DownsampledBucket], List[SpectralDataPoint]]
    metadata: dict
    cached: bool = Field(False, description="Was this response served from cache?")
    query_time_ms: float = Field(..., description="Database query time in milliseconds")

class MeasurementInfo(BaseModel):
    """Measurement metadata mapped to measurement_clean table"""
    measurement_id: str
    file_info_id: str
    measurement_index: int
    time_utc: Union[datetime, None] = None
    measurement_count: Optional[int] = None
    operation_mode: Optional[str] = None
    measurement_type: Optional[str] = None
    is_background: bool = False
    integration_time_us: Optional[int] = None
    number_of_pulses: Optional[int] = None
    laser_energy_v: Optional[int] = None

class HealthResponse(BaseModel):
    """API health check response"""
    status: str
    version: str
    database: bool
    redis: bool
    timestamp: datetime

class NistLine(BaseModel):
    """NIST Reference Spectral Line"""
    element: str
    ionization_stage: Optional[str] = None
    wavelength_nm: float
    relative_intensity: Optional[int] = None
    aki: Optional[float] = None
    ei_ev: Optional[float] = None
    ek_ev: Optional[float] = None

class ObservationInfo(BaseModel):
    """Observation session metadata"""
    observation_id: str
    target_name: Optional[str] = None
    creation_datetime: Optional[datetime] = None
    record_count: Optional[int] = None
