"""
Session management routes with resume functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
import logging

from ..utils.session_resume import session_resume_manager, ResumeStrategy
from ..utils.structured_logging import structured_logger
from ..utils.quota_tracking import quota_manager
from dependencies.session import get_session_manager, SessionManager
from auth.auth_manager import auth_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/sessions/resumable")
async def get_resumable_sessions(
    user_id: str = Depends(lambda: "current_user_id"),  # TODO: Get from auth
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get list of sessions that can be resumed
    
    Returns sessions that failed or got stuck and can be recovered.
    """
    try:
        resumable_sessions = await session_resume_manager.find_resumable_sessions(user_id)
        
        return {
            "resumable_sessions": resumable_sessions,
            "total_count": len(resumable_sessions),
            "timestamp": session_manager._get_current_time().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get resumable sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resumable sessions"
        )


@router.post("/sessions/{session_id}/resume")
async def resume_session(
    session_id: str,
    strategy: ResumeStrategy = ResumeStrategy.CONTINUE,
    user_id: str = Depends(lambda: "current_user_id")  # TODO: Get from auth
):
    """
    Resume a failed or stuck session
    
    Attempts to recover and continue a deployment that was interrupted.
    """
    try:
        success, message = await session_resume_manager.resume_session(
            session_id, user_id, strategy
        )
        
        if success:
            return {
                "status": "success",
                "message": message,
                "session_id": session_id,
                "strategy": strategy.value
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume session"
        )


@router.get("/sessions/{session_id}/recovery-info")
async def get_session_recovery_info(
    session_id: str,
    user_id: str = Depends(lambda: "current_user_id")  # TODO: Get from auth
):
    """
    Get detailed recovery information for a session
    
    Provides information needed to make resume decisions.
    """
    try:
        recovery_info = await session_resume_manager.get_session_recovery_info(session_id)
        
        if not recovery_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return recovery_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recovery info for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recovery information"
        )


@router.get("/sessions/{session_id}/logs")
async def get_session_logs(
    session_id: str,
    format_type: str = Query("structured", pattern="^(structured|raw)$"),
    user_id: str = Depends(lambda: "current_user_id")  # TODO: Get from auth
):
    """
    Get deployment logs for a session
    
    Returns either structured log data or raw log content.
    """
    try:
        # TODO: Verify user owns this session
        
        if format_type == "structured":
            # Return structured log summary (for display in UI)
            # This would come from the deployment logger
            return {
                "session_id": session_id,
                "log_format": "structured",
                "message": "Structured logs would be returned here",
                "summary": {
                    "total_steps": 0,
                    "errors": 0,
                    "warnings": 0,
                    "duration_seconds": 0
                }
            }
        else:
            # Return raw logs or download URL
            download_url = await structured_logger.get_logs_download_url(session_id)
            
            if download_url:
                return {
                    "session_id": session_id,
                    "log_format": "raw",
                    "download_url": download_url,
                    "expires_at": "24 hours from now"  # TODO: Calculate actual expiry
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Logs not found for this session"
                )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get logs for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session logs"
        )


@router.get("/sessions/{session_id}/logs/download")
async def download_session_logs(
    session_id: str,
    user_id: str = Depends(lambda: "current_user_id")  # TODO: Get from auth
):
    """
    Get download URL for session logs
    
    Returns a presigned S3 URL for downloading the complete log file.
    """
    try:
        # TODO: Verify user owns this session
        
        download_url = await structured_logger.get_logs_download_url(session_id)
        
        if not download_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Logs not available for download"
            )
        
        return {
            "session_id": session_id,
            "download_url": download_url,
            "expires_in_seconds": 86400,  # 24 hours
            "file_format": "json_lines",
            "description": "Structured deployment logs in JSON Lines format"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate download URL for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )


@router.get("/user/quota")
async def get_user_quota_status(
    user_id: str = Depends(lambda: "current_user_id")  # TODO: Get from auth
):
    """
    Get current quota usage and limits for user
    
    Returns comprehensive quota information for all plan limits.
    """
    try:
        quota_status = await quota_manager.get_user_quota_status(user_id)
        
        if "error" in quota_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=quota_status["error"]
            )
        
        return quota_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quota status for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota information"
        )


@router.get("/user/quota/check")
async def check_deployment_quota(
    user_id: str = Depends(lambda: "current_user_id")  # TODO: Get from auth
):
    """
    Check if user can create a new deployment
    
    Validates against all quota limits before allowing deployment.
    """
    try:
        can_deploy, reason = await quota_manager.check_deployment_quota(user_id)
        
        return {
            "can_deploy": can_deploy,
            "reason": reason,
            "user_id": user_id,
            "timestamp": quota_manager._get_current_time().isoformat() if hasattr(quota_manager, '_get_current_time') else None
        }
        
    except Exception as e:
        logger.error(f"Failed to check deployment quota for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check quota"
        )


@router.post("/sessions/cleanup")
async def cleanup_abandoned_sessions(
    max_age_hours: int = Query(48, ge=1, le=168)  # 1 hour to 1 week
):
    """
    Clean up abandoned sessions (admin only)
    
    Marks old stuck sessions as failed and cleans up resources.
    """
    try:
        # TODO: Add admin authentication check
        
        await session_resume_manager.cleanup_abandoned_sessions(max_age_hours)
        
        return {
            "status": "success",
            "message": f"Cleaned up sessions older than {max_age_hours} hours",
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup abandoned sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup abandoned sessions"
        )
