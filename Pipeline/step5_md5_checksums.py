#!/usr/bin/env python3
"""
LunarAtlas Ingestion Pipeline - Stage 5: MD5 Digital Signatures
==============================================================
Generates MD5 checksums for all processed spectral CSVs, XMLs, plots, and logs,
recording them in a centralized checksums manifest to establish scientific auditability.
"""

import sys
import hashlib
from pathlib import Path

DEFAULT_PROCESSED_DIR = r"c:\Users\ZBook\Desktop\LunarAtlas\datasets\processed"

def get_md5_checksum(file_path):
    """Computes the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def generate_md5_signatures(processed_dir):
    print("====================================================")
    print(" STAGE 5: MD5 DIGITAL SIGNATURES")
    print("====================================================")
    
    base_dir = Path(processed_dir)
    if not base_dir.exists():
        raise FileNotFoundError(f"Processed data directory not found: {base_dir}")
        
    print(f"[INFO] Scanning directory: {base_dir}")
    
    # Grab all generated CSVs, JSONs, PNGs, and XMLs
    extensions = ["*.csv", "*.json", "*.png", "*.xml"]
    all_files = []
    for ext in extensions:
        all_files.extend(list(base_dir.glob(f"calibrated/*/*/{ext}")))
        all_files.extend(list(base_dir.glob(f"calibrated/*/*/*/{ext}"))) # catch plots/
        
    print(f"[INFO] Found {len(all_files)} total files to sign.")
    
    checksum_lines = []
    total_signed = 0
    
    for file_path in sorted(all_files):
        # Exclude the manifest file itself if somehow captured
        if file_path.name == "checksums.md5":
            continue
            
        md5_hash = get_md5_checksum(file_path)
        # Compute path relative to datasets/processed/
        rel_path = file_path.relative_to(base_dir)
        checksum_lines.append(f"{md5_hash}  {rel_path.as_posix()}")
        total_signed += 1
        
    # Write master checksum signature manifest
    manifest_path = base_dir / "checksums.md5"
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(checksum_lines) + "\n")
        
    print("\n----------------------------------------------------")
    print(" SIGNATURE STAGE 5 SUMMARY METRICS")
    print("----------------------------------------------------")
    print(f"Total files signed            : {total_signed}")
    print(f"[SUCCESS] Digital signatures saved to: {manifest_path.relative_to(base_dir.parent)}")
    print("====================================================\n")
    return {"total_files_signed": total_signed}

if __name__ == "__main__":
    import sys
    import pipeline_logger
    processed = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROCESSED_DIR
    try:
        metrics = generate_md5_signatures(processed)
        pipeline_logger.log_stage_success("stage_5", "MD5 Digital Signatures", metrics)
        sys.exit(0)
    except Exception as e:
        pipeline_logger.log_stage_failure("stage_5", "MD5 Digital Signatures", str(e))
        sys.exit(1)
