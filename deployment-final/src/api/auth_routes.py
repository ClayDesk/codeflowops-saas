# Authentication API Routes - Simple Cognito authentication endpoints
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional, Any, Union
from pydantic import BaseModel, Field
import logging
import sys
import os

# Add the backend root to the path for imports
backend_root = os.path.join(os.path.dirname(__file__), '..', '..')
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

try:
    from src.auth.providers.cognito import CognitoAuthProvider
    from src.models.enhanced_models import User
    from src.config.env import get_settings
    from src.auth.dependencies import get_current_user
except ImportError:
    # Fallback imports
    try:
        from auth.providers.cognito import CognitoAuthProvider
        from models.enhanced_models import User
        from config.env import get_settings
        from auth.dependencies import get_current_user
    except ImportError as e:
        print(f"Import error in auth_routes: {e}")
        # Create minimal fallbacks for testing
        class CognitoAuthProvider:
            def __init__(self):
                pass
        
        class User:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        def get_settings():
            class MockSettings:
                def __init__(self):
                    self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
                    self.cognito_user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
                    self.cognito_client_id = os.getenv('COGNITO_CLIENT_ID')
            return MockSettings()
        
        def get_current_user():
            return None

router = APIRouter()
security = HTTPBearer()

# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")

class RegisterRequest(BaseModel):
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    full_name: Optional[str] = Field(None, description="Full name")

class AuthResponse(BaseModel):
    message: str
    user: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None

class LogoutRequest(BaseModel):
    access_token: str = Field(..., description="Access token to invalidate")

# Initialize Cognito provider
try:
    settings = get_settings()
    cognito_provider = CognitoAuthProvider()
    print("SUCCESS: Cognito provider initialized successfully")
except Exception as e:
    print(f"WARNING: Failed to initialize Cognito provider: {e}")
    cognito_provider = None

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Authenticate user with username/email and password"""
    if not cognito_provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )
    
    try:
        # Authenticate with Cognito
        auth_result = await cognito_provider.authenticate(request.username, request.password)
        
        if not auth_result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth_result.error_message or "Incorrect username or password"
            )
        
        # Return success response
        return AuthResponse(
            message="Login successful",
            user={
                "user_id": auth_result.user_id,
                "username": auth_result.username,
                "email": auth_result.email,
                "full_name": auth_result.full_name
            },
            access_token=auth_result.access_token,
            refresh_token=auth_result.refresh_token,
            expires_in=auth_result.expires_in
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    if not cognito_provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )
    
    try:
        # Register with Cognito
        user_data = {
            "username": request.username,
            "email": request.email,
            "password": request.password,
            "full_name": request.full_name
        }
        
        auth_result = await cognito_provider.register(user_data)
        
        if not auth_result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=auth_result.error_message or "Registration failed"
            )
        
        # Return success response (registration automatically logs in)
        return AuthResponse(
            message="Registration successful",
            user={
                "user_id": auth_result.user_id,
                "username": auth_result.username,
                "email": auth_result.email,
                "full_name": auth_result.full_name
            },
            access_token=auth_result.access_token,
            refresh_token=auth_result.refresh_token,
            expires_in=auth_result.expires_in
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration error: {str(e)}"
        )

@router.post("/logout")
async def logout(request: LogoutRequest):
    """Logout user by invalidating access token"""
    if not cognito_provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )
    
    try:
        # Invalidate token with Cognito
        success = await cognito_provider.logout(request.access_token)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to logout"
            )
        
        return {"message": "Logout successful"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout error: {str(e)}"
        )

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name
    }

@router.get("/health")
async def auth_health():
    """Health check for authentication service"""
    provider_status = "available" if cognito_provider else "unavailable"
    
    return {
        "status": "healthy",
        "provider": "cognito",
        "provider_status": provider_status,
        "timestamp": "2024-01-01T00:00:00Z"
    }

@router.get("/config")
async def get_auth_config():
    """Get authentication configuration (public info only)"""
    try:
        settings = get_settings()
        return {
            "provider": "cognito",
            "region": settings.aws_region,
            "user_pool_id": settings.cognito_user_pool_id,
            "client_id": settings.cognito_client_id
        }
    except Exception as e:
        return {
            "provider": "cognito",
            "status": "configuration_error",
            "error": str(e)
        }

# Simple in-memory storage for deployment history clear status per user
user_cleared_deployments = {}

# Deployment management endpoints for authenticated users
@router.get("/deployments")
async def get_user_deployments(current_user: User = Depends(get_current_user)):
    """Get deployments for the current user"""
    user_id = current_user.user_id if current_user else "demo_user"
    
    # Check if this user has cleared their deployments
    if user_cleared_deployments.get(user_id, False):
        # Return empty if history was cleared
        return {
            "user_id": user_id,
            "deployments": []
        }
    else:
        # Return mock deployments to simulate real data
        return {
            "user_id": user_id,
            "deployments": [
                {
                    "id": "1",
                    "name": "My Portfolio",
                    "repository": "github.com/user/portfolio",
                    "status": "success",
                    "url": "https://my-portfolio-abc123.vercel.app",
                    "createdAt": "2025-08-20T10:30:00Z",
                    "technology": "Next.js"
                },
                {
                    "id": "2",
                    "name": "Blog App", 
                    "repository": "github.com/user/blog-app",
                    "status": "building",
                    "createdAt": "2025-08-21T08:15:00Z",
                    "technology": "React"
                }
            ]
        }

@router.post("/deployments")
async def create_user_deployment(deployment_data: dict):
    """Create a new deployment for the current user"""
    # This is a placeholder - implement actual deployment creation
    return {
        "message": "Deployment created",
        "user_id": "demo_user",
        "deployment_data": deployment_data
    }

@router.delete("/deployments/clear")
async def clear_user_deployment_history(current_user: User = Depends(get_current_user)):
    """Clear all deployment history for the current user"""
    try:
        user_id = current_user.user_id if current_user else "demo_user"
        
        # Mark deployment history as cleared for this specific user
        user_cleared_deployments[user_id] = True
        
        return {
            "message": "Deployment history cleared successfully",
            "user_id": user_id,
            "cleared_count": 2  # Number of deployments that were cleared
        }
    except Exception as e:
        logging.error(f"Clear deployment history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear deployment history"
        )

@router.post("/deployments/reset")
async def reset_deployment_history(current_user: User = Depends(get_current_user)):
    """Reset deployment history (for testing)"""
    try:
        user_id = current_user.user_id if current_user else "demo_user"
        
        # Reset the flag so deployments show again for this user
        user_cleared_deployments[user_id] = False
        
        return {
            "message": "Deployment history reset successfully",
            "user_id": user_id
        }
    except Exception as e:
        logging.error(f"Reset deployment history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset deployment history"
        )
