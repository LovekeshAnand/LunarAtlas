from sqlalchemy import Column, String, Integer, Float, DateTime, Date, ForeignKey, BigInteger, Boolean
from sqlalchemy.sql import func
from app.models.base import Base

class Mission(Base):
    __tablename__ = "mission"
    
    mission_id = Column(String(20), primary_key=True)
    mission_code = Column(String(20), unique=True)
    mission_name = Column(String(100))
    organization = Column(String(200))
    launch_date = Column(DateTime(timezone=True))
    target_body = Column(String(100))
    description = Column(String)

class Instrument(Base):
    __tablename__ = "instrument"
    
    instrument_id = Column(String(50), primary_key=True)
    mission_id = Column(String(20), ForeignKey("mission.mission_id", ondelete="CASCADE"))
    instrument_name = Column(String(100))
    instrument_type = Column(String(50))
    wavelength_start = Column(Float)
    wavelength_end = Column(Float)
    resolution = Column(String(50))
    description = Column(String)

class InstrumentSpecLibs(Base):
    __tablename__ = "instrument_spec_libs"
    
    spec_id = Column(String(50), primary_key=True)
    instrument_id = Column(String(50), ForeignKey("instrument.instrument_id", ondelete="CASCADE"))
    detector_type = Column(String(50))
    spectral_channels = Column(Integer)
    calibration_source = Column(String)

class DatasetVersion(Base):
    __tablename__ = "dataset_version"
    
    dataset_version_id = Column(String(50), primary_key=True)
    spec_id = Column(String(50), ForeignKey("instrument_spec_libs.spec_id", ondelete="CASCADE"))
    version_code = Column(String(20))
    release_date = Column(Date)
    processing_level = Column(String(20))
    description = Column(String)

class ObservationSession(Base):
    __tablename__ = "observation_session"
    
    session_id = Column(String(50), primary_key=True)
    dataset_version_id = Column(String(50), ForeignKey("dataset_version.dataset_version_id", ondelete="CASCADE"))
    observation_date = Column(Date, index=True)
    orbit_number = Column(Integer)
    session_type = Column(String(50))

class Observation(Base):
    __tablename__ = "observation"
    
    observation_id = Column(String(100), primary_key=True)
    session_id = Column(String(50), ForeignKey("observation_session.session_id", ondelete="CASCADE"))
    start_time = Column(DateTime(timezone=True))
    stop_time = Column(DateTime(timezone=True))
    xml_label_name = Column(String(255))
    information_model_version = Column(String(50))
    processing_level = Column(String(20))

class ObservationFileInfo(Base):
    __tablename__ = "observation_file_info"
    
    file_info_id = Column(String(100), primary_key=True)
    observation_id = Column(String(100), ForeignKey("observation.observation_id", ondelete="CASCADE"))
    file_name = Column(String(255))
    file_size_bytes = Column(BigInteger)
    md5_checksum = Column(String(32))
    record_count = Column(Integer)

class MeasurementRaw(Base):
    __tablename__ = "measurement_raw"
    
    measurement_id = Column(String(50), primary_key=True)
    file_info_id = Column(String(100), ForeignKey("observation_file_info.file_info_id", ondelete="CASCADE"))
    shot_number = Column(Integer)
    laser_fire_status = Column(Integer)
    laser_energy_v = Column(Integer)
    integration_time_us = Column(Integer)
    is_valid_plasma = Column(Boolean)
    is_background = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SpectralDataRaw(Base):
    __tablename__ = "spectral_data_raw"
    
    spectral_data_id = Column(BigInteger, primary_key=True, autoincrement=True)
    measurement_id = Column(String(50), ForeignKey("measurement_raw.measurement_id", ondelete="CASCADE"), index=True)
    wavelength_nm = Column(Float, index=True)
    intensity = Column(Float)

class MeasurementClean(Base):
    __tablename__ = "measurement_clean"
    
    measurement_id = Column(String(50), primary_key=True)
    file_info_id = Column(String(100), ForeignKey("observation_file_info.file_info_id", ondelete="CASCADE"))
    shot_number = Column(Integer)
    laser_fire_status = Column(Integer)
    laser_energy_v = Column(Integer)
    integration_time_us = Column(Integer)
    is_valid_plasma = Column(Boolean)
    is_background = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SpectralDataClean(Base):
    __tablename__ = "spectral_data_clean"
    
    spectral_data_id = Column(BigInteger, primary_key=True, autoincrement=True)
    measurement_id = Column(String(50), ForeignKey("measurement_clean.measurement_id", ondelete="CASCADE"), index=True)
    wavelength_nm = Column(Float, index=True)
    intensity = Column(Float)

class NistLine(Base):
    __tablename__ = "nist_lines"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    element = Column(String(10))
    ionization_stage = Column(String(10))
    wavelength_nm = Column(Float, index=True)
    relative_intensity = Column(Integer)
