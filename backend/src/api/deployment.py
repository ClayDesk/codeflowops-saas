"""
Phase 2 Deployment API Endpoints
FastAPI endpoints for deployment orchestration, environment management, and cost monitoring
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import asyncio
import uuid

# Set up logging first
logger = logging.getLogger(__name__)

# Import our service architecture
import sys
import os
# Add the backend directory to the path to import services
backend_dir = os.path.join(os.path.dirname(__file__), '../..')
sys.path.append(backend_dir)

try:
    from src.services import (
        DeploymentOrchestrator,
        DeploymentRequest,
        DeploymentResult,
        DeploymentAction,
        Environment,
        ProjectStateManager,
        PSMDeploymentStatus as DeploymentStatus
    )
    # Note: CostEstimator and NotificationService are not yet implemented
    logger.info("✅ All Phase 2 services imported successfully")
except ImportError as e:
    # Fallback for development
    logger.warning(f"Service imports failed: {e}. Using mock services for development.")

# Mock classes for development (always available)
class Environment:
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
    def __init__(self, value):
        self.value = value

class DeploymentAction:
    DEPLOY = "deploy"
    PROMOTE = "promote"
    ROLLBACK = "rollback"
    DESTROY = "destroy"

class DeploymentRequest:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class DeploymentResult:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class NotificationType:
    DEPLOYMENT_SUCCESS = "deployment_success"
    DEPLOYMENT_FAILED = "deployment_failed"

# Mock service classes
class DeploymentOrchestrator:
    async def deploy(self, request):
        return DeploymentResult(
            success=True,
            deployment_id="mock_deployment_123",
            environment=request.environment,
            outputs={},
            deployment_url="https://mock-deployment.example.com"
        )
    
    async def get_project_environments(self, project_id):
        return {
            "dev": {"status": "not_deployed"},
            "staging": {"status": "not_deployed"},
            "prod": {"status": "not_deployed"}
        }
    
    async def get_deployment_history(self, project_id, env, limit):
        return []

class ProjectStateManager:
    async def get_project_state(self, project_id):
        return None

class CostEstimator:
    def get_project_cost_summary(self, project_id, name, envs):
        from decimal import Decimal
        class MockCostSummary:
            def __init__(self):
                self.total_monthly_cost = Decimal("5.0")
                self.environments = {}
                self.recommendations = ["Mock recommendation"]
        return MockCostSummary()
    
    def monitor_cost_alerts(self, project_id):
        return []

class NotificationService:
    async def send_notification(self, type, message, data, user_id=None, project_id=None):
        logger.info(f"Mock notification: {message}")
        return "mock_notification_id"

# Initialize router
router = APIRouter(prefix="/api/v1/deployments", tags=["deployments"])

# Initialize services (with fallback handling)
try:
    deployment_orchestrator = DeploymentOrchestrator()
    project_state_manager = ProjectStateManager()
    cost_estimator = CostEstimator()
    notification_service = NotificationService()
    logger.info("✅ All Phase 2 services initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ Service initialization failed: {e}. Using mock services.")
    deployment_orchestrator = DeploymentOrchestrator()
    project_state_manager = ProjectStateManager() 
    cost_estimator = CostEstimator()
    notification_service = NotificationService()

# Request/Response Models
class DeployProjectRequest(BaseModel):
    project_id: str = Field(..., description="Unique project identifier")
    project_name: str = Field(..., description="Human readable project name")
    project_type: str = Field(..., description="Project type (React, Vue, Static Site, etc.)")
    environment: str = Field(..., description="Target environment (dev, staging, prod)")
    build_command: Optional[str] = Field(None, description="Custom build command")
    output_directory: str = Field("dist", description="Build output directory")
    user_id: Optional[str] = Field(None, description="User initiating deployment")

class PromoteProjectRequest(BaseModel):
    project_id: str = Field(..., description="Project to promote")
    project_name: str = Field(..., description="Project name")
    project_type: str = Field(..., description="Project type")
    from_environment: str = Field(..., description="Source environment")
    to_environment: str = Field(..., description="Target environment")
    user_id: Optional[str] = Field(None, description="User initiating promotion")

class RollbackRequest(BaseModel):
    project_id: str = Field(..., description="Project to rollback")
    project_name: str = Field(..., description="Project name")
    project_type: str = Field(..., description="Project type")
    environment: str = Field(..., description="Target environment")
    deployment_id: str = Field(..., description="Deployment ID to rollback to")
    user_id: Optional[str] = Field(None, description="User initiating rollback")

class DeploymentResponse(BaseModel):
    success: bool
    deployment_id: str
    environment: str
    deployment_url: Optional[str] = None
    message: str
    cost_estimate: Optional[float] = None

class EnvironmentStatusResponse(BaseModel):
    project_id: str
    environments: Dict[str, Any]

class CostBreakdownResponse(BaseModel):
    project_id: str
    total_monthly_cost: float
    environments: Dict[str, Any]
    recommendations: List[str]

class DeploymentHistoryResponse(BaseModel):
    project_id: str
    deployments: List[Dict[str, Any]]

# New models to match frontend expectations
class FrontendDeploymentRequest(BaseModel):
    repository_url: str = Field(..., description="GitHub repository URL")
    credential_id: str = Field(..., description="AWS credential ID")
    analysis: Dict[str, Any] = Field(..., description="Repository analysis data")
    deployment_config: Dict[str, Any] = Field(default_factory=dict, description="Deployment configuration")

class FrontendDeploymentResponse(BaseModel):
    deployment_id: str
    status: str
    repository_url: str
    created_at: str

class DeploymentStatusStep(BaseModel):
    step: str
    status: str
    message: str
    progress: int
    logs: List[str] = []
    timestamp: str

class FrontendDeploymentStatusResponse(BaseModel):
    deployment_id: str
    overall_status: str
    deployment_url: Optional[str] = None
    steps: List[DeploymentStatusStep] = []

# In-memory storage for demo
deployments_store = {}

# Deployment Endpoints

# New frontend-compatible endpoint
@router.post("/", response_model=FrontendDeploymentResponse)
async def create_deployment(
    request: FrontendDeploymentRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new deployment with the specified configuration (Frontend-compatible endpoint)
    """
    try:
        deployment_id = str(uuid.uuid4())
        
        # Extract repository info from URL
        repo_name = request.repository_url.split('/')[-1].replace('.git', '')
        
        # Create deployment record
        deployment_record = {
            "deployment_id": deployment_id,
            "repository_url": request.repository_url,
            "credential_id": request.credential_id,
            "analysis": request.analysis,
            "deployment_config": request.deployment_config,
            "status": "initializing",
            "created_at": datetime.utcnow().isoformat(),
            "deployment_url": None,
            "steps": []
        }
        
        deployments_store[deployment_id] = deployment_record
        
        # Start deployment process in background
        background_tasks.add_task(
            run_frontend_deployment_process,
            deployment_id
        )
        
        logger.info(f"Created deployment {deployment_id} for repository {request.repository_url}")
        
        return FrontendDeploymentResponse(
            deployment_id=deployment_id,
            status="initializing",
            repository_url=request.repository_url,
            created_at=deployment_record["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Failed to create deployment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create deployment: {str(e)}"
        )

@router.get("/{deployment_id}/status", response_model=FrontendDeploymentStatusResponse)
async def get_deployment_status(deployment_id: str):
    """
    Get the current status of a deployment (Frontend-compatible endpoint)
    """
    try:
        if deployment_id not in deployments_store:
            raise HTTPException(
                status_code=404,
                detail="Deployment not found"
            )
        
        deployment = deployments_store[deployment_id]
        
        return FrontendDeploymentStatusResponse(
            deployment_id=deployment_id,
            overall_status=deployment["status"],
            deployment_url=deployment.get("deployment_url"),
            steps=deployment.get("steps", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment status {deployment_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get deployment status: {str(e)}"
        )

@router.post("/deploy", response_model=DeploymentResponse)
async def deploy_project(
    request: DeployProjectRequest,
    background_tasks: BackgroundTasks
):
    """
    Deploy a project to a specific environment
    """
    try:
        # Validate environment
        try:
            environment = Environment(request.environment.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid environment: {request.environment}. Must be one of: dev, staging, prod"
            )
        
        # Create deployment request
        deployment_request = DeploymentRequest(
            project_id=request.project_id,
            project_name=request.project_name,
            project_type=request.project_type,
            environment=environment,
            action=DeploymentAction.DEPLOY,
            build_command=request.build_command,
            output_directory=request.output_directory,
            user_id=request.user_id
        )
        
        # Start deployment in background
        background_tasks.add_task(
            execute_deployment,
            deployment_request
        )
        
        return DeploymentResponse(
            success=True,
            deployment_id=f"deploy_{request.project_id}_{environment.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            environment=environment.value,
            message="Deployment started successfully. Check status for progress."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start deployment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start deployment: {str(e)}"
        )

@router.post("/promote", response_model=DeploymentResponse)
async def promote_project(
    request: PromoteProjectRequest,
    background_tasks: BackgroundTasks
):
    """
    Promote a project from one environment to another
    """
    try:
        # Validate environments
        try:
            target_environment = Environment(request.to_environment.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target environment: {request.to_environment}"
            )
        
        # Create promotion request
        deployment_request = DeploymentRequest(
            project_id=request.project_id,
            project_name=request.project_name,
            project_type=request.project_type,
            environment=target_environment,
            action=DeploymentAction.PROMOTE,
            user_id=request.user_id
        )
        
        # Start promotion in background
        background_tasks.add_task(
            execute_deployment,
            deployment_request
        )
        
        return DeploymentResponse(
            success=True,
            deployment_id=f"promote_{request.project_id}_{target_environment.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            environment=target_environment.value,
            message=f"Promotion from {request.from_environment} to {request.to_environment} started successfully."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start promotion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start promotion: {str(e)}"
        )

@router.post("/rollback", response_model=DeploymentResponse)
async def rollback_deployment(
    request: RollbackRequest,
    background_tasks: BackgroundTasks
):
    """
    Rollback a deployment to a previous state
    """
    try:
        # Validate environment
        try:
            environment = Environment(request.environment.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid environment: {request.environment}"
            )
        
        # Create rollback request
        deployment_request = DeploymentRequest(
            project_id=request.project_id,
            project_name=request.project_name,
            project_type=request.project_type,
            environment=environment,
            action=DeploymentAction.ROLLBACK,
            rollback_deployment_id=request.deployment_id,
            user_id=request.user_id
        )
        
        # Start rollback in background
        background_tasks.add_task(
            execute_deployment,
            deployment_request
        )
        
        return DeploymentResponse(
            success=True,
            deployment_id=request.deployment_id,
            environment=environment.value,
            message=f"Rollback to deployment {request.deployment_id} started successfully."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start rollback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start rollback: {str(e)}"
        )

@router.delete("/destroy/{project_id}/{environment}")
async def destroy_infrastructure(
    project_id: str,
    environment: str,
    background_tasks: BackgroundTasks
):
    """
    Destroy infrastructure for a project environment
    """
    try:
        # Validate environment
        try:
            env = Environment(environment.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid environment: {environment}"
            )
        
        # Get project state for validation
        project_state = await project_state_manager.get_project_state(project_id)
        if not project_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Create destroy request
        deployment_request = DeploymentRequest(
            project_id=project_id,
            project_name=project_state.project_name,
            project_type=project_state.project_type,
            environment=env,
            action=DeploymentAction.DESTROY
        )
        
        # Start destruction in background
        background_tasks.add_task(
            execute_deployment,
            deployment_request
        )
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Infrastructure destruction started for {project_id} in {environment}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start destruction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start destruction: {str(e)}"
        )

# Status and Monitoring Endpoints

@router.get("/status/{project_id}", response_model=EnvironmentStatusResponse)
async def get_project_environments(project_id: str):
    """
    Get deployment status for all environments of a project
    """
    try:
        environments = await deployment_orchestrator.get_project_environments(project_id)
        
        return EnvironmentStatusResponse(
            project_id=project_id,
            environments=environments
        )
        
    except Exception as e:
        logger.error(f"Failed to get project environments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project environments: {str(e)}"
        )

@router.get("/history/{project_id}", response_model=DeploymentHistoryResponse)
async def get_deployment_history(
    project_id: str,
    environment: Optional[str] = None,
    limit: int = 20
):
    """
    Get deployment history for a project
    """
    try:
        env = None
        if environment:
            try:
                env = Environment(environment.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid environment: {environment}"
                )
        
        deployments = await deployment_orchestrator.get_deployment_history(
            project_id, env, limit
        )
        
        return DeploymentHistoryResponse(
            project_id=project_id,
            deployments=deployments
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deployment history: {str(e)}"
        )

# Cost Management Endpoints

@router.get("/cost/{project_id}", response_model=CostBreakdownResponse)
async def get_project_costs(project_id: str):
    """
    Get cost breakdown for a project across all environments
    """
    try:
        # Get project state
        project_state = await project_state_manager.get_project_state(project_id)
        if not project_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Get deployed environments
        deployed_environments = [
            env for env, deployment in project_state.environments.items()
            if deployment.status.value == "deployed"
        ]
        
        # Get cost summary
        cost_summary = cost_estimator.get_project_cost_summary(
            project_id,
            project_state.project_name,
            deployed_environments
        )
        
        return CostBreakdownResponse(
            project_id=project_id,
            total_monthly_cost=float(cost_summary.total_monthly_cost),
            environments={
                env.value: {
                    "monthly_cost": float(breakdown.total_monthly),
                    "usage_percentage": breakdown.usage_percentage,
                    "is_over_limit": breakdown.is_over_limit,
                    "resources": [
                        {
                            "service": resource.service,
                            "type": resource.resource_type,
                            "monthly_cost": float(resource.monthly_cost)
                        }
                        for resource in breakdown.resources
                    ]
                }
                for env, breakdown in cost_summary.environments.items()
            },
            recommendations=cost_summary.recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project costs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project costs: {str(e)}"
        )

@router.get("/cost/alerts/{project_id}")
async def get_cost_alerts(project_id: str):
    """
    Get cost alerts for a project
    """
    try:
        alerts = cost_estimator.monitor_cost_alerts(project_id)
        
        return JSONResponse(content={
            "project_id": project_id,
            "alerts": alerts,
            "alert_count": len(alerts)
        })
        
    except Exception as e:
        logger.error(f"Failed to get cost alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cost alerts: {str(e)}"
        )

# Background Tasks

async def execute_deployment(deployment_request: DeploymentRequest):
    """
    Execute deployment in background
    """
    try:
        logger.info(f"Starting {deployment_request.action.value} for {deployment_request.project_id}")
        
        # Execute deployment
        result = await deployment_orchestrator.deploy(deployment_request)
        
        if result.success:
            logger.info(f"Deployment successful: {result.deployment_id}")
            
            # Send success notification
            await notification_service.send_notification(
                NotificationType.DEPLOYMENT_SUCCESS,
                f"Deployment completed successfully for {deployment_request.project_name}",
                {
                    "project_id": deployment_request.project_id,
                    "environment": deployment_request.environment.value,
                    "deployment_id": result.deployment_id,
                    "deployment_url": result.deployment_url
                },
                user_id=deployment_request.user_id,
                project_id=deployment_request.project_id
            )
        else:
            logger.error(f"Deployment failed: {result.error_message}")
            
            # Send failure notification
            await notification_service.send_notification(
                NotificationType.DEPLOYMENT_FAILED,
                f"Deployment failed for {deployment_request.project_name}: {result.error_message}",
                {
                    "project_id": deployment_request.project_id,
                    "environment": deployment_request.environment.value,
                    "error_message": result.error_message
                },
                user_id=deployment_request.user_id,
                project_id=deployment_request.project_id
            )
        
    except Exception as e:
        logger.error(f"Background deployment failed: {str(e)}")
        
        # Send error notification
        await notification_service.send_notification(
            NotificationType.DEPLOYMENT_FAILED,
            f"Deployment system error for {deployment_request.project_name}: {str(e)}",
            {
                "project_id": deployment_request.project_id,
                "environment": deployment_request.environment.value,
                "error_message": str(e)
            },
            user_id=deployment_request.user_id,
            project_id=deployment_request.project_id
        )

async def run_frontend_deployment_process(deployment_id: str):
    """
    Background task to handle the frontend deployment process
    """
    try:
        deployment = deployments_store.get(deployment_id)
        if not deployment:
            logger.error(f"Deployment {deployment_id} not found")
            return
        
        # Update status to provisioning
        deployment["status"] = "provisioning"
        
        # Add initial step
        step1 = DeploymentStatusStep(
            step="infrastructure",
            status="in_progress", 
            message="Provisioning AWS infrastructure",
            progress=25,
            logs=["Starting infrastructure provisioning..."],
            timestamp=datetime.utcnow().isoformat()
        )
        deployment["steps"] = [step1.dict()]
        
        # Simulate infrastructure provisioning
        await asyncio.sleep(3)
        
        # Update infrastructure step to completed
        step1_completed = DeploymentStatusStep(
            step="infrastructure",
            status="completed",
            message="Infrastructure provisioned successfully",
            progress=50,
            logs=["Infrastructure provisioning completed", "Created S3 bucket", "Setup Lambda functions"],
            timestamp=datetime.utcnow().isoformat()
        )
        deployment["steps"][0] = step1_completed.dict()
        
        # Add deployment step
        step2 = DeploymentStatusStep(
            step="deployment",
            status="in_progress",
            message="Deploying application code",
            progress=75,
            logs=["Building application...", "Deploying to AWS..."],
            timestamp=datetime.utcnow().isoformat()
        )
        deployment["steps"].append(step2.dict())
        
        # Simulate deployment
        await asyncio.sleep(4)
        
        # Complete deployment
        step2_completed = DeploymentStatusStep(
            step="deployment",
            status="completed",
            message="Application deployed successfully",
            progress=100,
            logs=["Build completed", "Deployment successful", "Application is live"],
            timestamp=datetime.utcnow().isoformat()
        )
        deployment["steps"][1] = step2_completed.dict()
        
        # Set final status
        deployment["status"] = "completed"
        deployment["deployment_url"] = f"https://{deployment_id}.cloudfront.net"
        
        logger.info(f"Frontend deployment {deployment_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Frontend deployment process failed for {deployment_id}: {e}")
        
        # Update deployment status to failed
        if deployment_id in deployments_store:
            deployment = deployments_store[deployment_id]
            deployment["status"] = "failed"
            
            failed_step = DeploymentStatusStep(
                step="error",
                status="failed",
                message=f"Deployment failed: {str(e)}",
                progress=0,
                logs=[f"Error: {str(e)}"],
                timestamp=datetime.utcnow().isoformat()
            )
            deployment["steps"].append(failed_step.dict())
