import time
from fastapi import Request, HTTPException, status
from app.cache.redis_cache import cache

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute

    async def __call__(self, request: Request):
        # Fallback if Redis is not active
        if not cache.redis:
            return

        # Identify client (API key, user ID, or IP address as fallback)
        client_identifier = None
        
        # Check if auth/api key info is set in request state
        api_key_info = getattr(request.state, "api_key_info", None)
        if api_key_info:
            client_identifier = f"key:{api_key_info.get('key_prefix')}"
        else:
            user = getattr(request.state, "user", None)
            if user and hasattr(user, "id"):
                client_identifier = f"user:{user.id}"
            else:
                # Fallback to client IP
                client_identifier = f"ip:{request.client.host if request.client else 'unknown'}"
                
        endpoint = request.url.path
        redis_key = f"rate_limit:{client_identifier}:{endpoint}"
        
        now = time.time()
        window_start = now - 60
        
        try:
            # 1. Clean up old requests
            await cache.redis.zremrangebyscore(redis_key, 0, window_start)
            
            # 2. Count requests in current window
            request_count = await cache.redis.zcard(redis_key)
            
            # Save remaining requests to request state for endpoints to access
            remaining = max(0, self.requests_per_minute - request_count - 1)
            request.state.rate_limit_remaining = remaining
            
            if request_count >= self.requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later."
                )
                
            # 3. Log current request
            await cache.redis.zadd(redis_key, {str(now): now})
            # 4. Expire key after window length
            await cache.redis.expire(redis_key, 60)
            
        except HTTPException:
            raise
        except Exception as e:
            # Gracefully allow request if Redis fails during rate limiting
            request.state.rate_limit_remaining = self.requests_per_minute
            import logging
            logging.getLogger(__name__).warning(f"Rate limiting failure: {e}")
