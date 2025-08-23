"""
Health check utilities for CodeFlowOps
Provides comprehensive system health monitoring
"""

import logging
import asyncio
import aioredis
import psutil
import time
from typing import Dict, Any, List, Optional
import httpx
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def check_database_health() -> Dict[str, Any]:
    """
    Check database connectivity and performance
    
    Returns:
        Database health status
    """
    try:
        # Import database connection
        from database.connection import get_db_connection
        
        start_time = time.time()
        
        # Test database connection
        async with get_db_connection() as db:
            # Simple query to test connectivity
            result = await db.fetch("SELECT 1 as test")
            
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
            "details": "Database connection successful"
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Database connection failed"
        }


async def check_redis_health() -> Dict[str, Any]:
    """
    Check Redis connectivity and performance
    
    Returns:
        Redis health status
    """
    try:
        start_time = time.time()
        
        # Connect to Redis
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        redis = aioredis.from_url(redis_url, decode_responses=True)
        
        # Test Redis connection with ping
        await redis.ping()
        
        # Test basic operations
        test_key = "health_check_test"
        await redis.set(test_key, "test_value", ex=10)  # 10 second expiry
        test_value = await redis.get(test_key)
        await redis.delete(test_key)
        
        await redis.close()
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        if test_value == "test_value":
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "details": "Redis connection and operations successful"
            }
        else:
            return {
                "status": "unhealthy",
                "error": "Redis operation test failed",
                "details": "Redis connection successful but operations failed"
            }
            
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "Redis connection failed"
        }


async def check_aws_services_health() -> Dict[str, Any]:
    """
    Check AWS services connectivity and permissions
    
    Returns:
        AWS services health status
    """
    try:
        aws_status = {
            "s3": {"status": "unknown"},
            "cloudformation": {"status": "unknown"},
            "cloudfront": {"status": "unknown"}
        }
        
        # Check S3 service
        try:
            s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
            start_time = time.time()
            
            # Test S3 access by listing buckets
            s3_client.list_buckets()
            
            # Test specific bucket if configured
            if hasattr(settings, 'AWS_S3_BUCKET') and settings.AWS_S3_BUCKET:
                s3_client.head_bucket(Bucket=settings.AWS_S3_BUCKET)
                aws_status["s3"] = {
                    "status": "healthy",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "bucket_accessible": True
                }
            else:
                aws_status["s3"] = {
                    "status": "healthy",
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "bucket_accessible": False
                }
                
        except NoCredentialsError:
            aws_status["s3"] = {
                "status": "unhealthy",
                "error": "AWS credentials not configured"
            }
        except ClientError as e:
            aws_status["s3"] = {
                "status": "unhealthy",
                "error": f"S3 access failed: {str(e)}"
            }
        
        # Check CloudFormation service
        try:
            cf_client = boto3.client('cloudformation', region_name=settings.AWS_REGION)
            start_time = time.time()
            
            # Test CloudFormation access
            cf_client.describe_stacks()
            
            aws_status["cloudformation"] = {
                "status": "healthy",
                "response_time_ms": round((time.time() - start_time) * 1000, 2)
            }
            
        except NoCredentialsError:
            aws_status["cloudformation"] = {
                "status": "unhealthy",
                "error": "AWS credentials not configured"
            }
        except ClientError as e:
            aws_status["cloudformation"] = {
                "status": "unhealthy",
                "error": f"CloudFormation access failed: {str(e)}"
            }
        
        # Check CloudFront service
        try:
            cloudfront_client = boto3.client('cloudfront', region_name=settings.AWS_REGION)
            start_time = time.time()
            
            # Test CloudFront access
            cloudfront_client.list_distributions()
            
            aws_status["cloudfront"] = {
                "status": "healthy",
                "response_time_ms": round((time.time() - start_time) * 1000, 2)
            }
            
        except NoCredentialsError:
            aws_status["cloudfront"] = {
                "status": "unhealthy",
                "error": "AWS credentials not configured"
            }
        except ClientError as e:
            aws_status["cloudfront"] = {
                "status": "unhealthy",
                "error": f"CloudFront access failed: {str(e)}"
            }
        
        # Determine overall AWS health
        healthy_services = sum(1 for service in aws_status.values() if service["status"] == "healthy")
        total_services = len(aws_status)
        
        overall_status = "healthy" if healthy_services == total_services else "degraded" if healthy_services > 0 else "unhealthy"
        
        return {
            "status": overall_status,
            "services": aws_status,
            "healthy_services": f"{healthy_services}/{total_services}"
        }
        
    except Exception as e:
        logger.error(f"AWS health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "AWS health check failed"
        }


