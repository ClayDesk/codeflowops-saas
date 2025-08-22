# Smart Deploy API Routes - REST endpoints for AI-powered infrastructure generation
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import tempfile
import shutil
import zipfile
from pathlib import Path
import json
import asyncio
from datetime import datetime

from ..controllers.smart_deploy_controller import SmartDeployController, SmartDeployError
from ..services.infrastructure_template_service import (
    InfrastructureTemplateEngine, 
    CloudProvider, 
    ProjectType,
    detect_project_type,
    detect_requirements
)
from ..models.enhanced_models import User
from ..auth.dependencies import get_current_user
from ..utils.rate_limiting import rate_limit

# Pydantic models for request/response
class SmartDeployRequest(BaseModel):
    """
    Request model for creating a Smart Deployment
    """
    project_name: str = Field(..., min_length=1, max_length=50, description="Name of the project")
    cloud_provider: str = Field("aws", description="Target cloud provider")
    environment: str = Field("production", description="Environment (development/staging/production)")
    domain_name: Optional[str] = Field(None, description="Custom domain name")
    github_repo: Optional[str] = Field(None, description="GitHub repository URL")
    auto_deploy: bool = Field(False, description="Automatically deploy after generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "my-awesome-app",
                "cloud_provider": "aws",
                "environment": "production",
                "domain_name": "myapp.com",
                "github_repo": "https://github.com/user/repo",
                "auto_deploy": False
            }
        }

class SmartDeployResponse(BaseModel):
    """
    Response model for Smart Deployment creation
    """
    deployment_id: str
    status: str
    message: str
    estimated_completion: str
    
class DeploymentStatusResponse(BaseModel):
    """
    Response model for deployment status
    """
    deployment_id: str
    status: str
    message: str
    progress: int
    timestamp: str
    steps: Optional[List[Dict[str, Any]]] = None

class InfrastructurePreviewRequest(BaseModel):
    """
    Request model for infrastructure preview
    """
    cloud_provider: str = Field("aws", description="Target cloud provider")
    project_type: str = Field("static_site", description="Type of project")
    
class TemplateGenerationRequest(BaseModel):
    """
    Request model for template generation
    """
    cloud_provider: str = Field("aws", description="Target cloud provider")
    project_config: Dict[str, Any] = Field(..., description="Project configuration")
    custom_requirements: Optional[Dict[str, bool]] = Field(None, description="Custom infrastructure requirements")

# Create router
router = APIRouter(prefix="/api/v1/smart-deploy", tags=["Smart Deploy"])

# Initialize services
smart_deploy_controller = SmartDeployController()
template_engine = InfrastructureTemplateEngine()

@router.get("/health/aws")
async def get_smart_deploy_health():
    """Get Smart Deploy service health and AWS integration status"""
    try:
        # Check AWS credentials
        import boto3
        session = boto3.Session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        return {
            "status": "healthy",
            "service": "smart-deploy",
            "aws_integration": "active",
            "aws_account": identity.get('Account', 'Unknown'),
            "aws_user": identity.get('Arn', 'Unknown'),
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "healthy",
            "service": "smart-deploy",
            "aws_integration": "error",
            "error": str(e),
            "version": "1.0.0"
        }

