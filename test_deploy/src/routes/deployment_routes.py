"""
Deployment routes for AWS infrastructure provisioning
Handles complete deployment workflow with real-time updates
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any, List

from ..models.request_models import DeploymentInput, BuildConfiguration, StackConfiguration
from ..models.response_models import (
    DeploymentResponse, SessionInfo, ResponseStatus,
    BulkOperationResponse, BulkOperationResult
)
from dependencies.session import get_session_manager, SessionManager
from dependencies.rate_limiting import rate_limit_check
from background.deployment_tasks import start_deployment_task
from controllers.deploymentController import DeploymentController
from ..utils.validators import validate_aws_resources
from ..utils.job_queue import job_queue, JobPriority
from ..utils.deployment_locks import DeploymentLock

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/deploy", response_model=DeploymentResponse)
async def start_deployment(
    request: DeploymentInput,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager),
    rate_limit: Dict[str, Any] = Depends(rate_limit_check)
):
    """
    Start complete deployment process
    
    Deploys analyzed project to AWS using optimal infrastructure stack.
    Includes building (if needed), infrastructure provisioning, and file deployment.
    """
    try:
        logger.info(f"Starting deployment for session {request.session_id}")
        
        # Validate session exists and analysis is complete
        session_info = await session_manager.get_session(request.session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found. Please run analysis first."
            )
        
        if not session_info.analysis_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Analysis not completed. Cannot start deployment."
            )
        
        # Check if deployment is already in progress with locking
        async with DeploymentLock(request.session_id):
            # Re-check session status after acquiring lock
            session_info = await session_manager.get_session(request.session_id)
            if session_info.status in ["building", "deploying"]:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Deployment already in progress for this session"
                )
            
            # Validate AWS resources availability
            aws_validation = await validate_aws_resources(
                request.stack_type,
                request.project_name,
                session_info.analysis_result.project_type
            )
            if not aws_validation["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"AWS validation failed: {aws_validation['error']}"
                )
            
            # Update session for deployment
            await session_manager.update_session_status(
                request.session_id,
                "deploying",
                current_step="initializing_deployment",
                progress_percentage=0
            )
            
            # Queue deployment job with high priority
            job_id = await job_queue.add_job(
                "deployment",
                {
                    "session_id": request.session_id,
                    "deployment_config": request.dict(),
                    "task_type": "deploy"
                },
                priority=JobPriority.HIGH,
                retry_count=3
            )
            
            # Store job ID in session for tracking
            await session_manager.update_session_metadata(
                request.session_id,
                {"job_id": job_id}
            )
        
        # Send initial deployment update
        await session_manager.send_progress_update(
            request.session_id,
            step="deploying",
            progress=5,
            message="Deployment queued successfully..."
        )
        
        return DeploymentResponse(
            status=ResponseStatus.PENDING,
            message="Deployment started successfully",
            session_info=session_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deployment initiation failed for session {request.session_id}: {str(e)}")
        
        await session_manager.update_session_status(
            request.session_id,
            "failed",
            error_details=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start deployment"
        )


@router.get("/deployment/{session_id}", response_model=DeploymentResponse)
async def get_deployment_status(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
    include_logs: bool = False,
    include_metrics: bool = False
):
    """
    Get deployment status and results
    
    Returns current deployment progress, infrastructure details,
    and site URL when completed.
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
        
        # Determine response status
        response_status = ResponseStatus.SUCCESS
        message = "Deployment completed successfully"
        
        if session_info.status == "failed":
            response_status = ResponseStatus.ERROR
            message = "Deployment failed"
        elif session_info.status in ["pending", "building", "deploying"]:
            response_status = ResponseStatus.PENDING
            message = "Deployment in progress"
        
        return DeploymentResponse(
            status=response_status,
            message=message,
            session_info=session_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment status for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve deployment status"
        )


