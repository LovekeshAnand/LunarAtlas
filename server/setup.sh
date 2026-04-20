#!/bin/bash

# LunarAtlas Backend Setup Script
# version 1.0

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}           LunarAtlas Backend Automation Setup                     ${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Create Directory Structure
echo -e "${YELLOW}[1/4] Creating directory structure...${NC}"
mkdir -p app/api/v1 app/core app/models app/schemas app/database app/cache app/utils tests/unit tests/integration configs logs scripts data/uploads data/processed
touch app/__init__.py app/api/__init__.py app/api/v1/__init__.py app/core/__init__.py app/models/__init__.py app/schemas/__init__.py app/database/__init__.py app/cache/__init__.py app/utils/__init__.py tests/__init__.py
echo -e "${GREEN}✓ Directories created.${NC}"

# 2. Create requirements.txt
echo -e "${YELLOW}[2/4] Writing requirements.txt...${NC}"
cat <<EOF > requirements.txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6

# Database
asyncpg==0.29.0
psycopg2-binary==2.9.9
sqlalchemy==2.0.25

# Caching
redis==5.0.1
hiredis==2.3.2

# Data Processing
numpy==1.26.3
pandas==2.1.4
scipy==1.12.0

# Serialization
orjson==3.9.12
pydantic==2.5.3
pydantic-settings==2.1.0

# HTTP Client
httpx==0.26.0
aiohttp==3.9.1

# Utilities
python-dotenv==1.0.0
pyyaml==6.0.1

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0

# Development
black==24.1.1
flake8==7.0.0
mypy==1.8.0
EOF
echo -e "${GREEN}✓ requirements.txt written.${NC}"

# 3. Create .env.example
echo -e "${YELLOW}[3/4] Writing .env.example...${NC}"
cat <<EOF > .env.example
# Application
APP_NAME=LunarAtlas API
APP_VERSION=1.0.0
DEBUG=True

# Database (PostgreSQL)
DATABASE_URL=postgresql://lunaratlas_user:your_password@localhost:5432/LunarAtlas

# Database Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50
CACHE_TTL=3600

# API
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Performance
MAX_WORKERS=4
WORKER_CONNECTIONS=1000

# Downsampling Algorithm
BASE_BUCKETS=1000
MIN_BUCKET_SIZE=0.01
EOF
cp .env.example .env
echo -e "${GREEN}✓ .env.example created (copied to .env).${NC}"

# 4. Write Application Code
echo -e "${YELLOW}[4/4] Writing application code...${NC}"

# app/config.py
cat <<EOF > app/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "LunarAtlas API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    CACHE_TTL: int = 3600
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]
    MAX_WORKERS: int = 4
    WORKER_CONNECTIONS: int = 1000
    BASE_BUCKETS: int = 1000
    MIN_BUCKET_SIZE: float = 0.01
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
EOF

