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

CSV_FOLDER = r"C:\ch3_docs_summation\Wavelength vs Intensity_l2_csv"

# ============================================================================
# LOGGING
# ============================================================================
def log(msg, tag="INFO"):
    print(f"[{tag}] {msg}")

# ============================================================================
# VALUE CLEANER
# ============================================================================
def clean_value(val):
    if pd.isna(val):
        return None
    try:
        return val.item()
    except:
        return val

# ============================================================================
# SQL
# ============================================================================
INSERT_SQL = """
INSERT INTO spectral_data_clean (
    measurement_id,
    wavelength_nm,
    intensity
)
VALUES (%s, %s, %s)
"""

# ============================================================================
# MAIN
# ============================================================================
def process_spectral_clean():

    log("Starting spectral_data_clean ingestion", "START")

    files = [f for f in os.listdir(CSV_FOLDER) if f.endswith(".csv")]
    log(f"{len(files)} files found")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    total_inserted = 0

    for file in files:

        file_path = os.path.join(CSV_FOLDER, file)

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            log(f"{file} failed: {e}", "ERROR")
            continue

        # normalize columns
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        required = ["measurement_id", "wavelength_nm", "cleaned_intensity"]
        if not all(col in df.columns for col in required):
            log(f"{file} missing required columns", "ERROR")
            continue

        # ensure numeric ids
        df["measurement_id"] = pd.to_numeric(df["measurement_id"], errors="coerce")

        # build file_info_id from filename
        base_name = file.replace("_l1_cleaned.csv", "")
        parts = base_name.split("_")

        dt = parts[3]
        sub = parts[4]

        date = dt.split("T")[0]
        time = dt.split("T")[1]

        file_info_id = f"FI-{date}-{time}-{sub}"

        batch = []

        for _, row in df.iterrows():

            local_id = row["measurement_id"]

            if pd.isna(local_id):
                continue

            measurement_index = int(local_id)
            measurement_id = f"{file_info_id}-{measurement_index}"

            wavelength = clean_value(row["wavelength_nm"])
            intensity = clean_value(row["cleaned_intensity"])

            if wavelength is None or intensity is None:
                continue

            batch.append((measurement_id, float(wavelength), float(intensity)))

        if batch:
            execute_batch(cursor, INSERT_SQL, batch, page_size=5000)

        inserted = len(batch)
        total_inserted += inserted

        log(f"{file} → {inserted} spectral rows", "FILE")

    conn.commit()
    cursor.close()
    conn.close()

    log(f"Total inserted: {total_inserted}", "DONE")


# ============================================================================
# RUN
# ============================================================================
if __name__ == "__main__":
    process_spectral_clean()