#!/usr/bin/env python3
"""
Chandrayaan-3 LIBS Batch Data Cleaning System
==============================================

This script processes entire directories of LIBS data files and creates:
1. Cleaned datasets with background subtraction
2. Organized folder structure
3. Preserved metadata from XML files
4. API-ready JSON outputs
5. Dashboard-ready CSV exports

Author: LIBS Data Processing Team
Date: 2026-02-08
"""

import pandas as pd
import numpy as np
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import sys
import os

class LIBSBatchProcessor:
    """
    Batch processor for Chandrayaan-3 LIBS data
    Handles parent files, subfiles, and creates organized output structure
    """
    
    def __init__(self, input_dir, output_base_dir=None):
        """
        Initialize batch processor
        
        Parameters:
        -----------
        input_dir : str or Path
            Directory containing LIBS CSV and XML files
        output_base_dir : str or Path, optional
            Base directory for outputs (default: creates 'cleaned_libs_data' in input_dir)
        """
        self.input_dir = Path(input_dir)
        
        if output_base_dir is None:
            self.output_base_dir = self.input_dir / "cleaned_libs_data"
        else:
            self.output_base_dir = Path(output_base_dir)
        
        # Create timestamp for this processing run
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directory structure
        self.create_output_structure()
        
        print("="*80)
        print("CHANDRAYAAN-3 LIBS BATCH DATA PROCESSOR")
        print("="*80)
        print(f"Input Directory: {self.input_dir}")
        print(f"Output Directory: {self.output_base_dir}")
        print(f"Processing Timestamp: {self.timestamp}")
        print("="*80)
    
    def create_output_structure(self):
        """Create organized folder structure for outputs"""
        # Main folders
        self.cleaned_data_dir = self.output_base_dir / "cleaned_spectra"
        self.metadata_dir = self.output_base_dir / "metadata"
        self.api_json_dir = self.output_base_dir / "api_json"
        self.visualizations_dir = self.output_base_dir / "visualizations"
        self.logs_dir = self.output_base_dir / "logs"
        
        # Create all directories
        for directory in [self.cleaned_data_dir, self.metadata_dir, 
                         self.api_json_dir, self.visualizations_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        print(f"\n✓ Created output folder structure in: {self.output_base_dir}")
    
    def extract_metadata_from_xml(self, xml_path):
        """
        Extract all metadata from XML file for authenticity preservation
        
        Parameters:
        -----------
        xml_path : Path
            Path to XML file
            
        Returns:
        --------
        dict : Extracted metadata
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Define namespace
        ns = {'pds': 'http://pds.nasa.gov/pds4/pds/v1'}
        
        metadata = {}
        
        # Extract key metadata fields
        try:
            # Identification
            metadata['logical_identifier'] = root.find('.//pds:logical_identifier', ns).text
            metadata['version_id'] = root.find('.//pds:Identification_Area/pds:version_id', ns).text
            metadata['title'] = root.find('.//pds:title', ns).text
            
            # Time coordinates
            metadata['start_time'] = root.find('.//pds:start_date_time', ns).text
            metadata['stop_time'] = root.find('.//pds:stop_date_time', ns).text
            
            # File info
            metadata['file_name'] = root.find('.//pds:file_name', ns).text
            metadata['file_size'] = root.find('.//pds:file_size', ns).text
            metadata['records'] = root.find('.//pds:File/pds:records', ns).text
            
            # Column definitions
            columns_info = {}
            for field in root.findall('.//pds:Field_Delimited', ns):
                field_name = field.find('pds:name', ns).text
                field_desc = field.find('pds:description', ns)
                if field_desc is not None:
                    columns_info[field_name] = field_desc.text
            
            metadata['column_descriptions'] = columns_info
            
            # Instrument info
            instrument_desc = root.find('.//pds:Observing_System_Component[pds:type="Instrument"]/pds:description', ns)
            if instrument_desc is not None:
                metadata['instrument_description'] = instrument_desc.text
            
        except Exception as e:
            print(f"Warning: Could not extract some metadata from {xml_path.name}: {e}")
        
        return metadata
    
    def identify_file_pairs(self):
        """
        Identify parent files and their corresponding XML files
        
        Returns:
        --------
        list : List of (csv_path, xml_path) tuples
        """
        csv_files = sorted(self.input_dir.glob("*.csv"))
        file_pairs = []
        
        for csv_file in csv_files:
            # Look for corresponding XML
            xml_file = csv_file.with_suffix('.xml')
            
            if xml_file.exists():
                # Determine if this is a parent or subfile
                # Parent files: ch3_lib_002_20230825T104221_00_l1.csv
                # Subfiles: ch3_lib_002_20230825T104221_00_l1_0_1.csv
                
                base_name = csv_file.stem
                parts = base_name.split('_')
                
                # If last part is a number (like 0, 1, 2), it's a subfile - skip it
                # We only process parent files
                if len(parts) > 0 and parts[-1].isdigit():
                    continue  # Skip subfiles
                
                file_pairs.append((csv_file, xml_file))
        
        return file_pairs
    

    
    def clean_parent_file(self, csv_path, xml_path, clip_negatives=True):
        """
        Clean a parent LIBS file (wide format with backgrounds and plasmas)
        
        Parameters:
        -----------
        csv_path : Path
            Path to parent CSV file
        xml_path : Path
            Path to corresponding XML file
        clip_negatives : bool
            Whether to clip negative values to zero
            
        Returns:
        --------
        tuple : (cleaned_df, metadata_dict)
        """
        print(f"\n{'='*80}")
        print(f"Processing: {csv_path.name}")
        print(f"{'='*80}")
        
        # Extract metadata first
        metadata = self.extract_metadata_from_xml(xml_path)
        metadata['source_file'] = csv_path.name
        metadata['processing_timestamp'] = self.timestamp
        metadata['clip_negatives'] = clip_negatives
        
        # Load CSV
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} rows")
        
        # Identify columns
        metadata_cols = ['Time', 'Measurement Count', 'Operation Mode', 
                        'Measurement Type', 'Force Reset Status', 'Laser Fire Status']
        
        # Extract instrument parameter columns (last 8 columns)
        instrument_param_cols = df.columns[-8:].tolist()
        
        # Wavelength columns are between metadata and instrument params
        wavelength_cols = df.columns[6:-8].tolist()
        wavelengths = np.array([float(w) for w in wavelength_cols])
        
        print(f"Found {len(wavelength_cols)} wavelength channels: {wavelengths[0]:.2f} - {wavelengths[-1]:.2f} nm")
        
        # Identify backgrounds and plasmas
        bg_mask = (df['Force Reset Status'] == 1) & (df['Laser Fire Status'] == 0)
        plasma_mask = (df['Laser Fire Status'] == 1) & (df['Force Reset Status'] == 0)
        
        bg_df = df[bg_mask].copy()
        plasma_df = df[plasma_mask].copy()
        
        print(f"Background spectra: {len(bg_df)}")
        print(f"Plasma spectra: {len(plasma_df)}")
        
        # Process pairs
        n_pairs = 0
        cleaned_data = []

        if len(bg_df) == 0:
            print("Bg_df value was zero and no length was found!", len(bg_df))
            n_pairs = (len(plasma_df))
        elif len(plasma_df) == 0:
            print("Plasma_df value was zero and no length was found!", len(plasma_df))
            n_pairs = (len(bg_df))
        else: 
            print("Both bg_df and plasma_df have values, proceeding with min length for pairing.")
            n_pairs = min(len(bg_df), len(plasma_df))
        
        # n_pairs = min(len(bg_df), len(plasma_df))
        # Store instrument parameters for each measurement
        measurement_params = []

        
        for pair_id in range(n_pairs):
            print(f"  Cleaning pair {pair_id + 1}/{n_pairs}...", end=" ")

            bg_spectrum = None
            plasma_spectrum = None

            if len(bg_df) == 0:
                print("There is no value in bg_df so nothing will be stored in bg_Spectrun and only the plasma_specturm will be considered for cleaning.")
                bg_spectrum = np.zeros(len(wavelength_cols), dtype=float)
                plasma_spectrum = plasma_df.iloc[pair_id][wavelength_cols].values.astype(float)

            elif len(plasma_df) == 0:
                print("There is no value in plasma_df so nothing will be stored in plasma_Spectrun and only the bg_specturm will be considered for cleaning.")
                plasma_spectrum = np.zeros(len(wavelength_cols), dtype=float)
                bg_spectrum = bg_df.iloc[pair_id][wavelength_cols].values.astype(float)

            else:
                print("bg_df has a value and it will be considered for cleaning along with the plasma_spectrum.")
                bg_spectrum = bg_df.iloc[pair_id][wavelength_cols].values.astype(float)
                plasma_spectrum = plasma_df.iloc[pair_id][wavelength_cols].values.astype(float)


            plasma_row= None
            
            # Get instrument parameters from plasma row (the actual measurement)
            if len(plasma_df) > pair_id:
                plasma_row = plasma_df.iloc[pair_id]

                params = {
                    'Measurement_ID': pair_id + 1,
                    'Time': plasma_row['Time'],
                    'Operation_Mode': plasma_row['Operation Mode'],
                    'Measurement_Type': 'EP',
                    'Delay_Time_us': plasma_row['Delay Time'],
                    'Integration_Time_us': plasma_row['Integration Time'],
                    'Number_of_Pulses': plasma_row['Number of Pulses'],
                    'X_Factor': plasma_row['X Factor'],
                    'Laser_Energy_V': plasma_row['Laser Energy'],
                    'Laser_Pump_Current_A': plasma_row['Laser Pump Current'],
                    'PRR_Hz': plasma_row['PRR'],
                    'On_Off_Status': plasma_row['On Off Status']
                }
            else:
                # Background-only case — NO early return
                params = {
                    'Measurement_ID': pair_id + 1,
                    'Time': None,
                    'Operation_Mode': None,
                    'Measurement_Type': 'EP',
                    'Delay_Time_us': None,
                    'Integration_Time_us': None,
                    'Number_of_Pulses': None,
                    'X_Factor': None,
                    'Laser_Energy_V': None,
                    'Laser_Pump_Current_A': None,
                    'PRR_Hz': None,
                    'On_Off_Status': None
                }   
            measurement_params.append(params)
            
            # Background subtraction
            cleaned_spectrum = plasma_spectrum - bg_spectrum
            
            # Clip if requested
            n_negatives = (cleaned_spectrum < 0).sum()
            if clip_negatives:
                cleaned_spectrum = np.maximum(cleaned_spectrum, 0)
            
            print(f"{n_negatives} negatives ({100*n_negatives/len(cleaned_spectrum):.1f}%)")
            
            # Store in tidy format with ALL PDS4 metadata
            for wavelength, intensity in zip(wavelengths, cleaned_spectrum):
                cleaned_data.append({
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

        
        # Create cleaned dataframe
        cleaned_df = pd.DataFrame(cleaned_data)
        
        # Reorder columns for better readability (metadata first, then spectral data)
        column_order = [
            'Measurement_ID',
            'Time_UTC',
            'Measurement_Count',
            'Wavelength_nm',
            'Cleaned_Intensity',
            'Operation_Mode',
            'Measurement_Type',
            'Force_Reset_Status',
            'Laser_Fire_Status',
            'Is_Valid_Plasma',
            'Is_Background',
            'Delay_Time_us',
            'Integration_Time_us',
            'Number_of_Pulses',
            'X_Factor',
            'Laser_Energy_V',
            'Laser_Pump_Current_A',
            'PRR_Hz',
            'On_Off_Status'
        ]
        cleaned_df = cleaned_df[column_order]
        
        # Add metadata summary
        metadata['total_measurements'] = n_pairs
        metadata['wavelength_range_nm'] = f"{wavelengths[0]:.2f} - {wavelengths[-1]:.2f}"
        metadata['total_channels'] = len(wavelengths)
        
        print(f"\n✓ Cleaned {n_pairs} measurements with ALL PDS4 metadata preserved")
        print(f"  Total data points: {len(cleaned_df):,}")
        print(f"  Total columns: {len(cleaned_df.columns)} (15 PDS4 standard + 4 derived)")
        print(f"  Mean intensity: {cleaned_df['Cleaned_Intensity'].mean():.2f}")
        
        return cleaned_df, metadata, measurement_params
    
    def save_outputs(self, cleaned_df, metadata, measurement_params, base_filename):
        """
        Save all output files in organized structure
        
        Parameters:
        -----------
        cleaned_df : DataFrame
            Cleaned spectral data
        metadata : dict
            Metadata extracted from XML
        measurement_params : list
            Instrument parameters for each measurement
        base_filename : str
            Base name for output files
        """
        print(f"\nSaving outputs for {base_filename}...")
        
        # 1. Save cleaned CSV (for analysis/dashboard)
        csv_output = self.cleaned_data_dir / f"{base_filename}_cleaned.csv"
        cleaned_df.to_csv(csv_output, index=False)
        print(f"  ✓ Cleaned CSV: {csv_output.name}")
        
        # 2. Save metadata JSON (for authenticity)
        metadata_output = self.metadata_dir / f"{base_filename}_metadata.json"
        with open(metadata_output, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"  ✓ Metadata JSON: {metadata_output.name}")
        
        # 3. Save instrument parameters CSV (for researchers)
        params_df = pd.DataFrame(measurement_params)
        params_output = self.metadata_dir / f"{base_filename}_instrument_params.csv"
        params_df.to_csv(params_output, index=False)
        print(f"  ✓ Instrument params: {params_output.name}")
        
        # 4. Save API-ready JSON (for programmatic access)
        api_data = {
            'metadata': metadata,
            'instrument_parameters': [
                {k: (int(v) if isinstance(v, (np.integer, np.int64)) else 
                     float(v) if isinstance(v, (np.floating, np.float64)) else v)
                 for k, v in params.items()}
                for params in measurement_params
            ],
            'spectra': []
        }
        
        # Group by Measurement_ID for API
        for meas_id in cleaned_df['Measurement_ID'].unique():
            meas_data = cleaned_df[cleaned_df['Measurement_ID'] == meas_id]
            api_data['spectra'].append({
                'measurement_id': int(meas_id),
                'wavelengths': meas_data['Wavelength_nm'].tolist(),
                'intensities': meas_data['Cleaned_Intensity'].tolist()
            })
        
        api_output = self.api_json_dir / f"{base_filename}_api.json"
        with open(api_output, 'w') as f:
            json.dump(api_data, f, indent=2)
        print(f"  ✓ API JSON: {api_output.name}")
        
        # 5. Save summary statistics (for quick reference)
        summary = {
            'file': base_filename,
            'processing_date': self.timestamp,
            'num_measurements': int(cleaned_df['Measurement_ID'].nunique()),
            'num_wavelengths': int(cleaned_df['Wavelength_nm'].nunique()),
            'wavelength_range': metadata['wavelength_range_nm'],
            'intensity_stats': {
                'min': float(cleaned_df['Cleaned_Intensity'].min()),
                'max': float(cleaned_df['Cleaned_Intensity'].max()),
                'mean': float(cleaned_df['Cleaned_Intensity'].mean()),
                'std': float(cleaned_df['Cleaned_Intensity'].std())
            }
        }
        
        return summary
    
    def process_all_files(self, clip_negatives=True):
        """
        Process all parent files in the input directory
        
        Parameters:
        -----------
        clip_negatives : bool
            Whether to clip negative values to zero
            
        Returns:
        --------
        dict : Processing summary
        """
        file_pairs = self.identify_file_pairs()
        
        if not file_pairs:
            print("\n❌ No parent files found to process!")
            print("   Make sure you have matching CSV and XML files.")
            return None
        
        print(f"\nFound {len(file_pairs)} parent file(s) to process")
        
        processing_summary = {
            'processing_timestamp': self.timestamp,
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_base_dir),
            'clip_negatives': clip_negatives,
            'files_processed': []
        }
        
        for csv_path, xml_path in file_pairs:
            try:
                cleaned_df, metadata, measurement_params = self.clean_parent_file(
                    csv_path, xml_path, clip_negatives
                )
                
                base_filename = csv_path.stem
                file_summary = self.save_outputs(
                    cleaned_df, metadata, measurement_params, base_filename
                )
                
                processing_summary['files_processed'].append(file_summary)
                
            except Exception as e:
                print(f"\n❌ Error processing {csv_path.name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Save master summary
        summary_path = self.logs_dir / f"processing_summary_{self.timestamp}.json"
        with open(summary_path, 'w') as f:
            json.dump(processing_summary, f, indent=2)
        
        print(f"\n{'='*80}")
        print("BATCH PROCESSING COMPLETE")
        print(f"{'='*80}")
        print(f"Processed: {len(processing_summary['files_processed'])} file(s)")
        print(f"Summary saved to: {summary_path}")
        print(f"\nOutput structure:")
        print(f"  📁 {self.output_base_dir}/")
        print(f"     ├── cleaned_spectra/     (CSV files for analysis)")
        print(f"     ├── metadata/            (XML metadata + instrument params)")
        print(f"     ├── api_json/            (JSON for programmatic access)")
        print(f"     ├── visualizations/      (For future plots)")
        print(f"     └── logs/                (Processing summaries)")
        
        return processing_summary


def main():
    """
    Main entry point for batch processing
    Usage: python batch_process_libs.py [input_dir] [output_dir]
    """
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    else:
        input_dir = "/mnt/user-data/uploads"  # Default for this system
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = None  # Will create in input directory
    
    # Create processor
    processor = LIBSBatchProcessor(input_dir, output_dir)
    
    # Process all files
    summary = processor.process_all_files(clip_negatives=True)
    
    if summary:
        print("\n✓ All files processed successfully!")
        print(f"\nYou can now:")
        print("  • Load cleaned CSVs into dashboards")
        print("  • Access data via API JSON files")
        print("  • Reference original metadata for authenticity")
        print("  • Share structured data with researchers/developers")
    
    return summary


if __name__ == "__main__":
    summary = main()
