"""
Node.js LightSail Router - Simple & Reliable
Based on lessons learned from Python LightSail issues - uses simplified approach
"""

# Fix GitPython issue at the beginning
import os
os.environ['GIT_PYTHON_REFRESH'] = 'quiet'

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List, Union
import logging
import boto3
import json
import asyncio
import tempfile
import subprocess
from datetime import datetime
import uuid
from pathlib import Path
import git

logger = logging.getLogger(__name__)

router = APIRouter()

class NodeJSLightSailDeploymentRequest(BaseModel):
    repo_url: str
    deployment_id: str
    aws_access_key: str
    aws_secret_key: str
    region: str = "us-east-1"
    
    # Framework specification
    framework: Union[str, Dict[str, Any]] = "nodejs"
    
    # LightSail specific options
    instance_plan: str = "auto"
    container_service_name: Optional[str] = None
    domain_name: Optional[str] = None
    
    # Database options
    enable_database: bool = False
    database_plan: str = "micro_2_0"
    database_name: str = "appdb"
    
    # Application configuration
    environment_variables: Dict[str, str] = {}
    health_check_path: str = "/health"

class NodeJSLightSailDeploymentResult(BaseModel):
    success: bool
    deployment_id: str
    service_name: Optional[str] = None
    database_name: Optional[str] = None
    public_url: Optional[str] = None
    database_endpoint: Optional[str] = None
    deployment_logs: List[str] = []
    error_message: Optional[str] = None

