import os
import time
import requests
import psycopg2
import redis
from dotenv import load_dotenv

# Load local .env file if present
load_dotenv()

# Fetch environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
HEALTH_CHECK_URL = os.getenv("HEALTH_CHECK_URL")


def ping_database():
    if not DATABASE_URL:
        print("[SKIP] DATABASE_URL is not set.")
        return False
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        print("[OK] Database ping succeeded.")
        return True
    except Exception as e:
        print(f"[FAIL] Database ping failed: {e}")
        return False

def ping_redis():
    if not REDIS_URL:
        print("[SKIP] REDIS_URL is not set.")
        return False
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        print("[OK] Redis ping succeeded.")
        return True
    except Exception as e:
        print(f"[FAIL] Redis ping failed: {e}")
        return False

def ping_health_endpoint():
    if not HEALTH_CHECK_URL:
        print("[SKIP] HEALTH_CHECK_URL is not set.")
        return False
    try:
        res = requests.get(HEALTH_CHECK_URL, timeout=10)
        print(f"[OK] Health check endpoint returned status code: {res.status_code}")
        return True
    except Exception as e:
        print(f"[FAIL] Health check endpoint failed: {e}")
        return False

if __name__ == "__main__":
    print(f"--- Keep Alive Ping Run at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    ping_database()
    ping_redis()
    ping_health_endpoint()
