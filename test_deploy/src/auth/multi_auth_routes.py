"""
Updated authentication routes supporting multiple providers
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import secrets
from .auth_manager import auth_manager
from ..dependencies.rate_limiting import rate_limit

router = APIRouter(prefix="/auth", tags=["authentication"])

class LoginRequest(BaseModel):
    provider: str = "local"  # local, cognito, github, google
    username: Optional[str] = None
    password: Optional[str] = None
    code: Optional[str] = None  # For OAuth
    redirect_uri: Optional[str] = None  # For OAuth

class RegisterRequest(BaseModel):
    provider: str = "local"
    email: str
    password: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    organization: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    user: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None
    message: Optional[str] = None

@router.get("/providers")
async def get_auth_providers():
    """Get available authentication providers"""
    return {
        "providers": auth_manager.get_available_providers()
    }

@router.post("/login")
@rate_limit(max_requests=5, window_seconds=300)  # 5 attempts per 5 minutes
async def login(request: LoginRequest):
    """Login with any supported provider"""
    
    credentials = {}
    
    if request.provider == "local" or request.provider == "cognito":
        if not request.username or not request.password:
            raise HTTPException(
                status_code=400,
                detail="Username and password required"
            )
        credentials = {
            "username": request.username,
            "password": request.password
        }
    
    elif request.provider in ["github", "google"]:
        if not request.code or not request.redirect_uri:
            raise HTTPException(
                status_code=400,
                detail="Authorization code and redirect URI required for OAuth"
            )
        credentials = {
            "code": request.code,
            "redirect_uri": request.redirect_uri
        }
    
    result = await auth_manager.authenticate(request.provider, credentials)
    
    if not result.success:
        raise HTTPException(
            status_code=401,
            detail=result.error_message or "Authentication failed"
        )
    
    return AuthResponse(
        success=True,
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_in=result.expires_in,
        user={
            "id": result.user_id,
            "email": result.email,
            "username": result.username,
            "full_name": result.full_name,
            "role": result.role,
            "organization": result.organization
        },
        provider=request.provider,
        message="Login successful"
    )

@router.post("/register")
@rate_limit(max_requests=3, window_seconds=3600)  # 3 registrations per hour
async def register(request: RegisterRequest):
    """Register with supported provider"""
    
    user_data = {
        "email": request.email,
        "username": request.username or request.email.split("@")[0],
        "full_name": request.full_name or "",
        "organization": request.organization
    }
    
    if request.provider == "local":
        if not request.password:
            raise HTTPException(
                status_code=400,
                detail="Password required for local registration"
            )
        user_data["password"] = request.password
    
    result = await auth_manager.register(request.provider, user_data)
    
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=result.error_message or "Registration failed"
        )
    
    return AuthResponse(
        success=True,
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_in=result.expires_in,
        user={
            "id": result.user_id,
            "email": result.email,
            "username": result.username,
            "full_name": result.full_name,
            "role": result.role,
            "organization": result.organization
        },
        provider=request.provider,
        message="Registration successful"
    )

@router.get("/oauth/{provider}/authorize")
async def oauth_authorize(provider: str, redirect_uri: str):
    """Initiate OAuth authorization flow"""
    
    if provider not in ["github", "google"]:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth not supported for provider: {provider}"
        )
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state in session/cache (simplified here)
    # In production, store in Redis with expiration
    
    auth_url = auth_manager.get_oauth_authorization_url(provider, state, redirect_uri)
    
    if not auth_url:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate authorization URL for {provider}"
        )
    
    return {
        "authorization_url": auth_url,
        "state": state
    }

@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str, state: str, redirect_uri: str):
    """Handle OAuth callback"""
    
    # Verify state (simplified here)
    # In production, verify against stored state
    
    result = await auth_manager.authenticate(provider, {
        "code": code,
        "redirect_uri": redirect_uri
    })
    
    if not result.success:
        raise HTTPException(
            status_code=401,
            detail=result.error_message or "OAuth authentication failed"
        )
    
    return AuthResponse(
        success=True,
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        expires_in=result.expires_in,
        user={
            "id": result.user_id,
            "email": result.email,
            "username": result.username,
            "full_name": result.full_name
        },
        provider=provider,
        message="OAuth authentication successful"
    )

@router.post("/refresh")
async def refresh_token(refresh_token: str, provider: str):
    """Refresh access token"""
    
    result = await auth_manager.refresh_token(refresh_token, provider)
    
    if not result.success:
        raise HTTPException(
            status_code=401,
            detail=result.error_message or "Token refresh failed"
        )
    
    return {
        "access_token": result.access_token,
        "expires_in": result.expires_in,
        "message": "Token refreshed successfully"
    }

@router.post("/logout")
async def logout(access_token: str, provider: str):
    """Logout user"""
    
    success = await auth_manager.logout(access_token, provider)
    
    return {
        "success": success,
        "message": "Logout successful" if success else "Logout failed"
    }

@router.post("/validate")
async def validate_token(access_token: str, provider: Optional[str] = None):
    """Validate access token"""
    
    result = await auth_manager.validate_token(access_token, provider)
    
    if not result.success:
        raise HTTPException(
            status_code=401,
            detail=result.error_message or "Invalid token"
        )
    
    return {
        "valid": True,
        "user": {
            "id": result.user_id,
            "email": result.email,
            "username": result.username,
            "full_name": result.full_name,
            "role": result.role,
            "organization": result.organization
        },
        "provider": result.metadata.get("provider")
    }