# app/database/connection.py
cat <<EOF > app/database/connection.py
import asyncpg
from typing import Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=5,
                max_size=settings.DB_POOL_SIZE,
                command_timeout=60,
                timeout=30
            )
            logger.info(f"✓ Database pool created")
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            raise
    
    async def disconnect(self):
        if self.pool:
            await self.pool.close()
    
    async def fetch_one(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetch_all(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

db = Database()
EOF

# app/cache/redis_cache.py
cat <<EOF > app/cache/redis_cache.py
import hashlib
import orjson
import redis.asyncio as redis
from typing import Optional, Any
from functools import wraps
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class CacheLayer:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding='utf-8',
                decode_responses=False,
                max_connections=settings.REDIS_MAX_CONNECTIONS
            )
            await self.redis.ping()
        except Exception as e:
            logger.error(f"✗ Redis connection failed: {e}")
            self.redis = None
    
    async def disconnect(self):
        if self.redis:
            await self.redis.close()
    
    def generate_key(self, *args, **kwargs) -> str:
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_str = ":".join(key_parts)
        return f"lunaratlas:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        if not self.redis: return None
        try:
            cached = await self.redis.get(key)
            return orjson.loads(cached) if cached else None
        except Exception: return None
    
    async def set(self, key: str, value: Any, ttl: int = None):
        if not self.redis: return False
        try:
            if ttl is None: ttl = settings.CACHE_TTL
            await self.redis.setex(key, ttl, orjson.dumps(value))
            return True
        except Exception: return False
    
    async def clear_pattern(self, pattern: str):
        if not self.redis: return False
        try:
            async for key in self.redis.scan_iter(match=f"lunaratlas:{pattern}*"):
                await self.redis.delete(key)
            return True
        except Exception: return False

cache = CacheLayer()
EOF

# app/core/downsampling.py
cat <<EOF > app/core/downsampling.py
import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DownsampleConfig:
    BASE_BUCKETS: int = 1000
    B_MIN: float = 0.01
    OVERLAP_PCT: float = 0.05

def calculate_bucket_size(delta_lambda: float, zoom_level: int, config=DownsampleConfig()) -> float:
    b_size = delta_lambda / (config.BASE_BUCKETS * (2 ** zoom_level))
    return max(b_size, config.B_MIN)

def calculate_zoom_max(delta_lambda: float, config=DownsampleConfig()) -> int:
    if delta_lambda <= 0: return 0
    return int(math.log2(delta_lambda / (config.BASE_BUCKETS * config.B_MIN)))

def adaptive_minmax_downsample(data: np.ndarray, zoom_level: int, lambda_min: float, lambda_max: float, config=DownsampleConfig()) -> Dict:
    if len(data) == 0: return {"mode": "empty", "data": []}
    delta_lambda = lambda_max - lambda_min
    if delta_lambda <= 0: return {"mode": "error", "data": []}
    
    b_final = calculate_bucket_size(delta_lambda, zoom_level, config)
    z_max = calculate_zoom_max(delta_lambda, config)
    
    if zoom_level > z_max:
        return {"mode": "raw", "data": data.tolist(), "original_points": len(data)}
    
    n_buckets = math.ceil(delta_lambda / b_final)
    buckets = []
    for j in range(n_buckets):
        l_start = lambda_min + (j * b_final)
        l_end = l_start + b_final
        l_s_ext = l_start - (config.OVERLAP_PCT * b_final) if j > 0 else l_start
        l_e_ext = l_end + (config.OVERLAP_PCT * b_final) if j < n_buckets-1 else l_end
        
        mask = (data[:, 0] >= l_s_ext) & (data[:, 0] < l_e_ext)
        b_data = data[mask]
        if len(b_data) == 0: continue
        
        min_i = np.argmin(b_data[:, 1])
        max_i = np.argmax(b_data[:, 1])
        buckets.append({
            "bucket_id": j,
            "lambda_min": float(b_data[min_i, 0]),
            "intensity_min": float(b_data[min_i, 1]),
            "lambda_max": float(b_data[max_i, 0]),
            "intensity_max": float(b_data[max_i, 1]),
            "n_points": len(b_data),
            "lambda_center": float((l_start + l_end)/2)
        })
    return {"mode": "downsampled", "data": buckets, "original_points": len(data)}
EOF

# app/schemas/spectral.py
cat <<EOF > app/schemas/spectral.py
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime

class SpectralDataPoint(BaseModel):
    wavelength_nm: float
    intensity: float

class DownsampledBucket(BaseModel):
    bucket_id: int
    lambda_min: float
    intensity_min: float
    lambda_max: float
    intensity_max: float
    n_points: int
    lambda_center: float

class SpectralResponse(BaseModel):
    mode: str
    measurement_id: int
    lambda_min: float
    lambda_max: float
    zoom_level: int
    z_max: Optional[int] = None
    data: Union[List[DownsampledBucket], List[SpectralDataPoint]]
    metadata: dict
    cached: bool = False
    query_time_ms: float

class MeasurementInfo(BaseModel):
    id: int
    measurement_id: int
    time_utc: datetime
    laser_energy_v: Optional[int]
    integration_time_us: Optional[int]
    num_pulses: Optional[int]
    operation_mode: Optional[str]

class HealthResponse(BaseModel):
    status: str
    version: str
    database: bool
    redis: bool
    timestamp: datetime
EOF

# app/api/v1/endpoints.py
cat <<EOF > app/api/v1/endpoints.py
from fastapi import APIRouter, HTTPException, Query
from typing import List
import numpy as np
import time
import logging
from datetime import datetime
from app.schemas.spectral import SpectralResponse, MeasurementInfo, HealthResponse
from app.core.downsampling import adaptive_minmax_downsample, DownsampleConfig
from app.database.connection import db
from app.cache.redis_cache import cache
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    db_h = False
    try: await db.fetch_one("SELECT 1"); db_h = True
    except: pass
    re_h = False
    try: 
        if cache.redis: await cache.redis.ping(); re_h = True
    except: pass
    return HealthResponse(status="healthy" if db_h and re_h else "degraded", version=settings.APP_VERSION, database=db_h, redis=re_h, timestamp=datetime.now())

@router.get("/measurements", response_model=List[MeasurementInfo])
async def list_measurements(limit: int = 10):
    query = "SELECT id, measurement_id, time_utc, laser_energy_v, integration_time_us, num_pulses, operation_mode FROM measurement ORDER BY time_utc DESC LIMIT \$1"
    try:
        rows = await db.fetch_all(query, limit)
        return [MeasurementInfo(**dict(row)) for row in rows]
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="DB Error")

