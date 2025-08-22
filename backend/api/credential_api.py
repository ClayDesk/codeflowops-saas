"""
FastAPI endpoints for secure AWS credential management.
Provides REST API for credential CRUD operations with security controls.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from ..credential_manager.storage import CredentialStorage, CredentialType
from ..credential_manager.encryption import CredentialEncryption
from ..aws_integration import AWSSessionManager, PermissionValidator
from ..security import MFAManager, IPWhitelistManager, RateLimiter

logger = logging.getLogger(__name__)

# Initialize components
storage = CredentialStorage("postgresql://user:pass@localhost/codeflowops")  # Configure properly
session_manager = AWSSessionManager()
permission_validator = PermissionValidator()
mfa_manager = MFAManager()
ip_whitelist = IPWhitelistManager()
rate_limiter = RateLimiter()

# Security
security = HTTPBearer()

# API Router
router = APIRouter(prefix="/api/v1/credentials", tags=["AWS Credentials"])

# Pydantic Models
class CredentialCreateRequest(BaseModel):
    credential_name: str = Field(..., description="User-friendly name for the credential")
    credential_type: str = Field(..., description="Type of credential: access_key, role_arn")
    credential_data: Dict[str, Any] = Field(..., description="AWS credential data")
    aws_region: Optional[str] = Field(None, description="AWS region")
    permissions_policy: Optional[Dict[str, Any]] = Field(None, description="IAM policy document")
    allowed_ips: Optional[List[str]] = Field(None, description="Allowed IP addresses/ranges")
    mfa_required: bool = Field(True, description="Whether MFA is required for access")
    max_session_duration: str = Field("1h", description="Maximum session duration")
    rotation_schedule: Optional[str] = Field(None, description="Automatic rotation schedule")
    expires_at: Optional[str] = Field(None, description="Credential expiration date")

class CredentialResponse(BaseModel):
    credential_id: str
    credential_name: str
    credential_type: str
    aws_region: Optional[str]
    aws_account_id: Optional[str]
    created_at: str
    last_rotated: Optional[str]
    expires_at: Optional[str]
    is_active: bool
    is_validated: bool
    last_validated: Optional[str]
    mfa_required: bool
    rotation_schedule: Optional[str]

class CredentialAccessRequest(BaseModel):
    credential_id: str = Field(..., description="Credential identifier")
    mfa_token: Optional[str] = Field(None, description="MFA token if required")
    session_duration: int = Field(3600, description="Session duration in seconds")
    session_name: Optional[str] = Field(None, description="Optional session name")

class AWSSessionResponse(BaseModel):
    session_id: str
    access_key_id: str
    secret_access_key: str
    session_token: str
    expires_at: str
    region: str

class MFASetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]

class ValidationRequest(BaseModel):
    credential_data: Dict[str, Any] = Field(..., description="AWS credential data to validate")

class ValidationResponse(BaseModel):
    valid: bool
    identity: Optional[Dict[str, Any]]
    permissions: List[str]
    warnings: List[str]
    error: Optional[str]

# Dependency Functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user information from JWT token."""
    # TODO: Implement JWT token validation
    # For now, return mock user data
    return {
        "user_id": "user-123",
        "tenant_id": "tenant-456",
        "email": "user@example.com",
        "permissions": ["credentials:read", "credentials:write"]
    }

async def require_permission(permission: str):
    """Dependency to check user permissions."""
    def check_permission(user: dict = Depends(get_current_user)):
        if permission not in user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return user
    return check_permission

async def check_rate_limit(request: Request, action: str):
    """Check rate limiting for requests."""
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    identifier = f"{client_ip}:{user_agent}"
    
    allowed, limit_info = rate_limiter.check_rate_limit(action, "api_request", identifier)
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"X-RateLimit-Reset": limit_info.get("reset_time", "")}
        )
    
    return limit_info

# API Endpoints

@router.post("/", response_model=Dict[str, str])
async def create_credential(
    request: CredentialCreateRequest,
    http_request: Request,
    user: dict = Depends(require_permission("credentials:write")),
    rate_info: dict = Depends(lambda r: check_rate_limit(r, "credential_creation"))
):
    """Create new AWS credential for tenant."""
    try:
        # Validate credential data first
        validation_result = permission_validator.validate_credentials(request.credential_data)
        
        if not validation_result['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid credentials: {validation_result.get('error', 'Unknown error')}"
            )
        
        # Check for dangerous permissions
        if validation_result.get('warnings'):
            logger.warning(f"Dangerous permissions detected for tenant {user['tenant_id']}: {validation_result['warnings']}")
        
        # Prepare metadata
        metadata = {
            'permissions_policy': request.permissions_policy,
            'allowed_ips': request.allowed_ips,
            'mfa_required': request.mfa_required,
            'max_session_duration': request.max_session_duration,
            'rotation_schedule': request.rotation_schedule,
            'expires_at': request.expires_at
        }
        
        # Store credential
        credential_id = storage.store_credential(
            tenant_id=user['tenant_id'],
            user_id=user['user_id'],
            credential_name=request.credential_name,
            credential_type=CredentialType(request.credential_type),
            credential_data=request.credential_data,
            metadata=metadata,
            ip_address=http_request.client.host
        )
        
        return {"credential_id": credential_id, "message": "Credential created successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create credential"
        )

