# Rate Limiting Utilities for API Endpoints
# Provides decorators and middleware for rate limiting API requests

import time
import hashlib
from typing import Dict, Optional, Callable, Any
from functools import wraps
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded"""
    def __init__(self, detail: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)}
        )

class InMemoryRateLimiter:
    """
    In-memory rate limiter using token bucket algorithm
    For production, consider using Redis for distributed rate limiting
    """
    
    def __init__(self):
        self.buckets: Dict[str, Dict] = defaultdict(lambda: {
            'tokens': 0,
            'last_update': time.time(),
            'requests': deque()
        })
        self.cleanup_interval = 3600  # Cleanup old entries every hour
        self.last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Remove old rate limit entries to prevent memory leaks"""
        current_time = time.time()
        
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # Remove entries older than 1 hour
        keys_to_remove = []
        
        for key, bucket in self.buckets.items():
            if bucket['last_update'] < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.buckets[key]
        
        self.last_cleanup = current_time
        logger.debug(f"Cleaned up {len(keys_to_remove)} old rate limit entries")
    
    def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int, 
        burst_limit: Optional[int] = None
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit
        
        Args:
            key: Unique identifier for rate limiting (e.g., user ID, IP)
            limit: Number of requests allowed per window
            window: Time window in seconds
            burst_limit: Optional burst limit for token bucket
            
        Returns:
            Tuple of (is_allowed, info_dict)
        """
        self._cleanup_old_entries()
        
        current_time = time.time()
        bucket = self.buckets[key]
        
        # Use sliding window log approach
        bucket['requests'] = deque([
            req_time for req_time in bucket['requests'] 
            if current_time - req_time < window
        ])
        
        # Check if under limit
        current_requests = len(bucket['requests'])
        
        if current_requests >= limit:
            return False, {
                'allowed': False,
                'limit': limit,
                'remaining': 0,
                'reset_time': int(current_time + window),
                'retry_after': window
            }
        
        # Add current request
        bucket['requests'].append(current_time)
        bucket['last_update'] = current_time
        
        return True, {
            'allowed': True,
            'limit': limit,
            'remaining': limit - (current_requests + 1),
            'reset_time': int(current_time + window),
            'retry_after': 0
        }

# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()

def rate_limit(
    requests_per_minute: int = 60,
    per_user: bool = True,
    per_ip: bool = False,
    burst_multiplier: float = 1.5,
    key_func: Optional[Callable] = None
):
    """
    Rate limiting decorator for FastAPI endpoints
    
    Args:
        requests_per_minute: Number of requests allowed per minute
        per_user: Apply rate limit per authenticated user
        per_ip: Apply rate limit per IP address
        burst_multiplier: Multiplier for burst requests
        key_func: Custom function to generate rate limit key
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object
            request = None
            current_user = None
            
            for arg in args:
                if hasattr(arg, 'client') and hasattr(arg, 'url'):  # Request object
                    request = arg
                elif hasattr(arg, 'id') and hasattr(arg, 'email'):  # User object
                    current_user = arg
            
            # Also check kwargs
            if not request:
                request = kwargs.get('request')
            if not current_user:
                current_user = kwargs.get('current_user')
            
            # Generate rate limit key
            if key_func:
                rate_key = key_func(request, current_user)
            else:
                rate_key = _generate_rate_limit_key(
                    request, current_user, per_user, per_ip
                )
            
            # Check rate limit
            window = 60  # 1 minute window
            burst_limit = int(requests_per_minute * burst_multiplier)
            
            allowed, info = rate_limiter.is_allowed(
                rate_key, requests_per_minute, window, burst_limit
            )
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for key: {rate_key}, "
                    f"limit: {requests_per_minute}/min"
                )
                raise RateLimitExceeded(
                    detail=f"Too many requests. Limit: {requests_per_minute} per minute",
                    retry_after=info['retry_after']
                )
            
            # Add rate limit headers to response
            try:
                result = await func(*args, **kwargs)
                
                # If result is a Response, add headers
                if hasattr(result, 'headers'):
                    result.headers['X-RateLimit-Limit'] = str(info['limit'])
                    result.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                    result.headers['X-RateLimit-Reset'] = str(info['reset_time'])
                
                return result
                
            except Exception as e:
                # Re-raise the exception
                raise e
        
        return wrapper
    return decorator

def _generate_rate_limit_key(
    request: Optional[Request], 
    current_user: Optional[Any], 
    per_user: bool, 
    per_ip: bool
) -> str:
    """Generate rate limit key based on request and user context"""
    
    key_parts = []
    
    if per_user and current_user:
        user_id = getattr(current_user, 'id', None)
        if user_id:
            key_parts.append(f"user:{user_id}")
    
    if per_ip and request:
        # Get client IP (considering proxies)
        client_ip = request.client.host
        
        # Check for forwarded headers
        if 'x-forwarded-for' in request.headers:
            client_ip = request.headers['x-forwarded-for'].split(',')[0].strip()
        elif 'x-real-ip' in request.headers:
            client_ip = request.headers['x-real-ip']
        
        key_parts.append(f"ip:{client_ip}")
    
    if not key_parts:
        # Fallback to IP if no other identifier
        if request:
            client_ip = request.client.host
            key_parts.append(f"ip:{client_ip}")
        else:
            key_parts.append("anonymous")
    
    return ":".join(key_parts)

# Predefined rate limit decorators for common use cases
def rate_limit_strict(func):
    """Strict rate limiting: 30 requests per minute"""
    return rate_limit(requests_per_minute=30)(func)

def rate_limit_moderate(func):
    """Moderate rate limiting: 60 requests per minute"""
    return rate_limit(requests_per_minute=60)(func)

def rate_limit_generous(func):
    """Generous rate limiting: 120 requests per minute"""
    return rate_limit(requests_per_minute=120)(func)

def rate_limit_smart_deploy(func):
    """
    Rate limiting for Smart Deploy endpoints
    More restrictive due to resource-intensive operations
    """
    return rate_limit(
        requests_per_minute=10,  # Only 10 deployments per minute
        per_user=True,
        burst_multiplier=1.2
    )(func)

def rate_limit_analysis(func):
    """Rate limiting for code analysis endpoints"""
    return rate_limit(
        requests_per_minute=20,  # 20 analyses per minute
        per_user=True
    )(func)

def rate_limit_auth(func):
    """Rate limiting for authentication endpoints"""
    return rate_limit(
        requests_per_minute=10,  # 10 auth attempts per minute
        per_ip=True,  # Per IP to prevent brute force
        per_user=False
    )(func)

class RateLimitMiddleware:
    """
    FastAPI middleware for global rate limiting
    """
    
    def __init__(self, app, global_limit: int = 1000):
        self.app = app
        self.global_limit = global_limit
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create request object
        request = Request(scope, receive)
        
        # Apply global rate limit
        client_ip = request.client.host
        global_key = f"global:ip:{client_ip}"
        
        allowed, info = rate_limiter.is_allowed(
            global_key, self.global_limit, 3600  # 1 hour window
        )
        
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Global rate limit exceeded",
                    "limit": self.global_limit,
                    "retry_after": 3600
                },
                headers={"Retry-After": "3600"}
            )
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send)

# Utility functions for manual rate limit checking
async def check_rate_limit(
    key: str, 
    limit: int, 
    window: int = 60
) -> tuple[bool, dict]:
    """
    Manually check rate limit for a given key
    """
    return rate_limiter.is_allowed(key, limit, window)

async def reset_rate_limit(key: str):
    """
    Reset rate limit for a specific key
    """
    if key in rate_limiter.buckets:
        del rate_limiter.buckets[key]
        logger.info(f"Reset rate limit for key: {key}")

async def get_rate_limit_status(key: str) -> dict:
    """
    Get current rate limit status for a key
    """
    bucket = rate_limiter.buckets.get(key)
    if not bucket:
        return {
            'requests': 0,
            'last_request': None
        }
    
    current_time = time.time()
    recent_requests = [
        req_time for req_time in bucket['requests']
        if current_time - req_time < 60
    ]
    
    return {
        'requests': len(recent_requests),
        'last_request': max(bucket['requests']) if bucket['requests'] else None
    }