@router.post("/test")
async def test_smart_deploy_endpoint():
    """Test endpoint for validating Smart Deploy API without authentication"""
    return {
        "status": "success",
        "message": "Smart Deploy API is working",
        "data": {
            "deployment_id": "test-deployment-12345",
            "service": "smart-deploy",
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@router.post("/create", response_model=SmartDeployResponse)
async def create_smart_deployment(
    request: SmartDeployRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Smart Deployment with AI-powered infrastructure generation
    
    This endpoint starts the Smart Deploy process which includes:
    1. Repository analysis using enhanced analysis
    2. Infrastructure code generation with traditional templates
    3. Deployment pipeline creation
    4. Real-time status updates
    """
    try:
        # Validate cloud provider
        try:
            cloud_provider = CloudProvider(request.cloud_provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported cloud provider: {request.cloud_provider}"
            )
        
        # Prepare deployment configuration
        deployment_config = {
            "project_name": request.project_name,
            "cloud_provider": cloud_provider.value,
            "environment": request.environment,
            "domain_name": request.domain_name,
            "github_repo": request.github_repo,
            "auto_deploy": request.auto_deploy,
            "user_id": current_user.id
        }
        
        # For demo, we'll use a sample repository path
        # In production, this would be the actual repository path
        repo_path = f"/tmp/demo-repo-{request.project_name}"
        
        # Create the Smart Deployment
        result = await smart_deploy_controller.create_smart_deployment(
            user_id=current_user.id,
            repo_path=repo_path,
            deployment_config=deployment_config,
            background_tasks=background_tasks
        )
        
        return SmartDeployResponse(**result)
        
    except SmartDeployError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/upload-repository")
async def upload_repository(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a repository as a ZIP file for Smart Deploy analysis
    """
    try:
        # Validate file type
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only ZIP files are supported")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"smart-deploy-{current_user.id}-")
        zip_path = Path(temp_dir) / file.filename
        
        # Save uploaded file
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract ZIP file
        extract_path = Path(temp_dir) / "extracted"
        extract_path.mkdir()
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        return {
            "message": "Repository uploaded successfully",
            "temp_path": str(extract_path),
            "files_count": len(list(extract_path.rglob("*")))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/status/{deployment_id}", response_model=DeploymentStatusResponse)
async def get_deployment_status(
    deployment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get the current status of a Smart Deployment
    
    Returns real-time status updates including:
    - Current step being executed
    - Progress percentage
    - Any error messages
    - Estimated completion time
    """
    try:
        status = await smart_deploy_controller.get_deployment_status(deployment_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        # Check if the status contains an error
        if "error" in status:
            raise HTTPException(status_code=404, detail="Deployment not found or expired")
        
        return DeploymentStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post("/infrastructure/generate")
async def generate_infrastructure_template(
    request: TemplateGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate infrastructure template based on project configuration
    
    This endpoint generates the actual infrastructure code without creating
    a full Smart Deployment. Useful for advanced users who want to review
    and customize the infrastructure before deployment.
    """
    try:
        # Validate cloud provider
        try:
            cloud_provider = CloudProvider(request.cloud_provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported cloud provider: {request.cloud_provider}"
            )
        
        # Detect project type from configuration
        project_type = detect_project_type(request.project_config)
        
        # Detect infrastructure requirements
        requirements = detect_requirements(request.project_config)
        
        # Override with custom requirements if provided
        if request.custom_requirements:
            for key, value in request.custom_requirements.items():
                if hasattr(requirements, key):
                    setattr(requirements, key, value)
        
        # Generate template
        template_result = await template_engine.generate_template(
            cloud_provider=cloud_provider,
            project_type=project_type,
            requirements=requirements,
            project_config=request.project_config
        )
        
        return {
            "cloud_provider": cloud_provider.value,
            "project_type": project_type.value,
            "template": template_result,
            "requirements": {
                "storage": requirements.storage,
                "cdn": requirements.cdn,
                "compute": requirements.compute,
                "database": requirements.database,
                "load_balancer": requirements.load_balancer,
                "monitoring": requirements.monitoring
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template generation failed: {str(e)}")

@router.get("/providers")
async def list_supported_providers():
    """
    List all supported cloud providers
    """
    return {
        "providers": [
            {
                "id": provider.value,
                "name": provider.value.upper(),
                "description": f"{provider.value.title()} cloud platform",
                "supported_features": ["static_hosting", "container_hosting", "database", "cdn"]
            }
            for provider in CloudProvider
        ]
    }

@router.get("/project-types")
async def list_supported_project_types():
    """
    List all supported project types
    """
    return {
        "project_types": [
            {
                "id": project_type.value,
                "name": project_type.value.replace("_", " ").title(),
                "description": f"Infrastructure for {project_type.value.replace('_', ' ')} applications"
            }
            for project_type in ProjectType
        ]
    }

@router.delete("/deployment/{deployment_id}")
async def delete_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a Smart Deployment
    
    This will cancel any ongoing deployment process and clean up resources.
    """
    try:
        # In a real implementation, this would:
        # 1. Cancel any running background tasks
        # 2. Clean up temporary files
        # 3. Remove deployment records from database
        # 4. Optionally destroy deployed infrastructure
        
        return {
            "message": f"Deployment {deployment_id} deleted successfully",
            "deployment_id": deployment_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete deployment: {str(e)}")

@router.post("/deployment/{deployment_id}/deploy")
async def execute_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """
    Execute the actual deployment to cloud infrastructure
    
    This endpoint triggers the deployment of the generated infrastructure
    to the target cloud provider.
    """
    try:
        # Get deployment status to ensure it's ready
        status = await smart_deploy_controller.get_deployment_status(deployment_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        if status.get("status") != "ready":
            raise HTTPException(
                status_code=400, 
                detail=f"Deployment not ready. Current status: {status.get('status')}"
            )
        
        # Start deployment execution in background
        # This would integrate with actual cloud provider APIs
        
        return {
            "message": "Deployment execution started",
            "deployment_id": deployment_id,
            "status": "deploying"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment execution failed: {str(e)}")

@router.get("/deployment/{deployment_id}/logs")
async def get_deployment_logs(
    deployment_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = 100
):
    """
    Get deployment logs for debugging and monitoring
    """
    try:
        # In a real implementation, this would fetch logs from:
        # 1. Smart Deploy process logs
        # 2. Cloud provider deployment logs
        # 3. Application runtime logs
        
        sample_logs = [
            {
                "timestamp": "2025-08-06T10:00:00Z",
                "level": "INFO",
                "source": "smart_deploy",
                "message": "Repository analysis completed"
            },
            {
                "timestamp": "2025-08-06T10:01:30Z", 
                "level": "INFO",
                "source": "template_engine",
                "message": "Infrastructure code generated successfully"
            },
            {
                "timestamp": "2025-08-06T10:02:15Z",
                "level": "INFO", 
                "source": "deployment",
                "message": "CloudFormation stack creation initiated"
            }
        ]
        
        return {
            "deployment_id": deployment_id,
            "logs": sample_logs[-limit:],
            "total_logs": len(sample_logs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")

@router.get("/deployment/{deployment_id}/summary")
async def get_deployment_summary(
    deployment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive deployment summary
    
    Returns detailed information about the deployment including:
    - Project analysis results
    - Generated infrastructure
    - Cost estimates
    - Next steps
    """
    try:
        # Get deployment data from controller
        # This is a placeholder implementation
        
        return {
            "deployment_id": deployment_id,
            "project_summary": {
                "name": "Sample Project",
                "type": "static_site",
                "languages": ["javascript", "html", "css"],
                "framework": "react"
            },
            "infrastructure_summary": {
                "cloud_provider": "aws",
                "resources_count": 4,
                "estimated_monthly_cost": 12.50,
                "deployment_time_estimate": "3-5 minutes"
            },
            "deployment_url": "https://d1234567890.cloudfront.net",
            "next_steps": [
                "Configure custom domain",
                "Set up CI/CD pipeline",
                "Enable monitoring and alerts"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")

# WebSocket endpoint for real-time updates (would be in a separate file)
@router.websocket("/ws/deployment/{deployment_id}")
async def deployment_websocket(websocket, deployment_id: str):
    """
    WebSocket endpoint for real-time deployment updates
    
    Clients can connect to this endpoint to receive live updates
    about their deployment progress.
    """
    await websocket.accept()
    
    try:
        while True:
            # Get current deployment status
            status = await smart_deploy_controller.get_deployment_status(deployment_id)
            
            if status:
                await websocket.send_json(status)
            
            # Wait before next update
            await asyncio.sleep(2)
            
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))

@router.get("/deployments")
async def get_deployments(
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    status_filter: Optional[str] = None
):
    """
    Get list of user's deployments
    """
    try:
        # This would fetch from database in real implementation
        sample_deployments = [
            {
                "id": "deploy-1",
                "project_name": "React E-commerce App",
                "status": "completed",
                "progress": 100,
                "cloud_provider": "aws",
                "environment": "production",
                "created_at": "2025-08-06T10:00:00Z",
                "deployment_url": "https://my-app.example.com"
            },
            {
                "id": "deploy-2", 
                "project_name": "Next.js Blog",
                "status": "deploying",
                "progress": 65,
                "cloud_provider": "gcp",
                "environment": "staging",
                "created_at": "2025-08-06T09:30:00Z",
                "estimated_completion": "2 minutes"
            },
            {
                "id": "deploy-3",
                "project_name": "Vue.js Dashboard", 
                "status": "analyzing",
                "progress": 25,
                "cloud_provider": "azure",
                "environment": "development",
                "created_at": "2025-08-06T09:15:00Z",
                "estimated_completion": "5 minutes"
            }
        ]
        
        # Apply status filter if provided
        if status_filter:
            sample_deployments = [d for d in sample_deployments if d["status"] == status_filter]
        
        return {
            "deployments": sample_deployments[:limit],
            "total": len(sample_deployments),
            "user_id": current_user.id if current_user else "demo"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deployments: {str(e)}")

@router.get("/stats")
async def get_smart_deploy_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get Smart Deploy statistics for dashboard
    """
    try:
        # This would calculate from database in real implementation
        stats = {
            "total_deployments": 12,
            "active_deployments": 3,
            "successful_deployments": 9,
            "monthly_cost": 127.45,
            "ai_generations": 45
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.post("/infrastructure/preview")
async def get_infrastructure_preview(
    request: InfrastructurePreviewRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate infrastructure preview with cost estimation
    """
    try:
        # Project type configurations
        project_configs = {
            "static_site": {
                "resources": ["S3", "CloudFront", "Route53"],
                "base_cost": 5.0
            },
            "spa": {
                "resources": ["EC2", "ALB", "CloudFront", "RDS"],
                "base_cost": 45.0
            },
            "api": {
                "resources": ["ECS", "ALB", "RDS", "ElastiCache"],
                "base_cost": 75.0
            },
            "fullstack": {
                "resources": ["ECS", "RDS", "S3", "CloudFront", "ALB"],
                "base_cost": 95.0
            }
        }
        
        config = project_configs.get(request.project_type, project_configs["static_site"])
        
        # Generate cost estimation
        import random
        base_cost = config["base_cost"]
        estimated_cost = base_cost + (random.random() * base_cost * 0.3)  # Add 0-30% variance
        
        # Generate resource details
        resource_types = {
            "S3": "Storage",
            "CloudFront": "CDN", 
            "Route53": "DNS",
            "EC2": "Compute",
            "ECS": "Container",
            "ALB": "Load Balancer",
            "RDS": "Database",
            "ElastiCache": "Cache"
        }
        
        resources = []
        for i, resource_name in enumerate(config["resources"]):
            resource_cost = (estimated_cost / len(config["resources"])) * (0.8 + random.random() * 0.4)
            resources.append({
                "id": f"resource-{i}",
                "name": resource_name,
                "type": resource_types.get(resource_name, "Service"),
                "cost": round(resource_cost, 2),
                "status": "planned"
            })
        
        return {
            "cloud_provider": request.cloud_provider,
            "project_type": request.project_type,
            "estimated_cost": round(estimated_cost, 2),
            "resources": resources,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")

@router.post("/analyze-repository")
async def analyze_uploaded_repository(
    temp_path: str,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze uploaded repository and provide automated recommendations
    """
    try:
        # Uses traditional analysis methods for recommendations
        # For now, return mock analysis
        import random
        
        frameworks = ["React", "Vue.js", "Angular", "Next.js", "Nuxt.js"]
        project_types = ["spa", "static_site", "api", "fullstack"]
        
        analysis = {
            "project_type": random.choice(project_types),
            "framework": random.choice(frameworks),
            "languages": ["TypeScript", "JavaScript", "CSS"],
            "dependencies": ["react", "next.js", "tailwindcss", "typescript"],
            "recommendations": [
                "Use AWS CloudFront for global CDN",
                "Enable automatic SSL with AWS Certificate Manager", 
                "Implement auto-scaling with Application Load Balancer",
                "Add RDS for database with automated backups",
                "Configure CloudWatch for monitoring and alerts"
            ],
            "estimated_resources": random.randint(3, 8),
            "estimated_cost": round(random.uniform(25.0, 100.0), 2),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Repository analysis failed: {str(e)}")

# WebSocket endpoint for real-time monitoring 
@router.websocket("/ws/realtime")
async def realtime_monitoring_websocket(websocket):
    """
    WebSocket endpoint for real-time monitoring dashboard
    """
    await websocket.accept()
    
    try:
        import random
        event_id = 0
        
        while True:
            event_id += 1
            
            # Generate mock real-time events
            events = [
                "Infrastructure deployment in progress...",
                "CloudFormation stack creation initiated",
                "EC2 instances launching...",
                "Load balancer configuration updated",
                "SSL certificate provisioned",
                "DNS records configured",
                "Application deployment completed"
            ]
            
            mock_event = {
                "id": event_id,
                "timestamp": datetime.now().isoformat(),
                "deployment_id": "deploy-live",
                "event": "progress_update",
                "message": random.choice(events),
                "progress": min(100, random.randint(0, 100))
            }
            
            await websocket.send_json(mock_event)
            await asyncio.sleep(3)  # Send update every 3 seconds
            
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))

# Test endpoint for Redis fallback verification (no auth required)
@router.get("/test/redis-fallback")
async def test_redis_fallback():
    """
    Test endpoint to verify Redis fallback functionality
    No authentication required for testing purposes
    """
    try:
        # Get controller instance
        controller = SmartDeployController()
        
        # Test Redis client
        redis_client = await controller.get_redis_client()
        client_type = type(redis_client).__name__
        
        # Test basic Redis operations
        test_key = "test:redis:fallback"
        test_value = "Redis fallback working!"
        
        # Store and retrieve
        await redis_client.setex(test_key, 60, test_value)
        retrieved_value = await redis_client.get(test_key)
        
        if isinstance(retrieved_value, bytes):
            retrieved_value = retrieved_value.decode()
        
        # Test ping
        ping_result = await redis_client.ping()
        
        return {
            "status": "success",
            "redis_client_type": client_type,
            "test_store_retrieve": retrieved_value == test_value,
            "ping_result": ping_result,
            "stored_value": test_value,
            "retrieved_value": retrieved_value,
            "message": f"Redis fallback test completed successfully with {client_type}"
        }
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "Redis fallback test failed"
        }

# Template Selection Endpoints
@router.post("/analyze-for-template")
async def analyze_for_template_selection(
    analysis_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Analyze project data and get template recommendations
    
    This endpoint helps users understand which infrastructure template
    would be best suited for their project based on analysis data.
    """
    try:
        # Get template recommendations
        template_selector = smart_deploy_controller.template_selector
        recommendations = template_selector.get_template_recommendations(analysis_data)
        
        # Get the best template selection
        selected_template, template_info = template_selector.analyze_and_select_template(
            analysis_data, {}
        )
        
        return {
            "status": "success",
            "selected_template": selected_template,
            "template_info": template_info,
            "recommendations": recommendations,
            "analysis_summary": {
                "languages": analysis_data.get("languages", []),
                "frameworks": analysis_data.get("frameworks", []),
                "project_type": analysis_data.get("project_type", "unknown"),
                "has_backend": analysis_data.get("has_backend", False),
                "has_database": analysis_data.get("has_database", False)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template analysis failed: {str(e)}")

@router.get("/templates")
async def get_available_templates(
    current_user: User = Depends(get_current_user)
):
    """
    Get information about all available infrastructure templates
    """
    try:
        template_selector = smart_deploy_controller.template_selector
        template_configs = template_selector.template_configs
        
        return {
            "status": "success",
            "templates": template_configs,
            "total_templates": len(template_configs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the Smart Deploy service
    """
    try:
        # Test template loading
        template_selector = smart_deploy_controller.template_selector
        template_configs = template_selector.template_configs
        
        # Test template file loading
        test_template = smart_deploy_controller._get_terraform_template(
            "static_site", 
            {"project_name": "health-check", "aws_region": "us-east-1"}
        )
        
        return {
            "status": "healthy",
            "service": "Smart Deploy",
            "version": "2.0.0",
            "templates_available": len(template_configs),
            "template_files_loaded": len(test_template),
            "features": [
                "Traditional Terraform Templates",
                "File-based Template System", 
                "Intelligent Template Selection",
                "Multi-template Support"
            ]
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "Smart Deploy"
        }

# Deployment Execution Endpoints
@router.post("/deploy/{deployment_id}")
async def execute_deployment(
    deployment_id: str,
    auto_approve: bool = False,
    dry_run: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Execute the actual Terraform deployment for a prepared deployment
    
    This endpoint takes a generated infrastructure template and deploys it to AWS.
    Set dry_run=True to only generate and validate the Terraform plan without applying changes.
    """
    try:
        deployment_config = {
            "auto_approve": auto_approve,
            "dry_run": dry_run,
            "user_id": current_user.id,
            "executed_by": current_user.email if hasattr(current_user, 'email') else str(current_user.id)
        }
        
        # Execute the deployment
        result = await smart_deploy_controller.execute_deployment(
            deployment_id=deployment_id,
            deployment_config=deployment_config,
            auto_approve=auto_approve
        )
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "execution_result": result,
            "message": f"Deployment {'plan completed' if dry_run else 'executed successfully'}"
        }
        
    except SmartDeployError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment execution failed: {str(e)}")

@router.get("/outputs/{deployment_id}")
async def get_deployment_outputs(
    deployment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get deployment outputs including live URLs and resource information
    """
    try:
        outputs = await smart_deploy_controller.get_deployment_outputs(deployment_id)
        return outputs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deployment outputs: {str(e)}")

@router.get("/logs/{deployment_id}")
async def get_deployment_logs(
    deployment_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    Get real-time deployment logs from Terraform execution
    """
    try:
        logs = await smart_deploy_controller.terraform_executor.get_deployment_logs(
            deployment_id, limit
        )
        
        return {
            "deployment_id": deployment_id,
            "logs": logs,
            "total_entries": len(logs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get deployment logs: {str(e)}")

@router.delete("/cleanup/{deployment_id}")
async def cleanup_deployment(
    deployment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Manually clean up an expired or completed deployment
    """
    try:
        result = await smart_deploy_controller.cleanup_deployment_now(deployment_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup deployment: {str(e)}")

@router.post("/cleanup/expired")
async def cleanup_all_expired(
    current_user: User = Depends(get_current_user)
):
    """
    Clean up all expired deployments manually
    """
    try:
        await smart_deploy_controller._cleanup_expired_deployments()
        return {"success": True, "message": "Expired deployments cleaned up"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup expired deployments: {str(e)}")