class LightSailNodeJSDeploymentManager:
    """Simplified Node.js LightSail deployment - based on fixing Python issues"""
    
    def __init__(self, aws_access_key: str, aws_secret_key: str, region: str):
        self.lightsail_client = boto3.client(
            'lightsail',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        self.region = region

    async def deploy_nodejs_app(self, request: NodeJSLightSailDeploymentRequest) -> NodeJSLightSailDeploymentResult:
        """
        Deploy Node.js application to LightSail with simplified approach
        Fixes the complex command issues from Python deployment
        """
        logger.info(f"🚀 Starting simplified Node.js LightSail deployment: {request.deployment_id}")
        
        deployment_logs = []
        service_name = request.container_service_name or f"nodejs-app-{request.deployment_id[:8]}"
        
        try:
            # Step 1: Create Container Service (this works - reuse from Python)
            deployment_logs.append("📦 Creating LightSail Container Service...")
            container_service = await self._create_container_service(
                service_name, 
                request.instance_plan, 
                request.deployment_id
            )
            deployment_logs.append(f"✅ Container service created: {service_name}")
            
            # Step 2: Create Database (if requested - this also works)
            database_url = None
            database_endpoint = None
            if request.enable_database:
                deployment_logs.append("🗄️ Creating PostgreSQL database...")
                database_result = await self._create_database(
                    f"{service_name}-db",
                    request.database_plan,
                    request.deployment_id
                )
                database_endpoint = database_result.get("endpoint")
                database_url = f"postgresql://usertest{request.deployment_id[:4]}:password@{database_endpoint}:5432/{request.database_name}"
                deployment_logs.append(f"✅ Database created: {database_endpoint}")
            
            # Step 3: SIMPLIFIED Container Deployment (fix the Python issues)
            deployment_logs.append("🐳 Deploying container with simplified approach...")
            container_deployment = await self._deploy_simple_container(
                service_name,
                request,
                database_url,
                deployment_logs
            )
            
            deployment_logs.append("✅ Container deployment initiated")
            deployment_logs.append("⏳ Waiting for deployment to stabilize...")
            
            # Wait for deployment
            await asyncio.sleep(30)
            
            # Get service URL
            public_url = f"https://{service_name}.{self._get_lightsail_domain(self.region)}"
            
            return NodeJSLightSailDeploymentResult(
                success=True,
                deployment_id=request.deployment_id,
                service_name=service_name,
                public_url=public_url,
                database_endpoint=database_endpoint,
                deployment_logs=deployment_logs
            )
            
        except Exception as e:
            error_msg = f"Deployment failed: {str(e)}"
            logger.error(error_msg)
            deployment_logs.append(f"❌ {error_msg}")
            
            return NodeJSLightSailDeploymentResult(
                success=False,
                deployment_id=request.deployment_id,
                error_message=error_msg,
                deployment_logs=deployment_logs
            )

    async def _deploy_simple_container(self, service_name: str, request: NodeJSLightSailDeploymentRequest, database_url: Optional[str], logs: List[str]) -> Dict[str, Any]:
        """
        SIMPLIFIED container deployment - fixes Python LightSail issues
        Uses pre-built approach instead of complex git clone + build
        """
        logs.append("🔧 Using simplified container deployment approach...")
        
        # Simple container name
        container_name = "app"
        port = 3000
        
        # Simplified environment (no complex dynamic detection)
        env_vars = {
            "NODE_ENV": "production",
            "PORT": str(port)
        }
        
        # Add database URL if available
        if database_url:
            env_vars["DATABASE_URL"] = database_url
        
        # Add user environment variables
        env_vars.update(request.environment_variables)
        
        # SIMPLIFIED container spec - uses reliable base image + simple commands
        container_spec = {
            container_name: {
                "image": "public.ecr.aws/docker/library/node:18-alpine",
                "command": [
                    "sh", "-c",
                    # Simple, reliable commands
                    f"apk add --no-cache git && "
                    f"git clone {request.repo_url} /app && "
                    f"cd /app && "
                    f"npm ci && "
                    f"npm start"
                ],
                "environment": env_vars,
                "ports": {
                    str(port): "HTTP"
                }
            }
        }
        
        # Simple health check
        public_endpoint = {
            "containerName": container_name,
            "containerPort": port,
            "healthCheck": {
                "healthyThreshold": 2,
                "unhealthyThreshold": 3,
                "timeoutSeconds": 10,
                "intervalSeconds": 30,
                "path": request.health_check_path,
                "successCodes": "200"
            }
        }
        
        # Deploy container
        logs.append("📦 Creating container deployment...")
        response = self.lightsail_client.create_container_service_deployment(
            serviceName=service_name,
            containers=container_spec,
            publicEndpoint=public_endpoint
        )
        
        logs.append("✅ Container deployment created successfully")
        return response

    async def _create_container_service(self, service_name: str, instance_plan: str, deployment_id: str) -> Dict[str, Any]:
        """Create LightSail Container Service - reuse working code from Python"""
        logger.info(f"📦 Creating LightSail Container Service: {service_name}")
        
        # Plan mapping
        if instance_plan == "auto":
            plan = "nano"  # Start small
        else:
            plan = instance_plan
            
        try:
            response = self.lightsail_client.create_container_service(
                serviceName=service_name,
                power=plan,
                scale=1,
                tags=[
                    {"key": "deployment_id", "value": deployment_id},
                    {"key": "framework", "value": "nodejs"},
                    {"key": "managed_by", "value": "codeflowops"}
                ]
            )
            
            logger.info(f"✅ Container service created: {service_name}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to create container service: {e}")
            raise e

    async def _create_database(self, db_name: str, db_plan: str, deployment_id: str) -> Dict[str, Any]:
        """Create LightSail PostgreSQL database - reuse working code"""
        logger.info(f"🗄️ Creating PostgreSQL database: {db_name}")
        
        try:
            response = self.lightsail_client.create_relational_database(
                relationalDatabaseName=db_name,
                relationalDatabaseBlueprintId="postgres_13",
                relationalDatabaseBundleId=db_plan,
                masterDatabaseName="appdb",
                masterUsername=f"usertest{deployment_id[:4]}",
                masterUserPassword="StrongPassword123!",
                tags=[
                    {"key": "deployment_id", "value": deployment_id},
                    {"key": "framework", "value": "nodejs"},
                    {"key": "managed_by", "value": "codeflowops"}
                ]
            )
            
            # Wait for database to be available
            await asyncio.sleep(60)  # Databases take time
            
            # Get database details
            db_info = self.lightsail_client.get_relational_database(
                relationalDatabaseName=db_name
            )
            
            endpoint = db_info['relationalDatabase']['relationalDatabaseHardware']['endpoint']
            
            logger.info(f"✅ Database created: {endpoint}")
            return {"endpoint": endpoint, "response": response}
            
        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
            raise e

    def _get_lightsail_domain(self, region: str) -> str:
        """Get LightSail domain for region"""
        domain_map = {
            "us-east-1": "service.local",
            "us-west-2": "service.local", 
            "eu-west-1": "service.local"
        }
        return domain_map.get(region, "service.local")

# Router endpoints
@router.post("/deploy", response_model=NodeJSLightSailDeploymentResult)
async def deploy_nodejs_lightsail(request: NodeJSLightSailDeploymentRequest):
    """Deploy Node.js application to LightSail with simplified approach"""
    
    try:
        manager = LightSailNodeJSDeploymentManager(
            request.aws_access_key,
            request.aws_secret_key, 
            request.region
        )
        
        result = await manager.deploy_nodejs_app(request)
        return result
        
    except Exception as e:
        logger.error(f"❌ Node.js LightSail deployment failed: {e}")
        return NodeJSLightSailDeploymentResult(
            success=False,
            deployment_id=request.deployment_id,
            error_message=f"Deployment failed: {str(e)}",
            deployment_logs=[f"❌ Error: {str(e)}"]
        )

@router.get("/status/{deployment_id}")
async def get_deployment_status(deployment_id: str):
    """Get deployment status"""
    return {"deployment_id": deployment_id, "status": "Use AWS Console for detailed status"}
