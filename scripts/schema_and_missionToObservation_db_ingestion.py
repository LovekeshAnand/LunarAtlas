"""
CH3 LIBS Database Setup Script
==============================
This script creates the complete PostgreSQL database schema for the Chandrayaan-3 LIBS mission
and populates it with the provided data.

Requirements:
    - PostgreSQL server must be installed and running
    - psycopg2 library (install via: pip install psycopg2-binary)

Usage:
    python ch3_libs_db_setup.py

The script will:
    1. Create a new database 'LunarAtlas' (if it doesn't exist)
    2. Create all required tables
    3. Insert the provided data
    4. Display completion status

Note: Change database connection parameters (host, user, password) as needed for your setup.
"""

import psycopg2
from psycopg2 import sql, connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys


def get_connection_params():
    """
    Get database connection parameters.
    Modify these values according to your PostgreSQL setup.
    """
    return {
        'host': 'localhost',
        'user': 'postgres',
        'password': 'postgres',  # Change to your PostgreSQL password
        'port': 5432
    }


def create_database(conn, db_name='LunarAtlas'):
    """Create the database if it doesn't exist."""
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")
        print(f"[INFO] Dropped existing database '{db_name}' (if it existed)")
    except Exception as e:
        print(f"[WARNING] Could not drop database: {e}")
    
    try:
        cursor.execute(f"CREATE DATABASE {db_name};")
        print(f"[SUCCESS] Created database '{db_name}'")
    except psycopg2.Error as e:
        print(f"[ERROR] Failed to create database: {e}")
        cursor.close()
        return False
    
    cursor.close()
    return True


def connect_to_database(host, user, password, port, database):
    """Connect to a specific database."""
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            port=port,
            database=database
        )
        return conn
    except psycopg2.Error as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        return None


def execute_sql(cursor, sql_query, description=""):
    """Execute a single SQL query."""
    try:
        cursor.execute(sql_query)
        if description:
            print(f"[SUCCESS] {description}")
        return True
    except psycopg2.Error as e:
        print(f"[ERROR] Failed to execute: {description}")
        print(f"        Error: {e}")
        return False


