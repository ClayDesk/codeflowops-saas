"""
Session management routes
Handles session lifecycle, status tracking, and bulk operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.request_models import (
    SessionQuery, BulkOperationInput, PaginationParams, FilterParams
)
from ..models.response_models import (
    SessionListResponse, ResponseStatus, SessionInfo,
    BulkOperationResponse, BulkOperationResult, MetricsData, QuotaInfo
)
from dependencies.session import get_session_manager, SessionManager
from dependencies.rate_limiting import rate_limit_check
from ..utils.formatters import format_session_list

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    session_manager: SessionManager = Depends(get_session_manager),
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends(),
    rate_limit: Dict[str, Any] = Depends(rate_limit_check)
):
    """
    List sessions with filtering and pagination
    
    Returns paginated list of sessions with optional filtering
    by status, project type, and date range.
    """
    try:
        logger.info(f"Listing sessions with filters: {filters.dict()}")
        
        # Get filtered sessions
        sessions, total_count = await session_manager.list_sessions(
            page=pagination.page,
            page_size=pagination.page_size,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
            status_filter=filters.status,
            project_type_filter=filters.project_type,
            date_from=filters.date_from,
            date_to=filters.date_to
        )
        
        # Format pagination info
        pagination_info = {
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total_count": total_count,
            "total_pages": (total_count + pagination.page_size - 1) // pagination.page_size,
            "has_next": pagination.page * pagination.page_size < total_count,
            "has_previous": pagination.page > 1
        }
        
        return SessionListResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Retrieved {len(sessions)} sessions",
            sessions=sessions,
            pagination=pagination_info,
            total_count=total_count,
            filters_applied=filters.dict(exclude_none=True)
        )
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
    include_logs: bool = Query(False, description="Include session logs"),
    include_metrics: bool = Query(False, description="Include performance metrics")
):
    """
    Get detailed session information
    
    Returns complete session details including analysis results,
    deployment status, and optional logs and metrics.
    """
    try:
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Include additional data if requested
        if include_logs:
            session_info.logs = await session_manager.get_session_logs(session_id)
        
        if include_metrics:
            session_info.metrics = await session_manager.get_session_metrics(session_id)
        
        return session_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session information"
        )


@router.put("/session/{session_id}/status")
async def update_session_status(
    session_id: str,
    new_status: str,
    session_manager: SessionManager = Depends(get_session_manager),
    current_step: Optional[str] = None,
    progress_percentage: Optional[int] = None,
    error_details: Optional[str] = None
):
    """
    Update session status
    
    Manually update session status and progress.
    Used for administrative operations and error recovery.
    """
    try:
        # Validate status
        valid_statuses = ["pending", "analyzing", "building", "deploying", "completed", "failed", "cancelled"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )
        
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Update session
        await session_manager.update_session_status(
            session_id=session_id,
            status=new_status,
            current_step=current_step,
            progress_percentage=progress_percentage,
            error_details=error_details
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"Session status updated to {new_status}",
                "session_id": session_id,
                "new_status": new_status
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session {session_id} status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session status"
        )


@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
    cleanup_resources: bool = Query(True, description="Clean up AWS resources"),
    force: bool = Query(False, description="Force deletion even if active")
):
    """
    Delete session and associated resources
    
    Removes session data and optionally cleans up AWS resources.
    """
    try:
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if session is active
        if session_info.status in ["analyzing", "building", "deploying"] and not force:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete active session. Use force=true to override."
            )
        
        # Delete session
        await session_manager.delete_session(
            session_id=session_id,
            cleanup_resources=cleanup_resources
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Session deleted successfully",
                "session_id": session_id,
                "cleanup_performed": cleanup_resources
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )


@router.post("/sessions/bulk", response_model=BulkOperationResponse)
async def bulk_session_operations(
    request: BulkOperationInput,
    session_manager: SessionManager = Depends(get_session_manager),
    rate_limit: Dict[str, Any] = Depends(rate_limit_check)
):
    """
    Perform bulk operations on multiple sessions
    
    Supports cancel, retry, and cleanup operations on multiple sessions.
    """
    try:
        logger.info(f"Performing bulk {request.operation} on {len(request.session_ids)} sessions")
        
        results = []
        successful = 0
        failed = 0
        errors = []
        
        for session_id in request.session_ids:
            try:
                if request.operation == "cancel":
                    await session_manager.cancel_session(session_id)
                    results.append({"session_id": session_id, "status": "cancelled"})
                    successful += 1
                    
                elif request.operation == "retry":
                    # Check if session can be retried
                    session_info = await session_manager.get_session(session_id)
                    if session_info and session_info.status in ["failed", "cancelled"]:
                        await session_manager.update_session_status(session_id, "pending")
                        results.append({"session_id": session_id, "status": "retry_queued"})
                        successful += 1
                    else:
                        results.append({"session_id": session_id, "status": "cannot_retry"})
                        failed += 1
                        
                elif request.operation == "cleanup":
                    await session_manager.cleanup_session_resources(session_id)
                    results.append({"session_id": session_id, "status": "cleaned"})
                    successful += 1
                    
            except Exception as e:
                error_msg = f"Failed {request.operation} for {session_id}: {str(e)}"
                errors.append(error_msg)
                results.append({"session_id": session_id, "status": "error", "error": str(e)})
                failed += 1
        
        bulk_result = BulkOperationResult(
            operation=request.operation,
            total_requested=len(request.session_ids),
            successful=successful,
            failed=failed,
            results=results,
            errors=errors
        )
        
        return BulkOperationResponse(
            status=ResponseStatus.SUCCESS if failed == 0 else ResponseStatus.ERROR,
            message=f"Bulk {request.operation} completed. {successful} successful, {failed} failed.",
            result=bulk_result
        )
        
    except Exception as e:
        logger.error(f"Bulk operation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk operation"
        )


@router.get("/session/{session_id}/metrics", response_model=MetricsData)
async def get_session_metrics(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get detailed performance metrics for a session
    
    Returns timing, resource usage, and cost information.
    """
    try:
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        metrics = await session_manager.get_session_metrics(session_id)
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metrics not available for this session"
            )
        
        return MetricsData(**metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session metrics"
        )


@router.get("/sessions/active")
async def get_active_sessions(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get currently active sessions
    
    Returns all sessions that are currently processing.
    """
    try:
        active_sessions = await session_manager.get_active_sessions()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": f"Retrieved {len(active_sessions)} active sessions",
                "active_sessions": active_sessions,
                "count": len(active_sessions)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get active sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active sessions"
        )


@router.get("/quota")
async def get_quota_info(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get current usage quota information
    
    Returns usage limits and current consumption.
    """
    try:
        quota_info = await session_manager.get_quota_info()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "quota": quota_info
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get quota info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota information"
        )
