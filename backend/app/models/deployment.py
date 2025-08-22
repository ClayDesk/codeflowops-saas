"""
Database models for deployment operations - Simplified for development
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Deployment:
    """Deployment model"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    repository_url: str = ""
    credential_id: str = ""
    tenant_id: str = ""
    created_by: str = ""
    
    # Deployment status and metadata
    status: str = "initializing"  # initializing, running, completed, failed, cancelled
    deployment_url: Optional[str] = None
    error_message: Optional[str] = None
    
    # Configuration and analysis data
    analysis_data: Optional[Dict[str, Any]] = None
    deployment_config: Optional[Dict[str, Any]] = None
    infrastructure_config: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<Deployment(id={self.id}, status={self.status}, repository={self.repository_url})>"


@dataclass
class DeploymentStatus:
    """Deployment status tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deployment_id: str = ""
    
    # Status information
    step: str = ""  # e.g., "Repository Analysis", "Infrastructure Provisioning"
    status: str = ""  # pending, running, completed, failed
    message: str = ""
    progress: int = 0  # 0-100 percentage
    
    # Logs and details
    logs: Optional[List[str]] = None
    details: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<DeploymentStatus(id={self.id}, step={self.step}, status={self.status})>"


@dataclass
class DeploymentResource:
    """AWS Resource tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deployment_id: str = ""
    
    # AWS Resource information
    resource_type: str = ""  # e.g., "S3_BUCKET", "CLOUDFRONT_DISTRIBUTION"
    resource_id: str = ""    # AWS resource ID/ARN
    resource_name: Optional[str] = None   # Human-readable name
    aws_region: Optional[str] = None
    
    # Resource configuration
    configuration: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None
    
    # Resource status
    status: str = "creating"  # creating, active, updating, deleting, deleted, failed
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<DeploymentResource(id={self.id}, type={self.resource_type}, resource_id={self.resource_id})>"


@dataclass
class DeploymentLog:
    """Deployment logging"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    deployment_id: str = ""
    
    # Log information
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message: str = ""
    source: Optional[str] = None  # e.g., "terraform", "codebuild", "powershell"
    
    # Additional context
    context: Optional[Dict[str, Any]] = None
    
    # Timestamp
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<DeploymentLog(id={self.id}, level={self.level}, message={self.message[:50]}...)>"


# Simple in-memory storage for development
# In production, this would be replaced with proper database operations
_deployments: Dict[str, Deployment] = {}
_deployment_statuses: Dict[str, List[DeploymentStatus]] = {}
_deployment_resources: Dict[str, List[DeploymentResource]] = {}
_deployment_logs: Dict[str, List[DeploymentLog]] = {}


class MockQuery:
    """Mock query object for development"""
    def __init__(self, model_class, storage_dict):
        self.model_class = model_class
        self.storage = storage_dict
        self._filters = []
    
    def filter(self, *args, **kwargs):
        # In a real implementation, this would apply filters
        return self
    
    def order_by(self, *args, **kwargs):
        return self
    
    def offset(self, offset):
        return self
    
    def limit(self, limit):
        return self
    
    def first(self):
        # Return first item or None
        items = list(self.storage.values())
        return items[0] if items else None
    
    def all(self):
        # Return all items
        return list(self.storage.values())


class MockDB:
    """Mock database session for development"""
    def query(self, model_class):
        if model_class == Deployment:
            return MockQuery(model_class, _deployments)
        elif model_class == DeploymentStatus:
            return MockQuery(model_class, _deployment_statuses)
        elif model_class == DeploymentResource:
            return MockQuery(model_class, _deployment_resources)
        elif model_class == DeploymentLog:
            return MockQuery(model_class, _deployment_logs)
        return MockQuery(model_class, {})
    
    def add(self, obj):
        if isinstance(obj, Deployment):
            _deployments[obj.id] = obj
        elif isinstance(obj, DeploymentStatus):
            if obj.deployment_id not in _deployment_statuses:
                _deployment_statuses[obj.deployment_id] = []
            _deployment_statuses[obj.deployment_id].append(obj)
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass
    
    def delete(self, obj):
        if isinstance(obj, Deployment) and obj.id in _deployments:
            del _deployments[obj.id]
    
    def close(self):
        pass
