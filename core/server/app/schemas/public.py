from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PublicMeta(BaseModel):
    """Standard metadata envelope for public API responses, resembling ISRO catalog services."""
    agency: str = Field("ISRO", description="Space Agency providing the data source")
    data_standard: str = Field("PDS4", description="Data standard compliance framework (e.g., Planetary Data System)")
    licensing: str = Field("ISRO Open Data Sharing Policy (ISDA)", description="Licensing and terms of use statement")
    api_version: str = Field("1.0.0", description="Public Developer API major/minor version")
    rate_limit_limit: int = Field(1000, description="Allocated rate limit per window")
    rate_limit_remaining: int = Field(999, description="Remaining requests within the current window")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC Timestamp of API response generation")

class PublicResponseEnvelope(BaseModel):
    """Top-level response envelope for public APIs to standardize third-party integrations."""
    meta: PublicMeta = Field(default_factory=PublicMeta)
    results: Any = Field(..., description="The main data results payload")
    links: Dict[str, Optional[str]] = Field(default_factory=dict, description="HATEOAS style navigation links (self, next, prev, parent)")

class PublicMission(BaseModel):
    """Public details of a planetary science mission."""
    mission_id: str
    mission_code: str
    mission_name: str
    organization: str
    launch_date: Optional[datetime] = None
    target_body: str
    description: Optional[str] = None

class PublicInstrument(BaseModel):
    """Public details of a scientific instrument payload."""
    instrument_id: str
    mission_id: int
    instrument_code: str
    instrument_name: str
    instrument_type: str
    description: Optional[str] = None

class PublicObservation(BaseModel):
    """Public details of an observation session/product."""
    observation_id: str
    session_id: str
    logical_identifier: str
    observation_code: str
    observation_number: int
    sub_index: int
    start_time: datetime
    stop_time: Optional[datetime] = None
    pds_version_id: str
    information_model_version: str
    processing_level: str
    purpose: str
    observation_date: datetime
    target_description: Optional[str] = None
    record_count: Optional[int] = None

class PublicMeasurement(BaseModel):
    """Public metadata and physical telemetry values for a single laser shot/measurement."""
    measurement_id: str
    observation_id: str
    measurement_index: int
    time_utc: Optional[datetime] = None
    measurement_count: Optional[int] = None
    operation_mode: Optional[str] = None
    measurement_type: Optional[str] = None
    is_background: bool = False
    integration_time_us: Optional[int] = None
    number_of_pulses: Optional[int] = None
    laser_energy_v: Optional[int] = None

class PublicSpectrumPoint(BaseModel):
    """A single calibrated or cleaned wavelength channel's intensity value."""
    wavelength_nm: float = Field(..., description="Wavelength in nanometers (nm)")
    intensity: float = Field(..., description="Processed/Cleaned intensity in counts")
    raw_intensity: Optional[float] = Field(None, description="Uncleaned/Raw intensity in counts")

class PublicSpectrumDetail(BaseModel):
    """Scientific spectrum data product conforming to standard PDS metadata layouts."""
    measurement_id: str
    processing_level: str = Field(..., description="Processing status (e.g., Cleaned/Calibrated)")
    points_count: int = Field(..., description="Number of wavelength-intensity records returned")
    wavelength_range: Dict[str, float] = Field(..., description="Min/max spectral boundaries in nm")
    data: List[PublicSpectrumPoint] = Field(..., description="Wavelength and intensity point list")
