from sqlalchemy import Column, String, Integer, Float, DateTime, Date, ForeignKey, BigInteger, Boolean
from sqlalchemy.sql import func
from app.models.base import Base

class Mission(Base):
    __tablename__ = "mission"
    
    mission_id = Column(String(20), primary_key=True)
    mission_code = Column(String(20), unique=True, nullable=False)
    mission_name = Column(String(100), nullable=False)
    organization = Column(String(200), nullable=False)
    launch_date = Column(DateTime(timezone=True), nullable=False)
    target_body = Column(String(100))
    description = Column(String)

class Instrument(Base):
    __tablename__ = "instrument"
    
    instrument_id = Column(String(50), primary_key=True)
    mission_id = Column(String(20), ForeignKey("mission.mission_id", ondelete="CASCADE"), nullable=False)
    instrument_code = Column(String(50), nullable=False)
    instrument_name = Column(String(255))
    instrument_type = Column(String(100))
    description = Column(String)

class InstrumentSpecLibs(Base):
    __tablename__ = "instrument_spec_libs"
    
    spec_id = Column(String(50), primary_key=True)
    instrument_id = Column(String(50), ForeignKey("instrument.instrument_id", ondelete="CASCADE"), unique=True, nullable=False)
    wavelength_min_nm = Column(Float)
    wavelength_max_nm = Column(Float)
    spectral_resolution_nm = Column(Float)
    pixel_count = Column(Integer)
    detector_type = Column(String(200))
    calibration_version = Column(String(100))

class DatasetVersion(Base):
    __tablename__ = "dataset_version"
    
    dataset_version_id = Column(String(50), primary_key=True)
    spec_id = Column(String(50), ForeignKey("instrument_spec_libs.spec_id", ondelete="CASCADE"))
    version_label = Column(String(50), unique=True, nullable=False)
    version_number = Column(String(20))
    data_level = Column(String(10))
    processing_level = Column(String(50))
    base_path = Column(String)
    description = Column(String)
    released_at = Column(Date)
    created_at = Column(DateTime(timezone=True))

class ObservationSession(Base):
    __tablename__ = "observation_session"
    
    session_id = Column(String(50), primary_key=True)
    dataset_version_id = Column(String(50), ForeignKey("dataset_version.dataset_version_id", ondelete="CASCADE"), nullable=False)
    observation_date = Column(Date, index=True, nullable=False)
    date_folder = Column(String(10))
    target_description = Column(String)
    notes = Column(String)

class Observation(Base):
    __tablename__ = "observation"
    
    observation_id = Column(String(50), primary_key=True)
    session_id = Column(String(50), ForeignKey("observation_session.session_id", ondelete="CASCADE"), nullable=False)
    logical_identifier = Column(String, unique=True)
    observation_code = Column(String(100), unique=True)
    observation_number = Column(Integer)
    sub_index = Column(Integer)
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    pds_version_id = Column(String(10))
    information_model_version = Column(String(20))
    processing_level = Column(String(50))
    purpose = Column(String(100))

class ObservationFileInfo(Base):
    __tablename__ = "observation_file_info"
    
    file_info_id = Column(String(50), primary_key=True)
    observation_id = Column(String(50), ForeignKey("observation.observation_id", ondelete="CASCADE"), unique=True, nullable=False)
    base_file_name = Column(String(255))
    md5_checksum_raw = Column(String(32))
    md5_checksum_clean = Column(String(32))
    file_size_bytes_raw = Column(BigInteger)
    file_size_bytes_clean = Column(BigInteger)
    record_count = Column(Integer)
    xml_label_name = Column(String(255))
    creation_datetime = Column(DateTime)
    storage_path_clean = Column(String)

class MeasurementRaw(Base):
    __tablename__ = "measurement_raw"
    
    measurement_id = Column(String(50), primary_key=True)
    file_info_id = Column(String(50), ForeignKey("observation_file_info.file_info_id", ondelete="CASCADE"), nullable=False)
    measurement_index = Column(Integer, nullable=False)
    time_utc = Column(DateTime)
    measurement_count = Column(Integer)
    operation_mode = Column(String(10))
    measurement_type = Column(String(5))
    force_reset_status = Column(Integer)
    laser_fire_status = Column(Integer)
    delay_time_us = Column(Float)
    integration_time_us = Column(Integer)
    number_of_pulses = Column(Integer)
    x_factor = Column(Integer)
    laser_energy_v = Column(Integer)
    laser_pump_current_a = Column(Integer)
    prr_hz = Column(Integer)
    on_off_status = Column(Integer)

class SpectralDataRaw(Base):
    __tablename__ = "spectral_data_raw"
    
    spectral_data_id = Column(BigInteger, primary_key=True, autoincrement=True)
    measurement_id = Column(String(50), ForeignKey("measurement_raw.measurement_id", ondelete="CASCADE"), index=True, nullable=False)
    wavelength_nm = Column(Float, index=True, nullable=False)
    response_count = Column(Integer, nullable=False)

class MeasurementClean(Base):
    __tablename__ = "measurement_clean"
    
    measurement_id = Column(String(50), primary_key=True)
    file_info_id = Column(String(50), ForeignKey("observation_file_info.file_info_id", ondelete="CASCADE"), nullable=False)
    measurement_index = Column(Integer, nullable=False)
    time_utc = Column(DateTime)
    measurement_count = Column(Integer)
    operation_mode = Column(String(10))
    measurement_type = Column(String(50))
    force_reset_status = Column(Integer)
    laser_fire_status = Column(Integer)
    is_valid_plasma = Column(Boolean)
    is_background = Column(Boolean)
    delay_time_us = Column(Float)
    integration_time_us = Column(Integer)
    number_of_pulses = Column(Integer)
    x_factor = Column(Integer)
    laser_energy_v = Column(Integer)
    laser_pump_current_a = Column(Integer)
    prr_hz = Column(Integer)
    on_off_status = Column(Integer)

class SpectralDataClean(Base):
    __tablename__ = "spectral_data_clean"
    
    spectral_data_id = Column(BigInteger, primary_key=True, autoincrement=True)
    measurement_id = Column(String(50), ForeignKey("measurement_clean.measurement_id", ondelete="CASCADE"), index=True, nullable=False)
    wavelength_nm = Column(Float, index=True, nullable=False)
    intensity = Column(Float, nullable=False)

class NistLine(Base):
    __tablename__ = "nist_lines"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    element = Column(String(10), nullable=False)
    ionization_stage = Column(String(10))
    wavelength_nm = Column(Float, index=True, nullable=False)
    relative_intensity = Column(Integer)
