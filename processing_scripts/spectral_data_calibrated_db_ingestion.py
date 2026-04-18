import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# ============================================================================
# CONFIG
# ============================================================================
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "LunarAtlas",
    "user": "postgres",
    "password": "summertimesadness101"
}

CSV_FOLDER = r"C:\ch3_docs_summation\l1_csv"

# ============================================================================
# HELPERS
# ============================================================================
def generate_file_info_id(base_file_name):
    parts = base_file_name.split("_")
    dt = parts[3]
    sub = parts[4]
    date = dt.split("T")[0]
    time = dt.split("T")[1]
    return f"FI-{date}-{time}-{sub}"

def is_float_column(col):
    try:
        float(col)
        return True
    except:
        return False

def log(msg, tag="INFO"):
    print(f"[{tag}] {msg}")

# ============================================================================
# SQL
# ============================================================================
INSERT_SQL = """
INSERT INTO spectral_data_calibrated (
    measurement_id,
    wavelength_nm,
    response_count
)
VALUES (%s, %s, %s)
"""

# ============================================================================
# MAIN
# ============================================================================
def process_spectral_calibrated():

    log("Starting spectral calibrated ingestion", "START")

    if not os.path.exists(CSV_FOLDER):
        log("CSV folder not found", "ERROR")
        return

    files = [f for f in os.listdir(CSV_FOLDER) if f.endswith(".csv")]
    log(f"{len(files)} files found")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    total_rows = 0

    for file in files:

        file_path = os.path.join(CSV_FOLDER, file)
        base_name = file.replace(".csv", "")
        file_info_id = generate_file_info_id(base_name)

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            log(f"{file} failed to read: {e}", "ERROR")
            continue

        # ============================================================================
        # CLEAN COLUMN NAMES
        # ============================================================================
        df.columns = df.columns.astype(str).str.strip()

        # ============================================================================
        # IDENTIFY SPECTRAL COLUMNS SAFELY
        # ============================================================================
        spectral_cols = [col for col in df.columns if is_float_column(col)]

        if not spectral_cols:
            log(f"{file} → No spectral columns detected", "WARN")
            continue

        batch = []

        for idx, row in df.iterrows():

            measurement_index = idx + 1
            measurement_id = f"{file_info_id}-{measurement_index}"

            for col in spectral_cols:

                val = row[col]

                if pd.isna(val):
                    continue

                try:
                    wavelength = float(col)
                    response = int(val)
                except:
                    continue

                batch.append((measurement_id, wavelength, response))

        # ============================================================================
        # INSERT
        # ============================================================================
        if batch:
            execute_batch(cursor, INSERT_SQL, batch, page_size=5000)

        inserted = len(batch)
        total_rows += inserted

        log(f"{file} → {inserted} spectral rows", "FILE")

    conn.commit()
    cursor.close()
    conn.close()

    log(f"Total inserted: {total_rows}", "DONE")


# ============================================================================
# RUN
# ============================================================================
if __name__ == "__main__":
    process_spectral_calibrated()