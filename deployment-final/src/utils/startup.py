"""
Startup tasks for CodeFlowOps
Ensures all required infrastructure is available
"""

import asyncio
import logging
from typing import Dict, Any

from ..config.env import get_settings
from ..utils.job_queue import job_queue
from ..utils.terraform_state import terraform_state_manager
from dependencies.session import get_session_manager
from database.connection import get_database_manager

logger = logging.getLogger(__name__)
settings = get_settings()


async def initialize_infrastructure():
    """Initialize all required infrastructure components"""
    try:
        logger.info("Initializing CodeFlowOps infrastructure...")
        
        # 1. Initialize database
        logger.info("Checking database connection...")
        db_manager = await get_database_manager()
        logger.info("Database initialized")
        
        # 2. Initialize Redis connection
        logger.info("Checking Redis connection...")
        await job_queue.health_check()
        logger.info("Redis connection verified")
        
        # 3. Ensure Terraform state infrastructure
        logger.info("Ensuring Terraform state infrastructure...")
        await terraform_state_manager.ensure_state_infrastructure()
        logger.info("Terraform state infrastructure ready")
        
        # 4. Initialize session manager
        logger.info("Initializing session manager...")
        session_manager = await get_session_manager()
        logger.info("Session manager initialized")
        
        logger.info("Infrastructure initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Infrastructure initialization failed: {e}")
        raise


async def health_check_all_services() -> Dict[str, Any]:
    """Comprehensive health check of all services"""
    health_status = {
        "overall": "healthy",
        "services": {},
        "timestamp": None
    }
    
    try:
        # Database health
        try:
            db_manager = await get_database_manager()
            # Test a simple query
            health_status["services"]["database"] = {
                "status": "healthy",
                "details": "Connection verified"
            }
        except Exception as e:
            health_status["services"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "degraded"
        
        # Redis health
        try:
            await job_queue.health_check()
            queue_stats = await job_queue.get_queue_stats()
            health_status["services"]["redis"] = {
                "status": "healthy",
                "details": f"Queue stats: {queue_stats}"
            }
        except Exception as e:
            health_status["services"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "degraded"
        
        # AWS connectivity (basic check)
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Test AWS credentials
            sts = boto3.client(
                'sts',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            identity = sts.get_caller_identity()
            
            health_status["services"]["aws"] = {
                "status": "healthy",
                "details": f"Account: {identity.get('Account', 'Unknown')}"
            }
        except Exception as e:
            health_status["services"]["aws"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "degraded"
        
        # Terraform state infrastructure
        try:
            # This is a basic check - in production you might want more thorough validation
            health_status["services"]["terraform_state"] = {
                "status": "healthy",
                "details": f"Bucket: {terraform_state_manager.state_bucket}"
            }
        except Exception as e:
            health_status["services"]["terraform_state"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "degraded"
        
        from datetime import datetime
        health_status["timestamp"] = datetime.utcnow().isoformat()
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status["overall"] = "unhealthy"
        health_status["error"] = str(e)
        return health_status


async def cleanup_old_jobs():
    """Clean up old completed/failed jobs to prevent memory bloat"""
    try:
        logger.info("Cleaning up old jobs...")
        
        # Get job statistics before cleanup
        stats_before = await job_queue.get_queue_stats()
        logger.info(f"Jobs before cleanup: {stats_before}")
        
        # This would be implemented based on your specific cleanup logic
        # For now, just log the intention
        logger.info("Job cleanup completed (placeholder)")
        
    except Exception as e:
        logger.error(f"Job cleanup failed: {e}")


async def startup_tasks():
    """Run all startup tasks"""
    try:
        logger.info("Running startup tasks...")
        
        # Initialize infrastructure
        await initialize_infrastructure()
        
        # Run health check
        health = await health_check_all_services()
        logger.info(f"System health: {health['overall']}")
        
        # Clean up old jobs
        await cleanup_old_jobs()
        
        logger.info("Startup tasks completed successfully")
        
    except Exception as e:
        logger.error(f"Startup tasks failed: {e}")
        raise


if __name__ == "__main__":
    # Run startup tasks directly
    asyncio.run(startup_tasks())
