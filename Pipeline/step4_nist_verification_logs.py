#!/usr/bin/env python3
"""
LunarAtlas Ingestion Pipeline - Stage 4: NIST Verification Logs
===============================================================
Performs peak detection on each cleaned spectrum, cross-references with the NIST 
atomic emission database, and outputs individual tabular logs detailing the identified elements.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

DEFAULT_PROCESSED_DIR = r"c:\Users\ZBook\Desktop\LunarAtlas\datasets\processed"

# Peak detection threshold (prominence/minimum height)
MIN_PEAK_HEIGHT = 150.0  # counts

# NIST atomic reference database
NIST_DB = [
    {"element": "Mg II", "wavelength": 279.55},
    {"element": "Mg II", "wavelength": 280.27},
    {"element": "Mg I",  "wavelength": 285.21},
    {"element": "Si I",  "wavelength": 288.16},
    {"element": "Al I",  "wavelength": 308.22},
    {"element": "Al I",  "wavelength": 309.27},
    {"element": "Ti II", "wavelength": 334.94},
    {"element": "Fe I",  "wavelength": 373.49},
    {"element": "Fe I",  "wavelength": 385.99},
    {"element": "Si I",  "wavelength": 390.55},
    {"element": "Ca II", "wavelength": 393.37},
    {"element": "Al I",  "wavelength": 394.40},
    {"element": "Al I",  "wavelength": 396.15},
    {"element": "Ca II", "wavelength": 396.85},
    {"element": "Fe I",  "wavelength": 404.58},
    {"element": "Ca I",  "wavelength": 422.67},
    {"element": "Fe I",  "wavelength": 438.36},
    {"element": "Mg I",  "wavelength": 518.36},
    {"element": "Na I",  "wavelength": 588.99},
    {"element": "Na I",  "wavelength": 589.59},
    {"element": "H I",   "wavelength": 656.28},
    {"element": "O I",   "wavelength": 777.19},
    {"element": "Ca II", "wavelength": 849.80},
    {"element": "Ca II", "wavelength": 854.21},
    {"element": "Ca II", "wavelength": 866.21},
]

def find_peaks(wavelengths, intensities, min_height=MIN_PEAK_HEIGHT):
    """Simple peak detection finding local maxima exceeding a minimum height threshold."""
    peaks = []
    n = len(intensities)
    for i in range(1, n - 1):
        if intensities[i] > intensities[i - 1] and intensities[i] > intensities[i + 1]:
            if intensities[i] >= min_height:
                peaks.append((wavelengths[i], intensities[i]))
    return peaks

def generate_nist_logs(processed_dir):
    print("====================================================")
    print(" STAGE 4: NIST ELEMENT VERIFICATION LOGS")
    print("====================================================")
    
    base_dir = Path(processed_dir)
    if not base_dir.exists():
        print(f"[ERROR] Processed data directory not found: {base_dir}")
        return
        
    cleaned_files = list(base_dir.glob("calibrated/*/*/*_cleaned.csv"))
    print(f"[INFO] Scanning {len(cleaned_files)} files for peak-NIST alignment...")
    
    for csv_path in cleaned_files:
        stem_name = csv_path.name.replace("_cleaned.csv", "")
        df = pd.read_csv(csv_path)
        
        mids = sorted(df['Measurement_ID'].unique())
        log_records = []
        
        for mid in mids:
            sub = df[df['Measurement_ID'] == mid].sort_values('Wavelength_nm')
            wls = sub['Wavelength_nm'].values
            ints = sub['Cleaned_Intensity'].values
            
            # Detect peaks
            peaks = find_peaks(wls, ints, MIN_PEAK_HEIGHT)
            
            for pk_wl, pk_int in peaks:
                matched_element = "Unknown"
                ref_wl = None
                best_offset = 1.0  # max threshold is 0.5 nm
                
                # Check alignment with NIST references
                for entry in NIST_DB:
                    offset = abs(pk_wl - entry["wavelength"])
                    if offset < 0.5 and offset < best_offset:
                        best_offset = offset
                        matched_element = entry["element"]
                        ref_wl = entry["wavelength"]
                        
                log_records.append({
                    "Measurement_ID": int(mid),
                    "Detected_Wavelength_nm": float(round(pk_wl, 3)),
                    "Peak_Intensity_counts": float(round(pk_int, 2)),
                    "NIST_Element": matched_element,
                    "NIST_Wavelength_nm": ref_wl,
                    "Wavelength_Offset_nm": float(round(best_offset, 3)) if ref_wl else None,
                    "Verification_Status": "VERIFIED" if matched_element != "Unknown" else "UNREGISTERED"
                })
                
        # Save verification log table
        log_df = pd.DataFrame(log_records)
        if log_df.empty:
            log_df = pd.DataFrame(columns=[
                "Measurement_ID", "Detected_Wavelength_nm", "Peak_Intensity_counts",
                "NIST_Element", "NIST_Wavelength_nm", "Wavelength_Offset_nm", "Verification_Status"
            ])
        log_output = csv_path.parent / f"{stem_name}_nist_verification_log.csv"
        log_df.to_csv(log_output, index=False)
        
        # Log summary statistics
        verified_count = (log_df['Verification_Status'] == "VERIFIED").sum()
        total_peaks = len(log_df)
        hit_elements = log_df[log_df['Verification_Status'] == "VERIFIED"]['NIST_Element'].unique()
        
        print(f"  [SUCCESS] Ingested verification: {log_output.name}")
        print(f"    - Detected {total_peaks} peaks | Verified {verified_count} matching lines.")
        print(f"    - Identified elements: {', '.join(hit_elements)}")
        
    print("\n[SUCCESS] Stage 4: NIST element verification tables saved successfully.")
    print("====================================================\n")

if __name__ == "__main__":
    import sys
    processed = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROCESSED_DIR
    generate_nist_logs(processed)
