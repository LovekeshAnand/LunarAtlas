#!/usr/bin/env python3
"""
LunarAtlas Ingestion Pipeline - Stage 2: Process L1 Data
=========================================================
Crawls raw L1 data, performs background-subtraction cleaning,
and outputs processed results replicating the identical ISRO/PDS4 date and observation folder hierarchy.
"""

import os
import re
import json
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

DEFAULT_RAW_DIR = r"D:\ch3_libs\lib-v2\data\calibrated"
DEFAULT_PROCESSED_DIR = r"c:\Users\ZBook\Desktop\LunarAtlas\datasets\processed"

class L1DataProcessor:
    def __init__(self, raw_dir, processed_dir):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.stats = {
            'folders_processed': 0,
            'files_cleaned': 0,
            'points_generated': 0,
            'errors': 0
        }

    def extract_metadata_from_xml(self, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {'pds': 'http://pds.nasa.gov/pds4/pds/v1'}
        metadata = {
            'logical_identifier': None,
            'version_id': '1.0',
            'title': 'Unknown LIBS Spectrum',
            'start_time': None,
            'stop_time': None,
            'file_name': None,
            'file_size': 0,
            'records': 0,
            'column_descriptions': {},
            'instrument_description': 'ChaSTE-LIBS compact active spectrometer'
        }
        
        try:
            elem = root.find('.//pds:logical_identifier', ns)
            if elem is not None: metadata['logical_identifier'] = elem.text
            
            elem = root.find('.//pds:Identification_Area/pds:version_id', ns)
            if elem is not None: metadata['version_id'] = elem.text
            
            elem = root.find('.//pds:title', ns)
            if elem is not None: metadata['title'] = elem.text
            
            elem = root.find('.//pds:start_date_time', ns)
            if elem is not None: metadata['start_time'] = elem.text
            
            elem = root.find('.//pds:stop_date_time', ns)
            if elem is not None: metadata['stop_time'] = elem.text
            
            elem = root.find('.//pds:file_name', ns)
            if elem is not None: metadata['file_name'] = elem.text
            
            elem = root.find('.//pds:file_size', ns)
            if elem is not None: metadata['file_size'] = int(elem.text)
            
            elem = root.find('.//pds:File/pds:records', ns)
            if elem is not None: metadata['records'] = int(elem.text)
            
            columns_info = {}
            for field in root.findall('.//pds:Field_Delimited', ns):
                field_name = field.find('pds:name', ns).text
                field_desc = field.find('pds:description', ns)
                if field_desc is not None:
                    columns_info[field_name] = field_desc.text
            metadata['column_descriptions'] = columns_info
            
        except Exception as e:
            print(f"  [WARNING] Could not parse complete PDS4 XML metadata: {e}")
            
        return metadata

    def clean_libs_pair(self, csv_path, xml_path, target_folder):
        # Extract metadata
        metadata = self.extract_metadata_from_xml(xml_path)
        metadata['source_file'] = csv_path.name
        metadata['processing_timestamp'] = self.timestamp
        
        # Load CSV
        df = pd.read_csv(csv_path)
        
        # Wavelength columns are indices 6 through the 8th column from the end
        wavelength_cols = df.columns[6:-8].tolist()
        wavelengths = np.array([float(w) for w in wavelength_cols])
        
        # Filter backgrounds and plasmas
        bg_mask = (df['Force Reset Status'] == 1) & (df['Laser Fire Status'] == 0)
        plasma_mask = (df['Laser Fire Status'] == 1) & (df['Force Reset Status'] == 0)
        
        bg_df = df[bg_mask].copy()
        plasma_df = df[plasma_mask].copy()
        
        n_pairs = 0
        if len(bg_df) == 0:
            n_pairs = len(plasma_df)
        elif len(plasma_df) == 0:
            n_pairs = len(bg_df)
        else:
            n_pairs = min(len(bg_df), len(plasma_df))
            
        cleaned_records = []
        measurement_params = []
        
        for pair_id in range(n_pairs):
            bg_spectrum = np.zeros(len(wavelength_cols), dtype=float)
            plasma_spectrum = np.zeros(len(wavelength_cols), dtype=float)
            
            if len(bg_df) > 0:
                bg_spectrum = bg_df.iloc[pair_id][wavelength_cols].values.astype(float)
            if len(plasma_df) > 0:
                plasma_spectrum = plasma_df.iloc[pair_id][wavelength_cols].values.astype(float)
                
            # Perform background subtraction
            cleaned_spectrum = np.maximum(plasma_spectrum - bg_spectrum, 0) # clip negative to zero
            
            plasma_row = plasma_df.iloc[pair_id] if len(plasma_df) > pair_id else None
            
            params = {
                'Measurement_ID': pair_id + 1,
                'Time': None if plasma_row is None else plasma_row['Time'],
                'Operation_Mode': None if plasma_row is None else plasma_row['Operation Mode'],
                'Measurement_Type': 'Plasma' if plasma_row is not None else 'Background',
                'Delay_Time_us': None if plasma_row is None else plasma_row['Delay Time'],
                'Integration_Time_us': None if plasma_row is None else plasma_row['Integration Time'],
                'Number_of_Pulses': None if plasma_row is None else plasma_row['Number of Pulses'],
                'X_Factor': None if plasma_row is None else plasma_row['X Factor'],
                'Laser_Energy_V': None if plasma_row is None else plasma_row['Laser Energy'],
                'Laser_Pump_Current_A': None if plasma_row is None else plasma_row['Laser Pump Current'],
                'PRR_Hz': None if plasma_row is None else plasma_row['PRR'],
                'On_Off_Status': None if plasma_row is None else plasma_row['On Off Status']
            }
            measurement_params.append(params)
            
            for wavelength, intensity in zip(wavelengths, cleaned_spectrum):
                cleaned_records.append({
                    'Measurement_ID': params['Measurement_ID'],
                    'Time_UTC': params['Time'],
                    'Measurement_Count': None if plasma_row is None else plasma_row['Measurement Count'],
                    'Wavelength_nm': wavelength,
                    'Cleaned_Intensity': intensity,
                    'Operation_Mode': params['Operation_Mode'],
                    'Measurement_Type': params['Measurement_Type'],
                    'Force_Reset_Status': None if plasma_row is None else plasma_row['Force Reset Status'],
                    'Laser_Fire_Status': None if plasma_row is None else plasma_row['Laser Fire Status'],
                    'Is_Valid_Plasma': plasma_row is not None,
                    'Is_Background': plasma_row is None,
                    'Delay_Time_us': params['Delay_Time_us'],
                    'Integration_Time_us': params['Integration_Time_us'],
                    'Number_of_Pulses': params['Number_of_Pulses'],
                    'X_Factor': params['X_Factor'],
                    'Laser_Energy_V': params['Laser_Energy_V'],
                    'Laser_Pump_Current_A': params['Laser_Pump_Current_A'],
                    'PRR_Hz': params['PRR_Hz'],
                    'On_Off_Status': params['On_Off_Status']
                })
                
        cleaned_df = pd.DataFrame(cleaned_records)
        
        # Save output in identical authentic folders
        target_folder.mkdir(parents=True, exist_ok=True)
        base_name = csv_path.stem
        
        csv_output = target_folder / f"{base_name}_cleaned.csv"
        cleaned_df.to_csv(csv_output, index=False)
        
        metadata['total_measurements'] = n_pairs
        metadata['wavelength_range_nm'] = f"{wavelengths[0]:.2f} - {wavelengths[-1]:.2f}"
        metadata['total_channels'] = len(wavelengths)
        
        metadata_output = target_folder / f"{base_name}_metadata.json"
        with open(metadata_output, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        params_df = pd.DataFrame(measurement_params)
        params_output = target_folder / f"{base_name}_instrument_params.csv"
        params_df.to_csv(params_output, index=False)
        
        # Copy original PDS4 XML to maintain authenticity folder completeness
        xml_output = target_folder / xml_path.name
        xml_output.write_text(xml_path.read_text(encoding='utf-8'), encoding='utf-8')
        
        self.stats['files_cleaned'] += 1
        self.stats['points_generated'] += len(cleaned_df)
        print(f"  [SUCCESS] Processed: {csv_path.name} -> Cleaned CSV, metadata JSON, and original XML saved.")

    def run(self):
        print("====================================================")
        print(" STAGE 2: L1 DATA PROCESSING & AUTHENTIC STORAGE")
        print("====================================================")
        
        if not self.raw_dir.exists():
            print(f"[ERROR] Raw base path not found: {self.raw_dir}")
            return
            
        # Get YYYYMMDD folders
        date_folders = sorted([d for d in self.raw_dir.iterdir() 
                              if d.is_dir() and re.match(r'^\d{8}$', d.name)])
        
        for date_folder in date_folders:
            print(f"\nProcessing date directory: {date_folder.name}")
            
            obs_folders = sorted([f for f in date_folder.iterdir() 
                                 if f.is_dir() and re.match(r'^ch3_lib_\d{3}_\d{8}T\d{6}_\d{2}_l1$', f.name)])
            
            for obs_folder in obs_folders:
                # Replicate nesting inside processed folder
                target_folder = self.processed_dir / "calibrated" / date_folder.name / obs_folder.name
                
                # Find parent CSV and XML file pairs
                csv_files = sorted(obs_folder.glob("*.csv"))
                
                parent_csv = None
                parent_xml = None
                
                for csv_file in csv_files:
                    base_name = csv_file.stem
                    parts = base_name.split('_')
                    if len(parts) > 0 and not parts[-1].isdigit():
                        parent_csv = csv_file
                        break
                        
                if parent_csv:
                    parent_xml = parent_csv.with_suffix('.xml')
                    
                if parent_csv and parent_xml.exists():
                    self.stats['folders_processed'] += 1
                    try:
                        self.clean_libs_pair(parent_csv, parent_xml, target_folder)
                    except Exception as e:
                        self.stats['errors'] += 1
                        print(f"  [ERROR] Processing failed for {parent_csv.name}: {e}")
                        
        print("\n----------------------------------------------------")
        print(" PROCESSING STAGE 2 SUMMARY METRICS")
        print("----------------------------------------------------")
        print(f"Total Folders processed : {self.stats['folders_processed']}")
        print(f"Cleaned CSV files saved : {self.stats['files_cleaned']}")
        print(f"Total points generated  : {self.stats['points_generated']:,}")
        print(f"Encountered Errors      : {self.stats['errors']}")
        print(f"[SUCCESS] Processed spectra saved in ISRO hierarchy inside: {self.processed_dir}")
        print("====================================================\n")

if __name__ == "__main__":
    import sys
    raw = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RAW_DIR
    processed = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PROCESSED_DIR
    processor = L1DataProcessor(raw, processed)
    processor.run()
