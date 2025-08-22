"""
Analysis routes for repository processing
Handles GitHub repository analysis and project type detection
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from ..models.request_models import GitHubRepoInput, SessionQuery
from ..models.response_models import (
    AnalysisResponse, SessionInfo, ResponseStatus, 
    ErrorResponse, ErrorDetail
)
from dependencies.session import get_session_manager, SessionManager
from dependencies.rate_limiting import rate_limit_check
from background.analysis_tasks import start_analysis_task
from controllers.analysisController import AnalysisController
from ..utils.validators import validate_github_access

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_repository(
    request: GitHubRepoInput,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager),
    rate_limit: Dict[str, Any] = Depends(rate_limit_check)
):
    """
    Start repository analysis process
    
    Analyzes GitHub repository to determine project type, dependencies,
    and optimal deployment stack configuration.
    """
    try:
        logger.info(f"Starting analysis for session {request.session_id}")
        
        # Validate GitHub repository access
        github_validation = await validate_github_access(request.github_url)
        if not github_validation["accessible"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Repository not accessible: {github_validation['error']}"
            )
        
        # Check if session already exists and is in progress
        existing_session = await session_manager.get_session(request.session_id)
        if existing_session and existing_session.status in ["analyzing", "building", "deploying"]:
            if not request.force_reanalysis:
                return AnalysisResponse(
                    status=ResponseStatus.PENDING,
                    message="Analysis already in progress for this session",
                    session_id=request.session_id,
                    github_url=request.github_url
                )
        
        # Create or update session
        session_info = await session_manager.create_session(
            session_id=request.session_id,
            github_url=request.github_url,
            project_name=request.project_name,
            current_step="initializing"
        )
        
        # Start analysis in background
        background_tasks.add_task(
            start_analysis_task,
            request.session_id,
            request.github_url,
            request.project_name
        )
        
        # Send initial WebSocket update
        await session_manager.send_progress_update(
            request.session_id,
            step="analyzing",
            progress=5,
            message="Starting repository analysis..."
        )
        
        return AnalysisResponse(
            status=ResponseStatus.PENDING,
            message="Repository analysis started successfully",
            session_id=request.session_id,
            github_url=request.github_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis initiation failed for session {request.session_id}: {str(e)}")
        
        # Update session with error
        await session_manager.update_session_status(
            request.session_id,
            "failed",
            error_details=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start repository analysis"
        )


@router.get("/analysis/{session_id}", response_model=AnalysisResponse)
async def get_analysis_status(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
    include_logs: bool = False,
    include_metrics: bool = False
):
    """
    Get analysis status and results for a session
    
    Returns current analysis progress, results if completed,
    and optional logs and metrics.
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
        
        # Determine response status based on session state
        response_status = ResponseStatus.SUCCESS
        message = "Analysis completed successfully"
        
        if session_info.status == "failed":
            response_status = ResponseStatus.ERROR
            message = "Analysis failed"
        elif session_info.status in ["pending", "analyzing"]:
            response_status = ResponseStatus.PENDING
            message = "Analysis in progress"
        
        return AnalysisResponse(
            status=response_status,
            message=message,
            session_id=session_id,
            github_url=session_info.github_url,
            data=session_info.analysis_result,
            analysis_duration=session_info.metrics.get("analysis_duration") if session_info.metrics else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis status for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis status"
        )


@router.post("/analysis/{session_id}/retry")
async def retry_analysis(
    session_id: str,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager),
    rate_limit: Dict[str, Any] = Depends(rate_limit_check)
):
    """
    Retry failed analysis
    
    Restarts analysis process for a failed session with
    improved error handling and recovery mechanisms.
    """
    try:
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if session_info.status not in ["failed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot retry session with status: {session_info.status}"
            )
        
        # Reset session for retry
        await session_manager.update_session_status(
            session_id,
            "pending",
            current_step="retrying",
            progress_percentage=0
        )
        
        # Start retry analysis in background
        background_tasks.add_task(
            start_analysis_task,
            session_id,
            session_info.github_url,
            session_info.project_name,
            is_retry=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Analysis retry started successfully",
                "session_id": session_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry analysis for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry analysis"
        )


@router.delete("/analysis/{session_id}")
async def cancel_analysis(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Cancel ongoing analysis
    
    Stops analysis process and cleans up resources.
    """
    try:
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if session_info.status in ["completed", "failed", "cancelled"]:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "info",
                    "message": f"Session already in {session_info.status} state",
                    "session_id": session_id
                }
            )
        
        # Cancel analysis and cleanup
        await session_manager.cancel_session(session_id)
        
        # Send cancellation notification via WebSocket
        await session_manager.send_progress_update(
            session_id,
            step="cancelled",
            progress=0,
            message="Analysis cancelled by user"
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Analysis cancelled successfully",
                "session_id": session_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel analysis for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel analysis"
        )


@router.get("/analysis/{session_id}/logs")
async def get_analysis_logs(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
    level: str = "info",
    limit: int = 100
):
    """
    Get analysis logs for debugging
    
    Returns filtered logs for analysis troubleshooting.
    """
    try:
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        logs = await session_manager.get_session_logs(
            session_id,
            level=level,
            limit=limit,
            component="analysis"
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "session_id": session_id,
                "logs": logs,
                "total_count": len(logs),
                "level_filter": level,
                "limit": limit
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get logs for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis logs"
        )
