"""
Job status routes for tracking background tasks
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
import logging

from ..utils.job_queue import job_queue, JobStatus
from dependencies.session import get_session_manager, SessionManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get status of a specific job
    
    Returns job details including status, progress, and any error information.
    """
    try:
        job = await job_queue.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return {
            "job_id": job.id,
            "job_type": job.job_type,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "priority": job.priority.value,
            "retry_count": job.retry_count,
            "max_retries": job.max_retries,
            "error_message": job.error_message,
            "data": job.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status"
        )


@router.get("/jobs")
async def list_jobs(
    job_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    List jobs with optional filtering
    
    Useful for monitoring and debugging background tasks.
    """
    try:
        # Validate status filter
        if status_filter:
            try:
                JobStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        jobs = await job_queue.list_jobs(
            job_type=job_type,
            status=JobStatus(status_filter) if status_filter else None,
            limit=limit,
            offset=offset
        )
        
        job_list = []
        for job in jobs:
            job_list.append({
                "job_id": job.id,
                "job_type": job.job_type,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "priority": job.priority.value,
                "retry_count": job.retry_count,
                "error_message": job.error_message
            })
        
        return {
            "jobs": job_list,
            "total_count": len(job_list),
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a pending or running job
    
    Note: Jobs that are already running may not be cancelled immediately.
    """
    try:
        job = await job_queue.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status: {job.status.value}"
            )
        
        # Update job status to cancelled
        await job_queue.update_job_status(job_id, JobStatus.CANCELLED)
        
        # If it's a deployment job, update the session status too
        if job.job_type == "deployment" and "session_id" in job.data:
            session_manager = await get_session_manager()
            await session_manager.update_session_status(
                job.data["session_id"],
                "cancelled",
                error_details="Job cancelled by user"
            )
        
        return {
            "status": "success",
            "message": "Job cancelled",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel job"
        )


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str):
    """
    Retry a failed job
    
    Requeues the job for processing if it has retries remaining.
    """
    try:
        job = await job_queue.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        if job.status != JobStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Can only retry failed jobs. Current status: {job.status.value}"
            )
        
        if job.retry_count >= job.max_retries:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job has exceeded maximum retry attempts"
            )
        
        # Retry the job
        await job_queue.retry_job(job_id)
        
        return {
            "status": "success",
            "message": "Job queued for retry",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry job"
        )


@router.get("/queue/stats")
async def get_queue_stats():
    """
    Get queue statistics
    
    Returns counts of jobs by status and type for monitoring.
    """
    try:
        stats = await job_queue.get_queue_stats()
        
        return {
            "queue_stats": stats,
            "timestamp": job_queue._get_current_time().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve queue statistics"
        )
