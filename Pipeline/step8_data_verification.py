#!/usr/bin/env python3
"""
LunarAtlas Ingestion Pipeline - Stage 8: Comprehensive Data & MD5 Verification
=============================================================================
Establishes a quantitative verification audit. Recalculates MD5 digital signatures
for all files and cross-references them with the records stored in PostgreSQL.
"""

import hashlib
import psycopg2
from pathlib import Path
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

def get_md5_checksum(file_path):
    """Computes the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_datasets(processed_dir, db_url=None):
    print("====================================================")
    print(" STAGE 8: COMPREHENSIVE DATA & MD5 VERIFICATION")
    print("====================================================")
    
    base_dir = Path(processed_dir)
    if not base_dir.exists():
        raise FileNotFoundError(f"Processed data directory not found: {base_dir}")
        
    cleaned_files = list(base_dir.glob("calibrated/*/*/*_cleaned.csv"))
    if not cleaned_files:
        raise FileNotFoundError(f"No cleaned CSV files found to verify in: {base_dir}")
        
    try:
        conn = get_db_connection(db_url)
        cursor = conn.cursor()
        
        # 1. Fetch count stats from database
        cursor.execute("SELECT COUNT(*) FROM observation")
        db_obs_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM measurement_clean")
        db_meas_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spectral_data_clean")
        db_spec_count = cursor.fetchone()[0]
        
        print("\n----------------------------------------------------")
        print(" DATABASE AUDIT STATISTICS")
        print("----------------------------------------------------")
        print(f"Observations registered in DB : {db_obs_count}")
        print(f"Measurements registered in DB  : {db_meas_count}")
        print(f"Spectral data points in DB    : {db_spec_count:,}")
        
        # 2. Detailed 1:1 check for every processed file
        print("\n----------------------------------------------------")
        print(" DIGITAL SIGNATURE (MD5) INTEGRITY CHECK")
        print("----------------------------------------------------")
        
        failures = 0
        passes = 0
        
        for csv_path in cleaned_files:
            stem_name = csv_path.name.replace("_cleaned.csv", "")
            
            # Recalculate local MD5
            local_md5 = get_md5_checksum(csv_path)
            
            # Fetch MD5 stored in DB
            cursor.execute("""
                SELECT md5_checksum_clean, file_info_id 
                FROM observation_file_info 
                WHERE base_file_name = %s
            """, (csv_path.name,))
            
            result = cursor.fetchone()
            if not result:
                print(f"  [FAIL] {stem_name} -> Not registered in database observation_file_info!")
                failures += 1
                continue
                
            db_md5, file_info_id = result
            
            if local_md5 == db_md5:
                print(f"  [PASS] {stem_name} -> Checksum matches DB value exactly: {local_md5}")
                passes += 1
            else:
                print(f"  [FAIL] {stem_name} -> Checksum MISMATCH! Local: {local_md5} | DB: {db_md5}")
                failures += 1
                
        cursor.close()
        conn.close()
        
        print("\n----------------------------------------------------")
        print(" FINAL AUDIT VERIFICATION REPORT")
        print("----------------------------------------------------")
        print(f"Total Checksum Matches Passes : {passes}")
        print(f"Total Checksum Mismatch Fails : {failures}")
        
        if failures == 0 and passes > 0:
            print("\n====================================================")
            print(" [VALIDATED: 100% PASS]")
            print(" All files and database checksums are perfectly authentic.")
            print("====================================================")
            return {
                "checksum_passes": passes,
                "checksum_failures": failures,
                "db_observations": db_obs_count,
                "db_measurements": db_meas_count,
                "db_spectral_points": db_spec_count
            }
        else:
            print("\n====================================================")
            print(" [VALIDATION FAILED]")
            print(" Mismatches detected between local files and database records.")
            print("====================================================")
            raise ValueError(f"Validation failed: {failures} mismatches, {passes} passes.")
            
    except Exception as e:
        print(f"\n[ERROR] Quantitative verification failed: {e}")
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    import sys
    import pipeline_logger
    processed = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROCESSED_DIR
    db_url = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        metrics = verify_datasets(processed, db_url=db_url)
        pipeline_logger.log_stage_success("stage_8", "Quantitative Data & Checksum Verification", metrics)
        sys.exit(0)
    except Exception as e:
        pipeline_logger.log_stage_failure("stage_8", "Quantitative Data & Checksum Verification", str(e))
        sys.exit(1)
