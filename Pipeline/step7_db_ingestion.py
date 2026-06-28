#!/usr/bin/env python3
"""
LunarAtlas Ingestion Pipeline - Stage 7: Database Ingestion
===========================================================
Programmatically parses the local server .env, establishes connection to PostgreSQL,
and ingests processed observations, file info, clean measurements, and spectral curves.
"""

import re
import json
import hashlib
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DEFAULT_PROCESSED_DIR = r"c:\Users\ZBook\Desktop\LunarAtlas\datasets\processed"

def get_db_connection(db_url=None):
    """Establishes connection to PostgreSQL using a provided database URL. Creates the database if it doesn't exist."""
    if not db_url:
        print("\n[INPUT REQUIRED] Enter the PostgreSQL database URL.")
        print("  Format: postgresql://user:password@host:port/dbname")
        db_url = input("  DATABASE_URL: ").strip()

    if not db_url:
        raise ValueError("DATABASE_URL cannot be empty.")

    # Parse target database name
    parsed = urlparse(db_url)
    dbname = parsed.path.lstrip('/')
    if not dbname:
        dbname = "LunarAtlas"

    # Try connecting directly
    try:
        print(f"[INFO] Connecting to database '{dbname}'...")
        return psycopg2.connect(db_url)
    except psycopg2.OperationalError as e:
        err_msg = str(e)
        if "does not exist" in err_msg:
            print(f"[INFO] Database '{dbname}' does not exist. Attempting to create it...")
            # Rebuild system connection URL for 'postgres' database
            netloc = parsed.netloc
            scheme = parsed.scheme or "postgresql"
            sys_url = f"{scheme}://{netloc}/postgres"
            try:
                sys_conn = psycopg2.connect(sys_url)
                sys_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                sys_cursor = sys_conn.cursor()
                sys_cursor.execute(f'CREATE DATABASE "{dbname}"')
                sys_cursor.close()
                sys_conn.close()
                print(f"[SUCCESS] Database '{dbname}' created successfully.")
                # Connect again
                print(f"[INFO] Connecting to newly created database '{dbname}'...")
                return psycopg2.connect(db_url)
            except Exception as create_err:
                print(f"[ERROR] Failed to create database '{dbname}': {create_err}")
                raise e
        else:
            raise e

