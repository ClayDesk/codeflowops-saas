"""
Comprehensive Health Check System for CodeFlowOps
Tests actual system components instead of returning static responses
"""
import asyncio
import time
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import redis
import os
import logging

logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
    async def check_database(self) -> Dict[str, Any]:
        """Test PostgreSQL database connectivity"""
        try:
            from src.utils.database import SessionLocal
            
            start_time = time.time()
            db = SessionLocal()
            
            # Test simple query
            result = db.execute(text("SELECT 1 as test"))
            test_result = result.fetchone()
            
            response_time = time.time() - start_time
            db.close()
            
            if test_result and test_result[0] == 1:
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time * 1000, 2),
                    "connection": "active"
                }
            else:
                return {
                    "status": "unhealthy", 
                    "error": "Query returned unexpected result",
                    "response_time_ms": round(response_time * 1000, 2)
                }
                
        except SQLAlchemyError as e:
            return {
                "status": "unhealthy",
                "error": f"Database error: {str(e)[:100]}",
                "type": "database_connection_error"
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": f"Unexpected error: {str(e)[:100]}",
                "type": "unknown_error"
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Test Redis connectivity"""
        try:
            start_time = time.time()
            
            # Parse Redis URL
            redis_client = redis.from_url(self.redis_url, decode_responses=True)
            
            # Test ping
            ping_result = redis_client.ping()
            
            # Test set/get
            test_key = "health_check_test"
            redis_client.set(test_key, "test_value", ex=60)
            test_value = redis_client.get(test_key)
            redis_client.delete(test_key)
            
            response_time = time.time() - start_time
            
            if ping_result and test_value == "test_value":
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time * 1000, 2),
                    "ping": True,
                    "read_write": True
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Redis ping or read/write test failed",
                    "ping": ping_result,
                    "read_write": test_value == "test_value"
                }
                
        except redis.ConnectionError as e:
            return {
                "status": "unhealthy",
                "error": f"Redis connection error: {str(e)[:100]}",
                "type": "redis_connection_error"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": f"Redis error: {str(e)[:100]}",
                "type": "redis_error"
            }
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check basic system health"""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            }
        except ImportError:
            return {
                "status": "unavailable",
                "error": "psutil not installed - system metrics unavailable"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"System check error: {str(e)[:100]}"
            }
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        start_time = time.time()
        
        # Run checks in parallel
        db_task = asyncio.create_task(self.check_database())
        redis_task = asyncio.create_task(self.check_redis())
        system_task = asyncio.create_task(self.check_system_resources())
        
        try:
            db_health, redis_health, system_health = await asyncio.gather(
                db_task, redis_task, system_task, return_exceptions=True
            )
        except Exception as e:
            return {
                "status": "error",
                "error": f"Health check execution error: {str(e)}",
                "timestamp": time.time(),
                "total_check_time_ms": round((time.time() - start_time) * 1000, 2)
            }
        
        total_time = time.time() - start_time
        
        # Determine overall status
        db_healthy = isinstance(db_health, dict) and db_health.get("status") == "healthy"
        redis_healthy = isinstance(redis_health, dict) and redis_health.get("status") == "healthy"
        system_healthy = isinstance(system_health, dict) and system_health.get("status") in ["healthy", "unavailable"]
        
        overall_status = "healthy" if (db_healthy and redis_healthy and system_healthy) else "unhealthy"
        
        return {
            "status": overall_status,
            "service": "CodeFlowOps Streamlined API",
            "version": "2.0.0",
            "timestamp": time.time(),
            "total_check_time_ms": round(total_time * 1000, 2),
            "components": {
                "database": db_health if isinstance(db_health, dict) else {"status": "error", "error": str(db_health)},
                "redis": redis_health if isinstance(redis_health, dict) else {"status": "error", "error": str(redis_health)},
                "system": system_health if isinstance(system_health, dict) else {"status": "error", "error": str(system_health)}
            },
            "environment": {
                "database_url_configured": bool(os.getenv("DATABASE_URL")),
                "redis_url_configured": bool(os.getenv("REDIS_URL")),
                "debug_mode": os.getenv("DEBUG", "false").lower() == "true"
            }
        }

# Global health checker instance
health_checker = HealthChecker()
