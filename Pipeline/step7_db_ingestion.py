#!/usr/bin/env python3
"""
LunarAtlas Ingestion Pipeline - Stage 7: Database Ingestion
===========================================================
Programmatically parses the local server .env, establishes connection to PostgreSQL,
and ingests processed observations, file info, clean measurements, and spectral curves.
"""

import os
import re
import json
import hashlib
import psycopg2
from psycopg2.extras import execute_batch
from pathlib import Path
import pandas as pd
from datetime import datetime

ENV_PATH = r"c:\Users\ZBook\Desktop\LunarAtlas\core\server\.env"
DEFAULT_PROCESSED_DIR = r"c:\Users\ZBook\Desktop\LunarAtlas\datasets\processed"

def get_db_connection():
    """Parses database URL from .env file and establishes connection."""
    if not os.path.exists(ENV_PATH):
        raise FileNotFoundError(f"Server .env configuration not found at {ENV_PATH}")
        
    db_url = None
    with open(ENV_PATH, "r") as f:
        for line in f:
            if line.startswith("DATABASE_URL="):
                db_url = line.strip().split("=", 1)[1]
                break
                
    if not db_url:
        raise ValueError("DATABASE_URL parameter not set in server .env file.")
        
    # Standard postgresql://user:pass@host:port/dbname
    print(f"[INFO] Connecting to database using URL from .env...")
    return psycopg2.connect(db_url)

def get_md5_checksum(file_path):
    """Computes the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def ingest_core_records(cursor):
    """Insests core catalog records (mission, instrument, spec, version) if they are missing."""
    # 1. Mission
    cursor.execute("SELECT COUNT(*) FROM mission WHERE mission_id = '1'")
    if cursor.fetchone()[0] == 0:
        print("  [DB] Ingesting mission '1' (Chandrayaan-3)...")
        cursor.execute("""
            INSERT INTO mission (mission_id, mission_code, mission_name, organization, launch_date, target_body, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('1', 'CH3', 'LVM3-M4/Chandrayaan-3 Mission', 'ISRO', '2023-07-13 14:35:00+05:30', 'Moon-Lunar South Pole Region', 'Indian lunar lander and rover mission.'))

    # 2. Instrument
    cursor.execute("SELECT COUNT(*) FROM instrument WHERE instrument_id = 'CH3 LIBS'")
    if cursor.fetchone()[0] == 0:
        print("  [DB] Ingesting instrument 'CH3 LIBS'...")
        cursor.execute("""
            INSERT INTO instrument (instrument_id, mission_id, instrument_code, instrument_name, instrument_type, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('CH3 LIBS', '1', 'LIBS', 'Laser-Induced Breakdown Spectroscopy', 'Spectrometer', 'Compact Close-up LIBS instrument'))

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
        """, ('CH3_LIBS_V2', 'LIBS_SPEC_001', 'lib-v2', 'v2', 'l1', 'calibrated', 'D:\\ch3_libs\\lib-v2\\data\\calibrated', 'Calibrated LIBS v2', '2024-08-23', '2024-05-16 12:12:34+05:30'))

def ingest_cleaned_datasets(processed_dir):
    print("====================================================")
    print(" STAGE 7: POSTGRESQL DATABASE INGESTION")
    print("====================================================")
    
    base_dir = Path(processed_dir)
    if not base_dir.exists():
        print(f"[ERROR] Processed data directory not found: {base_dir}")
        return
        
    cleaned_files = list(base_dir.glob("calibrated/*/*/*_cleaned.csv"))
    if not cleaned_files:
        print("[WARNING] No cleaned CSV files found to ingest.")
        return
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
                cursor.execute("""
                    INSERT INTO observation_session (session_id, dataset_version_id, observation_date, date_folder, target_description, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (session_id, 'CH3_LIBS_V2', f"{date_folder[:4]}-{date_folder[4:6]}-{date_folder[6:]}", date_folder, 'Lunar South Pole Target', 'LIBS session'))
                
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
                """, (obs_id, session_id, meta['logical_identifier'], obs_code, int(parts[2]), int(sub) + 1, meta['start_time'].replace("Z", ""), meta['stop_time'].replace("Z", ""), meta['version_id'], meta['information_model_version'], meta['processing_level'], 'Science'))
                
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
                    INSERT INTO observation_file_info (file_info_id, observation_id, base_file_name, md5_checksum_calibrated, md5_checksum_clean, file_size_bytes_calibrated, file_size_bytes_clean, record_count, xml_label_name, creation_datetime, storage_path_clean)
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
                    row = meas_df.iloc[0]
                    
                    cursor.execute("""
                        INSERT INTO measurement_clean (measurement_id, file_info_id, measurement_index, time_utc, measurement_count, operation_mode, measurement_type, force_reset_status, laser_fire_status, is_valid_plasma, is_background, delay_time_us, integration_time_us, number_of_pulses, x_factor, laser_energy_v, laser_pump_current_a, prr_hz, on_off_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (meas_id, file_info_id, int(mid), row['Time_UTC'], None if pd.isna(row['Measurement_Count']) else int(row['Measurement_Count']), row['Operation_Mode'], row['Measurement_Type'], None if pd.isna(row['Force_Reset_Status']) else int(row['Force_Reset_Status']), None if pd.isna(row['Laser_Fire_Status']) else int(row['Laser_Fire_Status']), bool(row['Is_Valid_Plasma']), bool(row['Is_Background']), None if pd.isna(row['Delay_Time_us']) else float(row['Delay_Time_us']), None if pd.isna(row['Integration_Time_us']) else int(row['Integration_Time_us']), None if pd.isna(row['Number_of_Pulses']) else int(row['Number_of_Pulses']), None if pd.isna(row['X_Factor']) else int(row['X_Factor']), None if pd.isna(row['Laser_Energy_V']) else int(row['Laser_Energy_V']), None if pd.isna(row['Laser_Pump_Current_A']) else int(row['Laser_Pump_Current_A']), None if pd.isna(row['PRR_Hz']) else int(row['PRR_Hz']), None if pd.isna(row['On_Off_Status']) else int(row['On_Off_Status'])))
                    
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
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Database ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    # Only ingest if y/yes parameter passed or interactively selected
    ingest = True
    if len(sys.argv) > 1:
        ingest = sys.argv[1].lower() in ['y', 'yes', 'true', '1']
        
    if ingest:
        ingest_cleaned_datasets(DEFAULT_PROCESSED_DIR)
    else:
        print("[INFO] DB Ingestion bypassed based on command parameters.")
