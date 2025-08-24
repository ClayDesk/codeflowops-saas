"""
Core data models for the plugin architecture
"""
from pydantic import BaseModel, Field, ConfigDict
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

class AnalysisResult(BaseModel):
    """Result of repository analysis"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repo_url: str
    repo_dir: Path
    primary_lang: str
    framework: str
    findings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

class StackPlan(BaseModel):
    """Plan for building and deploying a specific stack"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    stack_key: str                 # "static", "react", "vue", etc.
    build_cmds: List[str]          # Commands to build the project
    output_dir: Path               # Where build artifacts are located
    env: Dict[str, str] = Field(default_factory=dict)  # Environment variables
    config: Dict[str, Any] = Field(default_factory=dict)  # Stack-specific config

class BuildResult(BaseModel):
    """Result of building a project"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    success: bool
    artifact_dir: Path
    logs_path: Optional[Path] = None
    build_time_seconds: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProvisionResult(BaseModel):
    """Result of provisioning AWS infrastructure"""
    success: bool
    outputs: Dict[str, Any] = Field(default_factory=dict)  # bucket, distro_id, urls...
    resource_ids: List[str] = Field(default_factory=list)  # For cleanup
    provision_time_seconds: float = 0.0
    error_message: Optional[str] = None
    
class DeployResult(BaseModel):
    """Final deployment result"""
    success: bool
    deployment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    live_url: str
    details: Dict[str, Any] = Field(default_factory=dict)
    deploy_time_seconds: float = 0.0
    error_message: Optional[str] = None
    deployment_logs: List[str] = Field(default_factory=list)

class DeploymentSession(BaseModel):
    """Complete deployment session tracking"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    analysis: AnalysisResult
    plan: Optional[StackPlan] = None
    build_result: Optional[BuildResult] = None
    provision_result: Optional[ProvisionResult] = None
    deploy_result: Optional[DeployResult] = None
    status: str = "created"  # created, analyzing, building, provisioning, deploying, completed, failed
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Request/Response models for API
class RepositoryAnalysisRequest(BaseModel):
    repository_url: str

class DeploymentRequest(BaseModel):
    repo_path: str
    aws_credentials: Dict[str, str]
    project_name: str = "project"
    config: Dict[str, Any] = Field(default_factory=dict)
    stack_override: Optional[str] = None  # Force specific stack

class CredentialValidationRequest(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"

# Response models
class AnalysisResponse(BaseModel):
    analysis_id: str
    framework: str
    language: str
    build_tool: str
    dependencies: List[str] = Field(default_factory=list)
    status: str
    deployment_time: str = "3-8 minutes"

class DeploymentResponse(BaseModel):
    deployment_id: str
    website_url: str
    s3_bucket: Optional[str] = None
    cloudfront_url: Optional[str] = None
    status: str

class CredentialValidationResponse(BaseModel):
    valid: bool
    permissions: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None

class StatusResponse(BaseModel):
    deployment_id: str
    status: str
    website_url: Optional[str] = None
    error_message: Optional[str] = None

class SessionState(BaseModel):
    """State tracking for deployment sessions"""
    deployment_id: str
    status: str = "created"  # created, detecting, building, provisioning, deploying, completed, failed
    current_step: str = "initialization"
    progress: int = 0  # 0-100
    logs: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