@router.get("/", response_model=List[CredentialResponse])
async def list_credentials(
    include_inactive: bool = False,
    http_request: Request = None,
    user: dict = Depends(require_permission("credentials:read")),
    rate_info: dict = Depends(lambda r: check_rate_limit(r, "credential_access"))
):
    """List all credentials for tenant."""
    try:
        credentials = storage.list_credentials(
            tenant_id=user['tenant_id'],
            user_id=user['user_id'],
            include_inactive=include_inactive,
            ip_address=http_request.client.host
        )
        
        return [CredentialResponse(**cred) for cred in credentials]
        
    except Exception as e:
        logger.error(f"Failed to list credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list credentials"
        )

@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: str,
    http_request: Request,
    user: dict = Depends(require_permission("credentials:read")),
    rate_info: dict = Depends(lambda r: check_rate_limit(r, "credential_access"))
):
    """Get credential metadata (no sensitive data)."""
    try:
        credentials = storage.list_credentials(
            tenant_id=user['tenant_id'],
            user_id=user['user_id'],
            ip_address=http_request.client.host
        )
        
        credential = next((c for c in credentials if c['credential_id'] == credential_id), None)
        
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
        return CredentialResponse(**credential)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get credential"
        )

@router.post("/access", response_model=AWSSessionResponse)
async def access_credential(
    request: CredentialAccessRequest,
    http_request: Request,
    user: dict = Depends(require_permission("credentials:use")),
    rate_info: dict = Depends(lambda r: check_rate_limit(r, "credential_access"))
):
    """Access credential and create AWS session."""
    try:
        # Retrieve credential
        credential_data = storage.retrieve_credential(
            tenant_id=user['tenant_id'],
            user_id=user['user_id'],
            credential_id=request.credential_id,
            ip_address=http_request.client.host
        )
        
        # Check if MFA is required
        if credential_data.get('mfa_required', True):
            if not request.mfa_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="MFA token required"
                )
            
            # TODO: Verify MFA token against user's configured MFA
            # For now, assume validation exists
            mfa_valid = True  # mfa_manager.verify_totp(user_secret, request.mfa_token)
            
            if not mfa_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA token"
                )
        
        # Create AWS session
        session_info = session_manager.create_session(
            tenant_id=user['tenant_id'],
            user_id=user['user_id'],
            credentials=credential_data,
            session_duration=request.session_duration,
            session_name=request.session_name
        )
        
        return AWSSessionResponse(**session_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to access credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to access credential"
        )

@router.put("/{credential_id}")
async def update_credential(
    credential_id: str,
    updates: Dict[str, Any],
    http_request: Request,
    user: dict = Depends(require_permission("credentials:write")),
    rate_info: dict = Depends(lambda r: check_rate_limit(r, "credential_access"))
):
    """Update credential metadata or data."""
    try:
        success = storage.update_credential(
            tenant_id=user['tenant_id'],
            user_id=user['user_id'],
            credential_id=credential_id,
            updates=updates,
            ip_address=http_request.client.host
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
        return {"message": "Credential updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update credential"
        )

@router.delete("/{credential_id}")
async def delete_credential(
    credential_id: str,
    hard_delete: bool = False,
    http_request: Request = None,
    user: dict = Depends(require_permission("credentials:delete")),
    rate_info: dict = Depends(lambda r: check_rate_limit(r, "credential_access"))
):
    """Delete (deactivate) credential."""
    try:
        success = storage.delete_credential(
            tenant_id=user['tenant_id'],
            user_id=user['user_id'],
            credential_id=credential_id,
            ip_address=http_request.client.host,
            hard_delete=hard_delete
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found"
            )
        
        return {"message": "Credential deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete credential"
        )

@router.post("/validate", response_model=ValidationResponse)
async def validate_credential(
    request: ValidationRequest,
    user: dict = Depends(require_permission("credentials:validate")),
    rate_info: dict = Depends(lambda r: check_rate_limit(r, "credential_access"))
):
    """Validate AWS credentials and check permissions."""
    try:
        result = permission_validator.validate_credentials(request.credential_data)
        return ValidationResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to validate credential: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate credential"
        )

# MFA Endpoints
@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    user: dict = Depends(get_current_user)
):
    """Set up MFA for user."""
    try:
        mfa_data = mfa_manager.setup_totp(user['user_id'], user['email'])
        return MFASetupResponse(**mfa_data)
        
    except Exception as e:
        logger.error(f"Failed to set up MFA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set up MFA"
        )

# Session Management
@router.get("/sessions")
async def list_active_sessions(
    user: dict = Depends(require_permission("sessions:read"))
):
    """List active AWS sessions for tenant."""
    try:
        sessions = session_manager.list_active_sessions(
            tenant_id=user['tenant_id'],
            user_id=user['user_id']
        )
        return {"sessions": sessions}
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list sessions"
        )

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    user: dict = Depends(require_permission("sessions:delete"))
):
    """Revoke an active AWS session."""
    try:
        success = session_manager.revoke_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )
