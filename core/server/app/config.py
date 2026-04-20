from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LunarAtlas API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50
    CACHE_TTL: int = 3600  # 1 hour
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]
    
    # Performance
    MAX_WORKERS: int = 4
    WORKER_CONNECTIONS: int = 1000
    
    # Downsampling (calibrated for CH3 LIBS: ~2094 channels per measurement)
    BASE_BUCKETS: int = 200
    MIN_BUCKET_SIZE: float = 0.01  # nm
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