def create_tables(cursor):
    """Create all required tables."""
    print("\n--- CREATING TABLES ---")
    
    # TABLE: mission
    sql_mission = """
    CREATE TABLE mission ( 
        mission_id      VARCHAR(20) PRIMARY KEY NOT NULL, 
        mission_code    VARCHAR(20) UNIQUE NOT NULL, 
        mission_name    VARCHAR(100) NOT NULL, 
        organization    VARCHAR(200) NOT NULL, 
        launch_date     TIMESTAMPTZ NOT NULL,
        target_body     VARCHAR(100), 
        description     TEXT
    );
    """
    execute_sql(cursor, sql_mission, "Created table: mission")
    
    # TABLE: instrument
    sql_instrument = """
    CREATE TABLE instrument ( 
        instrument_id    VARCHAR(50) PRIMARY KEY NOT NULL,
        mission_id       VARCHAR(20) NOT NULL, 
        instrument_code  VARCHAR(50) NOT NULL,
        instrument_name  VARCHAR(255), 
        instrument_type  VARCHAR(100), 
        description      TEXT, 
        FOREIGN KEY (mission_id) REFERENCES mission(mission_id) 
    );
    """
    execute_sql(cursor, sql_instrument, "Created table: instrument")
    
    # TABLE: instrument_spec_libs
    sql_instrument_spec_libs = """
    CREATE TABLE instrument_spec_libs ( 
        spec_id                  VARCHAR(50) PRIMARY KEY NOT NULL, 
        instrument_id            VARCHAR(50) NOT NULL UNIQUE, 
        wavelength_min_nm        DOUBLE PRECISION, 
        wavelength_max_nm        DOUBLE PRECISION, 
        spectral_resolution_nm   DOUBLE PRECISION, 
        pixel_count              INT, 
        detector_type            VARCHAR(200), 
        calibration_version      VARCHAR(100), 
        FOREIGN KEY (instrument_id) REFERENCES instrument(instrument_id) 
    );
    """
    execute_sql(cursor, sql_instrument_spec_libs, "Created table: instrument_spec_libs")
    
    # TABLE: dataset_version
    sql_dataset_version = """
    CREATE TABLE dataset_version ( 
        dataset_version_id  VARCHAR(50) PRIMARY KEY NOT NULL, 
        spec_id             VARCHAR(50),
        version_label       VARCHAR(50) NOT NULL,
        version_number      VARCHAR(20),
        data_level          VARCHAR(10),
        processing_level    VARCHAR(50),
        base_path           TEXT,
        description         TEXT, 
        released_at         DATE, 
        created_at          TIMESTAMPTZ, 
        UNIQUE (version_label), 
        FOREIGN KEY (spec_id) REFERENCES instrument_spec_libs(spec_id)
    );
    """
    execute_sql(cursor, sql_dataset_version, "Created table: dataset_version")
    
    # TABLE: observation_session
    sql_observation_session = """
    CREATE TABLE observation_session ( 
        session_id           VARCHAR(50) PRIMARY KEY NOT NULL, 
        dataset_version_id   VARCHAR(50) NOT NULL,
        observation_date     DATE NOT NULL, 
        date_folder          VARCHAR(10),
        target_description   TEXT, 
        notes                TEXT, 
        UNIQUE (dataset_version_id, observation_date), 
        FOREIGN KEY (dataset_version_id) 
            REFERENCES dataset_version(dataset_version_id) 
    );
    """
    execute_sql(cursor, sql_observation_session, "Created table: observation_session")
    
    # TABLE: observation
    sql_observation = """
    CREATE TABLE observation ( 
        observation_id             VARCHAR(50) PRIMARY KEY NOT NULL, 
        session_id                 VARCHAR(50) NOT NULL, 
        logical_identifier         TEXT UNIQUE, 
        observation_code           VARCHAR(100) UNIQUE,
        observation_number         INT,
        sub_index                  SMALLINT,
        start_time                 TIMESTAMP, 
        stop_time                  TIMESTAMP,
        pds_version_id             VARCHAR(10), 
        information_model_version  VARCHAR(20), 
        processing_level           VARCHAR(50), 
        purpose                    VARCHAR(100),
        FOREIGN KEY (session_id) 
            REFERENCES observation_session(session_id) 
    );
    """
    execute_sql(cursor, sql_observation, "Created table: observation")
    
    # TABLE: observation_file_info
    sql_observation_file_info = """
    CREATE TABLE observation_file_info (
        file_info_id          VARCHAR(50)   PRIMARY KEY,
        observation_id        VARCHAR(50)   UNIQUE NOT NULL,
        base_file_name        VARCHAR(255),
        md5_checksum_calibrated      VARCHAR(32),
        md5_checksum_clean    VARCHAR(32),
        file_size_bytes_calibrated   BIGINT,
        file_size_bytes_clean BIGINT,
        record_count          INT,
        xml_label_name        VARCHAR(255),
        creation_datetime     TIMESTAMP,
        storage_path_clean    TEXT,

        CONSTRAINT fk_observation
            FOREIGN KEY (observation_id)
            REFERENCES observation (observation_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );
    """
    execute_sql(cursor, sql_observation_file_info, "Created table: observation_file_info")
    
    # TABLE: measurement_calibrated
    sql_measurement_calibrated = """
    CREATE TABLE measurement_calibrated (
        measurement_id       VARCHAR(50)       PRIMARY KEY NOT NULL,
        file_info_id         VARCHAR(50)       NOT NULL REFERENCES observation_file_info(file_info_id),
        measurement_index    INT               NOT NULL,
        time_utc             TIMESTAMP,
        measurement_count    INT,
        operation_mode       VARCHAR(10),
        measurement_type     VARCHAR(5),
        force_reset_status   SMALLINT,
        laser_fire_status    SMALLINT,
        delay_time_us        DOUBLE PRECISION,
        integration_time_us  INT,
        number_of_pulses     INT,
        x_factor             INT,
        laser_energy_v       INT,
        laser_pump_current_a INT,
        prr_hz               INT,
        on_off_status        SMALLINT
    );
    """
    execute_sql(cursor, sql_measurement_calibrated, "Created table: measurement_calibrated")
    
    # TABLE: spectral_data_calibrated
    sql_spectral_data_calibrated = """
    CREATE TABLE spectral_data_calibrated (
        spectral_data_id  BIGSERIAL         PRIMARY KEY,
        measurement_id    VARCHAR(50)       NOT NULL REFERENCES measurement_calibrated(measurement_id),
        wavelength_nm     DOUBLE PRECISION  NOT NULL,
        response_count    INTEGER           NOT NULL
    );
    """
    execute_sql(cursor, sql_spectral_data_calibrated, "Created table: spectral_data_calibrated")
    
    # TABLE: measurement_clean
    sql_measurement_clean = """
    CREATE TABLE measurement_clean (
        measurement_id       VARCHAR(50)       PRIMARY KEY NOT NULL,
        file_info_id         VARCHAR(50)       NOT NULL REFERENCES observation_file_info(file_info_id),
        measurement_index    INT               NOT NULL,
        time_utc             TIMESTAMP,
        measurement_count    INT,
        operation_mode       VARCHAR(10),
        measurement_type     VARCHAR(50),
        force_reset_status   SMALLINT,
        laser_fire_status    SMALLINT,
        is_valid_plasma      BOOLEAN,
        is_background        BOOLEAN,
        delay_time_us        DOUBLE PRECISION,
        integration_time_us  INT,
        number_of_pulses     INT,
        x_factor             INT,
        laser_energy_v       INT,
        laser_pump_current_a INT,
        prr_hz               INT,
        on_off_status        SMALLINT
    );
    """
    execute_sql(cursor, sql_measurement_clean, "Created table: measurement_clean")
    
    # TABLE: spectral_data_clean
    sql_spectral_data_clean = """
    CREATE TABLE spectral_data_clean (
        spectral_data_id  BIGSERIAL         PRIMARY KEY,
        measurement_id    VARCHAR(50)       NOT NULL REFERENCES measurement_clean(measurement_id),
        wavelength_nm     DOUBLE PRECISION  NOT NULL,
        intensity         DOUBLE PRECISION  NOT NULL
    );
    """
    execute_sql(cursor, sql_spectral_data_clean, "Created table: spectral_data_clean")


def insert_data(cursor):
    """Insert data into tables."""
    print("\n--- INSERTING DATA ---")
    
    # INSERT INTO mission
    sql_insert_mission = """
    INSERT INTO mission (
        mission_id,
        mission_code,
        mission_name,
        organization,
        target_body,
        description,
        launch_date
    )
    VALUES (
        '1',
        'CH3',
        'LVM3-M4/Chandrayaan-3 Mission',
        'ISRO',
        'Moon-Lunar South Pole Region',
        'Chandrayaan-3, India''s third lunar exploration mission is ready to take off in fourth operational mission (M4) of LVM3 launcher. ISRO is crossing new frontiers by demonstrating soft landing on lunar surface by its lunar module and demonstrate roving on the lunar terrain.',
        '2023-07-13 14:35:00+05:30'
    );
    """
    execute_sql(cursor, sql_insert_mission, "Inserted data into mission table")
    
    # INSERT INTO instrument
    sql_insert_instrument = """
    INSERT INTO instrument (
        instrument_id,
        mission_id,
        instrument_code,
        instrument_name,
        instrument_type,
        description
    )
    VALUES (
        'CH3 LIBS',
        '1',
        'LIBS',
        'Laser-Induced Breakdown Spectroscopy',
        'Compact, Active, In-situ Spectrometer',
        'LIBS-Laser Induced Breakdown Spectroscope is an instrument developed based on the LIBS technique for close-by elemental analysis of lunar rocks, pebbles, regolith/soil of roving area. It possess the detection capability for minor/volatile elements i.e., H, He, C, N, P, S etc. LIBS zaps lunar surface to generate the plasma and captures emission spectra of investigation sites during the plasma decay. LIBS spectral range is from 220 nm to 800 nm and offers resolution of less than a nm.'
    );
    """
    execute_sql(cursor, sql_insert_instrument, "Inserted data into instrument table")
    
    # INSERT INTO instrument_spec_libs
    sql_insert_instrument_spec_libs = """
    INSERT INTO instrument_spec_libs (
        spec_id,
        instrument_id,
        wavelength_min_nm,
        wavelength_max_nm,
        spectral_resolution_nm,
        pixel_count,
        detector_type,
        calibration_version
    )
    VALUES (
        'LIBS_SPEC_001',
        'CH3 LIBS',
        220,
        800,
        1.0,
        2094,
        'Charged Coupled Device(CCD)',
        '1.0'
    );
    """
    execute_sql(cursor, sql_insert_instrument_spec_libs, "Inserted data into instrument_spec_libs table")
    
    # INSERT INTO dataset_version
    sql_insert_dataset_version = """
    INSERT INTO dataset_version (
        dataset_version_id,
        spec_id,
        version_label,
        version_number,
        data_level,
        processing_level,
        base_path,
        description,
        released_at,
        created_at
    )
    VALUES (
        'CH3_LIBS_V2',
        'LIBS_SPEC_001',
        'lib-v2',
        'v2',
        'l1',
        'calibrated',
        'C:\\ch3_libs\\lib-v2\\data\\calibrated',
        'This table contains calibrated payload',
        '2024-08-23',
        '2024-05-16 12:12:34+05:30'
    );
    """
    execute_sql(cursor, sql_insert_dataset_version, "Inserted data into dataset_version table")
    
    # INSERT INTO observation_session
    sql_insert_observation_session = """
    INSERT INTO observation_session(
        session_id,
        dataset_version_id,
        observation_date,
        date_folder,
        target_description,
        notes)
    VALUES
        (
        'CH3 LIBS v2 20230825',
        'CH3_LIBS_V2',
        '2023-08-25',
        '20230825',
        'Moon is a natural satellite of Earth',
        'DAY-01 of LIBS spectroscopy observation of lunar surface.'),
        (
        'CH3 LIBS v2 20230826',
        'CH3_LIBS_V2',
        '2023-08-26',
        '20230826',
        'Moon is a natural satellite of Earth',
        'DAY-02 of LIBS spectroscopy observation of lunar surface.'),
        (
        'CH3 LIBS v2 20230827',
        'CH3_LIBS_V2',
        '2023-08-27',
        '20230827',
        'Moon is a natural satellite of Earth',
        'DAY-03 of LIBS spectroscopy observation of lunar surface.'),
        (
        'CH3 LIBS v2 20230828',
        'CH3_LIBS_V2',
        '2023-08-28',
        '20230828',
        'Moon is a natural satellite of Earth',
        'DAY-04 of LIBS spectroscopy observation of lunar surface.'),
        (
        'CH3 LIBS v2 20230829',
        'CH3_LIBS_V2',
        '2023-08-29',
        '20230829',
        'Moon is a natural satellite of Earth',
        'DAY-05 of LIBS spectroscopy observation of lunar surface.'),
        (
        'CH3 LIBS v2 20230830',
        'CH3_LIBS_V2',
        '2023-08-30',
        '20230830',
        'Moon is a natural satellite of Earth',
        'DAY-06 of LIBS spectroscopy observation of lunar surface.'),
        (
        'CH3 LIBS v2 20230831',
        'CH3_LIBS_V2',
        '2023-08-31',
        '20230831',
        'Moon is a natural satellite of Earth',
        'DAY-07 of LIBS spectroscopy observation of lunar surface.'),
        (
        'CH3 LIBS v2 20230901',
        'CH3_LIBS_V2',
        '2023-09-01',
        '20230901',
        'Moon is a natural satellite of Earth',
        'DAY-08 of LIBS spectroscopy observation of lunar surface.'),
        (
        'CH3 LIBS v2 20230902',
        'CH3_LIBS_V2',
        '2023-09-02',
        '20230902',
        'Moon is a natural satellite of Earth',
        'DAY-09 of LIBS spectroscopy observation of lunar surface.');
    """
    execute_sql(cursor, sql_insert_observation_session, "Inserted data into observation_session table")


