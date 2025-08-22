"""
Health monitoring routes
Provides system health checks and status monitoring
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import logging
import time
import psutil
import asyncio
from datetime import datetime, timedelta

from ..models.response_models import HealthResponse, HealthStatus, SystemStatsResponse, SystemStats, ResponseStatus
from dependencies.session import get_session_manager, SessionManager
from ..config.env import get_settings
from ..utils.health_checks import (
    check_aws_connectivity,
    check_database_connectivity,
    check_redis_connectivity,
    check_terraform_availability
)

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Track application start time
start_time = datetime.utcnow()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint
    
    Returns overall application health status with
    dependency checks and system information.
    """
    try:
        current_time = datetime.utcnow()
        uptime = (current_time - start_time).total_seconds()
        
        # Perform health checks
        checks = {}
        dependencies = {}
        overall_healthy = True
        
        # AWS connectivity check
        try:
            aws_check = await check_aws_connectivity()
            checks["aws"] = {
                "status": "healthy" if aws_check["connected"] else "unhealthy",
                "response_time": aws_check["response_time"],
                "region": aws_check.get("region", "unknown")
            }
            if not aws_check["connected"]:
                overall_healthy = False
        except Exception as e:
            checks["aws"] = {"status": "error", "error": str(e)}
            overall_healthy = False
        
        # Database connectivity check
        try:
            db_check = await check_database_connectivity()
            checks["database"] = {
                "status": "healthy" if db_check["connected"] else "unhealthy",
                "response_time": db_check["response_time"],
                "type": db_check.get("type", "unknown")
            }
            dependencies["database"] = {
                "available": db_check["connected"],
                "type": db_check.get("type", "unknown")
            }
            if not db_check["connected"]:
                overall_healthy = False
        except Exception as e:
            checks["database"] = {"status": "error", "error": str(e)}
            dependencies["database"] = {"available": False, "error": str(e)}
            overall_healthy = False
        
        # Redis connectivity check
        try:
            redis_check = await check_redis_connectivity()
            checks["redis"] = {
                "status": "healthy" if redis_check["connected"] else "unhealthy",
                "response_time": redis_check["response_time"]
            }
            dependencies["redis"] = {
                "available": redis_check["connected"]
            }
            # Redis is optional for development
            if not redis_check["connected"] and settings.NODE_ENV == "production":
                overall_healthy = False
        except Exception as e:
            checks["redis"] = {"status": "error", "error": str(e)}
            dependencies["redis"] = {"available": False, "error": str(e)}
        
        # Terraform availability check
        try:
            terraform_check = await check_terraform_availability()
            checks["terraform"] = {
                "status": "healthy" if terraform_check["available"] else "unhealthy",
                "version": terraform_check.get("version", "unknown")
            }
            dependencies["terraform"] = {
                "available": terraform_check["available"],
                "version": terraform_check.get("version", "unknown")
            }
            if not terraform_check["available"]:
                overall_healthy = False
        except Exception as e:
            checks["terraform"] = {"status": "error", "error": str(e)}
            dependencies["terraform"] = {"available": False, "error": str(e)}
            overall_healthy = False
        
        # System resource checks
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            checks["system_resources"] = {
                "status": "healthy",
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "available_memory": memory.available,
                "available_disk": disk.free
            }
            
            # Flag warnings for high resource usage
            if cpu_percent > 80 or memory.percent > 85 or disk.percent > 90:
                checks["system_resources"]["status"] = "warning"
                if cpu_percent > 95 or memory.percent > 95 or disk.percent > 95:
                    checks["system_resources"]["status"] = "critical"
                    overall_healthy = False
                    
        except Exception as e:
            checks["system_resources"] = {"status": "error", "error": str(e)}
        
        health_status = HealthStatus(
            service="CodeFlowOps Backend",
            status="healthy" if overall_healthy else "unhealthy",
            uptime=uptime,
            version="1.0.0",
            environment=settings.NODE_ENV,
            checks=checks,
            dependencies=dependencies
        )
        
        response_status = ResponseStatus.SUCCESS if overall_healthy else ResponseStatus.ERROR
        
        return HealthResponse(
            status=response_status,
            message="Health check completed",
            health=health_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        
        error_health = HealthStatus(
            service="CodeFlowOps Backend",
            status="error",
            uptime=0,
            version="1.0.0",
            environment=settings.NODE_ENV,
            checks={"error": {"status": "error", "error": str(e)}},
            dependencies={}
        )
        
        return HealthResponse(
            status=ResponseStatus.ERROR,
            message="Health check failed",
            health=error_health
        )


@router.get("/ready")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint
    
    Returns 200 if application is ready to serve traffic.
    """
    try:
        # Quick checks for essential services
        aws_ready = await check_aws_connectivity()
        
        if aws_ready["connected"]:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": "CodeFlowOps Backend"
                }
            )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "reason": "AWS connectivity required",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    
    Returns 200 if application is alive and should not be restarted.
    """
    try:
        # Basic application liveness check
        current_time = datetime.utcnow()
        uptime = (current_time - start_time).total_seconds()
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "alive",
                "uptime": uptime,
                "timestamp": current_time.isoformat(),
                "service": "CodeFlowOps Backend"
            }
        )
        
    except Exception as e:
        logger.error(f"Liveness check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "reason": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get system-wide statistics
    
    Returns performance metrics and usage statistics.
    """
    try:
        # Get session statistics
        active_sessions = await session_manager.get_active_sessions()
        session_stats = await session_manager.get_session_statistics()
        
        # Calculate success rate
        total_deployments = session_stats.get("completed", 0) + session_stats.get("failed", 0)
        success_rate = (session_stats.get("completed", 0) / total_deployments * 100) if total_deployments > 0 else 0
        
        # Get system resource usage
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        
        system_load = {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "active_processes": len(psutil.pids())
        }
        
        stats = SystemStats(
            active_sessions=len(active_sessions),
            completed_deployments=session_stats.get("completed", 0),
            average_deployment_time=session_stats.get("average_duration", 0),
            success_rate=success_rate,
            popular_project_types=session_stats.get("project_types", {}),
            average_queue_time=session_stats.get("average_queue_time", 0),
            system_load=system_load
        )
        
        return SystemStatsResponse(
            status=ResponseStatus.SUCCESS,
            message="System statistics retrieved successfully",
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {str(e)}")
        return SystemStatsResponse(
            status=ResponseStatus.ERROR,
            message="Failed to retrieve system statistics",
            stats=SystemStats(
                active_sessions=0,
                completed_deployments=0,
                average_deployment_time=0,
                success_rate=0,
                popular_project_types={},
                average_queue_time=0,
                system_load={}
            )
        )


@router.get("/metrics")
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus format for monitoring.
    """
    try:
        # Get basic metrics
        current_time = datetime.utcnow()
        uptime = (current_time - start_time).total_seconds()
        
        # System metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        metrics = [
            f"codeflowops_uptime_seconds {uptime}",
            f"codeflowops_cpu_usage_percent {cpu_percent}",
            f"codeflowops_memory_usage_percent {memory.percent}",
            f"codeflowops_memory_available_bytes {memory.available}",
        ]
        
        # Add session metrics if available
        try:
            session_manager = get_session_manager()
            active_sessions = await session_manager.get_active_sessions()
            session_stats = await session_manager.get_session_statistics()
            
            metrics.extend([
                f"codeflowops_active_sessions {len(active_sessions)}",
                f"codeflowops_completed_deployments_total {session_stats.get('completed', 0)}",
                f"codeflowops_failed_deployments_total {session_stats.get('failed', 0)}",
            ])
        except Exception:
            # Skip session metrics if not available
            pass
        
        return JSONResponse(
            status_code=200,
            content={"metrics": "\n".join(metrics)},
            media_type="text/plain"
        )
        
    except Exception as e:
        logger.error(f"Failed to generate metrics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to generate metrics"},
            media_type="text/plain"
        )


@router.get("/version")
async def get_version():
    """
    Get application version information
    
    Returns version, build info, and environment details.
    """
    return JSONResponse(
        status_code=200,
        content={
            "service": "CodeFlowOps Backend",
            "version": "1.0.0",
            "environment": settings.NODE_ENV,
            "build_time": start_time.isoformat(),
            "uptime": (datetime.utcnow() - start_time).total_seconds(),
            "python_version": f"{psutil.version_info}",
            "api_docs": "/docs" if settings.NODE_ENV != "production" else "disabled"
        }
    )
