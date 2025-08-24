# Simple in-memory storage to replace Redis for development
import json
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class InMemoryStorage:
    """Thread-safe in-memory storage to replace Redis for development"""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, float] = {}
        self._lock = threading.RLock()
        
    def ping(self) -> str:
        """Test connection - always returns PONG"""
        return "PONG"
    
    def get(self, key: str) -> Optional[bytes]:
        """Get value by key"""
        with self._lock:
            self._cleanup_expired()
            if key in self._data:
                value = self._data[key]
                if isinstance(value, str):
                    return value.encode()
                return value
            return None
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiry in seconds"""
        with self._lock:
            self._cleanup_expired()
            if isinstance(value, bytes):
                value = value.decode()
            self._data[key] = value
            
            if ex:
                self._expiry[key] = time.time() + ex
            elif key in self._expiry:
                del self._expiry[key]
                
            return True
    
    def setex(self, key: str, time_seconds: int, value: Any) -> bool:
        """Set key-value pair with expiry time in seconds (Redis-compatible)"""
        return self.set(key, value, ex=time_seconds)
    
    def delete(self, key: str) -> int:
        """Delete key"""
        with self._lock:
            self._cleanup_expired()
            if key in self._data:
                del self._data[key]
                if key in self._expiry:
                    del self._expiry[key]
                return 1
            return 0
    
    def exists(self, key: str) -> int:
        """Check if key exists"""
        with self._lock:
            self._cleanup_expired()
            return 1 if key in self._data else 0
    
    def keys(self, pattern: str = "*") -> list:
        """Get all keys matching pattern"""
        with self._lock:
            self._cleanup_expired()
            if pattern == "*":
                return list(self._data.keys())
            # Simple pattern matching for basic cases
            import fnmatch
            return [key for key in self._data.keys() if fnmatch.fnmatch(key, pattern)]
    
    def flushdb(self) -> bool:
        """Clear all data"""
        with self._lock:
            self._data.clear()
            self._expiry.clear()
            return True
    
    def _cleanup_expired(self):
        """Remove expired keys"""
        current_time = time.time()
        expired_keys = [key for key, expiry_time in self._expiry.items() if current_time > expiry_time]
        for key in expired_keys:
            if key in self._data:
                del self._data[key]
            del self._expiry[key]

# Global instance
memory_storage = InMemoryStorage()

class MemoryRedisClient:
    """Redis-compatible interface using in-memory storage with async support"""
    
    def __init__(self, storage: InMemoryStorage = None):
        self.storage = storage or memory_storage
    
    async def ping(self):
        return self.storage.ping()
    
    async def get(self, key: str):
        return self.storage.get(key)
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        return self.storage.set(key, value, ex)
    
    async def setex(self, key: str, time_seconds: int, value: Any):
        return self.storage.setex(key, time_seconds, value)
    
    async def delete(self, key: str):
        return self.storage.delete(key)
    
    async def exists(self, key: str):
        return self.storage.exists(key)
    
    async def keys(self, pattern: str = "*"):
        return self.storage.keys(pattern)
    
    async def flushdb(self):
        return self.storage.flushdb()
    
    # Synchronous versions for backward compatibility
    def ping_sync(self):
        return self.storage.ping()
    
    def get_sync(self, key: str):
        return self.storage.get(key)
    
    def set_sync(self, key: str, value: Any, ex: Optional[int] = None):
        return self.storage.set(key, value, ex)
    
    def setex_sync(self, key: str, time_seconds: int, value: Any):
        return self.storage.setex(key, time_seconds, value)

def create_memory_redis_client() -> MemoryRedisClient:
    """Create a new in-memory Redis client"""
    return MemoryRedisClient()
