"""
GitHub OAuth Authentication Routes
Handles GitHub OAuth login and integrates with AWS Cognito
"""

from fastapi import APIRouter, HTTPException, Query, Request, status, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import logging
import uuid
import os
import asyncio
from urllib.parse import urlencode, urlparse
import time
from ..services.oauth_cognito_integration import oauth_cognito_service
from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

ALLOWED_FRONTENDS = {
    "https://www.codeflowops.com",
    "https://codeflowops.com",
}

def origin_only(u: str) -> str:
    p = urlparse((u or "").strip())
    return f"{p.scheme}://{p.netloc}".rstrip("/")

def sanitize_frontend_url(candidate: str) -> str:
    o = origin_only(candidate or settings.FRONTEND_URL or "")
    return o if o in ALLOWED_FRONTENDS else origin_only(settings.FRONTEND_URL)

# ---- Short-lived login token storage (Redis if available, otherwise in-memory) ----
LOGIN_TOKEN_TTL = 300  # 5 minutes

try:
    import redis.asyncio as redis  # pip install redis>=4
    _redis_url = os.getenv("REDIS_URL")
    _redis = redis.from_url(_redis_url, decode_responses=True) if _redis_url else None
except Exception:
    _redis = None

# In-memory fallback with TTL
_ephemeral_store = {}  # token -> (payload_dict, expiry_epoch)

async def store_login_token(token: str, payload: dict, ttl: int = LOGIN_TOKEN_TTL):
    expires_at = int(time.time()) + ttl
    if _redis:
        await _redis.hset(f"login_token:{token}", mapping=payload)
        await _redis.expire(f"login_token:{token}", ttl)
    else:
        _ephemeral_store[token] = (payload, expires_at)

async def pop_login_token(token: str) -> Optional[dict]:
    if _redis:
        key = f"login_token:{token}"
        exists = await _redis.exists(key)
        if not exists:
            return None
        data = await _redis.hgetall(key)
        await _redis.delete(key)
        return data or None
    else:
        item = _ephemeral_store.pop(token, None)
        if not item:
            return None
        payload, expires_at = item
        if time.time() > expires_at:
            return None
        return payload
# -----------------------------------------------------------------------------

def origin_only(u: str) -> str:
    """Ensure URL is origin-only, stripping any path segments"""
    p = urlparse((u or "").strip())
    return f"{p.scheme}://{p.netloc}".rstrip("/")

def build_frontend_callback_url(base: str, query: dict) -> str:
    """
    Always point to the static file to avoid SPA 404s on Amplify.
    Example: https://www.codeflowops.com/auth/callback/index.html?success=true...
    """
    base = sanitize_frontend_url(base)  # origin-only, whitelisted
    return f"{base}/auth/callback/index.html?{urlencode(query)}"

router = APIRouter(prefix="/api/v1/auth", tags=["GitHub OAuth Authentication"])


class GitHubOAuthResponse(BaseModel):
    """Response model for GitHub OAuth authentication"""
    success: bool
    message: str
    user: Optional[dict] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    cognito_integrated: bool = False


