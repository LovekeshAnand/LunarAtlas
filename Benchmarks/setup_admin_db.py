"""
Setup Admin User Database Table and Seed User
Author: LunarAtlas Research Team

Connects to the database and creates the `admin_users` table if it does not exist,
then seeds a default administrator account.

Usage:
  python setup_admin_db.py
"""

import sys
import os

# Add core/server to path to reuse app modules
sys.path.insert(0, 'd:/LunarAtlas-Admin/server')

# Load production env URL
os.environ['DATABASE_URL'] = 'postgresql://postgres.ljlgxaigoiqedgmkaukw:LUNARatlas%40%24%25@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres'
os.environ['REDIS_URL'] = 'rediss://red-d90hu6ho3t8c73c9a79g:nyWu9CpspTUxN7H7YIRKMcnizcu689m6@oregon-keyvalue.render.com:6379'

import psycopg2
from app.security import get_password_hash

def setup_db():
    db_url = os.environ['DATABASE_URL']
    print("[INFO] Connecting to Supabase database...")
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # 1. Create Table
        print("[INFO] Creating admin_users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        
        # Seed/update administrator accounts
        admins_to_seed = [
            ("admin@lunaratlas.in", "admin"),
            ("lovekeshanand@admin.lunaratlas.in", "LOVEkesh89@#$"),
            ("duasaeed@admin.lunaratlas.in", "DUAsaeed09@#$")
        ]
        
        print("[INFO] Seeding/updating administrator accounts...")
        for email, raw_password in admins_to_seed:
            hashed_pwd = get_password_hash(raw_password)
            cursor.execute("""
                INSERT INTO admin_users (email, hashed_password) 
                VALUES (%s, %s)
                ON CONFLICT (email) 
                DO UPDATE SET hashed_password = EXCLUDED.hashed_password
            """, (email, hashed_pwd))
        conn.commit()
        print("[SUCCESS] Seeding completed for admins:")
        for email, _ in admins_to_seed:
            print(f"  - {email}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[FAIL] Error setting up database: {e}")

if __name__ == "__main__":
    setup_db()
