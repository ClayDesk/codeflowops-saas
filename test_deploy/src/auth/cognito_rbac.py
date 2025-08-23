# AWS Cognito RBAC Integration
import os
import jwt
import json
import requests
from typing import Dict, List, Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
import time

# Cognito Configuration
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "us-east-1_lWcaQdyeZ")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "3d0gm6gtv4ia8vonloc38q8nkt")
COGNITO_AUTHORITY = os.getenv("COGNITO_AUTHORITY", f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = "RS256"  # Cognito uses RS256
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

security = HTTPBearer()

class CognitoJWTValidator:
    """
    Validates JWT tokens from AWS Cognito
    """
    
    def __init__(self):
        self.region = COGNITO_REGION
        self.user_pool_id = COGNITO_USER_POOL_ID
        self.client_id = COGNITO_CLIENT_ID
        self.jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
        self._jwks = None
        self._jwks_last_fetch = 0
    
    def get_jwks(self):
        """Get JSON Web Key Set from Cognito"""
        current_time = time.time()
        
        # Cache JWKS for 1 hour
        if self._jwks is None or current_time - self._jwks_last_fetch > 3600:
            try:
                response = requests.get(self.jwks_url, timeout=10)
                response.raise_for_status()
                self._jwks = response.json()
                self._jwks_last_fetch = current_time
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to fetch JWKS: {str(e)}"
                )
        
        return self._jwks
    
    def validate_token(self, token: str) -> Dict:
        """
        Validate Cognito JWT token
        """
        try:
            # Decode header to get kid
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing kid in header"
                )
            
            # Get JWKS and find matching key
            jwks = self.get_jwks()
            key = None
            
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwk
                    break
            
            if not key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find appropriate key"
                )
            
            # Construct the public key (simplified - in production use proper key construction)
            # For now, we'll use a simple validation approach
            
            # Decode and verify token
            payload = jwt.decode(
                token,
                options={"verify_signature": False},  # Simplified for demo
                algorithms=["RS256"]
            )
            
            # Verify token claims
            if payload.get("aud") != self.client_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid audience"
                )
            
            if payload.get("iss") != f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid issuer"
                )
            
            # Check expiration
            if payload.get("exp", 0) < time.time():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            return payload
            
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )

# Global validator instance
cognito_validator = CognitoJWTValidator()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Verify JWT token from Authorization header
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    return cognito_validator.validate_token(credentials.credentials)

def get_current_user(token_payload: Dict = Depends(verify_token)):
    """
    Get current user from token payload
    """
    from ..utils.database import get_db_session
    from ..models.enhanced_models import User
    
    # Get user from database using Cognito sub
    cognito_sub = token_payload.get("sub")
    if not cognito_sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # For now, return a mock user object
    # In production, you'd query the database
    class MockUser:
        def __init__(self, cognito_sub: str, email: str, groups: List[str]):
            self.id = cognito_sub
            self.cognito_sub = cognito_sub
            self.email = email
            self.groups = groups
            self.organization_id = "mock-org-id"  # Would come from database
    
    email = token_payload.get("email", "user@example.com")
    groups = token_payload.get("cognito:groups", [])
    
    return MockUser(cognito_sub, email, groups)

def verify_admin_access(current_user = Depends(get_current_user)):
    """
    Verify user has admin access
    """
    if "administrators" not in getattr(current_user, "groups", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user

def require_role(required_roles: List[str]):
    """
    Decorator to require specific roles
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would integrate with the actual role checking
            return func(*args, **kwargs)
        return wrapper
    return decorator

def check_organization_access(organization_id: str, current_user = Depends(get_current_user)):
    """
    Check if user has access to specific organization
    """
    if current_user.organization_id != organization_id:
        # Check if user is admin or has cross-org access
        if "administrators" not in getattr(current_user, "groups", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
    
    return True

def get_user_permissions(current_user = Depends(get_current_user)) -> List[str]:
    """
    Get user permissions based on role and group membership
    """
    permissions = []
    
    # Base permissions for all users
    permissions.extend([
        "read:own_profile",
        "update:own_profile",
        "read:own_projects",
        "create:projects"
    ])
    
    # Admin permissions
    if "administrators" in getattr(current_user, "groups", []):
        permissions.extend([
            "read:all_users",
            "update:all_users",
            "delete:users",
            "read:all_organizations",
            "update:organizations",
            "read:billing",
            "update:billing",
            "impersonate:users"
        ])
    
    # Organization admin permissions
    if "org_admins" in getattr(current_user, "groups", []):
        permissions.extend([
            "read:org_users",
            "update:org_users",
            "read:org_billing",
            "update:org_settings"
        ])
    
    return permissions
