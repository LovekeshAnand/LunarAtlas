"""
ingest_observation_file_info.py
--------------------------------
Populates the observation_file_info table by combining 3 sources:

  SOURCE 1 — Raw XML folder (files ending in _l0.xml)
             → md5_checksum_raw, file_size_bytes_raw

  SOURCE 2 — Clean XML folder (files ending in _l1.xml)
             → record_count, creation_datetime, base_file_name, xml_label_name

  SOURCE 3 — all_cleaned_checksums.csv
             → md5_checksum_clean, file_size_bytes_clean, storage_path_clean

  SOURCE 4 — observation_table.csv  (your exported observation table)
             → observation_id lookup keyed by observation_code
             → eliminates all hardcoded A/B maps

observation_id format (updated):
  LIB-YYYYMMDD-HHMMSS-SS
  e.g. ch3_lib_040_20230901T061242_00_l1 → LIB-20230901-061242-00
  The middle segment is now the HHMMSS timestamp, not the sequence number.
  There is no longer an A/B suffix.
"""

import os
import csv
import xml.etree.ElementTree as ET
import psycopg2
from datetime import datetime


# ---------------------------------------------------------------------------
# CONFIGURATION — update these before running
# ---------------------------------------------------------------------------

RAW_XML_DIR        = r"C:\ch3libs\raw_xmls"                              # folder with all _l0.xml files
CLEAN_XML_DIR      = r"C:\ch3libs\clean"                                 # folder with all _l1.xml files
CLEAN_CSV_PATH     = r"C:\Users\Dua Saeed\Downloads\all_cleaned_checksums.csv"
OBSERVATION_TABLE  = r"C:\Users\Dua Saeed\Desktop\prime.csv"   # your exported observation table

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "LunarAtlas",
    "user":     "postgres",
    "password": "summertimesadness101",
}

# PDS4 XML namespace
NS = {"pds": "http://pds.nasa.gov/pds4/pds/v1"}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def find_text(root, path):
    el = root.find(path, NS)
    return el.text.strip() if el is not None and el.text else None


def base_from_l0(filename):
    """ch3_lib_002_20230825T104221_00_l0.xml → ch3_lib_002_20230825T104221_00_l1"""
    return filename.replace("_l0.xml", "_l1").replace("_l0", "_l1")


def generate_file_info_id(base_file_name):
    """
    Derives a file_info_id from the base_file_name using the same
    structure as the updated observation_id (LIB-YYYYMMDD-HHMMSS-SS),
    but with an FI- prefix.

    Example:
      ch3_lib_040_20230901T061242_00_l1 → FI-20230901-061242-00

    Parts of the filename (split on '_'):
      [0] ch3
      [1] lib
      [2] 040          ← observation sequence number (unused in new format)
      [3] 20230901T061242  ← date + time
      [4] 00           ← sub-index
      [5] l1
    """
    parts    = base_file_name.split("_")
    datetime_part = parts[3]                    # e.g. '20230901T061242'
    date_str      = datetime_part.split("T")[0] # e.g. '20230901'
    time_str      = datetime_part.split("T")[1] # e.g. '061242'
    sub_idx       = parts[4]                    # e.g. '00'
    return f"FI-{date_str}-{time_str}-{sub_idx}"


# ---------------------------------------------------------------------------
# STEP 1: Build observation_code → observation_id lookup
#         directly from your exported observation table CSV
# ---------------------------------------------------------------------------