@router.get("/spectrum", response_model=SpectralResponse)
async def get_spectrum(measurement_id: int, lambda_min: float = 200, lambda_max: float = 800, zoom_level: int = 0, use_cache: bool = True):
    cache_key = cache.generate_key("spectrum", measurement_id, lambda_min, lambda_max, zoom_level)
    if use_cache:
        cached = await cache.get(cache_key)
        if cached: return SpectralResponse(**{**cached, "cached": True})
    
    query = "SELECT wavelength_nm, cleaned_intensity FROM spectral_data WHERE measurement_id = \$1 AND wavelength_nm >= \$2 AND wavelength_nm <= \$3 ORDER BY wavelength_nm ASC"
    db_s = time.time()
    rows = await db.fetch_all(query, measurement_id, lambda_min, lambda_max)
    db_t = (time.time() - db_s) * 1000
    if not rows: return {"mode": "empty", "measurement_id": measurement_id, "lambda_min": lambda_min, "lambda_max": lambda_max, "zoom_level": zoom_level, "data": [], "metadata": {}, "query_time_ms": db_t}
    
    data = np.array([[float(r['wavelength_nm']), float(r['cleaned_intensity'])] for r in rows])
    ds_res = adaptive_minmax_downsample(data, zoom_level, lambda_min, lambda_max)
    res = {**ds_res, "measurement_id": measurement_id, "lambda_min": lambda_min, "lambda_max": lambda_max, "zoom_level": zoom_level, "metadata": {"original_points": len(data)}, "query_time_ms": db_t}
    if use_cache: await cache.set(cache_key, res)
    return res
EOF

# app/main.py
cat <<EOF > app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging, sys, os
from app.config import settings
from app.database.connection import db
from app.cache.redis_cache import cache
from app.api.v1.endpoints import router as api_router

logging.basicConfig(level=logging.INFO)
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup_event():
    if not os.path.exists('logs'): os.makedirs('logs')
    await db.connect()
    await cache.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await db.disconnect()
    await cache.disconnect()

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
async def root(): return {"status": "online"}
EOF

