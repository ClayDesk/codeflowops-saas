"""
Phase 3 Multi-Tenant API Endpoints
FastAPI endpoints for tenant management, user management, and authentication
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Import our Phase 3 services
try:
    from services.TenantManager import tenant_manager, SubscriptionTier, TenantStatus
    from services.AuthenticationService import auth_service, UserRole, AuthProvider, UserStatus
    from services.SubdomainRoutingService import get_current_tenant, get_current_tenant_optional, tenant_service
except ImportError as e:
    logging.warning(f"Phase 3 service imports failed: {e}. Using mock services.")
    
    # Mock implementations for development
    class SubscriptionTier:
        FREE = "free"
        STARTER = "starter"
        PROFESSIONAL = "professional"
        ENTERPRISE = "enterprise"
    
    class UserRole:
        TENANT_OWNER = "tenant_owner"
        ADMIN = "admin"
        DEVOPS_ENGINEER = "devops_engineer"
        DEVELOPER = "developer"
        VIEWER = "viewer"
    
    class UserStatus:
        ACTIVE = "active"
        INACTIVE = "inactive"
        PENDING = "pending"
    
    class AuthProvider:
        LOCAL = "local"
        OKTA = "okta"
        AZURE_AD = "azure_ad"
        GOOGLE = "google"
    
    class TenantStatus:
        ACTIVE = "active"
        INACTIVE = "inactive"
        SUSPENDED = "suspended"

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Dependencies
async def get_current_user():
    """Get current authenticated user"""
    # This will be implemented with full JWT token verification
    # For now, return a mock user
    class MockUser:
        def __init__(self):
            self.user_id = "mock_user_123"
            self.email = "mock@example.com"
            self.role = UserRole.ADMIN
    
    return MockUser()

# Initialize router
router = APIRouter(prefix="/api/tenant", tags=["tenant-management"])

# Request/Response Models

class CreateTenantRequest(BaseModel):
    organization_name: str = Field(..., description="Organization name")
    billing_email: EmailStr = Field(..., description="Billing email address")
    subscription_tier: str = Field("free", description="Subscription tier")
    subdomain: Optional[str] = Field(None, description="Preferred subdomain")
    owner_email: EmailStr = Field(..., description="Owner email")
    owner_name: str = Field(..., description="Owner full name")

class TenantResponse(BaseModel):
    tenant_id: str
    organization_name: str
    subscription_tier: str
    status: str
    subdomain: str
    custom_domains: List[str]
    created_at: datetime
    owner_user_id: Optional[str]

class CreateUserRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    full_name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role")
    password: Optional[str] = Field(None, description="Password for local auth")

class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    status: str
    auth_provider: str
    last_login: Optional[datetime]
    created_at: datetime

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., description="API key name")
    scopes: List[str] = Field(..., description="API key scopes")
    expires_in_days: Optional[int] = Field(None, description="Expiration in days")

class APIKeyResponse(BaseModel):
    key_id: str
    name: str
    api_key: str
    scopes: List[str]
    expires_at: Optional[datetime]
    created_at: datetime

class TenantUsageResponse(BaseModel):
    tenant_id: str
    usage: Dict[str, Any]
    limits: Dict[str, Any]

# Tenant Management Endpoints

@router.post("/create", response_model=TenantResponse)
async def create_tenant(request: CreateTenantRequest):
    """
    Create a new tenant organization
    """
    try:
        # Validate subscription tier
        try:
            subscription_tier = SubscriptionTier(request.subscription_tier)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription tier: {request.subscription_tier}"
            )
        
        # Create tenant
        tenant = await tenant_manager.create_tenant(
            organization_name=request.organization_name,
            billing_email=request.billing_email,
            subscription_tier=subscription_tier,
            subdomain=request.subdomain
        )
        
        # Create owner user
        owner_user = await auth_service.create_user(
            tenant_id=tenant.tenant_id,
            email=request.owner_email,
            full_name=request.owner_name,
            role=UserRole.TENANT_OWNER,
            auth_provider=AuthProvider.LOCAL
        )
        
        # Update tenant with owner
        tenant.owner_user_id = owner_user.user_id
        
        logger.info(f"✅ Created tenant: {tenant.organization_name} with owner: {owner_user.email}")
        
        return TenantResponse(
            tenant_id=tenant.tenant_id,
            organization_name=tenant.organization_name,
            subscription_tier=tenant.subscription_tier.value,
            status=tenant.status.value,
            subdomain=tenant.subdomain,
            custom_domains=tenant.custom_domains,
            created_at=tenant.created_at,
            owner_user_id=tenant.owner_user_id
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}"
        )

@router.get("/info", response_model=TenantResponse)
async def get_tenant_info(current_tenant=Depends(get_current_tenant)):
    """
    Get current tenant information
    """
    return TenantResponse(
        tenant_id=current_tenant.tenant_id,
        organization_name=current_tenant.organization_name,
        subscription_tier=current_tenant.subscription_tier.value,
        status=current_tenant.status.value,
        subdomain=current_tenant.subdomain,
        custom_domains=current_tenant.custom_domains,
        created_at=current_tenant.created_at,
        owner_user_id=current_tenant.owner_user_id
    )

@router.put("/subscription/{new_tier}")
async def update_subscription(
    new_tier: str,
    current_tenant=Depends(get_current_tenant)
):
    """
    Update tenant subscription tier
    """
    try:
        subscription_tier = SubscriptionTier(new_tier)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid subscription tier: {new_tier}"
        )
    
    success = await tenant_manager.update_tenant_subscription(
        current_tenant.tenant_id,
        subscription_tier
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription"
        )
    
    return JSONResponse(content={
        "success": True,
        "message": f"Subscription updated to {new_tier}"
    })

@router.get("/usage", response_model=TenantUsageResponse)
async def get_tenant_usage(current_tenant=Depends(get_current_tenant)):
    """
    Get tenant resource usage and limits
    """
    usage_data = await tenant_service.get_tenant_resource_usage(current_tenant.tenant_id)
    
    return TenantUsageResponse(
        tenant_id=current_tenant.tenant_id,
        usage=usage_data,
        limits={
            "max_projects": current_tenant.resource_limits.max_projects,
            "max_users": current_tenant.resource_limits.max_users,
            "max_deployments_per_month": current_tenant.resource_limits.max_deployments_per_month,
            "max_storage_gb": current_tenant.resource_limits.max_storage_gb,
            "max_cost_per_month": float(current_tenant.resource_limits.max_cost_per_month)
        }
    )

# User Management Endpoints

@router.post("/users", response_model=UserResponse)
async def create_user(
    request: CreateUserRequest,
    current_tenant=Depends(get_current_tenant)
):
    """
    Create a new user in the tenant
    """
    try:
        # Validate role
        try:
            role = UserRole(request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {request.role}"
            )
        
        # Check if tenant has capacity for more users
        can_add_user = await tenant_manager.check_resource_limit(
            current_tenant.tenant_id,
            "users",
            1
        )
        
        if not can_add_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User limit reached for current subscription tier"
            )
        
        # Create user
        user = await auth_service.create_user(
            tenant_id=current_tenant.tenant_id,
            email=request.email,
            full_name=request.full_name,
            role=role,
            password=request.password
        )
        
        # Update tenant usage
        await tenant_manager.update_tenant_usage(
            current_tenant.tenant_id,
            current_users=await _get_current_user_count(current_tenant.tenant_id)
        )
        
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            auth_provider=user.auth_provider.value,
            last_login=user.last_login,
            created_at=user.created_at
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

@router.get("/users", response_model=List[UserResponse])
async def list_users(current_tenant=Depends(get_current_tenant)):
    """
    List all users in the tenant
    """
    users = await auth_service.list_tenant_users(current_tenant.tenant_id)
    
    return [
        UserResponse(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            auth_provider=user.auth_provider.value,
            last_login=user.last_login,
            created_at=user.created_at
        )
        for user in users
    ]

# Authentication Endpoints

@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """
    Authenticate user and return access token
    """
    # Extract tenant from request (should be set by middleware)
    tenant = getattr(req.state, 'tenant', None)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    # Get client IP for audit logging
    client_ip = req.client.host if req.client else None
    
    # Authenticate user
    user = await auth_service.authenticate_user(
        tenant_id=tenant.tenant_id,
        email=request.email,
        password=request.password,
        ip_address=client_ip
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create access token
    access_token = await auth_service.create_access_token(user)
    
    return LoginResponse(
        access_token=access_token,
        expires_in=24 * 3600,  # 24 hours
        user=UserResponse(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            auth_provider=user.auth_provider.value,
            last_login=user.last_login,
            created_at=user.created_at
        )
    )

@router.post("/auth/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user=Depends(get_current_user),  # Will implement this dependency
    current_tenant=Depends(get_current_tenant)
):
    """
    Create API key for programmatic access
    """
    api_key, api_key_record = await auth_service.create_api_key(
        user_id=current_user.user_id,
        tenant_id=current_tenant.tenant_id,
        name=request.name,
        scopes=request.scopes,
        expires_in_days=request.expires_in_days
    )
    
    return APIKeyResponse(
        key_id=api_key_record.key_id,
        name=api_key_record.name,
        api_key=api_key,  # Only returned once during creation
        scopes=api_key_record.scopes,
        expires_at=api_key_record.expires_at,
        created_at=api_key_record.created_at
    )

@router.get("/auth/verify")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify JWT token
    """
    token = credentials.credentials
    payload = await auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return JSONResponse(content={
        "valid": True,
        "user_id": payload["user_id"],
        "tenant_id": payload["tenant_id"],
        "role": payload["role"],
        "scopes": payload["scopes"]
    })

