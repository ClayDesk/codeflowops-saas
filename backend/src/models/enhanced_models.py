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

class SubscriptionPlan(enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    UNPAID = "unpaid"

class Customer(Base):
    """
    Stripe customer information linked to users
    """
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Stripe Information
    stripe_customer_id = Column(String(100), unique=True, nullable=False)
    
    # Customer Details
    email = Column(String(255), nullable=False)
    name = Column(String(200))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="customer")
    subscriptions = relationship("Subscription", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(email='{self.email}', stripe_id='{self.stripe_customer_id}')>"

class Subscription(Base):
    """
    Stripe subscription information
    """
    __tablename__ = "subscriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    
    # Stripe Information
    stripe_subscription_id = Column(String(100), unique=True, nullable=False)
    stripe_price_id = Column(String(100), nullable=False)
    
    # Subscription Details
    plan = Column(Enum(SubscriptionPlan), nullable=False)
    status = Column(Enum(SubscriptionStatus), nullable=False)
    
    # Billing Information
    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), default="usd")
    interval = Column(String(20), nullable=False)  # month, year
    
    # Dates
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime)
    ended_at = Column(DateTime)
    
    # Metadata
    metadata_json = Column(Text)  # Additional Stripe metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<Subscription(plan='{self.plan.value}', status='{self.status.value}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]
    
    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial period"""
        return self.status == SubscriptionStatus.TRIALING
    
    @property
    def days_until_end(self) -> int:
        """Calculate days until current period ends"""
        if not self.current_period_end:
            return 0
        
        from datetime import datetime
        now = datetime.utcnow()
        if self.current_period_end.replace(tzinfo=None) > now:
            delta = self.current_period_end.replace(tzinfo=None) - now
            return delta.days
        return 0

class Payment(Base):
    """
    Payment transaction records
    """
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    subscription_id = Column(String, ForeignKey("subscriptions.id"))
    
    # Stripe Information
    stripe_payment_intent_id = Column(String(100), unique=True)
    stripe_invoice_id = Column(String(100))
    
    # Payment Details
    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), default="usd")
    status = Column(String(50), nullable=False)  # succeeded, failed, pending, etc.
    
    # Metadata
    description = Column(Text)
    metadata_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer")
    subscription = relationship("Subscription")
    
    def __repr__(self):
        return f"<Payment(amount={self.amount}, status='{self.status}')>"
