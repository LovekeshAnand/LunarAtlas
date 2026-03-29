"""
Database setup script for LunarAtlas
Creates tables and loads sample LIBS data
"""

import psycopg2
import pandas as pd
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": "postgres",  # Connect to default first
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "lovekesh"),
    "port": os.getenv("DB_PORT", "5432")
}

def create_database():
    """Create the lunaratlas database"""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        # Drop if exists (for clean setup)
        cursor.execute("DROP DATABASE IF EXISTS lunaratlas")
        cursor.execute("CREATE DATABASE lunaratlas")
        print("✓ Database 'lunaratlas' created")
    except Exception as e:
        print(f"Error creating database: {e}")
    finally:
        cursor.close()
        conn.close()


def create_tables():
    """Create spectral_data table"""
    config = DB_CONFIG.copy()
    config['database'] = 'lunaratlas'
    
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()
    
    try:
        # Drop table if exists
        cursor.execute("DROP TABLE IF EXISTS spectral_data CASCADE")
        
        # Create spectral_data table
        cursor.execute("""
            CREATE TABLE spectral_data (
                id SERIAL PRIMARY KEY,
                measurement_id INTEGER NOT NULL,
                time_utc TIMESTAMP,
                measurement_count INTEGER,
                wavelength_nm DECIMAL(10, 4) NOT NULL,
                cleaned_intensity DECIMAL(12, 2) NOT NULL,
                operation_mode VARCHAR(50),
                measurement_type VARCHAR(50),
                force_reset_status INTEGER,
                laser_fire_status INTEGER,
                is_valid_plasma BOOLEAN,
                is_background BOOLEAN,
                delay_time_us DECIMAL(10, 6),
                integration_time_us INTEGER,
                number_of_pulses INTEGER,
                x_factor INTEGER,
                laser_energy_v INTEGER,
                laser_pump_current_a INTEGER,
                prr_hz INTEGER,
                on_off_status INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX idx_measurement_id ON spectral_data(measurement_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_wavelength ON spectral_data(wavelength_nm)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_measurement_wavelength 
            ON spectral_data(measurement_id, wavelength_nm)
        """)
        
        # Create BRIN index for large datasets
        cursor.execute("""
            CREATE INDEX idx_wavelength_brin 
            ON spectral_data USING BRIN(wavelength_nm)
        """)
        
        conn.commit()
        print("✓ Table 'spectral_data' created with indexes")
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating tables: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def load_sample_data(csv_path: str):
    """Load sample CSV data into database"""
    config = DB_CONFIG.copy()
    config['database'] = 'lunaratlas'
    
    print(f"Loading data from {csv_path}...")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    print(f"✓ Loaded {len(df)} rows from CSV")
    
    # Rename columns to match database
    column_mapping = {
        'Measurement_ID': 'measurement_id',
        'Time_UTC': 'time_utc',
        'Measurement_Count': 'measurement_count',
        'Wavelength_nm': 'wavelength_nm',
        'Cleaned_Intensity': 'cleaned_intensity',
        'Operation_Mode': 'operation_mode',
        'Measurement_Type': 'measurement_type',
        'Force_Reset_Status': 'force_reset_status',
        'Laser_Fire_Status': 'laser_fire_status',
        'Is_Valid_Plasma': 'is_valid_plasma',
        'Is_Background': 'is_background',
        'Delay_Time_us': 'delay_time_us',
        'Integration_Time_us': 'integration_time_us',
        'Number_of_Pulses': 'number_of_pulses',
        'X_Factor': 'x_factor',
        'Laser_Energy_V': 'laser_energy_v',
        'Laser_Pump_Current_A': 'laser_pump_current_a',
        'PRR_Hz': 'prr_hz',
        'On_Off_Status': 'on_off_status'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Connect and insert
    conn = psycopg2.connect(**config)
    cursor = conn.cursor()
    
    try:
        # Prepare insert query
        columns = list(column_mapping.values())
        placeholders = ','.join(['%s'] * len(columns))
        insert_query = f"""
            INSERT INTO spectral_data ({','.join(columns)})
            VALUES ({placeholders})
        """
        
        # Insert in batches
        batch_size = 1000
        total_inserted = 0
        
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            values = [tuple(row) for row in batch[columns].values]
            cursor.executemany(insert_query, values)
            total_inserted += len(values)
            
            if total_inserted % 5000 == 0:
                print(f"  Inserted {total_inserted} rows...")
        
        conn.commit()
        print(f"✓ Successfully inserted {total_inserted} rows into database")
        
        # Verify data
        cursor.execute("""
            SELECT 
                measurement_id,
                COUNT(*) as point_count,
                MIN(wavelength_nm) as min_wl,
                MAX(wavelength_nm) as max_wl
            FROM spectral_data
            GROUP BY measurement_id
        """)
        
        results = cursor.fetchall()
        print("\n✓ Data verification:")
        for row in results:
            print(f"  Measurement {row[0]}: {row[1]} points, "
                  f"wavelength range: {row[2]:.2f} - {row[3]:.2f} nm")
    
    except Exception as e:
        conn.rollback()
        print(f"Error loading data: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    """Main setup function"""
    print("=== LunarAtlas Database Setup ===\n")
    
    # Step 1: Create database
    print("Step 1: Creating database...")
    create_database()
    print()
    
    # Step 2: Create tables
    print("Step 2: Creating tables...")
    create_tables()
    print()
    
    # Step 3: Load sample data
    print("Step 3: Loading sample data...")
    csv_path = "/mnt/user-data/uploads/ch3_lib_002_20230825T104221_00_l1_cleaned.csv"
    
    if os.path.exists(csv_path):
        load_sample_data(csv_path)
    else:
        print(f"Warning: Sample data file not found at {csv_path}")
        print("You can load data later using load_sample_data() function")
    
    print("\n=== Setup Complete ===")
    print("\nDatabase: lunaratlas")
    print("Table: spectral_data")
    print("\nYou can now start the API server with:")
    print("  python main.py")


if __name__ == "__main__":
    main()