async def check_external_dependencies() -> Dict[str, Any]:
    """
    Check external service dependencies
    
    Returns:
        External dependencies health status
    """
    try:
        external_status = {
            "github_api": {"status": "unknown"},
            "npm_registry": {"status": "unknown"}
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check GitHub API
            try:
                start_time = time.time()
                github_response = await client.get("https://api.github.com/rate_limit")
                
                if github_response.status_code == 200:
                    rate_limit_data = github_response.json()
                    external_status["github_api"] = {
                        "status": "healthy",
                        "response_time_ms": round((time.time() - start_time) * 1000, 2),
                        "rate_limit_remaining": rate_limit_data.get("rate", {}).get("remaining", "unknown")
                    }
                else:
                    external_status["github_api"] = {
                        "status": "unhealthy",
                        "error": f"HTTP {github_response.status_code}"
                    }
                    
            except Exception as e:
                external_status["github_api"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # Check NPM Registry
            try:
                start_time = time.time()
                npm_response = await client.get("https://registry.npmjs.org/")
                
                if npm_response.status_code == 200:
                    external_status["npm_registry"] = {
                        "status": "healthy",
                        "response_time_ms": round((time.time() - start_time) * 1000, 2)
                    }
                else:
                    external_status["npm_registry"] = {
                        "status": "unhealthy",
                        "error": f"HTTP {npm_response.status_code}"
                    }
                    
            except Exception as e:
                external_status["npm_registry"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Determine overall external dependencies health
        healthy_deps = sum(1 for dep in external_status.values() if dep["status"] == "healthy")
        total_deps = len(external_status)
        
        overall_status = "healthy" if healthy_deps == total_deps else "degraded" if healthy_deps > 0 else "unhealthy"
        
        return {
            "status": overall_status,
            "dependencies": external_status,
            "healthy_dependencies": f"{healthy_deps}/{total_deps}"
        }
        
    except Exception as e:
        logger.error(f"External dependencies health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "details": "External dependencies health check failed"
        }


def get_system_metrics() -> Dict[str, Any]:
    """
    Get system performance metrics
    
    Returns:
        System metrics
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_usage = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
        
        # Network metrics
        network = psutil.net_io_counters()
        network_stats = {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv
        }
        
        # Process metrics
        current_process = psutil.Process()
        process_info = {
            "pid": current_process.pid,
            "memory_percent": current_process.memory_percent(),
            "cpu_percent": current_process.cpu_percent(),
            "num_threads": current_process.num_threads(),
            "create_time": current_process.create_time()
        }
        
        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "count": cpu_count
            },
            "memory": memory_usage,
            "disk": disk_usage,
            "network": network_stats,
            "process": process_info,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"System metrics collection failed: {str(e)}")
        return {
            "error": str(e),
            "timestamp": time.time()
        }


async def run_comprehensive_health_check() -> Dict[str, Any]:
    """
    Run comprehensive health check for all system components
    
    Returns:
        Complete health check results
    """
    try:
        start_time = time.time()
        
        # Run all health checks concurrently
        health_checks = await asyncio.gather(
            check_database_health(),
            check_redis_health(),
            check_aws_services_health(),
            check_external_dependencies(),
            return_exceptions=True
        )
        
        # Process results
        database_health = health_checks[0] if not isinstance(health_checks[0], Exception) else {
            "status": "unhealthy", "error": str(health_checks[0])
        }
        redis_health = health_checks[1] if not isinstance(health_checks[1], Exception) else {
            "status": "unhealthy", "error": str(health_checks[1])
        }
        aws_health = health_checks[2] if not isinstance(health_checks[2], Exception) else {
            "status": "unhealthy", "error": str(health_checks[2])
        }
        external_health = health_checks[3] if not isinstance(health_checks[3], Exception) else {
            "status": "unhealthy", "error": str(health_checks[3])
        }
        
        # Get system metrics
        system_metrics = get_system_metrics()
        
        # Determine overall health status
        component_statuses = [
            database_health.get("status"),
            redis_health.get("status"),
            aws_health.get("status"),
            external_health.get("status")
        ]
        
        healthy_count = sum(1 for status in component_statuses if status == "healthy")
        degraded_count = sum(1 for status in component_statuses if status == "degraded")
        
        if healthy_count == len(component_statuses):
            overall_status = "healthy"
        elif healthy_count + degraded_count > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        end_time = time.time()
        
        return {
            "status": overall_status,
            "timestamp": end_time,
            "check_duration_ms": round((end_time - start_time) * 1000, 2),
            "components": {
                "database": database_health,
                "redis": redis_health,
                "aws_services": aws_health,
                "external_dependencies": external_health
            },
            "system_metrics": system_metrics,
            "summary": {
                "healthy_components": f"{healthy_count}/{len(component_statuses)}",
                "degraded_components": degraded_count,
                "unhealthy_components": len(component_statuses) - healthy_count - degraded_count
            }
        }
        
    except Exception as e:
        logger.error(f"Comprehensive health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


async def check_deployment_readiness() -> Dict[str, Any]:
    """
    Check if system is ready for deployments
    
    Returns:
        Deployment readiness status
    """
    try:
        # Check critical components for deployment
        readiness_checks = await asyncio.gather(
            check_redis_health(),
            check_aws_services_health(),
            return_exceptions=True
        )
        
        redis_status = readiness_checks[0] if not isinstance(readiness_checks[0], Exception) else {
            "status": "unhealthy"
        }
        aws_status = readiness_checks[1] if not isinstance(readiness_checks[1], Exception) else {
            "status": "unhealthy"
        }
        
        # Check system resources
        system_metrics = get_system_metrics()
        
        # Readiness criteria
        redis_ready = redis_status.get("status") == "healthy"
        aws_ready = aws_status.get("status") in ["healthy", "degraded"]
        memory_ready = system_metrics.get("memory", {}).get("percent", 100) < 90
        disk_ready = system_metrics.get("disk", {}).get("percent", 100) < 90
        
        ready = all([redis_ready, aws_ready, memory_ready, disk_ready])
        
        readiness_report = {
            "ready": ready,
            "components": {
                "redis": redis_ready,
                "aws_services": aws_ready,
                "memory_available": memory_ready,
                "disk_space": disk_ready
            },
            "system_load": {
                "memory_usage_percent": system_metrics.get("memory", {}).get("percent"),
                "disk_usage_percent": system_metrics.get("disk", {}).get("percent"),
                "cpu_usage_percent": system_metrics.get("cpu", {}).get("usage_percent")
            }
        }
        
        if not ready:
            readiness_report["warnings"] = []
            if not redis_ready:
                readiness_report["warnings"].append("Redis not available")
            if not aws_ready:
                readiness_report["warnings"].append("AWS services not accessible")
            if not memory_ready:
                readiness_report["warnings"].append("High memory usage")
            if not disk_ready:
                readiness_report["warnings"].append("Low disk space")
        
        return readiness_report
        
    except Exception as e:
        logger.error(f"Deployment readiness check failed: {str(e)}")
        return {
            "ready": False,
            "error": str(e)
        }