def ensure_schema_tables_exist(cursor):
    """Creates all required database tables and indexes if they do not exist."""
    print("[INFO] Dropping old tables and recreating target schemas...")
    
    # Drop all tables to ensure clean, conforming schema structures
    tables_to_drop = [
        "api_usage_log", "api_keys", "app_users", "nist_lines",
        "spectral_data_clean", "measurement_clean", "spectral_data_raw", "measurement_raw",
        "observation_file_info", "observation", "observation_session", "dataset_version",
        "instrument_spec_libs", "instrument", "mission"
    ]
    for table in tables_to_drop:
        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    print("[INFO] Verifying database schema tables and indexes...")
    
    # 1. mission
    cursor.execute("""
        CREATE TABLE mission ( 
            mission_id      VARCHAR(20) PRIMARY KEY NOT NULL, 
            mission_code    VARCHAR(20) UNIQUE NOT NULL, 
            mission_name    VARCHAR(100) NOT NULL, 
            organization    VARCHAR(200) NOT NULL, 
            launch_date     TIMESTAMPTZ NOT NULL,
            target_body     VARCHAR(100), 
            description     TEXT
        )
    """)
    
    # 2. instrument
    cursor.execute("""
        CREATE TABLE instrument ( 
            instrument_id    VARCHAR(50) PRIMARY KEY NOT NULL,
            mission_id       VARCHAR(20) NOT NULL, 
            instrument_code  VARCHAR(50) NOT NULL,
            instrument_name  VARCHAR(255), 
            instrument_type  VARCHAR(100), 
            description      TEXT, 
            FOREIGN KEY (mission_id) REFERENCES mission(mission_id) 
        )
    """)
    
    # 3. instrument_spec_libs
    cursor.execute("""
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
        )
    """)
    
    # 4. dataset_version
    cursor.execute("""
        CREATE TABLE dataset_version ( 
            dataset_version_id  VARCHAR(50) PRIMARY KEY NOT NULL, 
            spec_id             VARCHAR(50),
            version_label       VARCHAR(50) NOT NULL UNIQUE, 
            version_number      VARCHAR(20),
            data_level          VARCHAR(10),
            processing_level    VARCHAR(50),
            base_path           TEXT,
            description         TEXT,
            released_at         DATE, 
            created_at          TIMESTAMPTZ, 
            FOREIGN KEY (spec_id) REFERENCES instrument_spec_libs(spec_id)
        )
    """)
    
    # 5. observation_session
    cursor.execute("""
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
        )
    """)
    
    # 6. observation
    cursor.execute("""
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
        )
    """)
    
    # 7. observation_file_info
    cursor.execute("""
        CREATE TABLE observation_file_info (
            file_info_id          VARCHAR(50)   PRIMARY KEY,
            observation_id        VARCHAR(50)   UNIQUE NOT NULL,
            base_file_name        VARCHAR(255),
            md5_checksum_raw      VARCHAR(32),
            md5_checksum_clean    VARCHAR(32),
            file_size_bytes_raw   BIGINT,
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
        )
    """)
    
    # 8. measurement_raw
    cursor.execute("""
        CREATE TABLE measurement_raw (
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
        )
    """)
    
    # 9. spectral_data_raw
    cursor.execute("""
        CREATE TABLE spectral_data_raw (
            spectral_data_id  BIGSERIAL         PRIMARY KEY,
            measurement_id    VARCHAR(50)       NOT NULL REFERENCES measurement_raw(measurement_id),
            wavelength_nm     DOUBLE PRECISION  NOT NULL,
            response_count    INTEGER           NOT NULL
        )
    """)
    
    # 10. measurement_clean
    cursor.execute("""
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
        )
    """)
    
    # 11. spectral_data_clean
    cursor.execute("""
        CREATE TABLE spectral_data_clean (
            spectral_data_id  BIGSERIAL         PRIMARY KEY,
            measurement_id    VARCHAR(50)       NOT NULL REFERENCES measurement_clean(measurement_id),
            wavelength_nm     DOUBLE PRECISION  NOT NULL,
            intensity         DOUBLE PRECISION  NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_spectral_data_clean_measurement ON spectral_data_clean(measurement_id)")

    # 12. nist_lines
    cursor.execute("""
        CREATE TABLE nist_lines (
            id SERIAL PRIMARY KEY,
            element VARCHAR(10) NOT NULL,
            ionization_stage VARCHAR(10),
            wavelength_nm DOUBLE PRECISION NOT NULL,
            relative_intensity INTEGER
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nist_lines_wavelength ON nist_lines(wavelength_nm)")
    
    # Seed nist_lines reference data
    nist_data = [
        ("Fe", "I", 248.327, 1000),
        ("Fe", "I", 274.918, 800),
        ("Fe", "I", 373.486, 900),
        ("Fe", "I", 404.581, 700),
        ("Fe", "II", 238.204, 850),
        ("Fe", "II", 259.940, 750),
        ("Mg", "I", 285.213, 1000),
        ("Mg", "I", 383.829, 600),
        ("Mg", "I", 517.268, 800),
        ("Mg", "I", 518.360, 900),
        ("Mg", "II", 279.553, 1000),
        ("Mg", "II", 280.270, 950),
        ("Si", "I", 251.611, 1000),
        ("Si", "I", 288.158, 900),
        ("Si", "I", 390.552, 500),
        ("Al", "I", 308.215, 900),
        ("Al", "I", 309.271, 1000),
        ("Al", "I", 394.401, 850),
        ("Al", "I", 396.152, 950),
        ("Ca", "I", 422.673, 1000),
        ("Ca", "I", 443.568, 400),
        ("Ca", "II", 393.366, 1000),
        ("Ca", "II", 396.847, 900),
        ("Ti", "I", 334.904, 800),
        ("Ti", "I", 336.121, 700),
        ("Ti", "II", 334.941, 900),
        ("Na", "I", 588.995, 1000),
        ("Na", "I", 589.592, 900),
        ("H", "I", 656.273, 1000),
        ("H", "I", 486.133, 500),
        ("O", "I", 777.194, 900),
        ("O", "I", 777.417, 800),
        ("O", "I", 777.539, 700)
    ]
    query = "INSERT INTO nist_lines (element, ionization_stage, wavelength_nm, relative_intensity) VALUES (%s, %s, %s, %s)"
    execute_batch(cursor, query, nist_data)
    print("[SUCCESS] NIST reference lines table created and seeded with 33 lines.")
    print("[SUCCESS] All database schema tables and indexes verified/created.")

def get_md5_checksum(file_path):
    """Computes the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def ingest_core_records(cursor):
    """Inserts core catalog records (mission, instrument, spec, version) if they are missing."""
    # 1. Mission
    cursor.execute("SELECT COUNT(*) FROM mission WHERE mission_id = '1'")
    if cursor.fetchone()[0] == 0:
        print("  [DB] Ingesting mission '1' (Chandrayaan-3)...")
        cursor.execute("""
            INSERT INTO mission (mission_id, mission_code, mission_name, organization, launch_date, target_body, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            '1',
            'CH3',
            'LVM3-M4/Chandrayaan-3 Mission',
            'ISRO',
            '2023-07-13 14:35:00+05:30',
            'Moon-Lunar South Pole Region',
            "Chandrayaan-3, India's third lunar exploration mission is ready to take off in fourth operational mission (M4) of LVM3 launcher. ISRO is crossing new frontiers by demonstrating soft landing on lunar surface by its lunar module and demonstrate roving on the lunar terrain."
        ))

    # 2. Instrument
    cursor.execute("SELECT COUNT(*) FROM instrument WHERE instrument_id = 'CH3 LIBS'")
    if cursor.fetchone()[0] == 0:
        print("  [DB] Ingesting instrument 'CH3 LIBS'...")
        cursor.execute("""
            INSERT INTO instrument (instrument_id, mission_id, instrument_code, instrument_name, instrument_type, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            'CH3 LIBS',
            '1',
            'LIBS',
            'Laser-Induced Breakdown Spectroscopy',
            'Compact, Active, In-situ Spectrometer',
            "LIBS-Laser Induced Breakdown Spectroscope is an instrument developed based on the LIBS technique for close-by elemental analysis of lunar rocks, pebbles, regolith/soil of roving area. It possess the detection capability for minor/volatile elements i.e., H, He, C, N, P, S etc. LIBS zaps lunar surface to generate the plasma and captures emission spectra of investigation sites during the plasma decay. LIBS spectral range is from 220 nm to 800 nm and offers resolution of less than a nm."
        ))

    # 3. Instrument Specs
    cursor.execute("SELECT COUNT(*) FROM instrument_spec_libs WHERE spec_id = 'LIBS_SPEC_001'")
    if cursor.fetchone()[0] == 0:
        print("  [DB] Ingesting spec 'LIBS_SPEC_001'...")
        cursor.execute("""
            INSERT INTO instrument_spec_libs (spec_id, instrument_id, wavelength_min_nm, wavelength_max_nm, spectral_resolution_nm, pixel_count, detector_type, calibration_version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, ('LIBS_SPEC_001', 'CH3 LIBS', 220.0, 800.0, 1.0, 2094, 'Charged Coupled Device(CCD)', '1.0'))

    # 4. Dataset Version
    cursor.execute("SELECT COUNT(*) FROM dataset_version WHERE dataset_version_id = 'CH3_LIBS_V2'")
    if cursor.fetchone()[0] == 0:
        print("  [DB] Ingesting dataset version 'CH3_LIBS_V2'...")
        cursor.execute("""
            INSERT INTO dataset_version (dataset_version_id, spec_id, version_label, version_number, data_level, processing_level, base_path, description, released_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'CH3_LIBS_V2',
            'LIBS_SPEC_001',
            'lib-v2',
            'v2',
            'l1',
            'calibrated',
            'D:\\ch3_libs\\lib-v2\\data\\calibrated',
            'This table contains calibrated payload',
            '2024-08-23',
            '2024-05-16 12:12:34+05:30'
        ))

def ingest_cleaned_datasets(processed_dir, db_url=None):
    print("====================================================")
    print(" STAGE 7: POSTGRESQL DATABASE INGESTION")
    print("====================================================")
    
    base_dir = Path(processed_dir)
    if not base_dir.exists():
        raise FileNotFoundError(f"Processed data directory not found: {base_dir}")
        
    cleaned_files = list(base_dir.glob("calibrated/*/*/*_cleaned.csv"))
    if not cleaned_files:
        print("[WARNING] No cleaned CSV files found to ingest.")
        return {"status": "success", "newly_ingested_measurements": 0, "newly_ingested_spectral_points": 0}
        
    try:
        conn = get_db_connection(db_url)
        cursor = conn.cursor()
        
        # Ensure schema tables and indexes exist
        ensure_schema_tables_exist(cursor)
        conn.commit()
        
        # 1. Ingest core structures
        ingest_core_records(cursor)
        conn.commit()
        
        total_spectral_rows = 0
        total_measurements = 0
        
        for csv_path in cleaned_files:
            stem_name = csv_path.name.replace("_cleaned.csv", "")
            
            # Find metadata JSON
            json_path = csv_path.parent / f"{stem_name}_metadata.json"
            if not json_path.exists():
                print(f"  [WARNING] Metadata file missing for {stem_name}, skipping.")
                continue
                
            with open(json_path, "r") as f:
                meta = json.load(f)
                
            # Date folder
            date_folder = csv_path.parent.parent.name
            session_id = f"CH3 LIBS v2 {date_folder}"
            
            # Ensure observation session exists
            cursor.execute("SELECT COUNT(*) FROM observation_session WHERE session_id = %s", (session_id,))
            if cursor.fetchone()[0] == 0:
                print(f"  [DB] Ingesting session: {session_id}")
                day_map = {
                    '20230825': 1, '20230826': 2, '20230827': 3, '20230828': 4,
                    '20230829': 5, '20230830': 6, '20230831': 7, '20230901': 8, '20230902': 9
                }
                day_num = day_map.get(date_folder, 1)
                notes = f"DAY-{day_num:02d} of LIBS spectroscopy observation of lunar surface."
                cursor.execute("""
                    INSERT INTO observation_session (session_id, dataset_version_id, observation_date, date_folder, target_description, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (session_id, 'CH3_LIBS_V2', f"{date_folder[:4]}-{date_folder[4:6]}-{date_folder[6:]}", date_folder, 'Moon is a natural satellite of Earth', notes))
                
            # Ingest Observation
            obs_code = meta['source_file'].replace(".csv", "")
            
            # Build observation_id in LIB-YYYYMMDD-HHMMSS-SS format
            parts = obs_code.split('_')
            dt = parts[3]
            sub = parts[4]
            date_str = dt.split("T")[0]
            time_str = dt.split("T")[1]
            obs_id = f"LIB-{date_str}-{time_str}-{sub}"
            
            cursor.execute("SELECT COUNT(*) FROM observation WHERE observation_id = %s", (obs_id,))
            if cursor.fetchone()[0] == 0:
                print(f"  [DB] Ingesting observation: {obs_id} ({obs_code})")
                cursor.execute("""
                    INSERT INTO observation (observation_id, session_id, logical_identifier, observation_code, observation_number, sub_index, start_time, stop_time, pds_version_id, information_model_version, processing_level, purpose)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (obs_id, session_id, meta['logical_identifier'], obs_code, int(parts[2]), int(sub) + 1, meta['start_time'].replace("Z", ""), meta['stop_time'].replace("Z", ""), meta['version_id'], meta.get('information_model_version', '1.20.0.0'), meta.get('processing_level', 'calibrated'), 'Science'))
                
            # Ingest File Info
            file_info_id = f"FI-{date_str}-{time_str}-{sub}"
            cursor.execute("SELECT COUNT(*) FROM observation_file_info WHERE file_info_id = %s", (file_info_id,))
            md5_clean = get_md5_checksum(csv_path)
            file_size_clean = csv_path.stat().st_size
            
            # Check raw file size and checksum if we can find it
            raw_csv_path = Path(r"D:\ch3_libs\lib-v2\data\calibrated") / date_folder / obs_code / f"{obs_code}.csv"
            raw_xml_path = raw_csv_path.with_suffix(".xml")
            
            md5_calib = get_md5_checksum(raw_csv_path) if raw_csv_path.exists() else None
            size_calib = raw_csv_path.stat().st_size if raw_csv_path.exists() else None
            xml_name = raw_xml_path.name if raw_xml_path.exists() else f"{obs_code}.xml"

            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO observation_file_info (file_info_id, observation_id, base_file_name, md5_checksum_raw, md5_checksum_clean, file_size_bytes_raw, file_size_bytes_clean, record_count, xml_label_name, creation_datetime, storage_path_clean)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (file_info_id, obs_id, f"{obs_code}_cleaned.csv", md5_calib, md5_clean, size_calib, file_size_clean, int(meta['records']), xml_name, datetime.now(), str(csv_path.resolve())))
            else:
                cursor.execute("""
                    UPDATE observation_file_info 
                    SET base_file_name = %s,
                        md5_checksum_clean = %s,
                        file_size_bytes_clean = %s,
                        storage_path_clean = %s
                    WHERE file_info_id = %s
                """, (f"{obs_code}_cleaned.csv", md5_clean, file_size_clean, str(csv_path.resolve()), file_info_id))
                
            # Load instrument params CSV
            params_path = csv_path.parent / f"{stem_name}_instrument_params.csv"
            if params_path.exists():
                df_params = pd.read_csv(params_path)
            else:
                df_params = pd.DataFrame()

            # Load raw CSV for raw measurements if it exists, and ingest into measurement_raw and spectral_data_raw
            if raw_csv_path.exists():
                print(f"  [DB] Ingesting raw measurements for {obs_code}...")
                df_raw = pd.read_csv(raw_csv_path)
                wavelength_cols_raw = df_raw.columns[6:-8].tolist()
                
                plasma_count = 0
                for idx, row_r in df_raw.iterrows():
                    m_count = row_r['Measurement Count']
                    m_count_int = int(m_count) if not pd.isna(m_count) else None
                    
                    # Pre-read trailing params to identify plasma vs background shots
                    trailing_vals = row_r.iloc[-8:].values
                    laser_energy = float(trailing_vals[4]) if not pd.isna(trailing_vals[4]) else 0.0
                    lfs = row_r.get('Laser Fire Status')
                    lfs_val = int(lfs) if not pd.isna(lfs) else 0
                    
                    is_plasma = (lfs_val == 1) or (laser_energy > 0.0)
                    
                    if is_plasma:
                        plasma_count += 1
                        meas_id_raw = f"{file_info_id}-{plasma_count}"
                    else:
                        # Background shot - use unique suffix to avoid duplicate keys
                        meas_id_raw = f"{file_info_id}-bg-{idx + 1}"
                        
                    cursor.execute("SELECT COUNT(*) FROM measurement_raw WHERE measurement_id = %s", (meas_id_raw,))
                    if cursor.fetchone()[0] == 0:
                        time_utc_raw = row_r['Time']
                        if pd.isna(time_utc_raw) or str(time_utc_raw).strip().lower() in ['nan', 'nat', '']:
                            try:
                                parts = obs_code.split('_')
                                dt_str = parts[3]
                                date_part, time_part = dt_str.split('T')
                                time_utc_raw = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                            except Exception:
                                time_utc_raw = meta.get('start_time', '').replace("Z", "") if meta.get('start_time') else None
                        
                        op_mode = row_r['Operation Mode']
                        m_type = row_r['Measurement Type']
                        frs_r = row_r['Force Reset Status']
                        lfs_r = row_r['Laser Fire Status']
                        
                        # Trailing params
                        trailing_vals = row_r.iloc[-8:].values
                        
                        cursor.execute("""
                            INSERT INTO measurement_raw (
                                measurement_id, file_info_id, measurement_index, time_utc, measurement_count, 
                                operation_mode, measurement_type, force_reset_status, laser_fire_status, 
                                delay_time_us, integration_time_us, number_of_pulses, x_factor, 
                                laser_energy_v, laser_pump_current_a, prr_hz, on_off_status
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            meas_id_raw, file_info_id, idx + 1, time_utc_raw,
                            m_count_int,
                            None if pd.isna(op_mode) else str(op_mode),
                            None if pd.isna(m_type) else str(m_type)[:5],
                            None if pd.isna(frs_r) else int(frs_r),
                            None if pd.isna(lfs_r) else int(lfs_r),
                            None if pd.isna(trailing_vals[0]) else float(trailing_vals[0]),
                            None if pd.isna(trailing_vals[1]) else int(trailing_vals[1]),
                            None if pd.isna(trailing_vals[2]) else int(trailing_vals[2]),
                            None if pd.isna(trailing_vals[3]) else int(trailing_vals[3]),
                            None if pd.isna(trailing_vals[4]) else int(trailing_vals[4]),
                            None if pd.isna(trailing_vals[5]) else int(trailing_vals[5]),
                            None if pd.isna(trailing_vals[6]) else int(trailing_vals[6]),
                            None if pd.isna(trailing_vals[7]) else int(trailing_vals[7])
                        ))
                        
                        # Batch insert raw spectral points
                        spectral_batch_raw = []
                        for wl_str in wavelength_cols_raw:
                            try:
                                wl = float(wl_str)
                                val = float(row_r[wl_str])
                                if not pd.isna(val):
                                    spectral_batch_raw.append((meas_id_raw, wl, int(val)))
                            except Exception:
                                pass
                        
                        if spectral_batch_raw:
                            execute_batch(cursor, """
                                INSERT INTO spectral_data_raw (measurement_id, wavelength_nm, response_count)
                                VALUES (%s, %s, %s)
                            """, spectral_batch_raw, page_size=5000)

            # Load cleaned CSV for measurements
            df_cleaned = pd.read_csv(csv_path)
            mids = sorted(df_cleaned['Measurement_ID'].unique())
            
            new_measurements_count = 0
            existing_measurements_count = 0
            
            for mid in mids:
                meas_id = f"{file_info_id}-{mid}"
                cursor.execute("SELECT COUNT(*) FROM measurement_clean WHERE measurement_id = %s", (meas_id,))
                
                if cursor.fetchone()[0] == 0:
                    meas_df = df_cleaned[df_cleaned['Measurement_ID'] == mid]
                    row = meas_df.iloc[0] if not meas_df.empty else None
                    
                    # Find parameter row
                    row_param = None
                    if not df_params.empty:
                        param_rows = df_params[df_params['Measurement_ID'] == mid]
                        if not param_rows.empty:
                            row_param = param_rows.iloc[0]
                    
                    # Safe get helper
                    def get_val(key, default=None):
                        if row_param is not None and key in row_param:
                            val = row_param[key]
                            return default if pd.isna(val) else val
                        return default
                    
                    # Map values with defaults
                    time_utc = get_val('Time', row['Time_UTC'] if row is not None else None)
                    if pd.isna(time_utc) or str(time_utc).strip().lower() in ['nan', 'nat', '']:
                        # Try parsing from observation code (e.g., ch3_lib_002_20230825T145453_02_l1)
                        try:
                            parts = obs_code.split('_')
                            dt_str = parts[3] # 20230825T145453
                            date_part, time_part = dt_str.split('T')
                            time_utc = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                        except Exception:
                            # Fallback to observation metadata start_time
                            time_utc = meta.get('start_time', '').replace("Z", "") if meta.get('start_time') else None
                    
                    meas_count = row['Measurement_Count'] if row is not None else get_val('Measurement_Count')
                    
                    operation_mode = get_val('Operation_Mode', 'Normal')
                    meas_type = get_val('Measurement_Type', 'Plasma')
                    
                    force_reset = get_val('Force_Reset_Status')
                    laser_fire = get_val('Laser_Fire_Status')
                    
                    is_valid = get_val('Is_Valid_Plasma', True)
                    is_bg = get_val('Is_Background', False)
                    
                    delay = get_val('Delay_Time_us')
                    integration = get_val('Integration_Time_us')
                    pulses = get_val('Number_of_Pulses')
                    x_factor = get_val('X_Factor')
                    energy = get_val('Laser_Energy_V')
                    current = get_val('Laser_Pump_Current_A')
                    prr = get_val('PRR_Hz')
                    on_off = get_val('On_Off_Status')
                    
                    cursor.execute("""
                        INSERT INTO measurement_clean (measurement_id, file_info_id, measurement_index, time_utc, measurement_count, operation_mode, measurement_type, force_reset_status, laser_fire_status, is_valid_plasma, is_background, delay_time_us, integration_time_us, number_of_pulses, x_factor, laser_energy_v, laser_pump_current_a, prr_hz, on_off_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        meas_id, file_info_id, int(mid), 
                        time_utc, 
                        None if pd.isna(meas_count) else int(meas_count), 
                        operation_mode, meas_type, 
                        None if pd.isna(force_reset) else int(force_reset), 
                        None if pd.isna(laser_fire) else int(laser_fire), 
                        bool(is_valid), bool(is_bg), 
                        None if pd.isna(delay) else float(delay), 
                        None if pd.isna(integration) else int(integration), 
                        None if pd.isna(pulses) else int(pulses), 
                        None if pd.isna(x_factor) else int(x_factor), 
                        None if pd.isna(energy) else int(energy), 
                        None if pd.isna(current) else int(current), 
                        None if pd.isna(prr) else int(prr), 
                        None if pd.isna(on_off) else int(on_off)
                    ))
                    
                    total_measurements += 1
                    new_measurements_count += 1
                    
                    # Batch Ingestion of spectral points (execute_batch is 100x faster than individual INSERTs)
                    spectral_batch = []
                    for _, s_row in meas_df.iterrows():
                        spectral_batch.append((
                            meas_id,
                            float(s_row['Wavelength_nm']),
                            float(s_row['Cleaned_Intensity'])
                        ))
                        
                    execute_batch(cursor, """
                        INSERT INTO spectral_data_clean (measurement_id, wavelength_nm, intensity)
                        VALUES (%s, %s, %s)
                    """, spectral_batch, page_size=5000)
                    
                    total_spectral_rows += len(spectral_batch)
                else:
                    existing_measurements_count += 1
                    
            conn.commit()
            print(f"    - Processed: {obs_code} -> Measurements (New: {new_measurements_count}, Exist: {existing_measurements_count}) | Total Ingested Points: {total_spectral_rows:,}")
            
        cursor.close()
        conn.close()
        
        print("\n----------------------------------------------------")
        print(" DATABASE INGESTION STAGE 7 SUMMARY METRICS")
        print("----------------------------------------------------")
        print(f"Newly Ingested Measurements   : {total_measurements}")
        print(f"Newly Ingested Spectral Points: {total_spectral_rows:,}")
        print(f"[SUCCESS] Processed spectra database entries fully updated/ingested.")
        print("====================================================\n")
        return {
            "status": "success",
            "newly_ingested_measurements": total_measurements,
            "newly_ingested_spectral_points": total_spectral_rows
        }
        
    except Exception as e:
        print(f"\n[ERROR] Database ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    import sys
    # Command line: step7_db_ingestion.py [ingest_flag] [db_url] [processed_dir]
    ingest = True
    db_url = None
    processed_dir = DEFAULT_PROCESSED_DIR
    if len(sys.argv) > 1:
        ingest = sys.argv[1].lower() in ['y', 'yes', 'true', '1']
    if len(sys.argv) > 2:
        db_url = sys.argv[2]
    if len(sys.argv) > 3:
        processed_dir = sys.argv[3]

    import pipeline_logger
    try:
        if ingest:
            metrics = ingest_cleaned_datasets(processed_dir, db_url=db_url)
            pipeline_logger.log_stage_success("stage_7", "Database Ingestion", metrics)
        else:
            print("[INFO] DB Ingestion bypassed based on command parameters.")
            pipeline_logger.log_stage_success("stage_7", "Database Ingestion", {"status": "skipped"})
        sys.exit(0)
    except Exception as e:
        pipeline_logger.log_stage_failure("stage_7", "Database Ingestion", str(e))
        sys.exit(1)