def load_observation_lookup(obs_csv_path):
    """
    Reads the observation table CSV and builds a dict:
      { observation_code → observation_id }

    Updated observation_id format: LIB-YYYYMMDD-HHMMSS-SS
    e.g. 'ch3_lib_040_20230901T061242_00_l1' → 'LIB-20230901-061242-00'

    This handles all cases automatically — no hardcoding needed.
    """
    lookup = {}
    with open(obs_csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            obs_code = row["observation_code"].strip()
            obs_id   = row["observation_id"].strip()
            lookup[obs_code] = obs_id
    print(f"  [OBS]   Loaded {len(lookup)} observation_code → observation_id mappings.")
    return lookup


# ---------------------------------------------------------------------------
# STEP 2: Load all_cleaned_checksums.csv → lookup by base_file_name
# ---------------------------------------------------------------------------

def load_clean_lookup(csv_path):
    lookup = {}
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            base = row["file_name"].replace("_cleaned.csv", "")
            lookup[base] = {
                "md5_checksum_clean":    row["md5_checksum"],
                "file_size_bytes_clean": int(row["file_size_bytes"]),
                "storage_path_clean":    row["file_path"],
            }
    print(f"  [CSV]   Loaded {len(lookup)} clean checksum records.")
    return lookup


# ---------------------------------------------------------------------------
# STEP 3: Parse raw _l0.xml → md5_checksum_raw, file_size_bytes_raw
# ---------------------------------------------------------------------------

def parse_raw_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    return {
        "md5_checksum_raw":    find_text(root, ".//pds:md5_checksum"),
        "file_size_bytes_raw": int(find_text(root, ".//pds:file_size") or 0) or None,
    }


# ---------------------------------------------------------------------------
# STEP 4: Parse clean _l1.xml → record_count, creation_datetime, etc.
# ---------------------------------------------------------------------------

def parse_clean_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    xml_filename     = os.path.basename(xml_path)
    base_file_name   = xml_filename.replace(".xml", "")

    record_count_str = find_text(root, ".//pds:records")
    creation_dt_str  = find_text(root, ".//pds:creation_date_time")

    creation_datetime = None
    if creation_dt_str:
        try:
            creation_datetime = datetime.strptime(
                creation_dt_str.rstrip("Z"), "%Y-%m-%dT%H:%M:%S"
            )
        except ValueError:
            pass

    return {
        "xml_label_name":    xml_filename,
        "base_file_name":    base_file_name,
        "record_count":      int(record_count_str) if record_count_str else None,
        "creation_datetime": creation_datetime,
    }


# ---------------------------------------------------------------------------
# STEP 5: INSERT SQL
# ---------------------------------------------------------------------------

INSERT_SQL = """
INSERT INTO observation_file_info (
    file_info_id,
    observation_id,
    base_file_name,
    md5_checksum_raw,
    md5_checksum_clean,
    file_size_bytes_raw,
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
    %(md5_checksum_raw)s,
    %(md5_checksum_clean)s,
    %(file_size_bytes_raw)s,
    %(file_size_bytes_clean)s,
    %(record_count)s,
    %(xml_label_name)s,
    %(creation_datetime)s,
    %(storage_path_clean)s
)
ON CONFLICT (file_info_id) DO NOTHING;
"""


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("\n=== observation_file_info Ingestion ===\n")

    # Load all lookups
    obs_lookup   = load_observation_lookup(OBSERVATION_TABLE)
    clean_lookup = load_clean_lookup(CLEAN_CSV_PATH)

    # Build raw XML lookup keyed by l1 base_file_name
    raw_xml_lookup = {}
    for fname in os.listdir(RAW_XML_DIR):
        if fname.endswith("_l0.xml"):
            base_l1 = base_from_l0(fname)
            raw_xml_lookup[base_l1] = os.path.join(RAW_XML_DIR, fname)
    print(f"  [RAW]   Found {len(raw_xml_lookup)} raw (_l0) XML files.")

    # Get all clean XMLs
    clean_xml_files = [
        os.path.join(CLEAN_XML_DIR, f)
        for f in sorted(os.listdir(CLEAN_XML_DIR))
        if f.endswith("_l1.xml")
    ]
    print(f"  [CLEAN] Found {len(clean_xml_files)} clean (_l1) XML files.")
    print(f"\nStarting ingestion...\n")

    conn   = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    success = 0
    errors  = 0

    for clean_xml_path in clean_xml_files:
        try:
            clean_meta = parse_clean_xml(clean_xml_path)
            base       = clean_meta["base_file_name"]

            # Derive observation_id from observation table lookup
            observation_id = obs_lookup.get(base)
            if not observation_id:
                print(f"  [WARN] No observation_id found for: {base} — skipping.")
                errors += 1
                continue

            # Get raw XML metadata
            raw_meta = {}
            if base in raw_xml_lookup:
                raw_meta = parse_raw_xml(raw_xml_lookup[base])
            else:
                print(f"  [WARN] No raw XML found for: {base}")

            # Get clean CSV metadata
            csv_meta = clean_lookup.get(base, {})
            if not csv_meta:
                print(f"  [WARN] No clean CSV record found for: {base}")

            row = {
                "file_info_id":          generate_file_info_id(base),
                "observation_id":        observation_id,
                "base_file_name":        base,
                "md5_checksum_raw":      raw_meta.get("md5_checksum_raw"),
                "md5_checksum_clean":    csv_meta.get("md5_checksum_clean"),
                "file_size_bytes_raw":   raw_meta.get("file_size_bytes_raw"),
                "file_size_bytes_clean": csv_meta.get("file_size_bytes_clean"),
                "record_count":          clean_meta["record_count"],
                "xml_label_name":        clean_meta["xml_label_name"],
                "creation_datetime":     clean_meta["creation_datetime"],
                "storage_path_clean":    csv_meta.get("storage_path_clean"),
            }

            cursor.execute(INSERT_SQL, row)
            success += 1
            print(f"  [OK]  {row['file_info_id']}  →  obs: {row['observation_id']}")

        except Exception as e:
            errors += 1
            print(f"  [ERR] {clean_xml_path}: {e}")
            conn.rollback()
            continue

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n=== Done ===")
    print(f"  Inserted : {success}")
    print(f"  Errors   : {errors}")


if __name__ == "__main__":
    main()