"""
Background analysis tasks for CodeFlowOps
Handles repository analysis in background processes
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from dependencies.session import get_session_manager
from controllers.analysisController import AnalysisController
from ..utils.validators import validate_github_access, get_repository_languages

logger = logging.getLogger(__name__)


async def start_analysis_task(
    session_id: str,
    github_url: str,
    project_name: Optional[str] = None,
    is_retry: bool = False
):
    """
    Background task to analyze GitHub repository
    
    Args:
        session_id: Session identifier
        github_url: GitHub repository URL
        project_name: Optional project name
        is_retry: Whether this is a retry attempt
    """
    session_manager = await get_session_manager()
    
    try:
        logger.info(f"Starting analysis task for session {session_id}")
        
        # Update session status
        await session_manager.update_session_status(
            session_id,
            "analyzing",
            current_step="validating_repository",
            progress_percentage=10
        )
        
        # Send progress update
        await session_manager.send_progress_update(
            session_id,
            step="validating_repository",
            progress=10,
            message="Validating GitHub repository access..."
        )
        
        # Validate repository access
        validation_result = await validate_github_access(github_url)
        if not validation_result["accessible"]:
            await _handle_analysis_error(
                session_manager,
                session_id,
                f"Repository validation failed: {validation_result['error']}",
                "validation_failed"
            )
            return
        
        # Update progress
        await session_manager.update_session_status(
            session_id,
            "analyzing",
            current_step="fetching_repository_info",
            progress_percentage=25
        )
        
        await session_manager.send_progress_update(
            session_id,
            step="fetching_repository_info",
            progress=25,
            message="Fetching repository information..."
        )
        
        # Get repository languages
        languages_result = await get_repository_languages(
            validation_result["owner"],
            validation_result["repo"]
        )
        
        # Initialize analysis controller
        analysis_controller = AnalysisController()
        
        # Update progress
        await session_manager.update_session_status(
            session_id,
            "analyzing",
            current_step="analyzing_project_structure",
            progress_percentage=50
        )
        
        await session_manager.send_progress_update(
            session_id,
            step="analyzing_project_structure",
            progress=50,
            message="Analyzing project structure and dependencies..."
        )
        
        # Perform repository analysis
        analysis_result = await analysis_controller.analyze_repository(
            github_url=github_url,
            session_id=session_id,
            validation_data=validation_result,
            languages_data=languages_result
        )
        
        if not analysis_result["success"]:
            await _handle_analysis_error(
                session_manager,
                session_id,
                f"Analysis failed: {analysis_result['error']}",
                "analysis_failed"
            )
            return
        
        # Update progress
        await session_manager.update_session_status(
            session_id,
            "analyzing",
            current_step="generating_deployment_config",
            progress_percentage=75
        )
        
        await session_manager.send_progress_update(
            session_id,
            step="generating_deployment_config",
            progress=75,
            message="Generating deployment configuration..."
        )
        
        # Generate deployment configuration
        deployment_config = await analysis_controller.generate_deployment_config(
            analysis_result["data"],
            session_id
        )
        
        # Complete analysis
        await session_manager.update_session_status(
            session_id,
            "analyzed",
            current_step="completed",
            progress_percentage=100
        )
        
        # Store analysis results in session
        session_data = await session_manager.get_session(session_id)
        if session_data:
            # Update session with analysis results
            analysis_data = {
                **analysis_result["data"],
                "deployment_config": deployment_config,
                "validation_info": validation_result,
                "languages_info": languages_result,
                "analysis_metadata": {
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "is_retry": is_retry,
                    "analyzer_version": "1.0.0"
                }
            }
            
            # Store in session (this would typically update the session storage)
            # For now, we'll send it via progress update
            await session_manager.send_progress_update(
                session_id,
                step="completed",
                progress=100,
                message="Repository analysis completed successfully",
                details=analysis_data
            )
        
        logger.info(f"Analysis completed successfully for session {session_id}")
        
    except Exception as e:
        logger.error(f"Analysis task failed for session {session_id}: {str(e)}")
        await _handle_analysis_error(
            session_manager,
            session_id,
            f"Unexpected error during analysis: {str(e)}",
            "internal_error"
        )


async def _handle_analysis_error(
    session_manager,
    session_id: str,
    error_message: str,
    error_type: str
):
    """
    Handle analysis errors and update session
    
    Args:
        session_manager: Session manager instance
        session_id: Session identifier
        error_message: Error description
        error_type: Type of error for categorization
    """
    try:
        # Update session with error
        await session_manager.update_session_status(
            session_id,
            "failed",
            current_step="error",
            error_details=error_message
        )
        
        # Send error notification
        await session_manager.send_progress_update(
            session_id,
            step="error",
            progress=0,
            message=f"Analysis failed: {error_message}",
            details={
                "error_type": error_type,
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.error(f"Analysis error for session {session_id}: {error_message}")
        
    except Exception as e:
        logger.error(f"Failed to handle analysis error for session {session_id}: {str(e)}")


async def retry_failed_analysis(session_id: str):
    """
    Retry analysis for a failed session
    
    Args:
        session_id: Session identifier
    """
    try:
        session_manager = await get_session_manager()
        session_data = await session_manager.get_session(session_id)
        
        if not session_data:
            logger.error(f"Session {session_id} not found for retry")
            return
        
        if session_data.status != "failed":
            logger.warning(f"Cannot retry session {session_id} with status: {session_data.status}")
            return
        
        logger.info(f"Retrying analysis for session {session_id}")
        
        # Start retry
        await start_analysis_task(
            session_id,
            session_data.github_url,
            session_data.project_name,
            is_retry=True
        )
        
    except Exception as e:
        logger.error(f"Failed to retry analysis for session {session_id}: {str(e)}")


async def cleanup_stale_analysis_sessions():
    """
    Clean up analysis sessions that have been running too long
    """
    try:
        session_manager = await get_session_manager()
        active_sessions = await session_manager.get_active_sessions()
        
        stale_sessions = []
        current_time = datetime.utcnow()
        
        for session in active_sessions:
            if session["status"] == "analyzing":
                created_at = datetime.fromisoformat(session["created_at"])
                duration = (current_time - created_at).total_seconds()
                
                # Consider sessions stale after 30 minutes
                if duration > 1800:  # 30 minutes
                    stale_sessions.append(session["session_id"])
        
        # Cancel stale sessions
        for session_id in stale_sessions:
            await session_manager.update_session_status(
                session_id,
                "failed",
                current_step="timeout",
                error_details="Analysis timed out"
            )
            
            await session_manager.send_progress_update(
                session_id,
                step="timeout",
                progress=0,
                message="Analysis timed out and was cancelled"
            )
        
        if stale_sessions:
            logger.info(f"Cleaned up {len(stale_sessions)} stale analysis sessions")
            
    except Exception as e:
        logger.error(f"Failed to cleanup stale analysis sessions: {str(e)}")


# Task scheduling functions

async def schedule_analysis_cleanup():
    """
    Schedule periodic cleanup of stale analysis sessions
    """
    while True:
        try:
            await cleanup_stale_analysis_sessions()
            # Sleep for 5 minutes
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Analysis cleanup scheduler error: {str(e)}")
            await asyncio.sleep(60)  # Retry after 1 minute on error


def start_analysis_cleanup_scheduler():
    """
    Start the analysis cleanup scheduler
    """
    try:
        asyncio.create_task(schedule_analysis_cleanup())
        logger.info("Analysis cleanup scheduler started")
    except Exception as e:
        logger.error(f"Failed to start analysis cleanup scheduler: {str(e)}")


# Analysis task registry for tracking

_analysis_tasks: Dict[str, asyncio.Task] = {}


async def register_analysis_task(session_id: str, task: asyncio.Task):
    """
    Register analysis task for tracking
    
    Args:
        session_id: Session identifier
        task: Analysis task
    """
    _analysis_tasks[session_id] = task


async def unregister_analysis_task(session_id: str):
    """
    Unregister completed analysis task
    
    Args:
        session_id: Session identifier
    """
    if session_id in _analysis_tasks:
        del _analysis_tasks[session_id]


async def cancel_analysis_task(session_id: str) -> bool:
    """
    Cancel running analysis task
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if task was cancelled
    """
    try:
        if session_id in _analysis_tasks:
            task = _analysis_tasks[session_id]
            if not task.done():
                task.cancel()
                await unregister_analysis_task(session_id)
                logger.info(f"Cancelled analysis task for session {session_id}")
                return True
        return False
    except Exception as e:
        logger.error(f"Failed to cancel analysis task for session {session_id}: {str(e)}")
        return False


async def get_active_analysis_tasks() -> Dict[str, Dict[str, Any]]:
    """
    Get information about active analysis tasks
    
    Returns:
        Dict mapping session IDs to task information
    """
    try:
        active_tasks = {}
        
        for session_id, task in _analysis_tasks.items():
            active_tasks[session_id] = {
                "done": task.done(),
                "cancelled": task.cancelled(),
                "exception": str(task.exception()) if task.done() and task.exception() else None
            }
        
        return active_tasks
        
    except Exception as e:
        logger.error(f"Failed to get active analysis tasks: {str(e)}")
        return {}
