"""
Authentication models for CodeFlowOps
Pydantic models for user management, tokens, and API keys
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import re


class UserRole(str, Enum):
    """User roles with different permission levels"""
    VIEWER = "viewer"      # Read-only access
    USER = "user"          # Standard deployment permissions
    ADMIN = "admin"        # Full system access


class UserCreate(BaseModel):
    """Model for user registration"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    password: str = Field(..., min_length=8, description="User password")
    organization: Optional[str] = Field(None, max_length=100, description="Organization name")
    invitation_code: Optional[str] = Field(None, description="Invitation code (if required)")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        
        return v


class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserUpdate(BaseModel):
    """Model for updating user information"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    organization: Optional[str] = Field(None, max_length=100)
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower() if v else v


class UserResponse(BaseModel):
    """Model for user information response"""
    user_id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Username")
    full_name: str = Field(..., description="User's full name")
    role: UserRole = Field(..., description="User role")
    organization: Optional[str] = Field(None, description="Organization name")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    deployment_count: Optional[int] = Field(None, description="Total deployment count")
    quota_info: Optional[Dict[str, Any]] = Field(None, description="User quota information")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TokenResponse(BaseModel):
    """Model for authentication token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: UserResponse = Field(..., description="User information")


class APIKeyCreate(BaseModel):
    """Model for creating API key"""
    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    permissions: List[str] = Field(
        default=["read", "deploy"], 
        description="API key permissions"
    )
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    
    @validator('permissions')
    def validate_permissions(cls, v):
        """Validate API key permissions"""
        valid_permissions = [
            "read",           # Read access to projects and deployments
            "deploy",         # Deploy applications
            "manage_keys",    # Manage own API keys
            "admin"           # Administrative access
        ]
        
        for permission in v:
            if permission not in valid_permissions:
                raise ValueError(f'Invalid permission: {permission}')
        
        return v


