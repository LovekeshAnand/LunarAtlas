import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.database.connection import db
from app.config import settings

# NIST Atomic Spectra Database - Standard LIBS Lines (Wavelengths in nm)
# Data source: NIST ASD (https://physics.nist.gov/PhysRefData/ASD/lines_form.html)
NIST_DATA = [
    # Iron (Fe I / Fe II)
    {"element": "Fe", "ionization": "I", "wavelength": 248.327, "rel_int": 1000},
    {"element": "Fe", "ionization": "I", "wavelength": 274.918, "rel_int": 800},
    {"element": "Fe", "ionization": "I", "wavelength": 373.486, "rel_int": 900},
    {"element": "Fe", "ionization": "I", "wavelength": 404.581, "rel_int": 700},
    {"element": "Fe", "ionization": "II", "wavelength": 238.204, "rel_int": 850},
    {"element": "Fe", "ionization": "II", "wavelength": 259.940, "rel_int": 750},
    
    # Magnesium (Mg I / Mg II)
    {"element": "Mg", "ionization": "I", "wavelength": 285.213, "rel_int": 1000},
    {"element": "Mg", "ionization": "I", "wavelength": 383.829, "rel_int": 600},
    {"element": "Mg", "ionization": "I", "wavelength": 517.268, "rel_int": 800},
    {"element": "Mg", "ionization": "I", "wavelength": 518.360, "rel_int": 900},
    {"element": "Mg", "ionization": "II", "wavelength": 279.553, "rel_int": 1000},
    {"element": "Mg", "ionization": "II", "wavelength": 280.270, "rel_int": 950},
    
    # Silicon (Si I)
    {"element": "Si", "ionization": "I", "wavelength": 251.611, "rel_int": 1000},
    {"element": "Si", "ionization": "I", "wavelength": 288.158, "rel_int": 900},
    {"element": "Si", "ionization": "I", "wavelength": 390.552, "rel_int": 500},
    
    # Aluminum (Al I)
    {"element": "Al", "ionization": "I", "wavelength": 308.215, "rel_int": 900},
    {"element": "Al", "ionization": "I", "wavelength": 309.271, "rel_int": 1000},
    {"element": "Al", "ionization": "I", "wavelength": 394.401, "rel_int": 850},
    {"element": "Al", "ionization": "I", "wavelength": 396.152, "rel_int": 950},
    
    # Calcium (Ca I / Ca II)
    {"element": "Ca", "ionization": "I", "wavelength": 422.673, "rel_int": 1000},
    {"element": "Ca", "ionization": "I", "wavelength": 443.568, "rel_int": 400},
    {"element": "Ca", "ionization": "II", "wavelength": 393.366, "rel_int": 1000},
    {"element": "Ca", "ionization": "II", "wavelength": 396.847, "rel_int": 900},
    
    # Titanium (Ti I / Ti II)
    {"element": "Ti", "ionization": "I", "wavelength": 334.904, "rel_int": 800},
    {"element": "Ti", "ionization": "I", "wavelength": 336.121, "rel_int": 700},
    {"element": "Ti", "ionization": "II", "wavelength": 334.941, "rel_int": 900},
    
    # Sodium (Na I)
    {"element": "Na", "ionization": "I", "wavelength": 588.995, "rel_int": 1000},
    {"element": "Na", "ionization": "I", "wavelength": 589.592, "rel_int": 900},

    # Hydrogen (H I)
    {"element": "H", "ionization": "I", "wavelength": 656.273, "rel_int": 1000}, # Balmer Alpha
    {"element": "H", "ionization": "I", "wavelength": 486.133, "rel_int": 500},  # Balmer Beta
    
    # Oxygen (O I)
    {"element": "O", "ionization": "I", "wavelength": 777.194, "rel_int": 900},
    {"element": "O", "ionization": "I", "wavelength": 777.417, "rel_int": 800},
    {"element": "O", "ionization": "I", "wavelength": 777.539, "rel_int": 700},
]

async def seed():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    await db.connect()
    
    try:
        # Clear existing lines
        await db.execute("DELETE FROM nist_lines")
        print("Cleared existing NIST data.")
        
        # Insert new lines
        query = """
            INSERT INTO nist_lines 
            (element, ionization_stage, wavelength_nm, relative_intensity)
            VALUES ($1, $2, $3, $4)
        """
        
        for entry in NIST_DATA:
            await db.execute(
                query, 
                entry["element"], 
                entry["ionization"], 
                entry["wavelength"], 
                entry["rel_int"]
            )
        
        print(f"Successfully seeded {len(NIST_DATA)} NIST emission lines.")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(seed())
