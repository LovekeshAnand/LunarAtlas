import asyncpg
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool with production-grade pooling settings"""
        try:
            self.pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=5,
                max_size=settings.DB_POOL_SIZE,
                max_inactive_connection_lifetime=1800,  # pool_recycle equivalent
                command_timeout=60,
                timeout=30
            )
            # Verify connection
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            logger.info(f"[OK] Database pool created (pool_size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW}, pool_recycle=1800s)")
        except Exception as e:
            logger.error(f"[FAIL] Database connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("[OK] Database pool closed")
    
    async def fetch_one(self, query: str, *args):
        """Execute query and fetch one row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetch_all(self, query: str, *args):
        """Execute query and fetch all rows"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute(self, query: str, *args):
        """Execute query without returning rows"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

# Global database instance
db = Database()
