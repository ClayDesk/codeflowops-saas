"""
Monitoring API Routes
Provides endpoints for system health and sync monitoring
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional, Dict, Any
import logging

from ..services.user_sync_monitor import sync_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

@router.get("/sync-health")
async def get_sync_health():
    """Get comprehensive user synchronization health status"""
    try:
        health_report = await sync_monitor.check_sync_health()
        return health_report
        
    except Exception as e:
        logger.error(f"Error getting sync health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync health: {str(e)}"
        )

@router.post("/fix-sync-issues")
async def fix_sync_issues(issue_types: Optional[List[str]] = None):
    """
    Attempt to fix synchronization issues.
    
    Args:
        issue_types: List of issue types to fix. If None, attempts to fix all issues.
                    Available types: ["missing_customer_records"]
    """
    try:
        fix_results = await sync_monitor.fix_sync_issues(issue_types)
        return fix_results
        
    except Exception as e:
        logger.error(f"Error fixing sync issues: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fix sync issues: {str(e)}"
        )

@router.get("/health")
async def monitoring_health_check():
    """Health check for monitoring service"""
    return {
        "service": "monitoring",
        "status": "healthy",
        "features": [
            "sync_health_monitoring",
            "issue_detection",
            "automatic_fixes"
        ],
        "timestamp": "2025-09-16T05:40:00Z"
    }