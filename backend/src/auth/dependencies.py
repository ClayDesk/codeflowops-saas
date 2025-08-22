# Authentication Dependencies for FastAPI
# Provides dependency injection for authentication and authorization

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import jwt
from datetime import datetime
import logging

from ..models.enhanced_models import User
from .auth_utils import decode_jwt_token, get_user_by_id

# Security scheme for Bearer token authentication
security = HTTPBearer()

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User: The authenticated user object
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Demo mode - accept demo-token for development
        if token == "demo-token":
            from ..models.enhanced_models import User
            demo_user = User()
            demo_user.id = "demo-user-123"
            demo_user.email = "demo@example.com"
            demo_user.username = "demo_user"
            demo_user.is_active = True
            return demo_user
        
        # Try Cognito validation first
        try:
            from ..auth.providers.cognito import CognitoAuthProvider
            cognito_provider = CognitoAuthProvider()
            result = await cognito_provider.validate_token(token)
            
            if result.success:
                from ..models.enhanced_models import User
                user = User()
                user.id = result.user_id
                user.email = result.email
                user.username = result.username
                user.full_name = result.full_name
                user.is_active = True
                return user
        except Exception as e:
            logger.warning(f"Cognito validation failed: {e}")
        
        # Fallback to JWT token validation
        try:
            payload = decode_jwt_token(token)
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user ID from payload
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        try:
            user = await get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Database error retrieving user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service unavailable"
            )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not getattr(user, 'is_active', True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user (alias for get_current_user)
    """
    return current_user

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Dependency to optionally get the current user (for endpoints that work with or without auth)
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        
    Returns:
        Optional[User]: The authenticated user if token is valid, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

def require_roles(*required_roles: str):
    """
    Decorator/dependency to require specific user roles
    
    Args:
        required_roles: List of role names that are allowed
        
    Returns:
        Dependency function that checks user roles
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role = getattr(current_user, 'role', 'user')
        
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker

def require_admin():
    """
    Dependency that requires admin role
    """
    return require_roles('admin', 'super_admin')

def require_pro_plan():
    """
    Dependency that requires pro plan or higher
    """
    def plan_checker(current_user: User = Depends(get_current_user)) -> User:
        user_plan = getattr(current_user, 'plan', 'free')
        
        if user_plan not in ['pro', 'enterprise']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This feature requires a Pro or Enterprise plan"
            )
        
        return current_user
    
    return plan_checker

# Mock user for development/testing when auth is disabled
def get_mock_user() -> User:
    """
    Get a mock user for development/testing purposes
    """
    # This would create a mock User object
    # In a real implementation, you'd return a proper User instance
    class MockUser:
        def __init__(self):
            self.id = "mock-user-123"
            self.email = "test@example.com"
            self.name = "Test User"
            self.role = "user"
            self.plan = "pro"
            self.is_active = True
    
    return MockUser()

async def get_user_for_smart_deploy(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency specifically for Smart Deploy endpoints with additional validation
    """
    # Check if user has Smart Deploy access (could be plan-based)
    user_plan = getattr(current_user, 'plan', 'free')
    
    # For now, allow all authenticated users
    # In production, you might want to restrict to certain plans
    if user_plan == 'free':
        # Could limit free users to fewer deployments, smaller projects, etc.
        pass
    
    return current_user
