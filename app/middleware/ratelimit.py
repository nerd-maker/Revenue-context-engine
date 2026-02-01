"""
Rate Limiting Middleware

Implements Redis-based distributed rate limiting with:
- 100 requests per 60 seconds per client (configurable)
- Client identification by IP address + tenant ID
- Rate limit headers in responses
- Health endpoint exemption
- Graceful Redis failure handling
"""
import aioredis
try:
    from fastapi import Request, HTTPException
except ImportError:
    Request = HTTPException = None
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
import time
import logging

logger = logging.getLogger("ratelimit")

# Rate limit configuration
DEFAULT_RATE_LIMIT = 100  # requests
DEFAULT_WINDOW_SECONDS = 60  # seconds
HEALTH_ENDPOINTS = ['/health', '/metrics', '/ready', '/live']


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based distributed rate limiting middleware.
    
    Limits requests per client (identified by IP + tenant ID) to prevent abuse.
    Includes rate limit headers in responses and gracefully handles Redis failures.
    """
    
    def __init__(self, app, redis_client=None, rate_limit=DEFAULT_RATE_LIMIT, window_seconds=DEFAULT_WINDOW_SECONDS):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            redis_client: Redis client instance (optional, will create if not provided)
            rate_limit: Maximum requests per window (default: 100)
            window_seconds: Time window in seconds (default: 60)
        """
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self._redis_available = True
    
    async def _get_redis(self):
        """Get or create Redis connection."""
        if self.redis_client:
            return self.redis_client.redis if hasattr(self.redis_client, 'redis') else self.redis_client
        
        # Fallback: create Redis connection if not provided
        try:
            if not hasattr(self, '_redis'):
                self._redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
            return self._redis
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis_available = False
            return None
    
    async def dispatch(self, request: Request, call_next):
        """
        Apply rate limiting to request.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain
            
        Returns:
            Response with rate limit headers or 429 if limit exceeded
        """
        # Skip rate limiting for health endpoints
        if request.url.path in HEALTH_ENDPOINTS:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        tenant_id = getattr(request.state, 'tenant_id', 'anonymous')
        client_id = f"{client_ip}:{tenant_id}"
        
        # Try to apply rate limiting
        try:
            redis = await self._get_redis()
            
            if not redis or not self._redis_available:
                # Redis unavailable - allow request but log warning
                logger.warning(f"Redis unavailable, skipping rate limit for {client_id}")
                return await call_next(request)
            
            # Rate limiting key
            current_window = int(time.time() / self.window_seconds)
            rate_key = f"ratelimit:{client_id}:{current_window}"
            
            # Increment counter
            count = await redis.incr(rate_key)
            
            # Set expiry on first request in window
            if count == 1:
                await redis.expire(rate_key, self.window_seconds)
            
            # Calculate remaining requests
            remaining = max(0, self.rate_limit - count)
            reset_time = (current_window + 1) * self.window_seconds
            
            # Check if limit exceeded
            if count > self.rate_limit:
                logger.warning(
                    f"Rate limit exceeded for {client_id}: {count}/{self.rate_limit} "
                    f"requests in {self.window_seconds}s window"
                )
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Maximum {self.rate_limit} requests per {self.window_seconds} seconds. "
                           f"Try again in {reset_time - int(time.time())} seconds.",
                    headers={
                        'X-RateLimit-Limit': str(self.rate_limit),
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(reset_time),
                        'Retry-After': str(reset_time - int(time.time()))
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            response.headers['X-RateLimit-Limit'] = str(self.rate_limit)
            response.headers['X-RateLimit-Remaining'] = str(remaining)
            response.headers['X-RateLimit-Reset'] = str(reset_time)
            
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions (rate limit exceeded)
            raise
        except Exception as e:
            # Log error but allow request through (graceful degradation)
            logger.error(f"Rate limiting error for {client_id}: {e}")
            self._redis_available = False
            return await call_next(request)