# configs/schema.sql
cat <<EOF > configs/schema.sql
CREATE TABLE IF NOT EXISTS mission (id SERIAL PRIMARY KEY, name VARCHAR(255) NOT NULL, agency VARCHAR(255), launch_date DATE, landing_date DATE, status VARCHAR(50), description TEXT, created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW());
CREATE TABLE IF NOT EXISTS instrument (id SERIAL PRIMARY KEY, mission_id INTEGER REFERENCES mission(id) ON DELETE CASCADE, name VARCHAR(255) NOT NULL, type VARCHAR(100), wavelength_range_min NUMERIC(8,2), wavelength_range_max NUMERIC(8,2), spectral_resolution NUMERIC(6,4), description TEXT, created_at TIMESTAMPTZ DEFAULT NOW());
CREATE TABLE IF NOT EXISTS observation (id SERIAL PRIMARY KEY, instrument_id INTEGER REFERENCES instrument(id) ON DELETE CASCADE, start_time TIMESTAMPTZ NOT NULL, stop_time TIMESTAMPTZ, target_name VARCHAR(255), site_latitude NUMERIC(10,6), site_longitude NUMERIC(10,6), operation_mode VARCHAR(100), created_at TIMESTAMPTZ DEFAULT NOW());
CREATE TABLE IF NOT EXISTS file_version (id SERIAL PRIMARY KEY, observation_id INTEGER REFERENCES observation(id) ON DELETE CASCADE, filename VARCHAR(512) NOT NULL, file_size_bytes BIGINT, md5_checksum VARCHAR(32) UNIQUE, algorithm_version VARCHAR(50), processing_level VARCHAR(20), ingested_at TIMESTAMPTZ DEFAULT NOW());
CREATE TABLE IF NOT EXISTS measurement (id SERIAL PRIMARY KEY, file_version_id INTEGER REFERENCES file_version(id) ON DELETE CASCADE, measurement_id INTEGER NOT NULL, time_utc TIMESTAMPTZ NOT NULL, laser_energy_v INTEGER, integration_time_us INTEGER, num_pulses INTEGER, operation_mode VARCHAR(50), is_background BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(file_version_id, measurement_id));
CREATE TABLE IF NOT EXISTS spectral_data (id BIGSERIAL, measurement_id INTEGER NOT NULL REFERENCES measurement(id) ON DELETE CASCADE, wavelength_nm NUMERIC(8,2) NOT NULL, cleaned_intensity NUMERIC(10,2), raw_intensity NUMERIC(10,2), is_background BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT NOW()) PARTITION BY RANGE (measurement_id);
CREATE TABLE IF NOT EXISTS spectral_data_p0 PARTITION OF spectral_data FOR VALUES FROM (0) TO (1000);
CREATE TABLE IF NOT EXISTS spectral_data_p1 PARTITION OF spectral_data FOR VALUES FROM (1000) TO (2000);
CREATE INDEX IF NOT EXISTS idx_wavelength_brin_p0 ON spectral_data_p0 USING BRIN (wavelength_nm);
EOF

# scripts/insert_test_data.py
cat <<EOF > scripts/insert_test_data.py
import asyncio, asyncpg, numpy as np, os from dotenv import load_dotenv
load_dotenv()
async def run():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    print("Inserting data...")
    m = await conn.fetch("SELECT id FROM measurement LIMIT 1")
    if not m: return print("Run schema first")
    wl = np.linspace(200, 800, 1000)
    it = 50 + np.random.normal(0, 5, 1000)
    recs = [(m[0]['id'], float(w), float(i), float(i)) for w, i in zip(wl, it)]
    await conn.copy_records_to_table('spectral_data', records=recs, columns=['measurement_id', 'wavelength_nm', 'cleaned_intensity', 'raw_intensity'])
    await conn.close()
    print("Done")
if __name__ == "__main__": asyncio.run(run())
EOF

echo -e "${GREEN}✓ All files written successfully.${NC}"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "Next steps:"
echo -e "1. ${YELLOW}python3 -m venv venv${NC}"
echo -e "2. ${YELLOW}source venv/bin/activate${NC}"
echo -e "3. ${YELLOW}pip install -r requirements.txt${NC}"
echo -e "4. Update ${YELLOW}.env${NC} with your credentials"
echo -e "5. Start server: ${YELLOW}uvicorn app.main:app --host 0.0.0.0 --port 8000${NC}"
echo -e "${BLUE}======================================================================${NC}"
