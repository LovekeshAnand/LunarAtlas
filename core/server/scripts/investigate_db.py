import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def list_tables():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    try:
        # Get all tables
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        print("Tables:", [t['table_name'] for t in tables])
        
        # Get columns of measurement_clean
        if 'measurement_clean' in [t['table_name'] for t in tables]:
            cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'measurement_clean'")
            print("measurement_clean columns:", [c['column_name'] for c in cols])
            
        # Get columns of spectral_data_clean
        if 'spectral_data_clean' in [t['table_name'] for t in tables]:
            cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'spectral_data_clean'")
            print("spectral_data_clean columns:", [c['column_name'] for c in cols])
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(list_tables())
