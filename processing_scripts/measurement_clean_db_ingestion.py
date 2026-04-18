import os
import pandas as pd
import psycopg2

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
# VALUE CLEANER (fix numpy → postgres issue)
# ============================================================================
def clean_value(val):
    if pd.isna(val):
        return None

    if isinstance(val, pd.Timestamp):
        return val.to_pydatetime()

    try:
        return val.item()  # converts numpy → python type
    except:
        return val

# ============================================================================
# SQL
# ============================================================================
INSERT_SQL = """
INSERT INTO measurement_clean (
    measurement_id,
    file_info_id,
    measurement_index,
    time_utc,
    measurement_count,
    operation_mode,
    measurement_type,
    force_reset_status,
    laser_fire_status,
    is_valid_plasma,
    is_background,
    delay_time_us,
    integration_time_us,
    number_of_pulses,
    x_factor,
    laser_energy_v,
    laser_pump_current_a,
    prr_hz,
    on_off_status
)
VALUES (
    %(measurement_id)s,
    %(file_info_id)s,
    %(measurement_index)s,
    %(time_utc)s,
    %(measurement_count)s,
    %(operation_mode)s,
    %(measurement_type)s,
    %(force_reset_status)s,
    %(laser_fire_status)s,
    %(is_valid_plasma)s,
    %(is_background)s,
    %(delay_time_us)s,
    %(integration_time_us)s,
    %(number_of_pulses)s,
    %(x_factor)s,
    %(laser_energy_v)s,
    %(laser_pump_current_a)s,
    %(prr_hz)s,
    %(on_off_status)s
)
ON CONFLICT (measurement_id) DO NOTHING;
"""

# ============================================================================
# MAIN
# ============================================================================
def process_measurement_clean():

    log("Starting measurement_clean ingestion", "START")

    if not os.path.exists(CSV_FOLDER):
        log("CSV folder not found", "ERROR")
        return

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
            log(f"{file} failed to read: {e}", "ERROR")
            continue

        # ============================================================================
        # NORMALIZE COLUMNS
        # ============================================================================
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        if "measurement_id" not in df.columns:
            log(f"{file} missing measurement_id column", "ERROR")
            continue

        # ensure numeric IDs
        df["measurement_id"] = pd.to_numeric(df["measurement_id"], errors="coerce")

        # ============================================================================
        # BUILD file_info_id FROM FILENAME
        # ============================================================================
        base_name = file.replace("_l1_cleaned.csv", "")
        parts = base_name.split("_")

        dt = parts[3]
        sub = parts[4]

        date = dt.split("T")[0]
        time = dt.split("T")[1]

        file_info_id = f"FI-{date}-{time}-{sub}"

        # ============================================================================
        # GROUP BY measurement_id (critical for L2)
        # ============================================================================
        grouped = df.groupby("measurement_id")

        rows_inserted = 0

        for local_id, group in grouped:

            if pd.isna(local_id):
                continue

            measurement_index = int(local_id)
            measurement_id = f"{file_info_id}-{measurement_index}"

            row = group.iloc[0]

            record = {
                "measurement_id": measurement_id,
                "file_info_id": file_info_id,
                "measurement_index": int(measurement_index),

                "time_utc": clean_value(pd.to_datetime(row.get("time_utc"), errors="coerce")),
                "measurement_count": clean_value(row.get("measurement_count")),
                "operation_mode": clean_value(row.get("operation_mode")),
                "measurement_type": clean_value(row.get("measurement_type")),
                "force_reset_status": clean_value(row.get("force_reset_status")),
                "laser_fire_status": clean_value(row.get("laser_fire_status")),
                "is_valid_plasma": clean_value(row.get("is_valid_plasma")),
                "is_background": clean_value(row.get("is_background")),
                "delay_time_us": clean_value(row.get("delay_time_us")),
                "integration_time_us": clean_value(row.get("integration_time_us")),
                "number_of_pulses": clean_value(row.get("number_of_pulses")),
                "x_factor": clean_value(row.get("x_factor")),
                "laser_energy_v": clean_value(row.get("laser_energy_v")),
                "laser_pump_current_a": clean_value(row.get("laser_pump_current_a")),
                "prr_hz": clean_value(row.get("prr_hz")),
                "on_off_status": clean_value(row.get("on_off_status")),
            }

            cursor.execute(INSERT_SQL, record)
            rows_inserted += 1

        total_inserted += rows_inserted
        log(f"{file} → {rows_inserted} measurements", "FILE")

    conn.commit()
    cursor.close()
    conn.close()

    log(f"Total inserted: {total_inserted}", "DONE")


# ============================================================================
# RUN
# ============================================================================
if __name__ == "__main__":
    process_measurement_clean()