@router.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration values"""
    # Try to import AWS config manager to test it directly
    try:
        from ..config.aws_config import config_manager
        aws_config = config_manager.get_all_config()
        frontend_url_from_aws = config_manager.get_parameter('FRONTEND_URL')
        aws_available = config_manager.aws_available
        
        # Test direct SSM call
        try:
            import boto3
            ssm_client = boto3.client('ssm', region_name='us-east-1')
            direct_ssm_response = ssm_client.get_parameter(Name="/codeflowops/production/FRONTEND_URL")
            direct_ssm_value = direct_ssm_response['Parameter']['Value']
        except Exception as ssm_error:
            direct_ssm_value = f"Error: {str(ssm_error)}"
        
        return {
            "frontend_url": settings.FRONTEND_URL,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "aws_config": aws_config,
            "frontend_url_from_aws": frontend_url_from_aws,
            "aws_available": aws_available,
            "environment_var": os.getenv('ENVIRONMENT'),
            "frontend_url_env": os.getenv('FRONTEND_URL'),
            "direct_ssm_test": direct_ssm_value,
            "config_manager_details": {
                "app_name": config_manager.app_name,
                "environment": config_manager.environment,
                "region": config_manager.region,
                "expected_path": f"/{config_manager.app_name}/{config_manager.environment}/FRONTEND_URL"
            }
        }
    except Exception as e:
        return {
            "frontend_url": settings.FRONTEND_URL,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "aws_error": str(e),
            "environment_var": os.getenv('ENVIRONMENT'),
            "frontend_url_env": os.getenv('FRONTEND_URL')
        }


@router.get("/test-redirect")
async def test_redirect():
    """Test endpoint to see what redirect URL is being generated"""
    frontend_url = settings.FRONTEND_URL
    # DO NOT send real tokens here; this is only a structure preview
    q = {
        "success": "true",
        "user_id": "test_user",
        "email": "test@example.com",
        "username": "testuser",
        "login_token": "dummy",  # frontend would exchange this
        "cognito_integrated": "true"
    }
    return {
        "frontend_url": frontend_url,
        "redirect_url": build_frontend_callback_url(frontend_url, q),
        "message": "This is what the OAuth success redirect should look like",
        "will_redirect_to": f"{origin_only(frontend_url)}/auth/callback/index.html"
    }


@router.get("/force-redirect-test")
async def force_redirect_test():
    """Force redirect test to auth callback"""
    frontend_url = settings.FRONTEND_URL
    q = {"test": "true", "source": "backend_test"}
    return RedirectResponse(url=build_frontend_callback_url(frontend_url, q), status_code=302)


class GitHubAuthUrlResponse(BaseModel):
    """Response model for GitHub authorization URL"""
    authorization_url: str
    state: str


class GitHubCodeExchangeRequest(BaseModel):
    """Request model for GitHub code exchange"""
    code: str = Field(..., description="Authorization code from GitHub")
    redirect_uri: str = Field(..., description="Redirect URI that was used")
    state: Optional[str] = Field(None, description="State parameter")


class GitHubLinkRequest(BaseModel):
    """Request model for linking GitHub to existing user"""
    cognito_username: str = Field(..., description="Existing Cognito username")
    github_access_token: str = Field(..., description="GitHub access token")


class LoginTokenRequest(BaseModel):
    """Request model for consuming login token"""
    token: str


@router.get("/status")
async def auth_status():
    """
    Get authentication status
    Simple endpoint to check if the auth service is available
    """
    return {
        "authenticated": False,
        "message": "Authentication required",
        "login_url": "https://api.codeflowops.com/api/v1/auth/github/authorize"
    }


@router.get("/github/authorize", response_model=GitHubAuthUrlResponse)
async def get_github_auth_url(
    redirect_uri: str = Query(..., description="Frontend callback URL"),
    state: Optional[str] = Query(None, description="State parameter for CSRF protection")
):
    """
    Get GitHub OAuth authorization URL
    """
    try:
        # Generate state if not provided
        if not state:
            state = str(uuid.uuid4())
        
        # The redirect_uri should point to this backend callback, not frontend
        backend_redirect_uri = "https://api.codeflowops.com/api/v1/auth/github"
        
        # Get authorization URL
        auth_url = await oauth_cognito_service.get_oauth_authorization_url(
            provider="github",
            redirect_uri=backend_redirect_uri,
            state=state
        )
        
        # Store the original frontend redirect URI in session/cache if needed
        # For now, we'll pass it as part of the state
        enhanced_state = f"{state}|{redirect_uri}"
        
        # Replace the state in URL with enhanced state
        auth_url = auth_url.replace(f"state={state}", f"state={enhanced_state}")
        
        return GitHubAuthUrlResponse(
            authorization_url=auth_url,
            state=enhanced_state
        )
        
    except Exception as e:
        logger.error(f"Error generating GitHub auth URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {str(e)}"
        )


@router.get("/github")
async def github_oauth_callback(
    code: Optional[str] = Query(None, description="Authorization code from GitHub"),
    state: Optional[str] = Query(None, description="State parameter"),
    error: Optional[str] = Query(None, description="Error from GitHub"),
    error_description: Optional[str] = Query(None, description="Error description from GitHub")
):
    """Handle GitHub OAuth callback with immediate redirect to prevent timeouts"""
    # 1) Immediate error handling
    if error:
        fe = sanitize_frontend_url(settings.FRONTEND_URL)
        return RedirectResponse(
            url=f"{fe}/login?error={error}&error_description={error_description}",
            status_code=302
        )
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")

    # 2) Extract original frontend URL (right side of the '|')
    frontend_redirect_uri = None
    if state and "|" in state:
        _, frontend_redirect_uri = state.split("|", 1)

    # 3) Issue short-lived login_token and mark pending
    login_token = str(uuid.uuid4())
    await store_login_token(login_token, {"status": "pending"})

    # 4) Kick off the heavy work in the background and finish storing results
    async def finalize():
        try:
            backend_redirect_uri = "https://api.codeflowops.com/api/v1/auth/github"
            auth_result = await oauth_cognito_service.authenticate_with_oauth_and_store_in_cognito(
                provider="github",
                code=code,
                redirect_uri=backend_redirect_uri
            )
            if auth_result and auth_result.success:
                await store_login_token(login_token, {
                    "status": "ready",
                    "user_id": auth_result.user_id or "",
                    "email": auth_result.email or "",
                    "username": auth_result.username or "",
                    "full_name": auth_result.full_name or "",
                    "access_token": auth_result.access_token or "",
                    "refresh_token": auth_result.refresh_token or "",
                    "expires_in": str(auth_result.expires_in or 0),
                    "cognito_integrated": "true"
                })
            else:
                await store_login_token(login_token, {
                    "status": "error",
                    "message": (getattr(auth_result, "error_message", None) or "Auth failed")
                })
        except Exception as e:
            await store_login_token(login_token, {"status": "error", "message": str(e)})

    asyncio.create_task(finalize())

    # 5) Redirect immediately to the static file (no Amplify rewrites needed)
    fe = sanitize_frontend_url(frontend_redirect_uri or settings.FRONTEND_URL)
    query = {"success": "true", "login_token": login_token, "provider": "github"}
    return RedirectResponse(url=build_frontend_callback_url(fe, query), status_code=302)


@router.post("/session/consume", response_model=None)
async def consume_login_token(body: LoginTokenRequest):
    """Exchange login token for real credentials with polling support"""
    payload = await pop_login_token(body.token)
    if not payload:
        return JSONResponse({"success": False, "message": "Invalid or expired login token"}, status_code=400)

    status = payload.get("status", "ready")
    if status == "pending":
        # put back so next poll sees it
        await store_login_token(body.token, payload)
        return JSONResponse({"success": False, "pending": True, "message": "Finalizing"}, status_code=202)

    if status == "error":
        return JSONResponse({"success": False, "message": payload.get("message", "Auth failed")}, status_code=400)

    return JSONResponse({
        "success": True,
        "message": "Session established",
        "user": {
            "user_id": payload.get("user_id"),
            "email": payload.get("email"),
            "username": payload.get("username"),
            "full_name": payload.get("full_name")
        },
        "access_token": payload.get("access_token"),
        "refresh_token": payload.get("refresh_token"),
        "expires_in": int(payload.get("expires_in") or 0),
        "cognito_integrated": (payload.get("cognito_integrated") == "true")
    }, status_code=200)


@router.post("/github/exchange", response_model=GitHubOAuthResponse)
async def exchange_github_code(request: GitHubCodeExchangeRequest):
    """
    Exchange GitHub authorization code for tokens (alternative to callback)
    This endpoint can be called directly by the frontend
    """
    try:
        # Authenticate with GitHub and store in Cognito
        auth_result = await oauth_cognito_service.authenticate_with_oauth_and_store_in_cognito(
            provider="github",
            code=request.code,
            redirect_uri=request.redirect_uri
        )
        
        if not auth_result.success:
            logger.error(f"GitHub OAuth authentication failed: {auth_result.error_message}")
            return GitHubOAuthResponse(
                success=False,
                message=auth_result.error_message or "GitHub authentication failed"
            )
        
        logger.info(f"GitHub OAuth successful for user: {auth_result.email}")
        
        return GitHubOAuthResponse(
            success=True,
            message="GitHub authentication successful",
            user={
                "user_id": auth_result.user_id,
                "email": auth_result.email,
                "username": auth_result.username,
                "full_name": auth_result.full_name
            },
            access_token=auth_result.access_token,
            refresh_token=auth_result.refresh_token,
            expires_in=auth_result.expires_in,
            cognito_integrated=True
        )
        
    except Exception as e:
        logger.error(f"GitHub OAuth exchange error: {str(e)}")
        return GitHubOAuthResponse(
            success=False,
            message=f"Authentication failed: {str(e)}"
        )


@router.get("/github/user")
async def get_github_user_info(
    access_token: str = Query(..., description="GitHub access token")
):
    """
    Get GitHub user information using access token
    """
    try:
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            user_info = response.json()
        
        return {
            "success": True,
            "user": {
                "id": user_info.get("id"),
                "username": user_info.get("login"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "avatar_url": user_info.get("avatar_url"),
                "company": user_info.get("company"),
                "location": user_info.get("location"),
                "bio": user_info.get("bio")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting GitHub user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user information: {str(e)}"
        )


@router.post("/github/link")
async def link_github_to_existing_user(request: GitHubLinkRequest):
    """
    Link GitHub account to existing Cognito user
    """
    try:
        # Get GitHub user info
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {request.github_access_token}"}
            )
            response.raise_for_status()
            github_user = response.json()
        
        # Create auth result from GitHub data
        from ..auth.providers.base import AuthResult
        
        auth_result = AuthResult(
            success=True,
            user_id=str(github_user.get("id")),
            email=github_user.get("email"),
            username=github_user.get("login"),
            full_name=github_user.get("name"),
            metadata={"oauth_user_info": github_user}
        )
        
        # Link to existing Cognito user
        success = await oauth_cognito_service.link_oauth_to_existing_user(
            cognito_username=request.cognito_username,
            provider="github",
            oauth_result=auth_result
        )
        
        if success:
            return {
                "success": True,
                "message": "GitHub account successfully linked to Cognito user"
            }
        else:
            return {
                "success": False,
                "message": "Failed to link GitHub account"
            }
            
    except Exception as e:
        logger.error(f"Error linking GitHub account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link GitHub account: {str(e)}"
        )


@router.get("/github/user/current")
async def get_current_github_user_placeholder(request: Request):
    """
    Get current GitHub user info (placeholder endpoint)
    This endpoint is called by the frontend but we don't have session management yet
    """
    # For now, return 401 to indicate user needs to authenticate
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not authenticated. Please login with GitHub."
    )
