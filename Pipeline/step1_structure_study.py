#!/usr/bin/env python3
"""
LunarAtlas Ingestion Pipeline - Stage 1: Folder Structure Study
==============================================================
Scans the raw PDS4 directory structure of Chandrayaan-3 LIBS calibrated tables
and generates a structural summary of date folders, observation folders, and file pairs.
"""

import os
import re
import json
from pathlib import Path

DEFAULT_RAW_DIR = r"D:\ch3_libs\lib-v2\data\calibrated"

def study_folder_structure(raw_dir_path):
    print("====================================================")
    print(" STAGE 1: FOLDER STRUCTURE STUDY")
    print("====================================================")
    
    raw_dir = Path(raw_dir_path)
    if not raw_dir.exists():
        print(f"[ERROR] Raw calibrated data directory not found: {raw_dir}")
        return None
        
    print(f"[INFO] Scanning raw PDS4 directory: {raw_dir}")
    
    # 1. Detect all YYYYMMDD date folders
    date_folders = sorted([d for d in raw_dir.iterdir() 
                          if d.is_dir() and re.match(r'^\d{8}$', d.name)])
    
    print(f"[SUCCESS] Detected {len(date_folders)} authentic date directories:")
    for df in date_folders:
        print(f"  - {df.name}/")
        
    study_results = {
        "raw_base_directory": str(raw_dir),
        "total_date_folders": len(date_folders),
        "date_folders_list": [df.name for df in date_folders],
        "sessions": {}
    }
    
    total_observation_folders = 0
    total_parent_csv_files = 0
    total_parent_xml_files = 0
    total_sub_files = 0
    
    # 2. Iterate through date folders and inspect observation subdirectories
    for date_folder in date_folders:
        date_str = date_folder.name
        # Find all observation directories in date folder matching ISRO naming convention
        obs_folders = sorted([f for f in date_folder.iterdir() 
                             if f.is_dir() and re.match(r'^ch3_lib_\d{3}_\d{8}T\d{6}_\d{2}_l1$', f.name)])
        
        study_results["sessions"][date_str] = {
            "observation_folders_count": len(obs_folders),
            "observations": []
        }
        
        total_observation_folders += len(obs_folders)
        
        for obs_folder in obs_folders:
            obs_code = obs_folder.name
            
            # Count CSVs, XMLs, parent pairs and subfiles
            csv_files = sorted(obs_folder.glob("*.csv"))
            xml_files = sorted(obs_folder.glob("*.xml"))
            
            parent_csv = None
            parent_xml = None
            sub_csv_count = 0
            sub_xml_count = 0
            
            for csv_file in csv_files:
                base_name = csv_file.stem
                parts = base_name.split('_')
                # If last part is a number, it's a subfile (e.g. _0_1)
                if len(parts) > 0 and parts[-1].isdigit():
                    sub_csv_count += 1
                else:
                    parent_csv = csv_file
                    total_parent_csv_files += 1
                    
            for xml_file in xml_files:
                base_name = xml_file.stem
                parts = base_name.split('_')
                if len(parts) > 0 and parts[-1].isdigit():
                    sub_xml_count += 1
                else:
                    parent_xml = xml_file
                    total_parent_xml_files += 1
                    
            total_sub_files += (sub_csv_count + sub_xml_count)
            
            has_valid_pair = (parent_csv is not None) and (parent_xml is not None)
            
            study_results["sessions"][date_str]["observations"].append({
                "observation_code": obs_code,
                "has_parent_csv": parent_csv is not None,
                "has_parent_xml": parent_xml is not None,
                "valid_parent_pair": has_valid_pair,
                "subfiles_csv_count": sub_csv_count,
                "subfiles_xml_count": sub_xml_count
            })
            
    study_results["summary_metrics"] = {
        "total_observation_folders": total_observation_folders,
        "total_parent_csv_files": total_parent_csv_files,
        "total_parent_xml_files": total_parent_xml_files,
        "total_sub_files_detected": total_sub_files
    }
    
    # Save the study result JSON inside Pipeline/
    pipeline_dir = Path(__file__).parent
    output_summary_path = pipeline_dir / "study_summary.json"
    with open(output_summary_path, 'w') as f:
        json.dump(study_results, f, indent=2)
        
    print("\n----------------------------------------------------")
    print(" FOLDER STUDY SUMMARY METRICS")
    print("----------------------------------------------------")
    print(f"Total Date Folders scanned   : {len(date_folders)}")
    print(f"Total Observation Folders    : {total_observation_folders}")
    print(f"Total Parent CSVs detected   : {total_parent_csv_files}")
    print(f"Total Parent XMLs detected   : {total_parent_xml_files}")
    print(f"Total Subfiles (unprocessed) : {total_sub_files}")
    print(f"[SUCCESS] Study results saved to: {output_summary_path.name}")
    print("====================================================\n")
    return study_results

if __name__ == "__main__":
    import sys
    import pipeline_logger
    raw_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RAW_DIR
    try:
        res = study_folder_structure(raw_dir)
        if res is None:
            pipeline_logger.log_stage_failure(
                "stage_1", 
                "Folder Structure Study", 
                "Raw directory scan failed (directory might not exist)."
            )
            sys.exit(1)
        pipeline_logger.log_stage_success("stage_1", "Folder Structure Study", {
            "total_date_folders": res.get("total_date_folders", 0),
            "total_observation_folders": res.get("summary_metrics", {}).get("total_observation_folders", 0),
            "total_parent_csv_files": res.get("summary_metrics", {}).get("total_parent_csv_files", 0),
            "total_parent_xml_files": res.get("summary_metrics", {}).get("total_parent_xml_files", 0),
            "total_sub_files_detected": res.get("summary_metrics", {}).get("total_sub_files_detected", 0)
        })
        sys.exit(0)
    except Exception as e:
        pipeline_logger.log_stage_failure("stage_1", "Folder Structure Study", str(e))
        sys.exit(1)
