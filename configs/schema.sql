-- LunarAtlas Database Schema
-- Complete schema for Chandrayaan-3 LIBS data

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ============================================
-- 1. MISSION TABLE
-- ============================================
CREATE TABLE mission (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    agency VARCHAR(255),
    launch_date DATE,
    landing_date DATE,
    status VARCHAR(50),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 2. INSTRUMENT TABLE
-- ============================================
CREATE TABLE instrument (
    id SERIAL PRIMARY KEY,
    mission_id INTEGER REFERENCES mission(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    wavelength_range_min NUMERIC(8,2),
    wavelength_range_max NUMERIC(8,2),
    spectral_resolution NUMERIC(6,4),
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 3. OBSERVATION TABLE
-- ============================================
CREATE TABLE observation (
    id SERIAL PRIMARY KEY,
    instrument_id INTEGER REFERENCES instrument(id) ON DELETE CASCADE,
    start_time TIMESTAMPTZ NOT NULL,
    stop_time TIMESTAMPTZ,
    target_name VARCHAR(255),
    site_latitude NUMERIC(10,6),
    site_longitude NUMERIC(10,6),
    operation_mode VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 4. FILE VERSION TABLE
-- ============================================
CREATE TABLE file_version (
    id SERIAL PRIMARY KEY,
    observation_id INTEGER REFERENCES observation(id) ON DELETE CASCADE,
    filename VARCHAR(512) NOT NULL,
    file_size_bytes BIGINT,
    md5_checksum VARCHAR(32) UNIQUE,
    algorithm_version VARCHAR(50),
    processing_level VARCHAR(20),
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 5. MEASUREMENT TABLE
-- ============================================
CREATE TABLE measurement (
    id SERIAL PRIMARY KEY,
    file_version_id INTEGER REFERENCES file_version(id) ON DELETE CASCADE,
    measurement_id INTEGER NOT NULL,
    time_utc TIMESTAMPTZ NOT NULL,
    laser_energy_v INTEGER,
    integration_time_us INTEGER,
    num_pulses INTEGER,
    operation_mode VARCHAR(50),
    is_background BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique measurement per file
    UNIQUE(file_version_id, measurement_id)
);

-- Create index on measurement_id for partitioning
CREATE INDEX idx_measurement_id ON measurement(measurement_id);

-- ============================================
-- 6. SPECTRAL DATA - PARTITIONED TABLE
-- ============================================
CREATE TABLE spectral_data (
    id BIGSERIAL,
    measurement_id INTEGER NOT NULL REFERENCES measurement(id) ON DELETE CASCADE,
    wavelength_nm NUMERIC(8,2) NOT NULL,
    cleaned_intensity NUMERIC(10,2),
    raw_intensity NUMERIC(10,2),
    is_background BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (measurement_id);

-- Create partitions
CREATE TABLE spectral_data_p0 PARTITION OF spectral_data
    FOR VALUES FROM (0) TO (1000);

CREATE TABLE spectral_data_p1 PARTITION OF spectral_data
    FOR VALUES FROM (1000) TO (2000);

CREATE TABLE spectral_data_p2 PARTITION OF spectral_data
    FOR VALUES FROM (2000) TO (3000);

CREATE TABLE spectral_data_p3 PARTITION OF spectral_data
    FOR VALUES FROM (3000) TO (4000);

CREATE TABLE spectral_data_p4 PARTITION OF spectral_data
    FOR VALUES FROM (4000) TO (5000);

-- ============================================
-- 7. NIST REFERENCE LINES
-- ============================================
CREATE TABLE nist_lines (
    id SERIAL PRIMARY KEY,
    element VARCHAR(10) NOT NULL,
    ionization_stage VARCHAR(10),
    wavelength_nm NUMERIC(10,4) NOT NULL,
    aki NUMERIC,
    ei_ev NUMERIC,
    ek_ev NUMERIC,
    lower_level VARCHAR(255),
    upper_level VARCHAR(255),
    relative_intensity INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================

-- BRIN indexes on wavelength
CREATE INDEX idx_wavelength_brin_p0 ON spectral_data_p0 
    USING BRIN (wavelength_nm) WITH (pages_per_range = 64);

CREATE INDEX idx_wavelength_brin_p1 ON spectral_data_p1 
    USING BRIN (wavelength_nm) WITH (pages_per_range = 64);

CREATE INDEX idx_wavelength_brin_p2 ON spectral_data_p2 
    USING BRIN (wavelength_nm) WITH (pages_per_range = 64);

CREATE INDEX idx_wavelength_brin_p3 ON spectral_data_p3 
    USING BRIN (wavelength_nm) WITH (pages_per_range = 64);

CREATE INDEX idx_wavelength_brin_p4 ON spectral_data_p4 
    USING BRIN (wavelength_nm) WITH (pages_per_range = 64);

-- NIST reference line indexes
CREATE INDEX idx_nist_wavelength ON nist_lines(wavelength_nm);
CREATE INDEX idx_nist_element ON nist_lines(element);

-- ============================================
-- SAMPLE DATA
-- ============================================

INSERT INTO mission (name, agency, launch_date, landing_date, status, description)
VALUES 
    ('Chandrayaan-3', 'ISRO', '2023-07-14', '2023-08-23', 'Active', 'Indian lunar mission with LIBS instrument');

INSERT INTO instrument (mission_id, name, type, wavelength_range_min, wavelength_range_max, spectral_resolution)
VALUES 
    (1, 'ChaSTE-LIBS', 'LIBS', 164.35, 878.26, 0.01);

INSERT INTO observation (instrument_id, start_time, target_name, site_latitude, site_longitude, operation_mode)
VALUES 
    (1, NOW(), 'Lunar South Pole', -89.5, 45.0, 'Science');

INSERT INTO file_version (observation_id, filename, file_size_bytes, md5_checksum, algorithm_version, processing_level)
VALUES 
    (1, 'CH3_LIBS_20230823_001.dat', 1048576, 'a1b2c3d4e5f6', 'v1.0', 'L1');

INSERT INTO measurement (file_version_id, measurement_id, time_utc, laser_energy_v, integration_time_us, num_pulses, operation_mode)
VALUES 
    (1, 1, NOW(), 100, 1000, 50, 'Normal'),
    (1, 2, NOW(), 100, 1000, 50, 'Normal');
