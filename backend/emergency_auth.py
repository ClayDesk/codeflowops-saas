"""
Emergency Cognito Authentication Service
This file provides a standalone authentication service that can work even if the main application fails.
"""

import os
import sys
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Pydantic models
class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")

class AuthResponse(BaseModel):
    message: str
    success: bool = True
    user: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None

# Initialize Cognito provider
cognito_provider = None

try:
    # Try to import Cognito provider
    from src.auth.providers.cognito import CognitoAuthProvider
    from src.config.env import get_settings
    
    settings = get_settings()
    cognito_provider = CognitoAuthProvider()
    logger.info("✅ CognitoAuthProvider initialized successfully")
    
except Exception as e:
    logger.error(f"❌ Failed to initialize CognitoAuthProvider: {e}")
    # Try fallback import paths
    try:
        sys.path.append(os.path.join(current_dir, 'src'))
        from auth.providers.cognito import CognitoAuthProvider  # type: ignore
        from config.env import get_settings  # type: ignore
        
        settings = get_settings()
        cognito_provider = CognitoAuthProvider()
        logger.info("✅ CognitoAuthProvider initialized with fallback imports")
        
    except Exception as fallback_error:
        logger.error(f"❌ Fallback import also failed: {fallback_error}")

# Create router
router = APIRouter(prefix="/api/v1/auth")

@router.get("/status")
async def auth_status():
    """Check authentication service status"""
    return {
        "service": "authentication",
        "status": "available" if cognito_provider else "unavailable",
        "provider": "aws_cognito",
        "message": "Cognito authentication service" if cognito_provider else "Cognito provider not initialized"
    }

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Authenticate user with AWS Cognito"""
    if not cognito_provider:
        raise HTTPException(
            status_code=503,
            detail="Authentication service not available - Cognito provider not initialized"
        )
    
    try:
        # Authenticate with Cognito
        auth_result = await cognito_provider.authenticate(request.username, request.password)
        
        if not auth_result.success:
            raise HTTPException(
                status_code=401,
                detail=auth_result.error_message or "Incorrect username or password"
            )
        
        # NEW: Sync user to database for future subscription features
        try:
            from src.middleware.user_sync import UserSyncMiddleware
            auth_result = await UserSyncMiddleware.sync_user_on_login(auth_result)
        except Exception as e:
            # Don't block authentication if sync fails
            logger.warning(f"User sync failed for {auth_result.email}: {e}")
        
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
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication error: {str(e)}"
        )

@router.post("/logout")
async def logout():
    """Logout user (placeholder for now)"""
    return {"message": "Logout successful", "success": True}

# Create standalone app for emergency auth
def create_emergency_auth_app():
    """Create a standalone auth app for emergency use"""
    app = FastAPI(title="CodeFlowOps Emergency Auth Service", version="1.0.0")
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://www.codeflowops.com",
            "https://codeflowops.com", 
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Include auth router
    app.include_router(router)
    
    @app.get("/")
    async def root():
        return {"message": "CodeFlowOps Emergency Auth Service", "status": "active"}
    
    @app.get("/health")
    async def health():
        return {"status": "active", "service": "emergency_auth"}
    
    return app

# Export the router for use in other applications
__all__ = ["router", "create_emergency_auth_app"]

if __name__ == "__main__":
    # Run as standalone service
    import uvicorn
    app = create_emergency_auth_app()
    uvicorn.run(app, host="0.0.0.0", port=8001)