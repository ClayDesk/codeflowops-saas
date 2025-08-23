"""
Rate limiting middleware for CodeFlowOps
Protects against abuse and ensures fair usage
"""

from fastapi import HTTPException, status, Request
from typing import Dict, Any, Optional
import time
import asyncio
import redis.asyncio as redis
import json
import logging
from datetime import datetime, timedelta
import hashlib

from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimiter:
    """
    Rate limiting implementation with Redis backend
    Supports multiple rate limiting strategies
    """
    
    def __init__(self):
        self.redis_client = None
        self.memory_store = {}  # Fallback for when Redis is unavailable
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    async def initialize(self):
        """Initialize Redis connection for rate limiting"""
        try:
            if settings.REDIS_URL:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=settings.REDIS_MAX_CONNECTIONS
                )
                await self.redis_client.ping()
                logger.info("Redis connection established for rate limiting")
            else:
                logger.warning("Redis not configured, using in-memory rate limiting")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for rate limiting: {str(e)}")
            self.redis_client = None
    
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        burst_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Check if request is within rate limits
        
        Uses token bucket algorithm with sliding window
        """
        try:
            now = time.time()
            
            if self.redis_client:
                return await self._redis_rate_limit(
                    identifier, limit, window_seconds, burst_limit, now
                )
            else:
                return await self._memory_rate_limit(
                    identifier, limit, window_seconds, burst_limit, now
                )
                
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # Fail open - allow request if rate limiting fails
            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit,
                "reset_time": now + window_seconds,
                "retry_after": None
            }
    
    async def _redis_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        burst_limit: Optional[int],
        now: float
    ) -> Dict[str, Any]:
        """Redis-based rate limiting using sliding window"""
        key = f"rate_limit:{identifier}"
        window_key = f"rate_limit_window:{identifier}"
        
        # Use Lua script for atomic operations
        lua_script = """
            local key = KEYS[1]
            local window_key = KEYS[2]
            local now = tonumber(ARGV[1])
            local limit = tonumber(ARGV[2])
            local window = tonumber(ARGV[3])
            local burst_limit = tonumber(ARGV[4]) or limit
            
            -- Clean old entries
            redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
            
            -- Count current requests
            local current = redis.call('ZCARD', key)
            
            -- Check burst limit first
            if current >= burst_limit then
                local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                if #oldest > 0 then
                    local retry_after = math.ceil(oldest[2] + window - now)
                    return {0, current, limit, now + window, retry_after}
                end
            end
            
            -- Check regular limit
            if current >= limit then
                local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                if #oldest > 0 then
                    local retry_after = math.ceil(oldest[2] + window - now)
                    return {0, current, limit, now + window, retry_after}
                end
            end
            
            -- Add current request
            redis.call('ZADD', key, now, now .. ':' .. math.random())
            redis.call('EXPIRE', key, window + 1)
            
            return {1, current + 1, limit, now + window, 0}
        """
        
        result = await self.redis_client.eval(
            lua_script, 
            2, 
            key, window_key,
            now, limit, window_seconds, burst_limit or limit
        )
        
        allowed, current, limit_val, reset_time, retry_after = result
        
        return {
            "allowed": bool(allowed),
            "limit": limit_val,
            "remaining": max(0, limit_val - current),
            "reset_time": reset_time,
            "retry_after": retry_after if retry_after > 0 else None
        }
    
    async def _memory_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        burst_limit: Optional[int],
        now: float
    ) -> Dict[str, Any]:
        """Memory-based rate limiting (fallback)"""
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            await self._cleanup_memory_store(now)
            self.last_cleanup = now
        
        if identifier not in self.memory_store:
            self.memory_store[identifier] = []
        
        requests = self.memory_store[identifier]
        
        # Remove old requests outside the window
        cutoff = now - window_seconds
        requests[:] = [req_time for req_time in requests if req_time > cutoff]
        
        # Check limits
        current_count = len(requests)
        effective_limit = burst_limit or limit
        
        if current_count >= effective_limit:
            # Find when the oldest request will expire
            if requests:
                oldest_request = min(requests)
                retry_after = max(1, int(oldest_request + window_seconds - now))
            else:
                retry_after = window_seconds
            
            return {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "reset_time": now + window_seconds,
                "retry_after": retry_after
            }
        
        # Add current request
        requests.append(now)
        
        return {
            "allowed": True,
            "limit": limit,
            "remaining": limit - len(requests),
            "reset_time": now + window_seconds,
            "retry_after": None
        }
    
    async def _cleanup_memory_store(self, now: float):
        """Clean up expired entries from memory store"""
        try:
            expired_keys = []
            for identifier, requests in self.memory_store.items():
                # Remove entries older than 1 hour
                cutoff = now - 3600
                requests[:] = [req_time for req_time in requests if req_time > cutoff]
                
                # Remove empty entries
                if not requests:
                    expired_keys.append(identifier)
            
            for key in expired_keys:
                del self.memory_store[key]
                
        except Exception as e:
            logger.error(f"Memory store cleanup failed: {str(e)}")


# Global rate limiter instance
_rate_limiter = None


async def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
        await _rate_limiter.initialize()
    
    return _rate_limiter


def get_client_identifier(request: Request, user_id: Optional[str] = None) -> str:
    """
    Generate client identifier for rate limiting
    
    Uses user ID if authenticated, otherwise IP address
    """
    if user_id:
        return f"user:{user_id}"
    
    # Get client IP (handle proxy headers)
    client_ip = request.client.host
    
    # Check for forwarded IP headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        client_ip = real_ip.strip()
    
    return f"ip:{client_ip}"


async def rate_limit_check(
    request: Request,
    limit: int = 100,
    window_seconds: int = 3600,  # 1 hour
    burst_limit: Optional[int] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Rate limit dependency for FastAPI routes
    
    Can be used as a dependency to protect endpoints
    """
    try:
        rate_limiter = await get_rate_limiter()
        identifier = get_client_identifier(request, user_id)
        
        result = await rate_limiter.check_rate_limit(
            identifier=identifier,
            limit=limit,
            window_seconds=window_seconds,
            burst_limit=burst_limit
        )
        
        if not result["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": result["limit"],
                    "retry_after": result["retry_after"],
                    "reset_time": result["reset_time"]
                },
                headers={
                    "X-RateLimit-Limit": str(result["limit"]),
                    "X-RateLimit-Remaining": str(result["remaining"]),
                    "X-RateLimit-Reset": str(int(result["reset_time"])),
                    "Retry-After": str(result["retry_after"]) if result["retry_after"] else "3600"
                }
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limit check failed: {str(e)}")
        # Fail open - allow request if rate limiting fails
        return {
            "allowed": True,
            "limit": limit,
            "remaining": limit,
            "reset_time": time.time() + window_seconds,
            "retry_after": None
        }


class RateLimitConfig:
    """Rate limiting configuration for different endpoints"""
    
    # Authentication endpoints (stricter limits)
    AUTH_LOGIN = {"limit": 5, "window_seconds": 300, "burst_limit": 10}  # 5 per 5 min, burst 10
    AUTH_REGISTER = {"limit": 3, "window_seconds": 3600, "burst_limit": 5}  # 3 per hour, burst 5
    AUTH_PASSWORD_RESET = {"limit": 3, "window_seconds": 3600}  # 3 per hour
    
    # API endpoints (moderate limits)
    API_GENERAL = {"limit": 100, "window_seconds": 3600, "burst_limit": 150}  # 100 per hour, burst 150
    API_DEPLOYMENT = {"limit": 10, "window_seconds": 3600, "burst_limit": 15}  # 10 per hour, burst 15
    API_ANALYSIS = {"limit": 50, "window_seconds": 3600, "burst_limit": 75}  # 50 per hour, burst 75
    
    # Admin endpoints (higher limits)
    ADMIN_GENERAL = {"limit": 500, "window_seconds": 3600}  # 500 per hour
    
    # WebSocket connections
    WEBSOCKET_CONNECT = {"limit": 20, "window_seconds": 3600}  # 20 connections per hour


async def create_rate_limit_dependency(config: Dict[str, Any]):
    """
    Create rate limit dependency with specific configuration
    
    Factory function for creating configured rate limit dependencies
    """
    async def rate_limit_dep(request: Request, user_id: Optional[str] = None):
        return await rate_limit_check(
            request=request,
            limit=config["limit"],
            window_seconds=config["window_seconds"],
            burst_limit=config.get("burst_limit"),
            user_id=user_id
        )
    
    return rate_limit_dep


# Pre-configured rate limit dependencies
auth_rate_limit = create_rate_limit_dependency(RateLimitConfig.AUTH_LOGIN)
register_rate_limit = create_rate_limit_dependency(RateLimitConfig.AUTH_REGISTER)
api_rate_limit = create_rate_limit_dependency(RateLimitConfig.API_GENERAL)
deployment_rate_limit = create_rate_limit_dependency(RateLimitConfig.API_DEPLOYMENT)
analysis_rate_limit = create_rate_limit_dependency(RateLimitConfig.API_ANALYSIS)