class APIKeyResponse(BaseModel):
    """Model for API key response"""
    key_id: str = Field(..., description="API key identifier")
    name: str = Field(..., description="API key name")
    api_key: str = Field(..., description="API key value (shown only once)")
    permissions: List[str] = Field(..., description="API key permissions")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    last_used: Optional[datetime] = Field(None, description="Last used timestamp")
    is_active: Optional[bool] = Field(True, description="Key active status")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class PasswordChangeRequest(BaseModel):
    """Model for password change request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        
        return v


class UserQuota(BaseModel):
    """Model for user quota information"""
    deployments_per_month: int = Field(..., description="Monthly deployment limit")
    concurrent_deployments: int = Field(..., description="Concurrent deployment limit")
    used_deployments_month: int = Field(0, description="Used deployments this month")
    active_deployments: int = Field(0, description="Currently active deployments")
    storage_limit_gb: Optional[int] = Field(None, description="Storage limit in GB")
    storage_used_gb: Optional[float] = Field(None, description="Used storage in GB")


class RolePermissions(BaseModel):
    """Model for role permissions"""
    role: UserRole = Field(..., description="User role")
    permissions: List[str] = Field(..., description="List of permissions")
    description: str = Field(..., description="Role description")


class InvitationCreate(BaseModel):
    """Model for creating invitations"""
    email: EmailStr = Field(..., description="Invitee email address")
    role: UserRole = Field(UserRole.USER, description="Default role for invitee")
    organization: Optional[str] = Field(None, description="Organization to invite to")
    expires_in_days: int = Field(7, ge=1, le=30, description="Invitation expiration in days")
    message: Optional[str] = Field(None, max_length=500, description="Optional invitation message")


class InvitationResponse(BaseModel):
    """Model for invitation response"""
    invitation_id: str = Field(..., description="Invitation identifier")
    email: EmailStr = Field(..., description="Invitee email")
    role: UserRole = Field(..., description="Assigned role")
    organization: Optional[str] = Field(None, description="Organization")
    code: str = Field(..., description="Invitation code")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    is_used: bool = Field(..., description="Whether invitation has been used")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: str = Field(..., description="Creator user ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SessionAuditLog(BaseModel):
    """Model for session audit logs"""
    log_id: str = Field(..., description="Log entry identifier")
    session_id: str = Field(..., description="Associated session ID")
    user_id: str = Field(..., description="User who performed action")
    action: str = Field(..., description="Action performed")
    resource: str = Field(..., description="Resource affected")
    details: Dict[str, Any] = Field(..., description="Action details")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    timestamp: datetime = Field(..., description="Action timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class AuthenticationEvent(BaseModel):
    """Model for authentication events"""
    event_id: str = Field(..., description="Event identifier")
    user_id: Optional[str] = Field(None, description="User ID (if known)")
    email: Optional[str] = Field(None, description="Email used in attempt")
    event_type: str = Field(..., description="Type of auth event")
    success: bool = Field(..., description="Whether authentication succeeded")
    ip_address: str = Field(..., description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    timestamp: datetime = Field(..., description="Event timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# Database Models (for internal use)

class User(BaseModel):
    """Internal user model for database operations"""
    user_id: str
    email: str
    username: str
    full_name: str
    hashed_password: str
    role: UserRole
    organization: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class APIKey(BaseModel):
    """Internal API key model for database operations"""
    key_id: str
    user_id: str
    name: str
    hashed_key: str
    permissions: List[str]
    expires_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    last_used: Optional[datetime] = None


class Invitation(BaseModel):
    """Internal invitation model for database operations"""
    invitation_id: str
    email: str
    role: UserRole
    organization: Optional[str] = None
    code: str
    expires_at: datetime
    is_used: bool = False
    created_at: datetime
    created_by: str
    used_at: Optional[datetime] = None
    used_by: Optional[str] = None
    
    class Config:
        use_enum_values = True


# Permission Constants

class Permissions:
    """Permission constants for role-based access control"""
    
    # Basic permissions
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    
    # Deployment permissions
    DEPLOY = "deploy"
    DEPLOY_DELETE = "deploy_delete"
    DEPLOY_CANCEL = "deploy_cancel"
    
    # User management permissions
    USER_READ = "user_read"
    USER_WRITE = "user_write"
    USER_DELETE = "user_delete"
    
    # API key permissions
    API_KEY_READ = "api_key_read"
    API_KEY_WRITE = "api_key_write"
    API_KEY_DELETE = "api_key_delete"
    
    # Administrative permissions
    ADMIN_READ = "admin_read"
    ADMIN_WRITE = "admin_write"
    SYSTEM_CONFIG = "system_config"
    
    # Audit permissions
    AUDIT_READ = "audit_read"
    AUDIT_EXPORT = "audit_export"


# Role to Permission Mapping

ROLE_PERMISSIONS = {
    UserRole.VIEWER: [
        Permissions.READ,
        Permissions.API_KEY_READ
    ],
    UserRole.USER: [
        Permissions.READ,
        Permissions.WRITE,
        Permissions.DEPLOY,
        Permissions.DEPLOY_CANCEL,
        Permissions.API_KEY_READ,
        Permissions.API_KEY_WRITE,
        Permissions.API_KEY_DELETE
    ],
    UserRole.ADMIN: [
        # All permissions
        Permissions.READ,
        Permissions.WRITE,
        Permissions.DELETE,
        Permissions.DEPLOY,
        Permissions.DEPLOY_DELETE,
        Permissions.DEPLOY_CANCEL,
        Permissions.USER_READ,
        Permissions.USER_WRITE,
        Permissions.USER_DELETE,
        Permissions.API_KEY_READ,
        Permissions.API_KEY_WRITE,
        Permissions.API_KEY_DELETE,
        Permissions.ADMIN_READ,
        Permissions.ADMIN_WRITE,
        Permissions.SYSTEM_CONFIG,
        Permissions.AUDIT_READ,
        Permissions.AUDIT_EXPORT
    ]
}
