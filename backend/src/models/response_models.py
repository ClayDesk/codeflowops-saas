"""
Pydantic models for API responses
Consistent response formatting with dynamic data
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class DeploymentStatus(str, Enum):
    PENDING = "pending"
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    ANALYSIS_COMPLETE = "analysis_complete"
    GENERATING = "generating"
    INFRASTRUCTURE_READY = "infrastructure_ready"
    CREATING_PIPELINE = "creating_pipeline"
    BUILDING = "building"
    DEPLOYING = "deploying"
    RUNNING = "running"
    READY = "ready"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectType(str, Enum):
    STATIC_SITE = "static-site"
    REACT_APP = "react-app"


class BaseResponse(BaseModel):
    """Base response model with consistent structure"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    status: ResponseStatus
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class AnalysisResult(BaseModel):
    """Repository analysis results"""
    project_type: ProjectType
    framework_version: Optional[str] = None
    build_command: str
    dependencies: Dict[str, str]
    package_manager: str
    has_build_script: bool
    estimated_build_time: int  # in seconds
    repository_size: int  # in bytes
    file_count: int
    supported_features: List[str]
    recommendations: List[str]
    potential_issues: List[str]


class AnalysisResponse(BaseResponse):
    """Response for repository analysis"""
    data: Optional[AnalysisResult] = None
    session_id: str
    github_url: str
    analysis_duration: Optional[float] = None  # in seconds


class BuildResult(BaseModel):
    """Build process results"""
    success: bool
    build_duration: float  # in seconds
    output_size: int  # in bytes
    build_command: str
    install_command: str
    artifacts_count: int
    build_logs: List[str]
    warnings: List[str]
    errors: List[str]


class InfrastructureResult(BaseModel):
    """Infrastructure provisioning results"""
    stack_id: str
    aws_region: str
    s3_bucket: str
    cloudfront_distribution: str
    cloudfront_domain: str
    codebuild_project: Optional[str] = None
    iam_roles: List[str]
    provisioning_duration: float  # in seconds
    terraform_outputs: Dict[str, Any]


class DeploymentResult(BaseModel):
    """Complete deployment results"""
    site_url: str
    cloudfront_url: str
    s3_bucket: str
    deployment_duration: float  # in seconds
    files_deployed: int
    total_size: int  # in bytes
    cache_invalidation_id: Optional[str] = None
    ssl_certificate: Optional[str] = None


class SessionInfo(BaseModel):
    """Session information and status"""
    session_id: str
    status: DeploymentStatus
    created_at: datetime
    updated_at: datetime
    github_url: str
    project_name: str
    project_type: Optional[ProjectType] = None
    current_step: str
    progress_percentage: int
    estimated_completion: Optional[datetime] = None
    
    # Optional detailed information
    analysis_result: Optional[AnalysisResult] = None
    build_result: Optional[BuildResult] = None
    infrastructure_result: Optional[InfrastructureResult] = None
    deployment_result: Optional[DeploymentResult] = None
    
    # Logs and metrics
    logs: Optional[List[str]] = None
    metrics: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DeploymentResponse(BaseResponse):
    """Response for deployment operations"""
    session_info: SessionInfo


class SessionListResponse(BaseResponse):
    """Response for session list queries"""
    sessions: List[SessionInfo]
    pagination: Dict[str, Any]
    total_count: int
    filters_applied: Dict[str, Any]


class StackInfo(BaseModel):
    """Infrastructure stack information"""
    stack_type: str
    name: str
    description: str
    aws_services: List[str]
    estimated_cost_monthly: float  # in USD
    setup_time_minutes: int
    features: List[str]
    use_cases: List[str]
    requirements: List[str]


class StackListResponse(BaseResponse):
    """Response for available stacks"""
    stacks: List[StackInfo]


class HealthStatus(BaseModel):
    """Health check status"""
    service: str
    status: str
    uptime: float  # in seconds
    version: str
    environment: str
    checks: Dict[str, Dict[str, Union[str, bool, float]]]
    dependencies: Dict[str, Dict[str, Union[str, bool]]]


class HealthResponse(BaseResponse):
    """Health check response"""
    health: HealthStatus


class ErrorDetail(BaseModel):
    """Detailed error information"""
    error_code: str
    error_type: str
    description: str
    context: Dict[str, Any]
    suggestions: List[str]
    retry_possible: bool
    support_contact: Optional[str] = None


class ErrorResponse(BaseResponse):
    """Error response with detailed information"""
    error: ErrorDetail
    session_id: Optional[str] = None


class ProgressUpdate(BaseModel):
    """Real-time progress update"""
    session_id: str
    step: str
    progress_percentage: int
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LogEntry(BaseModel):
    """Individual log entry"""
    timestamp: datetime
    level: str
    component: str
    message: str
    context: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricsData(BaseModel):
    """Performance metrics"""
    session_id: str
    total_duration: float  # in seconds
    analysis_duration: float
    build_duration: Optional[float] = None
    deployment_duration: float
    queue_time: float
    resource_usage: Dict[str, Any]
    cost_estimate: Optional[float] = None  # in USD


class BulkOperationResult(BaseModel):
    """Result of bulk operations"""
    operation: str
    total_requested: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    errors: List[str]


class BulkOperationResponse(BaseResponse):
    """Response for bulk operations"""
    result: BulkOperationResult


class QuotaInfo(BaseModel):
    """User quota information"""
    deployments_used: int
    deployments_limit: int
    storage_used: int  # in bytes
    storage_limit: int  # in bytes
    concurrent_sessions: int
    concurrent_limit: int
    reset_date: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemStats(BaseModel):
    """System-wide statistics"""
    active_sessions: int
    completed_deployments: int
    average_deployment_time: float  # in seconds
    success_rate: float  # percentage
    popular_project_types: Dict[str, int]
    average_queue_time: float  # in seconds
    system_load: Dict[str, float]


class SystemStatsResponse(BaseResponse):
    """System statistics response"""
    stats: SystemStats
    
    
# Response model for WebSocket messages
class WebSocketResponse(BaseModel):
    """WebSocket message response"""
    type: str
    session_id: str
    data: Union[ProgressUpdate, LogEntry, ErrorDetail, Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