def main():
    """Main function to orchestrate database setup."""
    print("=" * 60)
    print("CH3 LIBS Database Setup")
    print("=" * 60)
    
    params = get_connection_params()
    
    # Step 1: Connect to default postgres database to create new database
    print("\n[STEP 1] Connecting to PostgreSQL server...")
    try:
        initial_conn = psycopg2.connect(
            host=params['host'],
            user=params['user'],
            password=params['password'],
            port=params['port'],
            database='postgres'
        )
        print("[SUCCESS] Connected to PostgreSQL server")
    except psycopg2.Error as e:
        print(f"[ERROR] Failed to connect to PostgreSQL server")
        print(f"        Error: {e}")
        print("\n[HINT] Make sure PostgreSQL is running and credentials are correct:")
        print(f"       Host: {params['host']}")
        print(f"       User: {params['user']}")
        print(f"       Port: {params['port']}")
        return False
    
    # Step 2: Create database
    print("\n[STEP 2] Creating database...")
    if not create_database(initial_conn, 'ch3_libs_db'):
        initial_conn.close()
        return False
    initial_conn.close()
    
    # Step 3: Connect to new database
    print("\n[STEP 3] Connecting to 'ch3_libs_db' database...")
    conn = connect_to_database(params['host'], params['user'], params['password'], params['port'], 'ch3_libs_db')
    if not conn:
        return False
    print("[SUCCESS] Connected to 'ch3_libs_db'")
    
    cursor = conn.cursor()
    
    # Step 4: Create tables
    print("\n[STEP 4] Creating database schema...")
    create_tables(cursor)
    
    # Step 5: Insert data
    print("\n[STEP 5] Populating database with data...")
    insert_data(cursor)
    
    # Step 6: Commit and close
    print("\n[STEP 6] Finalizing...")
    try:
        conn.commit()
        print("[SUCCESS] All changes committed to database")
    except psycopg2.Error as e:
        print(f"[ERROR] Failed to commit changes: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("DATABASE SETUP COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nDatabase: ch3_libs_db")
    print("Host: localhost")
    print("Port: 5432")
    print("\nYou can now connect to the database using:")
    print("  psql -h localhost -U postgres -d ch3_libs_db")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)