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
        """Initialize Redis connection pool"""
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding='utf-8',
                decode_responses=False,  # We handle decoding with orjson
                max_connections=settings.REDIS_MAX_CONNECTIONS
            )
            # Test connection
            await self.redis.ping()
            logger.info(f"✓ Redis pool created ({settings.REDIS_MAX_CONNECTIONS} connections)")
        except Exception as e:
            logger.error(f"✗ Redis connection failed: {e}")
            logger.warning("Cache will be disabled")
            self.redis = None
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("✓ Redis pool closed")
    
    def generate_key(self, *args, **kwargs) -> str:
        """Generate deterministic cache key from arguments"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
        key_str = ":".join(key_parts)
        return f"lunaratlas:{hashlib.md5(key_str.encode()).hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache"""
        if not self.redis:
            return None
        
        try:
            cached = await self.redis.get(key)
            if cached:
                logger.debug(f"Cache HIT: {key[:32]}...")
                return orjson.loads(cached)
            logger.debug(f"Cache MISS: {key[:32]}...")
            return None
        except Exception as e:
            logger.error(f"Cache GET error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None):
        """Store value in cache with optional TTL"""
        if not self.redis:
            return False
        
        try:
            if ttl is None:
                ttl = settings.CACHE_TTL
            
            serialized = orjson.dumps(value)
            await self.redis.setex(key, ttl, serialized)
            logger.debug(f"Cache SET: {key[:32]}... (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache SET error: {e}")
            return False
    
    async def delete(self, key: str):
        """Delete value from cache"""
        if not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            logger.debug(f"Cache DELETE: {key[:32]}...")
            return True
        except Exception as e:
            logger.error(f"Cache DELETE error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.redis:
            return False
        
        try:
            async for key in self.redis.scan_iter(match=f"lunaratlas:{pattern}*"):
                await self.redis.delete(key)
            logger.info(f"Cache CLEARED: pattern={pattern}")
            return True
        except Exception as e:
            logger.error(f"Cache CLEAR error: {e}")
            return False

# Global cache instance
cache = CacheLayer()

# Decorator for caching function results
def cached(ttl: int = None, key_prefix: str = ""):
    """Decorator to cache function results in Redis"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache.generate_key(
                key_prefix,
                func.__name__,
                *args,
                **{k: v for k, v in kwargs.items() if k != 'cache_instance'}
            )
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
