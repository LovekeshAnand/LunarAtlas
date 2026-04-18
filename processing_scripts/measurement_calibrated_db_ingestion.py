import os
import pandas as pd
import psycopg2

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
# PATH
# ============================================================================
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

# ============================================================================
# SQL
# ============================================================================
INSERT_SQL = """
INSERT INTO measurement_calibrated (
    measurement_id,
    file_info_id,
    measurement_index,
    time_utc,
    measurement_count,
    operation_mode,
    measurement_type,
    force_reset_status,
    laser_fire_status,
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
# MAIN FUNCTION
# ============================================================================
def process_measurements():
    print("\n[START] Processing measurements...\n")

    if not os.path.exists(CSV_FOLDER):
        print(f"[ERROR] Folder not found: {CSV_FOLDER}")
        return

    files = [f for f in os.listdir(CSV_FOLDER) if f.endswith(".csv")]
    print(f"[INFO] Found {len(files)} CSV files\n")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    total_inserted = 0

    for file in files:
        file_path = os.path.join(CSV_FOLDER, file)
        base_name = file.replace(".csv", "")
        file_info_id = generate_file_info_id(base_name)

        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"[ERROR] Failed to read {file}: {e}")
            continue

        # Clean + rename columns
        df.columns = df.columns.str.strip()

        df = df.rename(columns={
            "Time": "time_utc",
            "Measurement Count": "measurement_count",
            "Operation Mode": "operation_mode",
            "Measurement Type": "measurement_type",
            "Force Reset Status": "force_reset_status",
            "Laser Fire Status": "laser_fire_status",
            "Delay Time": "delay_time_us",
            "Integration Time": "integration_time_us",
            "Number of Pulses": "number_of_pulses",
            "X Factor": "x_factor",
            "Laser Energy": "laser_energy_v",
            "Laser Pump Current": "laser_pump_current_a",
            "PRR": "prr_hz",
            "On Off Status": "on_off_status",
        })

        if "time_utc" in df.columns:
            df["time_utc"] = pd.to_datetime(df["time_utc"], errors="coerce")

        rows_inserted = 0

        for idx, row in df.iterrows():
            measurement_index = idx + 1

            record = {
                "measurement_id": f"{file_info_id}-{measurement_index}",
                "file_info_id": file_info_id,
                "measurement_index": measurement_index,
                "time_utc": row.get("time_utc"),
                "measurement_count": row.get("measurement_count"),
                "operation_mode": row.get("operation_mode"),
                "measurement_type": row.get("measurement_type"),
                "force_reset_status": row.get("force_reset_status"),
                "laser_fire_status": row.get("laser_fire_status"),
                "delay_time_us": row.get("delay_time_us"),
                "integration_time_us": row.get("integration_time_us"),
                "number_of_pulses": row.get("number_of_pulses"),
                "x_factor": row.get("x_factor"),
                "laser_energy_v": row.get("laser_energy_v"),
                "laser_pump_current_a": row.get("laser_pump_current_a"),
                "prr_hz": row.get("prr_hz"),
                "on_off_status": row.get("on_off_status"),
            }

            cursor.execute(INSERT_SQL, record)
            rows_inserted += 1

        total_inserted += rows_inserted
        print(f"[FILE] {file} → {rows_inserted} rows inserted")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n[DONE] Total inserted: {total_inserted}\n")
if __name__ == "__main__":
    process_measurements()