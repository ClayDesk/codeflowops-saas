"""
Pydantic models for API requests
Dynamic validation with configurable constraints
"""

from pydantic import BaseModel, validator, Field, ConfigDict
from typing import Optional, Dict, Any, List
import re
from datetime import datetime

from ..config.env import get_settings

settings = get_settings()


class GitHubRepoInput(BaseModel):
    """Input model for GitHub repository analysis"""
    session_id: str = Field(..., min_length=1, max_length=100)
    github_url: str = Field(..., min_length=1, max_length=500)
    project_name: Optional[str] = Field(None, min_length=1, max_length=100)
    force_reanalysis: Optional[bool] = False
    
    @validator('github_url')
    def validate_github_url(cls, v):
        github_pattern = r'^https://github\.com/[^/]+/[^/]+/?$'
        if not re.match(github_pattern, v):
            raise ValueError('Invalid GitHub repository URL format')
        return v.rstrip('/')
    
    @validator('project_name')
    def validate_project_name(cls, v):
        if v is not None:
            # Dynamic validation based on AWS naming constraints
            if not re.match(r'^[a-zA-Z0-9-]+$', v):
                raise ValueError('Project name must contain only letters, numbers, and hyphens')
            if len(v) > settings.MAX_PROJECT_NAME_LENGTH:
                raise ValueError(f'Project name must be less than {settings.MAX_PROJECT_NAME_LENGTH} characters')
        return v

    @validator('session_id')
    def validate_session_id(cls, v):
        # Validate session ID format
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid session ID format')
        return v


class DeploymentInput(BaseModel):
    """Input model for deployment requests"""
    session_id: str = Field(..., min_length=1, max_length=100)
    stack_type: str = Field(..., pattern=r'^(static-site|react-app)$')
    project_name: str = Field(..., min_length=1, max_length=100)
    environment: Optional[str] = Field('production', pattern=r'^(development|staging|production)$')
    custom_domain: Optional[str] = Field(None, max_length=253)
    environment_variables: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    @validator('custom_domain')
    def validate_custom_domain(cls, v):
        if v is not None:
            # Basic domain validation
            domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
            if not re.match(domain_pattern, v):
                raise ValueError('Invalid domain format')
        return v
    
    @validator('environment_variables')
    def validate_env_vars(cls, v):
        if v:
            # Limit number of environment variables
            if len(v) > settings.MAX_ENV_VARS:
                raise ValueError(f'Maximum {settings.MAX_ENV_VARS} environment variables allowed')
            
            # Validate env var names and values
            for key, value in v.items():
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                    raise ValueError(f'Invalid environment variable name: {key}')
                if len(value) > settings.MAX_ENV_VAR_LENGTH:
                    raise ValueError(f'Environment variable value too long: {key}')
        return v


class BuildConfiguration(BaseModel):
    """Build configuration for React projects"""
    build_command: Optional[str] = Field('npm run build')
    install_command: Optional[str] = Field('npm install')
    node_version: Optional[str] = Field(default="18.x")
    build_timeout: Optional[int] = Field(default=900)
    environment_variables: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    @validator('build_timeout')
    def validate_build_timeout(cls, v):
        if v < 60 or v > settings.MAX_BUILD_TIMEOUT:
            raise ValueError(f'Build timeout must be between 60 and {settings.MAX_BUILD_TIMEOUT} seconds')
        return v
    
    @validator('node_version')
    def validate_node_version(cls, v):
        # Validate Node.js version format
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError('Invalid Node.js version format (expected: x.y.z)')
        return v


class StackConfiguration(BaseModel):
    """Infrastructure stack configuration"""
    stack_type: str = Field(..., pattern=r'^(static-site|react-app)$')
    aws_region: Optional[str] = Field(default="us-east-1")
    cloudfront_price_class: Optional[str] = Field(default="PriceClass_100")
    enable_waf: Optional[bool] = Field(False)
    enable_logging: Optional[bool] = Field(True)
    cache_behavior: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('aws_region')
    def validate_aws_region(cls, v):
        # Validate AWS region format
        if not re.match(r'^[a-z]+-[a-z]+-\d+$', v):
            raise ValueError('Invalid AWS region format')
        return v
    
    @validator('cloudfront_price_class')
    def validate_price_class(cls, v):
        valid_classes = ['PriceClass_100', 'PriceClass_200', 'PriceClass_All']
        if v not in valid_classes:
            raise ValueError(f'Invalid price class. Must be one of: {valid_classes}')
        return v


class SessionQuery(BaseModel):
    """Query parameters for session operations"""
    session_id: str = Field(..., min_length=1, max_length=100)
    include_logs: Optional[bool] = Field(False)
    include_metrics: Optional[bool] = Field(False)


class BulkOperationInput(BaseModel):
    """Input for bulk operations on multiple sessions"""
    session_ids: List[str] = Field(..., min_items=1, max_items=10)
    operation: str = Field(..., pattern=r'^(cancel|retry|cleanup)$')
    force: Optional[bool] = Field(False)
    
    @validator('session_ids')
    def validate_session_ids(cls, v):
        for session_id in v:
            if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
                raise ValueError(f'Invalid session ID format: {session_id}')
        return v


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    type: str = Field(..., pattern=r'^(progress|error|success|log)$')
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints"""
    page: int = Field(1, ge=1, le=1000)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: Optional[str] = Field('created_at')
    sort_order: Optional[str] = Field('desc', pattern=r'^(asc|desc)$')


class FilterParams(BaseModel):
    """Filter parameters for session queries"""
    status: Optional[str] = Field(None, pattern=r'^(pending|analyzing|building|deploying|completed|failed|cancelled)$')
    project_type: Optional[str] = Field(None, pattern=r'^(static-site|react-app)$')
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    @validator('date_to')
    def validate_date_range(cls, v, values):
        if v and 'date_from' in values and values['date_from']:
            if v <= values['date_from']:
                raise ValueError('date_to must be after date_from')
        return v
