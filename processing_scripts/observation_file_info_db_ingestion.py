import os
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from typing import Dict, Optional
import logging
import psycopg2

# ============================================================================
# LOGGING
# ============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# DB CONFIG
# ============================================================================
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "LunarAtlas",
    "user": "postgres",
    "password": "summertimesadness101"
}

# ============================================================================
# NORMALIZATION FUNCTION (KEY FIX)
# ============================================================================

def normalize_name(name: str) -> str:
    """Normalize filenames to comparable base."""
    name = name.strip()

    # remove extension
    if '.' in name:
        name = name.rsplit('.', 1)[0]

    # remove _cleaned suffix
    if name.lower().endswith('_cleaned'):
        name = name[:-len('_cleaned')]

    return name

def generate_file_info_id(base_file_name: str) -> str:
    """
    Convert:
    ch3_lib_040_20230901T061242_00_l1
    → FI-20230901-061242-00
    """
    try:
        parts = base_file_name.split("_")

        datetime_part = parts[3]        # 20230901T061242
        sub_index = parts[4]            # 00

        date_part = datetime_part.split("T")[0]
        time_part = datetime_part.split("T")[1]

        return f"FI-{date_part}-{time_part}-{sub_index}"

    except Exception as e:
        logger.error(f"Failed to generate file_info_id for {base_file_name}: {e}")
        return None
# ============================================================================
# XML PARSER
# ============================================================================

def parse_xml_file(xml_path: str) -> Dict:
    data = {
        'xml_label_name': os.path.basename(xml_path),
        'base_file_name': None,
        'md5_checksum_calibrated': None,
        'file_size_bytes_calibrated': None,
        'record_count': None,
        'creation_datetime': None,
        'observation_code': None,
        'error': None
    }

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {'pds': 'http://pds.nasa.gov/pds4/pds/v1'}

        logical_id = root.find('.//pds:logical_identifier', ns)
        if logical_id is not None and logical_id.text:
            data['observation_code'] = logical_id.text.split(':')[-1]

        file_elem = root.find('.//pds:File', ns)
        if file_elem is not None:

            file_name_elem = file_elem.find('pds:file_name', ns)
            if file_name_elem is not None and file_name_elem.text:
                # 🔥 normalize XML side
                data['base_file_name'] = normalize_name(file_name_elem.text)

            creation_elem = file_elem.find('pds:creation_date_time', ns)
            if creation_elem is not None and creation_elem.text:
                dt = datetime.fromisoformat(creation_elem.text.replace('Z', '+00:00'))
                data['creation_datetime'] = dt

            file_size_elem = file_elem.find('pds:file_size', ns)
            if file_size_elem is not None and file_size_elem.text:
                data['file_size_bytes_calibrated'] = int(file_size_elem.text)

            checksum_elem = file_elem.find('pds:md5_checksum', ns)
            if checksum_elem is not None and checksum_elem.text:
                data['md5_checksum_calibrated'] = checksum_elem.text.strip()

            records_elem = file_elem.find('pds:records', ns)
            if records_elem is not None and records_elem.text:
                data['record_count'] = int(records_elem.text)

        if not data['observation_code']:
            data['error'] = "Missing observation_code"

        return data

    except Exception as e:
        data['error'] = str(e)
        logger.error(f"Error parsing {xml_path}: {e}")
        return data

# ============================================================================
# CSV LOADER (FIXED)
# ============================================================================

def load_cleaned_checksums(csv_path: str) -> Dict[str, Dict]:
    mapping = {}

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:

            file_name = row.get('file_name', '').strip()
            base_name = normalize_name(file_name)

            try:
                size = int(row.get('file_size_bytes', '').strip())
            except:
                size = None

            mapping[base_name] = {
                'md5_checksum_clean': row.get('md5_checksum', '').strip() or None,
                'file_size_bytes_clean': size,
                'storage_path_clean': row.get('file_path', '').strip() or None
            }

    logger.info(f"Loaded {len(mapping)} cleaned checksum records")
    return mapping

# ============================================================================
# OBS TABLE
# ============================================================================

def load_observation_table(csv_path: str) -> Dict[str, str]:
    mapping = {}
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row['observation_code'].strip()] = row['observation_id'].strip()
    return mapping

# ============================================================================
# SQL
# ============================================================================

INSERT_SQL = """
INSERT INTO observation_file_info (
    file_info_id,
    observation_id,
    base_file_name,
    md5_checksum_calibrated,
    md5_checksum_clean,
    file_size_bytes_calibrated,
    file_size_bytes_clean,
    record_count,
    xml_label_name,
    creation_datetime,
    storage_path_clean
)
VALUES (
    %(file_info_id)s,
    %(observation_id)s,
    %(base_file_name)s,
    %(md5_checksum_calibrated)s,
    %(md5_checksum_clean)s,
    %(file_size_bytes_calibrated)s,
    %(file_size_bytes_clean)s,
    %(record_count)s,
    %(xml_label_name)s,
    %(creation_datetime)s,
    %(storage_path_clean)s
)
ON CONFLICT (file_info_id) DO NOTHING;
"""

# ============================================================================
# MAIN
# ============================================================================

def process_all_files(xml_folder, obs_csv, clean_csv):

    obs_map = load_observation_table(obs_csv)
    clean_map = load_cleaned_checksums(clean_csv)

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    for file in os.listdir(xml_folder):
        if not file.endswith("_l1.xml"):
            continue

        xml_path = os.path.join(xml_folder, file)
        xml_data = parse_xml_file(xml_path)

        if xml_data['error']:
            continue

        cleaned = clean_map.get(xml_data['base_file_name'])

        if not cleaned:
            logger.warning(f"MISS: {xml_data['base_file_name']}")

        record = {
            'file_info_id': generate_file_info_id(xml_data['base_file_name']),
            'observation_id': obs_map.get(xml_data['observation_code']),
            'base_file_name': xml_data['base_file_name'],
            'md5_checksum_calibrated': xml_data['md5_checksum_calibrated'],
            'md5_checksum_clean': cleaned.get('md5_checksum_clean') if cleaned else None,
            'file_size_bytes_calibrated': xml_data['file_size_bytes_calibrated'],
            'file_size_bytes_clean': cleaned.get('file_size_bytes_clean') if cleaned else None,
            'record_count': xml_data['record_count'],
            'xml_label_name': xml_data['xml_label_name'],
            'creation_datetime': xml_data['creation_datetime'],
            'storage_path_clean': cleaned.get('storage_path_clean') if cleaned else None
        }

        cursor.execute(INSERT_SQL, record)

    conn.commit()
    cursor.close()
    conn.close()

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    process_all_files(
        xml_folder=r"C:\ch3_docs_summation\l1_xmls",
        obs_csv=r"C:\ch3_docs_summation\db_csv\observation.csv",
        clean_csv=r"C:\ch3_docs_summation\all_cleaned_checksums.csv"
    )