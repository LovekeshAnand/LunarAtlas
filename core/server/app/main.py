from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

from app.config import settings
from app.database.connection import db
from app.cache.redis_cache import cache
from app.api.v1.endpoints import router as api_router
from app.api.v1.auth import router as auth_router
from app.api.v1.export import router as export_router

os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/api.log')
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LunarAtlas Backend API - Spectral Data Processing",
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    
    # Connect to database
    try:
        await db.connect()
        # Initialize users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                institution VARCHAR(255),
                interest VARCHAR(255),
                hashed_password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("[OK] Assured app_users table exists")
    except Exception as e:
        logger.error(f"Failed to connect to database or init table: {e}")
        # sys.exit(1) # We might want to keep it running for testing

    
    # Connect to Redis
    try:
        await cache.connect()
    except Exception as e:
        logger.warning(f"Redis connection failed, caching disabled: {e}")
    
    logger.info("[OK] All services initialized")
    logger.info(f"API available at: http://localhost:8000{settings.API_V1_PREFIX}")
    logger.info("=" * 60)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down...")
    await db.disconnect()
    await cache.disconnect()
    logger.info("✓ Services shut down cleanly")

# Include API router
app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX,
    tags=["spectral-data"]
)

# Include Auth router
app.include_router(
    auth_router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["auth"]
)

# Include Export router
app.include_router(
    export_router,
    prefix=f"{settings.API_V1_PREFIX}/export",
    tags=["export"]
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }
