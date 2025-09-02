"""
GitHub OAuth Authentication Routes
Handles GitHub OAuth login and integrates with AWS Cognito
"""

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import logging
import uuid
import os
from ..services.oauth_cognito_integration import oauth_cognito_service
from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
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
    test_redirect_url = (
        f"{frontend_url}/callback?"
        f"success=true&"
        f"user_id=test_user&"
        f"email=test@example.com&"
        f"username=testuser&"
        f"access_token=test_token&"
        f"cognito_integrated=true"
    )
    
    return {
        "frontend_url": frontend_url,
        "redirect_url": test_redirect_url,
        "message": "This is what the OAuth success redirect should look like",
        "will_redirect_to": f"{frontend_url}/callback"
    }


@router.get("/force-redirect-test")
async def force_redirect_test():
    """Force redirect test to auth callback"""
    frontend_url = settings.FRONTEND_URL
    redirect_url = f"{frontend_url}/callback?test=true&source=backend_test"
    
    return RedirectResponse(url=redirect_url, status_code=302)


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
    """
    Handle GitHub OAuth callback
    This is the callback URL configured in GitHub OAuth app
    """
    try:
        # Handle OAuth errors
        if error:
            error_msg = error_description or error
            logger.warning(f"GitHub OAuth error: {error_msg}")
            
            # Redirect to frontend with error
            frontend_url = settings.FRONTEND_URL
            return RedirectResponse(
                url=f"{frontend_url}/login?error={error}&error_description={error_description}",
                status_code=302
            )
        
        # Validate required parameters
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is required"
            )
        
        # Parse state to get original frontend redirect URI
        frontend_redirect_uri = None
        if state and "|" in state:
            state_parts = state.split("|", 1)
            state = state_parts[0]
            frontend_redirect_uri = state_parts[1]
        
        # The redirect_uri must match what was sent to GitHub
        backend_redirect_uri = "https://api.codeflowops.com/api/v1/auth/github"
        
        # Authenticate with GitHub and store in Cognito
        auth_result = await oauth_cognito_service.authenticate_with_oauth_and_store_in_cognito(
            provider="github",
            code=code,
            redirect_uri=backend_redirect_uri
        )
        
        if not auth_result.success:
            logger.error(f"GitHub OAuth authentication failed: {auth_result.error_message}")
            
            # Redirect to frontend with error
            frontend_url = frontend_redirect_uri or settings.FRONTEND_URL
            return RedirectResponse(
                url=f"{frontend_url}/login?error=auth_failed&error_description={auth_result.error_message}",
                status_code=302
            )
        
        # Success - redirect to frontend with tokens
        frontend_url = frontend_redirect_uri or settings.FRONTEND_URL
        
        # For security, we'll include a success token that the frontend can exchange for the actual tokens
        success_token = str(uuid.uuid4())
        
        # Store the auth result temporarily (in production, use Redis or similar)
        # Redirect to auth callback page with user info
        redirect_url = (
            f"{frontend_url}/callback?"
            f"success=true&"
            f"user_id={auth_result.user_id}&"
            f"email={auth_result.email}&"
            f"username={auth_result.username}&"
            f"access_token={auth_result.access_token}&"
            f"cognito_integrated=true"
        )
        
        logger.info(f"GitHub OAuth successful for user: {auth_result.email}")
        
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub OAuth callback error: {str(e)}")
        
        # Redirect to frontend with error
        frontend_url = settings.FRONTEND_URL
        return RedirectResponse(
            url=f"{frontend_url}/login?error=server_error&error_description=Internal server error",
            status_code=302
        )


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


@router.get("/github/user")
async def get_github_user(request: Request):
    """
    Get current GitHub user info (placeholder endpoint)
    This endpoint is called by the frontend but we don't have session management yet
    """
    # For now, return 401 to indicate user needs to authenticate
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not authenticated. Please login with GitHub."
    )
