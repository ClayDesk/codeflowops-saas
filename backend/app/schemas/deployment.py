"""
Pydantic schemas for deployment operations
"""

from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class RepositoryAnalysisRequest(BaseModel):
    repository_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "repository_url": "https://github.com/username/repository"
            }
        }


class InfrastructureRecommendation(BaseModel):
    compute: str  # "serverless" or "container"
    storage: List[str]
    networking: List[str]


class RepositoryAnalysisResponse(BaseModel):
    framework: str
    language: str
    dependencies: List[str]
    infrastructure: InfrastructureRecommendation
    deployment_strategy: str
    build_commands: List[str]
    environment_variables: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "framework": "Next.js",
                "language": "JavaScript",
                "dependencies": ["react", "next", "@types/react"],
                "infrastructure": {
                    "compute": "serverless",
                    "storage": ["S3"],
                    "networking": ["CloudFront"]
                },
                "deployment_strategy": "static_site",
                "build_commands": ["npm run build", "npm run export"],
                "environment_variables": ["NODE_ENV"]
            }
        }


class DeploymentConfig(BaseModel):
    environment: str = "production"
    auto_scaling: bool = True
    monitoring: bool = True
    custom_domain: Optional[str] = None
    environment_variables: Optional[Dict[str, str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "environment": "production",
                "auto_scaling": True,
                "monitoring": True,
                "custom_domain": "myapp.example.com",
                "environment_variables": {
                    "NODE_ENV": "production",
                    "API_URL": "https://api.example.com"
                }
            }
        }


class DeploymentCreate(BaseModel):
    repository_url: str
    credential_id: str
    analysis: Dict[str, Any]
    deployment_config: DeploymentConfig

    class Config:
        json_schema_extra = {
            "example": {
                "repository_url": "https://github.com/username/repository",
                "credential_id": "cred_123456789",
                "analysis": {
                    "framework": "Next.js",
                    "infrastructure": {
                        "compute": "serverless"
                    }
                },
                "deployment_config": {
                    "environment": "production",
                    "auto_scaling": True,
                    "monitoring": True
                }
            }
        }


class DeploymentResponse(BaseModel):
    deployment_id: str
    status: str
    repository_url: str
    deployment_url: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "deployment_id": "deploy_123456789",
                "status": "completed",
                "repository_url": "https://github.com/username/repository",
                "deployment_url": "https://d1234567890.cloudfront.net",
                "created_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:45:00Z"
            }
        }


class DeploymentStep(BaseModel):
    step: str
    status: str  # "pending", "running", "completed", "failed"
    message: str
    progress: int  # 0-100
    timestamp: str
    logs: List[str] = []

    class Config:
        json_schema_extra = {
            "example": {
                "step": "Infrastructure Provisioning",
                "status": "completed",
                "message": "AWS infrastructure provisioned successfully",
                "progress": 70,
                "timestamp": "2024-01-15T10:35:00Z",
                "logs": [
                    "Creating S3 bucket...",
                    "Configuring CloudFront distribution...",
                    "Setting up CodeBuild project..."
                ]
            }
        }


class DeploymentStatusResponse(BaseModel):
    deployment_id: str
    overall_status: str
    deployment_url: Optional[str] = None
    steps: List[DeploymentStep]

    class Config:
        json_schema_extra = {
            "example": {
                "deployment_id": "deploy_123456789",
                "overall_status": "completed",
                "deployment_url": "https://d1234567890.cloudfront.net",
                "steps": [
                    {
                        "step": "Repository Analysis",
                        "status": "completed",
                        "message": "Repository analysis completed successfully",
                        "progress": 25,
                        "timestamp": "2024-01-15T10:31:00Z",
                        "logs": []
                    },
                    {
                        "step": "Infrastructure Provisioning",
                        "status": "completed",
                        "message": "AWS infrastructure provisioned successfully",
                        "progress": 70,
                        "timestamp": "2024-01-15T10:35:00Z",
                        "logs": []
                    },
                    {
                        "step": "Application Deployment",
                        "status": "completed",
                        "message": "Application deployed successfully",
                        "progress": 100,
                        "timestamp": "2024-01-15T10:45:00Z",
                        "logs": []
                    }
                ]
            }
        }


# Enums for better type safety
class DeploymentStatus(str, Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class InfrastructureType(str, Enum):
    SERVERLESS = "serverless"
    CONTAINER = "container"
    STATIC = "static"
