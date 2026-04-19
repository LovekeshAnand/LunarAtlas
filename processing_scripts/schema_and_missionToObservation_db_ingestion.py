import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DB_NAME = "LunarAtlas"

DB_CONFIG = {
    "host": "localhost",
    "user": "postgres",
    "password": "your_password_here",
    "port": 5432
}

# ============================================================================
# SQL (your full schema + inserts)
# ============================================================================
SQL_SCHEMA = """
-- ======================
-- MISSION
-- ======================
CREATE TABLE IF NOT EXISTS mission (
    mission_id VARCHAR(20) PRIMARY KEY,
    mission_code VARCHAR(20) UNIQUE,
    mission_name VARCHAR(100),
    organization VARCHAR(200),
    launch_date TIMESTAMPTZ,
    target_body VARCHAR(100),
    description TEXT
);

INSERT INTO mission VALUES (
    '1','CH3','LVM3-M4/Chandrayaan-3 Mission','ISRO',
    '2023-07-13 14:35:00+05:30',
    'Moon-Lunar South Pole Region',
    'Chandrayaan-3 mission'
) ON CONFLICT DO NOTHING;

-- ======================
-- INSTRUMENT
-- ======================
CREATE TABLE IF NOT EXISTS instrument (
    instrument_id VARCHAR(50) PRIMARY KEY,
    mission_id VARCHAR(20),
    instrument_code VARCHAR(50),
    instrument_name VARCHAR(255),
    instrument_type VARCHAR(100),
    description TEXT,
    FOREIGN KEY (mission_id) REFERENCES mission(mission_id)
);

INSERT INTO instrument VALUES (
    'CH3 LIBS','1','LIBS',
    'Laser-Induced Breakdown Spectroscopy',
    'Spectrometer','LIBS instrument'
) ON CONFLICT DO NOTHING;

-- ======================
-- DATASET VERSION
-- ======================
CREATE TABLE IF NOT EXISTS dataset_version (
    dataset_version_id VARCHAR(50) PRIMARY KEY,
    spec_id VARCHAR(50),
    version_label VARCHAR(50),
    version_number VARCHAR(20),
    data_level VARCHAR(10),
    processing_level VARCHAR(50),
    base_path TEXT,
    description TEXT,
    released_at DATE,
    created_at TIMESTAMPTZ
);

INSERT INTO dataset_version VALUES (
    'CH3_LIBS_V2','LIBS_SPEC_001','lib-v2','v2','l1','calibrated',
    'C:\\ch3_libs\\lib-v2','dataset','2024-08-23','2024-05-16'
) ON CONFLICT DO NOTHING;

-- ======================
-- OBSERVATION SESSION
-- ======================
CREATE TABLE IF NOT EXISTS observation_session (
    session_id VARCHAR(50) PRIMARY KEY,
    dataset_version_id VARCHAR(50),
    observation_date DATE,
    date_folder VARCHAR(10),
    target_description TEXT,
    notes TEXT
);

-- ======================
-- OBSERVATION
-- ======================
CREATE TABLE IF NOT EXISTS observation (
    observation_id VARCHAR(50) PRIMARY KEY,
    session_id VARCHAR(50),
    logical_identifier TEXT,
    observation_code VARCHAR(100),
    observation_number INT,
    sub_index SMALLINT,
    start_time TIMESTAMP,
    stop_time TIMESTAMP,
    pds_version_id VARCHAR(10),
    information_model_version VARCHAR(20),
    processing_level VARCHAR(50),
    purpose VARCHAR(100)
);

-- ======================
-- FILE INFO
-- ======================
CREATE TABLE IF NOT EXISTS observation_file_info (
    file_info_id VARCHAR(50) PRIMARY KEY,
    observation_id VARCHAR(50) UNIQUE,
    base_file_name VARCHAR(255),
    md5_checksum_raw VARCHAR(32),
    md5_checksum_clean VARCHAR(32),
    file_size_bytes_raw BIGINT,
    file_size_bytes_clean BIGINT,
    record_count INT,
    xml_label_name VARCHAR(255),
    creation_datetime TIMESTAMP,
    storage_path_clean TEXT
);

-- ======================
-- MEASUREMENT CLEAN
-- ======================
CREATE TABLE IF NOT EXISTS measurement_clean (
    measurement_id VARCHAR(50) PRIMARY KEY,
    file_info_id VARCHAR(50),
    measurement_index INT,
    time_utc TIMESTAMP,
    measurement_count INT,
    operation_mode VARCHAR(10),
    measurement_type VARCHAR(50),
    force_reset_status SMALLINT,
    laser_fire_status SMALLINT,
    is_valid_plasma BOOLEAN,
    is_background BOOLEAN,
    delay_time_us DOUBLE PRECISION,
    integration_time_us INT,
    number_of_pulses INT,
    x_factor INT,
    laser_energy_v INT,
    laser_pump_current_a INT,
    prr_hz INT,
    on_off_status SMALLINT
);

-- ======================
-- SPECTRAL CLEAN
-- ======================
CREATE TABLE IF NOT EXISTS spectral_data_clean (
    spectral_data_id BIGSERIAL PRIMARY KEY,
    measurement_id VARCHAR(50),
    wavelength_nm DOUBLE PRECISION,
    intensity DOUBLE PRECISION
);
"""

# ============================================================================
# FUNCTIONS
# ============================================================================
def create_database():
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG["port"]
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    exists = cursor.fetchone()

    if not exists:
        print(f"[INFO] Creating database: {DB_NAME}")
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
    else:
        print(f"[INFO] Database already exists")

    cursor.close()
    conn.close()


def setup_schema():
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        database=DB_NAME,
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        port=DB_CONFIG["port"]
    )
    cursor = conn.cursor()

    print("[INFO] Creating tables...")
    cursor.execute(SQL_SCHEMA)

    conn.commit()
    cursor.close()
    conn.close()

    print("[DONE] Database setup complete!")


# ============================================================================
# RUN
# ============================================================================
if __name__ == "__main__":
    create_database()
    setup_schema()