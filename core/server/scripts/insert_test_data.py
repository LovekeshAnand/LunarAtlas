import asyncio
import asyncpg
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def insert_test_data():
    """Insert synthetic spectral data for testing"""
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Inserting test spectral data...")
        
        # Get measurement IDs
        measurements = await conn.fetch("SELECT id, measurement_id FROM measurement LIMIT 2")
        
        if not measurements:
            print("No measurements found. Please run schema.sql first.")
            return

        for meas in measurements:
            meas_id = meas['id']
            meas_num = meas['measurement_id']
            
            print(f"\nGenerating spectrum for measurement {meas_num} (DB ID: {meas_id})")
            
            # Generate synthetic spectrum (200-800 nm, 2049 points)
            wavelengths = np.linspace(200.0, 800.0, 2049)
            
            # Baseline with noise
            baseline = 50 + np.random.normal(0, 5, 2049)
            intensities = baseline.copy()
            
            # Add 10 Gaussian peaks (emission lines)
            for i in range(10):
                peak_lambda = np.random.uniform(200, 800)
                peak_intensity = np.random.uniform(200, 600)
                peak_width = np.random.uniform(0.5, 2.0)
                
                peak = peak_intensity * np.exp(
                    -((wavelengths - peak_lambda) ** 2) / (2 * peak_width ** 2)
                )
                intensities += peak
            
            # Insert data points
            print(f"Inserting {len(wavelengths)} data points...")
            
            # Use copy_records_to_table for faster insertion
            records = [
                (meas_id, float(wl), float(intensity), float(intensity))
                for wl, intensity in zip(wavelengths, intensities)
            ]
            
            await conn.copy_records_to_table(
                'spectral_data',
                records=records,
                columns=['measurement_id', 'wavelength_nm', 'cleaned_intensity', 'raw_intensity']
            )
            
            print(f"✓ Inserted data for measurement {meas_num}")
        
        print("\n✓ All test data inserted successfully")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(insert_test_data())