# SSO Configuration Endpoints

@router.post("/sso/configure")
async def configure_sso(
    provider: str,
    config: Dict[str, Any],
    current_tenant=Depends(get_current_tenant)
):
    """
    Configure SSO for tenant (Enterprise feature)
    """
    if not current_tenant.resource_limits.sso_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SSO not available for current subscription tier"
        )
    
    success = await tenant_manager.configure_sso(
        tenant_id=current_tenant.tenant_id,
        provider=provider,
        provider_config=config,
        enabled=True
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure SSO"
        )
    
    return JSONResponse(content={
        "success": True,
        "message": f"SSO configured with {provider}"
    })

# Admin Endpoints

@router.get("/admin/tenants")
async def list_all_tenants(
    status_filter: Optional[str] = None,
    tier_filter: Optional[str] = None,
    limit: int = 50
):
    """
    List all tenants (System admin only)
    """
    # This would require system admin authentication
    # For now, implementing basic functionality
    
    status = TenantStatus(status_filter) if status_filter else None
    tier = SubscriptionTier(tier_filter) if tier_filter else None
    
    tenants = await tenant_manager.list_tenants(
        status=status,
        subscription_tier=tier,
        limit=limit
    )
    
    return [
        TenantResponse(
            tenant_id=tenant.tenant_id,
            organization_name=tenant.organization_name,
            subscription_tier=tenant.subscription_tier.value,
            status=tenant.status.value,
            subdomain=tenant.subdomain,
            custom_domains=tenant.custom_domains,
            created_at=tenant.created_at,
            owner_user_id=tenant.owner_user_id
        )
        for tenant in tenants
    ]

# Helper Functions

async def _get_current_user_count(tenant_id: str) -> int:
    """Get current user count for tenant"""
    users = await auth_service.list_tenant_users(tenant_id)
    return len([user for user in users if user.status == UserStatus.ACTIVE])
