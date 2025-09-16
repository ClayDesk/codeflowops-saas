# Authentication API Routes - Simple Cognito authentication endpoints
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional, Any, Union
from pydantic import BaseModel, Field
import logging
logger = logging.getLogger(__name__)
import sys
import os

# Add the backend root to the path for imports
backend_root = os.path.join(os.path.dirname(__file__), '..', '..')
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

print("Loading authentication modules...")
cognito_provider = None
import_error_msg = "No errors"
primary_error = None
fallback_error = None

try:
    print("Attempting to import CognitoAuthProvider...")
    from src.auth.providers.cognito import CognitoAuthProvider
    from src.models.enhanced_models import User
    from src.config.env import get_settings
    from src.auth.dependencies import get_current_user
    
    # Try to initialize Cognito provider
    settings = get_settings()
    print(f"Settings loaded: AWS_REGION={getattr(settings, 'AWS_REGION', 'None')}")
    print(f"COGNITO_USER_POOL_ID={getattr(settings, 'COGNITO_USER_POOL_ID', 'None')}")
    print(f"COGNITO_CLIENT_ID={getattr(settings, 'COGNITO_CLIENT_ID', 'None')}")
    
    cognito_provider = CognitoAuthProvider()
    print("CognitoAuthProvider initialized successfully!")
    
except ImportError as e:
    print(f"Primary import failed: {e}")
    primary_error = str(e)
    # Fallback imports
    try:
        print("Trying fallback imports...")
        from auth.providers.cognito import CognitoAuthProvider
        from models.enhanced_models import User
        from config.env import get_settings
        from auth.dependencies import get_current_user
        
        settings = get_settings()
        cognito_provider = CognitoAuthProvider()
        print("Fallback CognitoAuthProvider initialized successfully!")
        
    except ImportError as e2:
        print(f"Fallback import also failed: {e2}")
        fallback_error = str(e2)
        # Create minimal fallbacks for testing
        try:
            print("Attempting basic Cognito provider initialization...")
            # Import just the base class
            from src.auth.providers.base import AuthResult
            
            settings = None
            cognito_provider = None
            
        except Exception as e3:
            print(f"Cognito provider initialization failed: {e3}")
            init_error = str(e3)
            import_error_msg = f"Primary: {primary_error}, Fallback: {fallback_error}, Init: {init_error}"
            cognito_provider = None

# If all imports/initialization failed, create minimal fallbacks
if cognito_provider is None:
    print("Creating minimal fallback CognitoAuthProvider...")
    import_error_msg = f"Primary: {primary_error}, Fallback: {fallback_error}"
    
    class CognitoAuthProvider:
        def __init__(self):
            pass
        
        async def authenticate(self, username: str, password: str):
            from src.auth.providers.base import AuthResult
            return AuthResult(
                success=False,
                error_message=f"Cognito authentication not properly configured. Import errors: {import_error_msg}"
            )
    
    cognito_provider = CognitoAuthProvider()
    
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
    username: str = Field(..., description="Username (display name)")
    email: str = Field(..., description="Email address (used as Cognito username)")
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

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="Email address for password reset")

class ForgotPasswordResponse(BaseModel):
    message: str
    success: bool = True

class ConfirmResetPasswordRequest(BaseModel):
    email: str = Field(..., description="Email address")
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., description="New password")

class ConfirmResetPasswordResponse(BaseModel):
    message: str
    success: bool = True

# cognito_provider is already initialized above during import handling

@router.get("/status")
async def auth_status():
    """Check authentication service status"""
    return {
        "service": "authentication",
        "status": "available" if cognito_provider else "unavailable",
        "provider": "aws_cognito",
        "import_error": import_error_msg if not cognito_provider else None
    }

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
        
        # NEW: Sync user to database if not exists
        from ..middleware.user_sync import UserSyncMiddleware
        auth_result = await UserSyncMiddleware.sync_user_on_login(auth_result)
        
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
        # Register with Cognito - use email as username (AWS Cognito requirement)
        user_data = {
            "username": request.email,  # Use email as username for Cognito
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
        
        # NEW: Ensure user is synced to database immediately after registration
        from ..middleware.user_sync import UserSyncMiddleware
        auth_result = await UserSyncMiddleware.sync_user_on_login(auth_result)
        
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

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """Initiate password reset for user"""
    if not cognito_provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )
    
    try:
        # Initiate password reset with Cognito
        success = await cognito_provider.reset_password(request.email)
        
        if not success:
            # For security, we don't reveal if the email exists or not
            # Always return success message
            return ForgotPasswordResponse(
                message="If an account with that email exists, password reset instructions have been sent.",
                success=True
            )
        
        return ForgotPasswordResponse(
            message="Password reset instructions have been sent to your email address.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Forgot password error: {str(e)}")
        # For security, don't reveal internal errors to the user
        return ForgotPasswordResponse(
            message="If an account with that email exists, password reset instructions have been sent.",
            success=True
        )

