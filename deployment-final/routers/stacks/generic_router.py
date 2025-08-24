"""
Generic Stack Router
Fallback router for unsupported or generic stack types
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class GenericDeploymentRequest(BaseModel):
    session_id: str
    project_name: str
    repo_url: str
    stack_type: str
    branch: Optional[str] = "main"
    aws_region: Optional[str] = "us-east-1"

@router.post("/deploy")
async def deploy_generic_stack(
    request: GenericDeploymentRequest,
    background_tasks: BackgroundTasks
):
    """Generic deployment handler"""
    logger.info(f"🚀 Generic deployment for stack: {request.stack_type}")
    
    return {
        "success": False,
        "status": "unsupported",
        "message": f"Stack type '{request.stack_type}' is not yet supported. Please use a supported stack type.",
        "supported_stacks": ["static", "nextjs", "react", "python", "php"]
    }

@router.get("/status/{deployment_id}")
async def get_generic_deployment_status(deployment_id: str):
    """Get status for generic deployment"""
    return {
        "deployment_id": deployment_id,
        "status": "unsupported",
        "message": "Generic deployments are not supported"
    }