@router.post("/deployment/{session_id}/retry")
async def retry_deployment(
    session_id: str,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager),
    force_rebuild: bool = False,
    rate_limit: Dict[str, Any] = Depends(rate_limit_check)
):
    """
    Retry failed deployment
    
    Restarts deployment process with optional force rebuild.
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
                detail=f"Cannot retry deployment with status: {session_info.status}"
            )
        
        # Reset session for retry
        await session_manager.update_session_status(
            session_id,
            "pending",
            current_step="retrying_deployment",
            progress_percentage=0
        )
        
        # Start retry deployment
        background_tasks.add_task(
            start_deployment_task,
            session_id,
            session_info.dict(),
            is_retry=True,
            force_rebuild=force_rebuild
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Deployment retry started successfully",
                "session_id": session_id,
                "force_rebuild": force_rebuild
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry deployment for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry deployment"
        )


@router.delete("/deployment/{session_id}")
async def cancel_deployment(
    session_id: str,
    cleanup_resources: bool = True,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Cancel ongoing deployment
    
    Stops deployment and optionally cleans up AWS resources.
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
                    "message": f"Deployment already in {session_info.status} state",
                    "session_id": session_id
                }
            )
        
        # Cancel deployment with optional cleanup
        await session_manager.cancel_session(session_id, cleanup_resources)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Deployment cancelled successfully",
                "session_id": session_id,
                "cleanup_performed": cleanup_resources
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel deployment for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel deployment"
        )


@router.post("/build", response_model=DeploymentResponse)
async def build_project(
    session_id: str,
    build_config: BuildConfiguration,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager),
    rate_limit: Dict[str, Any] = Depends(rate_limit_check)
):
    """
    Build project independently
    
    Runs build process for React projects before deployment.
    """
    try:
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if not session_info.analysis_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Analysis not completed. Cannot start build."
            )
        
        if session_info.analysis_result.project_type != "react-app":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Build process only required for React applications"
            )
        
        # Start build process
        from background.deployment_tasks import start_build_task
        
        background_tasks.add_task(
            start_build_task,
            session_id,
            build_config.dict()
        )
        
        await session_manager.update_session_status(
            session_id,
            "building",
            current_step="building_project",
            progress_percentage=10
        )
        
        return DeploymentResponse(
            status=ResponseStatus.PENDING,
            message="Build process started successfully",
            session_info=session_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Build initiation failed for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start build process"
        )


@router.post("/infrastructure", response_model=DeploymentResponse)
async def provision_infrastructure(
    session_id: str,
    stack_config: StackConfiguration,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager),
    rate_limit: Dict[str, Any] = Depends(rate_limit_check)
):
    """
    Provision AWS infrastructure
    
    Creates AWS resources using Terraform based on project type.
    """
    try:
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Start infrastructure provisioning
        from background.deployment_tasks import start_infrastructure_task
        
        background_tasks.add_task(
            start_infrastructure_task,
            session_id,
            stack_config.dict()
        )
        
        await session_manager.update_session_status(
            session_id,
            "deploying",
            current_step="provisioning_infrastructure",
            progress_percentage=40
        )
        
        return DeploymentResponse(
            status=ResponseStatus.PENDING,
            message="Infrastructure provisioning started",
            session_info=session_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Infrastructure provisioning failed for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start infrastructure provisioning"
        )


@router.post("/finalize")
async def finalize_deployment(
    session_id: str,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Finalize deployment
    
    Completes deployment with final configurations and cleanup.
    """
    try:
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Start finalization
        from background.deployment_tasks import start_finalization_task
        
        background_tasks.add_task(
            start_finalization_task,
            session_id
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Deployment finalization started",
                "session_id": session_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deployment finalization failed for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to finalize deployment"
        )


@router.post("/destroy/{session_id}")
async def destroy_deployment(
    session_id: str,
    background_tasks: BackgroundTasks,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Destroy AWS resources for a deployed project
    
    Runs terraform destroy to clean up all AWS resources.
    """
    try:
        logger.info(f"Starting destroy process for session {session_id}")
        
        # Validate session exists
        session_info = await session_manager.get_session(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if not session_info.deployment_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No deployment found to destroy"
            )
        
        # Use deployment lock to prevent concurrent operations
        async with DeploymentLock(session_id):
            # Re-check session status after acquiring lock
            session_info = await session_manager.get_session(session_id)
            if session_info.status in ["building", "deploying", "destroying"]:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot destroy while operation is in progress"
                )
            
            # Update session status
            await session_manager.update_session_status(
                session_id,
                "destroying",
                current_step="initializing_destroy",
                progress_percentage=0
            )
            
            # Queue destroy job with high priority
            job_id = await job_queue.add_job(
                "deployment",
                {
                    "session_id": session_id,
                    "task_type": "destroy"
                },
                priority=JobPriority.HIGH,
                retry_count=2
            )
            
            # Store destroy job ID in session
            await session_manager.update_session_metadata(
                session_id,
                {"destroy_job_id": job_id}
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "Resource destruction started",
                "session_id": session_id,
                "job_id": job_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start destruction for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start resource destruction"
        )


@router.get("/projects")
async def list_projects(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    List all projects/deployments for the current user
    
    Returns summary of all user's deployment sessions with status.
    """
    try:
        # Get all sessions for current user (would need user auth context)
        # For now, return all sessions
        sessions = await session_manager.get_all_sessions()
        
        projects = []
        for session in sessions:
            if session.deployment_result:
                projects.append({
                    "session_id": session.session_id,
                    "project_name": session.analysis_result.get("project_name") if session.analysis_result else "Unknown",
                    "repository_url": session.analysis_result.get("repository_url") if session.analysis_result else None,
                    "status": session.status,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "deployment_url": session.deployment_result.get("primary_url") if session.deployment_result else None,
                    "framework": session.analysis_result.get("framework") if session.analysis_result else None
                })
        
        return {
            "status": "success",
            "projects": projects,
            "total_count": len(projects)
        }
        
    except Exception as e:
        logger.error(f"Failed to list projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )


@router.get("/quotas")
async def get_user_quotas():
    """
    Get user plan limits and current usage
    
    Returns quota information including deployments, builds, storage usage.
    """
    try:
        # This would integrate with user management and billing
        # For now, return sample quota data
        quotas = {
            "plan": "free",
            "limits": {
                "deployments_per_month": 10,
                "concurrent_deployments": 2,
                "storage_gb": 1,
                "build_minutes_per_month": 100
            },
            "usage": {
                "deployments_this_month": 3,
                "concurrent_deployments": 0,
                "storage_used_gb": 0.2,
                "build_minutes_used": 25
            },
            "percentages": {
                "deployments": 30,
                "storage": 20,
                "build_minutes": 25
            }
        }
        
        return {
            "status": "success",
            "quotas": quotas
        }
        
    except Exception as e:
        logger.error(f"Failed to get quotas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota information"
        )