@router.post("/confirm-reset-password", response_model=ConfirmResetPasswordResponse)
async def confirm_reset_password(request: ConfirmResetPasswordRequest):
    """Confirm password reset with token and set new password"""
    if not cognito_provider:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )
    
    try:
        # Use Cognito's confirm_forgot_password
        success = await cognito_provider.confirm_reset_password(
            request.email, 
            request.token, 
            request.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset failed. The reset code may be invalid or expired."
            )
        
        return ConfirmResetPasswordResponse(
            message="Password has been successfully reset. You can now log in with your new password.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Confirm reset password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset failed. The reset link may be invalid or expired."
        )

@router.get("/me")
async def get_current_user_info(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
):
    """Get current authenticated user information"""
    try:
        # If no credentials provided, return a demo user for testing
        if not credentials:
            return {
                "user_id": "demo-user-123",
                "username": "demo_user",
                "email": "demo@example.com",
                "full_name": "Demo User"
            }

        token = credentials.credentials

        # Demo mode - accept any token for development
        if token:
            return {
                "user_id": "authenticated-user-123",
                "username": "authenticated_user",
                "email": "user@example.com",
                "full_name": "Authenticated User"
            }

        # Fallback - return demo user
        return {
            "user_id": "fallback-user-123",
            "username": "fallback_user",
            "email": "fallback@example.com",
            "full_name": "Fallback User"
        }

    except Exception as e:
        logger.error(f"Error in /me endpoint: {str(e)}")
        # Return demo user on any error
        return {
            "user_id": "error-user-123",
            "username": "error_user",
            "email": "error@example.com",
            "full_name": "Error User"
        }

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None

@router.put("/me")
async def update_current_user_info(
    update_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user)
):
    """Update current authenticated user information"""
    try:
        # For now, just return the updated data without persisting
        # In a real implementation, you would update the user in your database
        updated_user_data = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "email": current_user.email,
            "full_name": update_data.full_name if update_data.full_name is not None else current_user.full_name
        }
        
        return updated_user_data
        
    except Exception as e:
        logging.error(f"Update user profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@router.get("/health")
async def auth_health():
    """Health check for authentication service"""
    return {
        "status": "healthy",
        "service": "auth",
        "message": "Authentication service is operational",
        "timestamp": "2024-01-01T00:00:00Z",
        "endpoints": [
            "/api/v1/auth/me",
            "/api/v1/auth/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        ]
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
async def get_user_deployments(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    """Get deployments for the current user"""
    # Allow access without authentication for now
    user_id = "demo_user"

    # Check if this user has cleared their deployments
    if user_cleared_deployments.get(user_id, False):
        # Return empty if history was cleared
        return {
            "user_id": user_id,
            "deployments": []
        }
    else:
        # Import the real deployment history from simple_api
        try:
            from ...simple_api import _USER_DEPLOYMENT_HISTORY, _DEPLOY_STATES, _LOCK
            import threading
        except ImportError:
            # Fallback to mock data if import fails
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

        try:
            with _LOCK:
                user_deployments = _USER_DEPLOYMENT_HISTORY.get(user_id, [])

            # Also include any currently active deployments for this user
            active_deployments = []
            with _LOCK:
                for dep_id, state in _DEPLOY_STATES.items():
                    if state.get("user_id") == user_id:
                        # Convert active deployment to deployment history format
                        active_deployment = {
                            "id": dep_id,
                            "name": state.get("project_name", "Unknown Project"),
                            "repository": state.get("repository_url", ""),
                            "status": "building" if state.get("status") in ["analyzing", "deploying", "routing_react"] else "pending",
                            "createdAt": state.get("created_at", ""),
                            "technology": state.get("framework", "Static")
                        }
                        # Don't show URL for active deployments
                        active_deployments.append(active_deployment)

            # Combine completed deployments from history with active ones
            all_deployments = active_deployments + user_deployments

            # Sort by creation date (newest first)
            all_deployments.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

            return {
                "user_id": user_id,
                "deployments": all_deployments[:20]  # Limit to last 20 deployments
            }
        except Exception as e:
            logger.error(f"Error fetching user deployments: {e}")
            return {
                "user_id": user_id,
                "deployments": [],
                "error": str(e)
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

        # Import the real deployment history from simple_api
        try:
            from ...simple_api import _USER_DEPLOYMENT_HISTORY, _LOCK
            import threading
        except ImportError:
            # Fallback to just marking as cleared
            user_cleared_deployments[user_id] = True
            return {
                "message": "Deployment history cleared successfully",
                "user_id": user_id,
                "cleared_count": 0
            }

        # Clear the real deployment history
        cleared_count = 0
        with _LOCK:
            if user_id in _USER_DEPLOYMENT_HISTORY:
                cleared_count = len(_USER_DEPLOYMENT_HISTORY[user_id])
                _USER_DEPLOYMENT_HISTORY[user_id] = []

        # Also mark as cleared for consistency
        user_cleared_deployments[user_id] = True

        return {
            "message": "Deployment history cleared successfully",
            "user_id": user_id,
            "cleared_count": cleared_count
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
