#!/usr/bin/env python3
"""
LunarAtlas Ingestion Pipeline - Stage 6: Creation of Segregated Data Folders
=============================================================================
Manages clean and unprocessed data folder segregation. If DB ingestion is enabled,
it isolates raw unprocessed files in datasets/uploads/ and clean datasets in datasets/processed/.
"""

import sys
import shutil
from pathlib import Path

DEFAULT_RAW_DIR = r"D:\ch3_libs\lib-v2\data\calibrated"
DEFAULT_PROCESSED_DIR = r"c:\Users\ZBook\Desktop\LunarAtlas\datasets\processed"
DEFAULT_UPLOADS_DIR = r"c:\Users\ZBook\Desktop\LunarAtlas\datasets\uploads"

def segregate_datasets(raw_base, processed_base, uploads_base, db_ingest_choice=True):
    print("====================================================")
    print(" STAGE 6: CREATION OF SEGREGATED DATA FOLDERS")
    print("====================================================")
    
    if not db_ingest_choice:
        print("[INFO] Database Ingestion is disabled or not selected.")
        print("[INFO] Skipping physical file copying and segregation steps.")
        print("====================================================\n")
        return {"status": "skipped"}
        
    raw_dir = Path(raw_base)
    processed_dir = Path(processed_base)
    uploads_dir = Path(uploads_base)
    
    # Create segregated target directories
    processed_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[INFO] Segregating data assets:")
    print(f"  - Raw unprocessed storage  : {uploads_dir}")
    print(f"  - Cleaned processed storage: {processed_dir}")
    
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw calibrated folder not found: {raw_dir}")
        
    # Copy raw unprocessed files from the raw mount to datasets/uploads/ to isolate them
    raw_files = list(raw_dir.glob("*/*/*.csv")) + list(raw_dir.glob("*/*/*.xml"))
    print(f"[INFO] Copying {len(raw_files)} raw PDS4 files into uploads/ for isolated preservation...")
    
    total_copied = 0
    for file_path in raw_files:
        # Replicate subfolder structure inside uploads/
        date_folder = file_path.parent.parent.name
        obs_folder = file_path.parent.name
        
        target_path = uploads_dir / date_folder / obs_folder
        target_path.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(file_path, target_path / file_path.name)
        total_copied += 1
        
    print("\n----------------------------------------------------")
    print(" SEGREGATION STAGE 6 SUMMARY METRICS")
    print("----------------------------------------------------")
    print(f"Raw source files copied       : {total_copied}")
    print(f"[SUCCESS] Clean and unprocessed datasets fully isolated.")
    print("====================================================\n")
    return {"status": "success", "raw_source_files_copied": total_copied}

if __name__ == "__main__":
    import sys
    # Read command line options: step6_segregate_data_folders.py [ingest_flag_y_or_n] [raw_dir] [processed_dir] [uploads_dir]
    choice = True
    raw_dir = DEFAULT_RAW_DIR
    processed_dir = DEFAULT_PROCESSED_DIR
    uploads_dir = DEFAULT_UPLOADS_DIR
    
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower() in ['y', 'yes', 'true', '1']
    if len(sys.argv) > 2:
        raw_dir = sys.argv[2]
    if len(sys.argv) > 3:
        processed_dir = sys.argv[3]
    if len(sys.argv) > 4:
        uploads_dir = sys.argv[4]
        
    try:
        import pipeline_logger
        metrics = segregate_datasets(raw_dir, processed_dir, uploads_dir, choice)
        pipeline_logger.log_stage_success("stage_6", "Creation of Segregated Data Folders", metrics)
        sys.exit(0)
    except Exception as e:
        import pipeline_logger
        pipeline_logger.log_stage_failure("stage_6", "Creation of Segregated Data Folders", str(e))
        sys.exit(1)
