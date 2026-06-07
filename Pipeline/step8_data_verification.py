#!/usr/bin/env python3
"""
LunarAtlas Ingestion Pipeline - Stage 8: Comprehensive Data & MD5 Verification
=============================================================================
Establishes a quantitative verification audit. Recalculates MD5 digital signatures
for all files and cross-references them with the records stored in PostgreSQL.
"""

import os
import hashlib
import psycopg2
from pathlib import Path

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
        
    return psycopg2.connect(db_url)

def get_md5_checksum(file_path):
    """Computes the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def verify_datasets(processed_dir):
    print("====================================================")
    print(" STAGE 8: COMPREHENSIVE DATA & MD5 VERIFICATION")
    print("====================================================")
    
    base_dir = Path(processed_dir)
    if not base_dir.exists():
        print(f"[ERROR] Processed data directory not found: {base_dir}")
        return False
        
    cleaned_files = list(base_dir.glob("calibrated/*/*/*_cleaned.csv"))
    if not cleaned_files:
        print("[WARNING] No cleaned CSV files found to verify.")
        return False
        
    try:
        conn = get_db_connection()
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
            return True
        else:
            print("\n====================================================")
            print(" [VALIDATION FAILED]")
            print(" Mismatches detected between local files and database records.")
            print("====================================================")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Quantitative verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    processed = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROCESSED_DIR
    verify_datasets(processed)
