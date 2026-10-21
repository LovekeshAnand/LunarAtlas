#!/usr/bin/env python3
"""
LunarAtlas Ingestion Pipeline - Stage 2: Process L1 Data
=========================================================
Crawls raw L1 data, performs background-subtraction cleaning,
and outputs processed results replicating the identical ISRO/PDS4 date and observation folder hierarchy.

Edge cases handled:
  - Consecutive plasma shots (each subtracted from last seen background)
  - Consecutive backgrounds (last one wins)
  - Plasma before any background (excluded, logged; Measurement_ID numbering keeps its slot)
  - Trailing background with no plasma after it (logged, skipped)
  - File with only backgrounds, no plasma
  - File with only plasma, no background
  - Empty file (0 data rows)
  - Ambiguous rows (0,0) or (1,1) in status columns
  - NaN in status columns
  - NaN in spectral intensity values
  - Wrong number of trailing metadata columns
  - Missing XML file for a session CSV
  - Background intensity higher than plasma (>50% channels with negative residual: warning only)
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
DEFAULT_PROCESSED_DIR = str(Path(__file__).resolve().parent.parent / "datasets" / "processed")

# Quality warning: fraction of channels with a negative pre-clamp residual (flag only, nothing is dropped)
CLIP_WARNING_FRACTION = 0.5

EXPECTED_TRAILING_COLS = [
    'Delay Time', 'Integration Time', 'Number of Pulses',
    'X Factor', 'Laser Energy', 'Laser Pump Current', 'PRR', 'On Off Status'
]


class L1DataProcessor:
    def __init__(self, raw_dir, processed_dir):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.stats = {
            'folders_processed': 0,
            'files_cleaned': 0,
            'points_generated': 0,
            'errors': 0,
            'empty_files_skipped': 0,
            'bg_only_files': 0,
            'plasma_only_files': 0,
            'missing_xml_skipped': 0,
            'ambiguous_rows': 0,
            'nan_status_rows': 0,
            'plasma_no_background': 0,
            'high_zero_clip_warnings': 0,
        }

    # ------------------------------------------------------------------
    # XML metadata extraction
    # ------------------------------------------------------------------
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
            'instrument_description': 'ChaSTE-LIBS compact active spectrometer',
            'information_model_version': '1.20.0.0',
            'processing_level': 'calibrated'
        }

        try:
            elem = root.find('.//pds:logical_identifier', ns)
            if elem is not None: metadata['logical_identifier'] = elem.text

            elem = root.find('.//pds:Identification_Area/pds:version_id', ns)
            if elem is not None: metadata['version_id'] = elem.text

            elem = root.find('.//pds:information_model_version', ns)
            if elem is not None: metadata['information_model_version'] = elem.text

            elem = root.find('.//pds:processing_level', ns)
            if elem is not None: metadata['processing_level'] = elem.text

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

    # ------------------------------------------------------------------
    # Core processing
    # ------------------------------------------------------------------
    def clean_libs_pair(self, csv_path, xml_path, target_folder):
        fname = csv_path.name

        # ── Extract metadata ──────────────────────────────────────────
        metadata = self.extract_metadata_from_xml(xml_path)
        metadata['source_file'] = fname
        metadata['processing_timestamp'] = self.timestamp

        # ── Load CSV ──────────────────────────────────────────────────
        df = pd.read_csv(csv_path)

        # Edge case 4: empty file
        if df.empty:
            print(f"  [WARNING] Empty file skipped: {fname}")
            self.stats['empty_files_skipped'] += 1
            return

        # ── Validate column layout ────────────────────────────────────
        # Edge case 8: wrong number of trailing metadata columns
        actual_trailing = df.columns[-8:].tolist()
        if actual_trailing != EXPECTED_TRAILING_COLS:
            print(f"  [WARNING] Unexpected trailing columns in {fname}: {actual_trailing}")
            print(f"            Expected                             : {EXPECTED_TRAILING_COLS}")
            # Attempt to locate them by name instead of position
            missing = [c for c in EXPECTED_TRAILING_COLS if c not in df.columns]
            if missing:
                print(f"  [ERROR] Cannot proceed — missing columns: {missing}")
                self.stats['errors'] += 1
                return

        wavelength_cols = df.columns[6:-8].tolist()
        wavelengths = np.array([float(w) for w in wavelength_cols])

        # ── Row-by-row processing ─────────────────────────────────────
        last_bg_spectrum = None
        last_bg_row = None
        cleaned_records = []
        measurement_params = []
        trailing_bg_count = 0   # backgrounds seen after the last plasma
        # Plasma sequence index; Measurement_ID must equal it so cleaned rows stay linked to
        # measurement_raw ({file_info_id}-{plasma_count}) even when unpaired shots are excluded
        plasma_index = 0
        excluded_no_bg = 0

        for idx, row in df.iterrows():
            frs = row['Force Reset Status']
            lfs = row['Laser Fire Status']

            # Edge case 9: NaN in status columns
            if pd.isna(frs) or pd.isna(lfs):
                print(f"  [WARNING] NaN status at data row {idx + 1} in {fname} — skipped")
                self.stats['nan_status_rows'] += 1
                continue

            frs, lfs = int(frs), int(lfs)
            is_bg     = (frs == 1) and (lfs == 0)
            is_plasma = (lfs == 1) and (frs == 0)

            # ── Background row ────────────────────────────────────────
            if is_bg:
                spectrum = row[wavelength_cols].values.astype(float)

                # Edge case 10: NaN intensities in background
                if np.any(np.isnan(spectrum)):
                    print(f"  [WARNING] NaN intensities in background at row {idx + 1} in {fname} — bg not updated")
                else:
                    last_bg_spectrum = spectrum   # last-bg-wins (edge case 1)
                    last_bg_row = idx + 1         # 1-based data row, kept for pairing provenance
                    trailing_bg_count += 1

            # ── Plasma row ────────────────────────────────────────────
            elif is_plasma:
                trailing_bg_count = 0   # reset trailing bg counter
                plasma_index += 1

                # Edge case 2 & 6: plasma with no preceding background — excluded (raw row is kept in measurement_raw only if the product has other, paired shots)
                if last_bg_spectrum is None:
                    print(f"  [WARNING] Plasma at row {idx + 1} has no preceding background in {fname} — excluded")
                    self.stats['plasma_no_background'] += 1
                    excluded_no_bg += 1
                    continue

                plasma_spectrum = row[wavelength_cols].values.astype(float)

                # Edge case 10: NaN intensities in plasma
                nan_in_plasma = np.any(np.isnan(plasma_spectrum))
                if nan_in_plasma:
                    print(f"  [WARNING] NaN intensities in plasma at row {idx + 1} in {fname} — intensities set to 0")
                    plasma_spectrum = np.nan_to_num(plasma_spectrum, nan=0.0)

                residual = plasma_spectrum - last_bg_spectrum
                cleaned_spectrum = np.maximum(residual, 0)
                is_bg_subtracted = True

                # Edge case 11: background exceeds plasma on most channels.
                # Clip fraction = channels with a negative residual *before* clamping, over all
                # stored channels (exact zeros, P == B, are not clipping and are not counted)
                clip_fraction = np.sum(residual < 0) / len(residual)
                if clip_fraction > CLIP_WARNING_FRACTION:
                    print(f"  [WARNING] {clip_fraction*100:.0f}% channels clipped at row {idx + 1} in {fname} "
                          f"(background may exceed plasma signal)")
                    self.stats['high_zero_clip_warnings'] += 1

                params = {
                    'Measurement_ID':       plasma_index,
                    'Time':                 row['Time'],
                    'Measurement_Count':    row['Measurement Count'],
                    'Operation_Mode':       row['Operation Mode'],
                    'Measurement_Type':     'Plasma',
                    'Force_Reset_Status':   row['Force Reset Status'],
                    'Laser_Fire_Status':    row['Laser Fire Status'],
                    'Delay_Time_us':        row['Delay Time'],
                    'Integration_Time_us':  row['Integration Time'],
                    'Number_of_Pulses':     row['Number of Pulses'],
                    'X_Factor':             row['X Factor'],
                    'Laser_Energy_V':       row['Laser Energy'],
                    'Laser_Pump_Current_A': row['Laser Pump Current'],
                    'PRR_Hz':               row['PRR'],
                    'On_Off_Status':        row['On Off Status'],
                    'Background_Subtracted': is_bg_subtracted,
                    'Background_Row':        last_bg_row,
                    'Has_NaN_Intensities':   nan_in_plasma,
                    'Clip_Fraction':         round(float(clip_fraction), 4),
                }
                measurement_params.append(params)

                for wavelength, intensity in zip(wavelengths, cleaned_spectrum):
                    cleaned_records.append({
                        'Measurement_ID':        params['Measurement_ID'],
                        'Time_UTC':              row['Time'],
                        'Measurement_Count':     row['Measurement Count'],
                        'Wavelength_nm':         wavelength,
                        'Cleaned_Intensity':     intensity,
                        'Operation_Mode':        row['Operation Mode'],
                        'Measurement_Type':      'Plasma',
                        'Force_Reset_Status':    frs,
                        'Laser_Fire_Status':     lfs,
                        'Is_Valid_Plasma':       True,
                        'Background_Subtracted': is_bg_subtracted,
                        'Delay_Time_us':         params['Delay_Time_us'],
                        'Integration_Time_us':   params['Integration_Time_us'],
                        'Number_of_Pulses':      params['Number_of_Pulses'],
                        'X_Factor':              params['X_Factor'],
                        'Laser_Energy_V':        params['Laser_Energy_V'],
                        'Laser_Pump_Current_A':  params['Laser_Pump_Current_A'],
                        'PRR_Hz':                params['PRR_Hz'],
                        'On_Off_Status':         params['On_Off_Status'],
                    })

            # ── Ambiguous row (0,0) or (1,1) ─────────────────────────
            else:
                print(f"  [WARNING] Ambiguous status at row {idx + 1} "
                      f"(Force Reset={frs}, Laser Fire={lfs}) in {fname} — skipped")
                self.stats['ambiguous_rows'] += 1

        # Edge case 3: trailing backgrounds with no plasma after them
        if trailing_bg_count > 0:
            print(f"  [WARNING] {trailing_bg_count} trailing background row(s) at end of {fname} with no plasma after them")

        if len(cleaned_records) == 0:
            # Edge case 6: every plasma shot lacked a preceding background
            if excluded_no_bg > 0:
                print(f"  [WARNING] No plasma shot in {fname} has a preceding background — "
                      f"all {excluded_no_bg} excluded, skipping output")
                self.stats['plasma_only_files'] += 1
            # Edge case 5: only backgrounds, no plasma at all
            elif last_bg_spectrum is not None:
                print(f"  [WARNING] No plasma shots found in {fname} — only background rows present, skipping output")
                self.stats['bg_only_files'] += 1
            return

        # ── Save outputs ──────────────────────────────────────────────
        cleaned_df = pd.DataFrame(cleaned_records)
        target_folder.mkdir(parents=True, exist_ok=True)
        base_name = csv_path.stem

        csv_output = target_folder / f"{base_name}_cleaned.csv"
        cleaned_df.to_csv(csv_output, index=False)

        metadata['total_measurements']  = len(measurement_params)
        metadata['wavelength_range_nm'] = f"{wavelengths[0]:.2f} - {wavelengths[-1]:.2f}"
        metadata['total_channels']      = len(wavelengths)

        metadata_output = target_folder / f"{base_name}_metadata.json"
        with open(metadata_output, 'w') as f:
            json.dump(metadata, f, indent=2)

        params_df = pd.DataFrame(measurement_params)
        params_output = target_folder / f"{base_name}_instrument_params.csv"
        params_df.to_csv(params_output, index=False)

        # Copy original PDS4 XML to maintain authenticity
        xml_output = target_folder / xml_path.name
        xml_output.write_text(xml_path.read_text(encoding='utf-8'), encoding='utf-8')

        self.stats['files_cleaned']    += 1
        self.stats['points_generated'] += len(cleaned_df)
        print(f"  [SUCCESS] Processed: {fname} -> {len(measurement_params)} plasma shots cleaned "
              f"({len(cleaned_df):,} spectral points)")

    # ------------------------------------------------------------------
    # Main crawl
    # ------------------------------------------------------------------
    def run(self):
        print("====================================================")
        print(" STAGE 2: L1 DATA PROCESSING & AUTHENTIC STORAGE")
        print("====================================================")

        if not self.raw_dir.exists():
            raise FileNotFoundError(f"Raw base path not found: {self.raw_dir}")

        # Get YYYYMMDD folders
        date_folders = sorted([
            d for d in self.raw_dir.iterdir()
            if d.is_dir() and re.match(r'^\d{8}$', d.name)
        ])

        for date_folder in date_folders:
            print(f"\nProcessing date directory: {date_folder.name}")

            obs_folders = sorted([
                f for f in date_folder.iterdir()
                if f.is_dir() and re.match(r'^ch3_lib_\d{3}_\d{8}T\d{6}_\d{2}_l1$', f.name)
            ])

            for obs_folder in obs_folders:
                target_folder = self.processed_dir / "calibrated" / date_folder.name / obs_folder.name

                # Find parent session CSV (stem does not end with a digit)
                csv_files = sorted(obs_folder.glob("*.csv"))
                parent_csv = None
                for csv_file in csv_files:
                    parts = csv_file.stem.split('_')
                    if parts and not parts[-1].isdigit():
                        parent_csv = csv_file
                        break

                if parent_csv is None:
                    print(f"  [WARNING] No parent session CSV found in {obs_folder.name} — skipped")
                    continue

                parent_xml = parent_csv.with_suffix('.xml')

                # Edge case 12: missing XML
                if not parent_xml.exists():
                    print(f"  [WARNING] Missing XML for {parent_csv.name} — skipped")
                    self.stats['missing_xml_skipped'] += 1
                    continue

                self.stats['folders_processed'] += 1
                try:
                    self.clean_libs_pair(parent_csv, parent_xml, target_folder)
                except Exception as e:
                    self.stats['errors'] += 1
                    print(f"  [ERROR] Processing failed for {parent_csv.name}: {e}")

        # ── Summary ───────────────────────────────────────────────────
        print("\n----------------------------------------------------")
        print(" PROCESSING STAGE 2 SUMMARY METRICS")
        print("----------------------------------------------------")
        print(f"Folders processed          : {self.stats['folders_processed']}")
        print(f"Cleaned CSV files saved    : {self.stats['files_cleaned']}")
        print(f"Total spectral points      : {self.stats['points_generated']:,}")
        print(f"Errors                     : {self.stats['errors']}")
        print(f"Empty files skipped        : {self.stats['empty_files_skipped']}")
        print(f"Background-only files      : {self.stats['bg_only_files']}")
        print(f"Plasma-only files (no bg)  : {self.stats['plasma_only_files']}")
        print(f"Missing XML skipped        : {self.stats['missing_xml_skipped']}")
        print(f"Ambiguous status rows      : {self.stats['ambiguous_rows']}")
        print(f"NaN status rows            : {self.stats['nan_status_rows']}")
        print(f"Plasma shots without bg    : {self.stats['plasma_no_background']}")
        print(f"High zero-clip warnings    : {self.stats['high_zero_clip_warnings']}")
        print(f"\n[SUCCESS] Processed spectra saved in ISRO hierarchy inside: {self.processed_dir}")
        print("====================================================\n")


if __name__ == "__main__":
    import sys
    import pipeline_logger
    raw       = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RAW_DIR
    processed = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PROCESSED_DIR
    try:
        processor = L1DataProcessor(raw, processed)
        processor.run()
        pipeline_logger.log_stage_success("stage_2", "L1 Data Processing", processor.stats)
        sys.exit(0)
    except Exception as e:
        pipeline_logger.log_stage_failure("stage_2", "L1 Data Processing", str(e))
        sys.exit(1)