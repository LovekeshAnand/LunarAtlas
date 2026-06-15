import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_vals():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    try:
        # Check first 5 rows of clean
        clean_rows = await conn.fetch("SELECT * FROM spectral_data_clean LIMIT 5")
        print("Clean data:", [dict(r) for r in clean_rows])
        
        # Check first 5 rows of calibrated
        cal_rows = await conn.fetch("SELECT * FROM spectral_data_calibrated LIMIT 5")
        print("Calibrated data:", [dict(r) for r in cal_rows])
        
        # Check if they have the same measurement_id
        if clean_rows:
            m_id = clean_rows[0]['measurement_id']
            # Fetch joined
            joined = await conn.fetch("""
                SELECT c.wavelength_nm, c.intensity, cal.response_count 
                FROM spectral_data_clean c 
                JOIN spectral_data_calibrated cal 
                  ON c.measurement_id = cal.measurement_id 
                  AND c.wavelength_nm = cal.wavelength_nm
                WHERE c.measurement_id = $1 
                LIMIT 5
            """, m_id)
            print("Joined values for", m_id)
            for r in joined:
                print(f"  wl={r['wavelength_nm']:.2f}: cleaned={r['intensity']} | raw={r['response_count']}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_vals())
