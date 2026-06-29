from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os
import time

from app.config import settings
from app.database.connection import db
from app.cache.redis_cache import cache
from app.api.v1.endpoints import router as api_router
from app.api.v1.auth import router as auth_router
from app.api.v1.export import router as export_router
from app.api.v1.public.endpoints import router as public_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.usage import router as usage_router

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

# Middleware for tracking public API usage
@app.middleware("http")
async def log_api_usage_middleware(request: Request, call_next):
    # Only run for public endpoints
    if not request.url.path.startswith(f"{settings.API_V1_PREFIX}/public"):
        return await call_next(request)
        
    start_time = time.time()
    
    # Initialize request state key info
    request.state.api_key_info = None
    
    response = await call_next(request)
    
    process_time_ms = (time.time() - start_time) * 1000
    
    # Check if request has api key info set by dependency
    auth = getattr(request.state, "api_key_info", None)
    if auth:
        content_length = response.headers.get("content-length")
        response_bytes = int(content_length) if content_length else 0
        try:
            from app.api.v1.public.endpoints import log_api_usage
            await log_api_usage(
                request=request,
                auth=auth,
                status_code=response.status_code,
                response_bytes=response_bytes,
                response_time_ms=process_time_ms
            )
        except Exception as e:
            logger.warning(f"Error logging API usage in middleware: {e}")
            
    return response

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
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")


    
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
    logger.info("Services shut down cleanly")

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

# Include API Keys router
app.include_router(
    api_keys_router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["api-keys"]
)

# Include Usage router
app.include_router(
    usage_router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["usage"]
)

# Include Export router
app.include_router(
    export_router,
    prefix=f"{settings.API_V1_PREFIX}/export",
    tags=["export"]
)

# Include Public router
app.include_router(
    public_router,
    prefix=f"{settings.API_V1_PREFIX}/public",
    tags=["public-developer-api"]
)

from fastapi import Response, status

# Health endpoint at the root for ping monitors
@app.get("/health")
async def health_check_root(response: Response):
    """
    Root-level health check endpoint for Uptime/Ping monitoring.
    Returns HTTP 200 if database is reachable, HTTP 503 if database is degraded.
    """
    import time
    
    db_healthy = False
    db_latency = 0.0
    try:
        start_time = time.perf_counter()
        await db.fetch_one("SELECT 1")
        db_latency = (time.perf_counter() - start_time) * 1000.0
        db_healthy = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    redis_healthy = False
    try:
        if cache.redis:
            await cache.redis.ping()
            redis_healthy = True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        
    healthy = db_healthy
    
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return {
        "status": "healthy" if healthy else "degraded",
        "version": settings.APP_VERSION,
        "database": db_healthy,
        "db_latency_ms": round(db_latency, 2),
        "redis": redis_healthy,
        "timestamp": time.time()
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }

