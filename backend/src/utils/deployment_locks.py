"""
Deployment locking mechanism to prevent concurrent operations
"""

import redis
import time
import asyncio
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging

from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class DeploymentLock:
    """Redis-based distributed lock for deployments"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
        self.lock_prefix = "codeflowops:lock"
        self.default_timeout = 3600  # 1 hour
    
    def _get_lock_key(self, resource_type: str, resource_id: str) -> str:
        """Generate lock key for resource"""
        return f"{self.lock_prefix}:{resource_type}:{resource_id}"
    
    async def acquire_lock(
        self,
        resource_type: str,
        resource_id: str,
        timeout: Optional[int] = None,
        owner: Optional[str] = None
    ) -> bool:
        """
        Acquire a lock for a resource
        
        Args:
            resource_type: Type of resource (session, user, project)
            resource_id: Resource identifier
            timeout: Lock timeout in seconds
            owner: Lock owner identifier
            
        Returns:
            True if lock acquired, False otherwise
        """
        lock_key = self._get_lock_key(resource_type, resource_id)
        lock_timeout = timeout or self.default_timeout
        lock_owner = owner or f"process_{time.time()}"
        
        # Try to acquire lock with expiration
        result = self.redis_client.set(
            lock_key,
            lock_owner,
            nx=True,  # Only set if key doesn't exist
            ex=lock_timeout  # Set expiration
        )
        
        if result:
            logger.info(f"Acquired lock for {resource_type}:{resource_id} by {lock_owner}")
            return True
        else:
            current_owner = self.redis_client.get(lock_key)
            logger.warning(f"Failed to acquire lock for {resource_type}:{resource_id}, owned by {current_owner}")
            return False
    
    async def release_lock(
        self,
        resource_type: str,
        resource_id: str,
        owner: Optional[str] = None
    ) -> bool:
        """
        Release a lock for a resource
        
        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            owner: Lock owner identifier (for verification)
            
        Returns:
            True if lock released, False otherwise
        """
        lock_key = self._get_lock_key(resource_type, resource_id)
        
        if owner:
            # Verify ownership before releasing
            current_owner = self.redis_client.get(lock_key)
            if current_owner != owner:
                logger.warning(f"Cannot release lock for {resource_type}:{resource_id}, not owned by {owner}")
                return False
        
        result = self.redis_client.delete(lock_key)
        
        if result:
            logger.info(f"Released lock for {resource_type}:{resource_id}")
            return True
        else:
            logger.warning(f"Lock for {resource_type}:{resource_id} was not found")
            return False
    
    async def is_locked(self, resource_type: str, resource_id: str) -> bool:
        """Check if resource is locked"""
        lock_key = self._get_lock_key(resource_type, resource_id)
        return self.redis_client.exists(lock_key) > 0
    
    async def get_lock_info(self, resource_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get lock information"""
        lock_key = self._get_lock_key(resource_type, resource_id)
        
        owner = self.redis_client.get(lock_key)
        if not owner:
            return None
        
        ttl = self.redis_client.ttl(lock_key)
        
        return {
            "owner": owner,
            "ttl": ttl,
            "expires_at": time.time() + ttl if ttl > 0 else None
        }
    
    async def extend_lock(
        self,
        resource_type: str,
        resource_id: str,
        additional_time: int,
        owner: Optional[str] = None
    ) -> bool:
        """
        Extend lock duration
        
        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            additional_time: Additional seconds to add
            owner: Lock owner for verification
            
        Returns:
            True if lock extended, False otherwise
        """
        lock_key = self._get_lock_key(resource_type, resource_id)
        
        if owner:
            current_owner = self.redis_client.get(lock_key)
            if current_owner != owner:
                return False
        
        current_ttl = self.redis_client.ttl(lock_key)
        if current_ttl < 0:
            return False
        
        new_ttl = current_ttl + additional_time
        result = self.redis_client.expire(lock_key, new_ttl)
        
        if result:
            logger.info(f"Extended lock for {resource_type}:{resource_id} by {additional_time}s")
        
        return result
    
    @asynccontextmanager
    async def lock_context(
        self,
        resource_type: str,
        resource_id: str,
        timeout: Optional[int] = None,
        owner: Optional[str] = None,
        wait_timeout: int = 30
    ):
        """
        Context manager for automatic lock acquisition and release
        
        Args:
            resource_type: Type of resource
            resource_id: Resource identifier
            timeout: Lock timeout in seconds
            owner: Lock owner identifier
            wait_timeout: How long to wait for lock acquisition
        """
        lock_owner = owner or f"context_{time.time()}"
        acquired = False
        
        # Try to acquire lock with retries
        start_time = time.time()
        while time.time() - start_time < wait_timeout:
            if await self.acquire_lock(resource_type, resource_id, timeout, lock_owner):
                acquired = True
                break
            await asyncio.sleep(1)
        
        if not acquired:
            raise TimeoutError(f"Failed to acquire lock for {resource_type}:{resource_id} within {wait_timeout}s")
        
        try:
            yield
        finally:
            await self.release_lock(resource_type, resource_id, lock_owner)

# Global deployment lock instance
deployment_lock = DeploymentLock()

# Convenience functions for common lock operations
async def lock_session_deployment(session_id: str, timeout: int = 3600) -> bool:
    """Lock a session for deployment operations"""
    return await deployment_lock.acquire_lock("session", session_id, timeout)

async def unlock_session_deployment(session_id: str) -> bool:
    """Unlock a session from deployment operations"""
    return await deployment_lock.release_lock("session", session_id)

async def is_session_deployment_locked(session_id: str) -> bool:
    """Check if session deployment is locked"""
    return await deployment_lock.is_locked("session", session_id)

@asynccontextmanager
async def session_deployment_lock(session_id: str, timeout: int = 3600):
    """Context manager for session deployment lock"""
    async with deployment_lock.lock_context("session", session_id, timeout):
        yield
