# Enhanced Models for CodeFlowOps SaaS Platform
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Text, ForeignKey, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

Base = declarative_base()

class OrganizationPlan(enum.Enum):
    FREE = "free"
    STARTER = "starter" 
    PRO = "pro"
    ENTERPRISE = "enterprise"

class UserRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class DeploymentStatus(enum.Enum):
    PENDING = "pending"
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    ANALYSIS_COMPLETE = "analysis_complete"
    GENERATING = "generating"
    INFRASTRUCTURE_READY = "infrastructure_ready"
    CREATING_PIPELINE = "creating_pipeline"
    RUNNING = "running"
    DEPLOYING = "deploying"
    READY = "ready"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Organization(Base):
    """
    Organization model for multi-tenancy
    """
    __tablename__ = "organizations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    
    # Contact Information
    admin_email = Column(String(255), nullable=False)
    company_size = Column(String(50))  # startup, small, medium, large, enterprise
    industry = Column(String(100))
    
    # Plan Information
    plan_type = Column(Enum(OrganizationPlan), default=OrganizationPlan.FREE)
    
    # Settings
    settings_json = Column(Text)  # JSON string for organization settings
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    teams = relationship("Team", back_populates="organization")
    projects = relationship("Project", back_populates="organization")
    deployment_history = relationship("DeploymentHistory", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization(name='{self.name}', plan='{self.plan_type.value}')>"

class Team(Base):
    """
    Teams within organizations for access control
    """
    __tablename__ = "teams"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Permissions
    permissions_json = Column(Text)  # JSON string for team permissions
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="teams")
    users = relationship("User", back_populates="team")

class User(Base):
    """
    Enhanced user model with organization and team relationships
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    team_id = Column(String, ForeignKey("teams.id"))
    
    # User Information
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(200))
    avatar_url = Column(String(500))
    
    # Authentication
    cognito_sub = Column(String(100), unique=True)  # AWS Cognito user sub
    auth_provider = Column(String(50), default="cognito")  # cognito, github, google
    
    # Role and Permissions
    role = Column(Enum(UserRole), default=UserRole.MEMBER)
    permissions_json = Column(Text)  # JSON string for user-specific permissions
    
    # Usage Tracking
    current_month_deployments = Column(Integer, default=0)
    total_deployments = Column(Integer, default=0)
    last_deployment_at = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    team = relationship("Team", back_populates="users")
    projects = relationship("Project", back_populates="owner")
    deployment_history = relationship("DeploymentHistory", back_populates="user")
    
    def __repr__(self):
        return f"<User(email='{self.email}', role='{self.role.value}')>"

class Project(Base):
    """
    Projects within organizations
    """
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Project Details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    github_repo_url = Column(String(500))
    github_repo_name = Column(String(200))
    github_owner = Column(String(100))
    
    # AWS Configuration
    aws_region = Column(String(50), default="us-east-1")
    aws_account_id = Column(String(20))
    
    # Deployment Configuration
    deploy_environment = Column(String(50), default="staging")  # staging, production
    auto_deploy_enabled = Column(Boolean, default=False)
    auto_deploy_branch = Column(String(100), default="main")
    
    # Settings
    settings_json = Column(Text)  # JSON string for project settings
    
    # Status
    is_active = Column(Boolean, default=True)
    last_deployed_at = Column(DateTime)
    deployment_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="projects")
    owner = relationship("User", back_populates="projects")
    deployment_history = relationship("DeploymentHistory", back_populates="project")
    
    def __repr__(self):
        return f"<Project(name='{self.name}', owner='{self.owner.email if self.owner else 'Unknown'}')>"

class DeploymentHistory(Base):
    """
    Track all deployment attempts and their outcomes
    """
    __tablename__ = "deployment_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Deployment Details
    session_id = Column(String(100), unique=True, nullable=False)
    status = Column(Enum(DeploymentStatus), default=DeploymentStatus.PENDING)
    
    # GitHub Information
    github_repo_url = Column(String(500))
    github_commit_sha = Column(String(100))
    github_branch = Column(String(100))
    
    # AWS Information
    aws_region = Column(String(50))
    aws_stack_name = Column(String(200))
    aws_cloudformation_stack_id = Column(String(500))
    
    # Deployment Metrics
    duration_seconds = Column(Integer)  # Total deployment time
    build_minutes_used = Column(Integer, default=0)  # For billing
    
    # URLs and Endpoints
    deployment_url = Column(String(500))  # Final deployment URL
    log_file_url = Column(String(500))   # S3 URL for deployment logs
    
    # Error Information
    error_message = Column(Text)
    error_stack_trace = Column(Text)
    
    # Metadata
    metadata_json = Column(Text)  # Additional deployment metadata
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="deployment_history")
    project = relationship("Project", back_populates="deployment_history")
    user = relationship("User", back_populates="deployment_history")
    
    def __repr__(self):
        return f"<DeploymentHistory(session_id='{self.session_id}', status='{self.status.value}')>"

class Usage(Base):
    """
    Track usage for billing and quota enforcement
    """
    __tablename__ = "usage"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"))
    
    # Usage Metrics
    resource_type = Column(String(50), nullable=False)  # deployments, build_minutes, storage_gb
    quantity = Column(Float, nullable=False)
    billing_month = Column(String(7), nullable=False)  # YYYY-MM format
    
    # Metadata
    metadata_json = Column(Text)  # Additional usage data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")
    
    def __repr__(self):
        return f"<Usage(resource='{self.resource_type}', quantity={self.quantity})>"
