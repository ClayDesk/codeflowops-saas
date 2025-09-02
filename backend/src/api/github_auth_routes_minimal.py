"""
GitHub OAuth Authentication Routes - Working Version
Handles GitHub OAuth login and integrates with AWS Cognito
"""

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict
import logging
import uuid
import os
import json
import jwt  # PyJWT
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
import time
import boto3
import requests

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter()

# GitHub OAuth Configuration (with fallbacks)
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "Ov23li4xEOeDgSAMz2rg")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")

# JWT Secret for stateless tokens
SESSION_TOKEN_SECRET = os.getenv("SESSION_TOKEN_SECRET", "dev-session-secret-change-me-fallback")

class GitHubAuthUrlResponse(BaseModel):
    authorization_url: str
    state: str

class GitHubOAuthResponse(BaseModel):
    access_token: str
    user_info: Dict
    cognito_session: Optional[Dict] = None

@router.get("/test")
def test_endpoint():
    """Simple test endpoint to verify the router is working"""
    return {"status": "GitHub auth routes are working!", "test": True}

@router.get("/github/test")
def github_test_endpoint():
    """Test GitHub route path"""
    return {"status": "GitHub test endpoint working", "path": "/github/test"}

@router.get("/github/status")
def github_status():
    """GitHub OAuth status endpoint"""
    return {
        "service": "GitHub OAuth",
        "status": "active",
        "github_client_id": GITHUB_CLIENT_ID,
        "has_client_secret": bool(GITHUB_CLIENT_SECRET),
        "endpoints": ["/github/authorize", "/github/callback", "/github/test", "/github/status"]
    }

@router.get("/github/authorize", response_model=GitHubAuthUrlResponse)
def get_github_authorization_url(
    redirect_uri: str = Query(..., description="The redirect URI for OAuth callback"),
    next: Optional[str] = Query(None, description="URL to redirect to after successful authentication")
):
    """Generate GitHub OAuth authorization URL"""
    try:
        # Generate a unique state parameter
        state = str(uuid.uuid4())
        
        # Store the redirect info in the state (you could also use a database)
        state_data = {
            "redirect_uri": redirect_uri,
            "next": next,
            "timestamp": int(time.time())
        }
        
        # Create JWT token with state data
        state_token = jwt.encode(state_data, SESSION_TOKEN_SECRET, algorithm="HS256")
        
        # GitHub OAuth parameters
        params = {
            "client_id": GITHUB_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "user:email",
            "state": state_token,
            "response_type": "code"
        }
        
        # Build GitHub authorization URL
        auth_url = "https://github.com/login/oauth/authorize?" + urlencode(params)
        
        return GitHubAuthUrlResponse(
            authorization_url=auth_url,
            state=state_token
        )
        
    except Exception as e:
        logger.error(f"Error generating GitHub authorization URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate authorization URL")

@router.get("/github")
def github_oauth_redirect(
    redirect_uri: str = Query(..., description="The redirect URI for OAuth callback"),
    next: Optional[str] = Query(None, description="URL to redirect to after successful authentication")
):
    """Initiate GitHub OAuth flow - redirects to GitHub"""
    try:
        # Get the authorization URL
        auth_response = get_github_authorization_url(redirect_uri=redirect_uri, next=next)
        
        # Redirect to GitHub
        return RedirectResponse(url=auth_response.authorization_url)
        
    except Exception as e:
        logger.error(f"Error initiating GitHub OAuth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate GitHub OAuth")

@router.get("/github/callback")
async def github_oauth_callback(
    code: str = Query(..., description="Authorization code from GitHub"),
    state: str = Query(..., description="State parameter to prevent CSRF"),
    error: Optional[str] = Query(None, description="Error from GitHub OAuth")
):
    """Handle GitHub OAuth callback"""
    try:
        # Handle OAuth errors
        if error:
            logger.error(f"GitHub OAuth error: {error}")
            raise HTTPException(status_code=400, detail=f"GitHub OAuth error: {error}")
        
        # Verify and decode state
        try:
            state_data = jwt.decode(state, SESSION_TOKEN_SECRET, algorithms=["HS256"])
            redirect_uri = state_data.get("redirect_uri")
            next_url = state_data.get("next", "/profile")
        except jwt.InvalidTokenError:
            logger.error("Invalid state token")
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Exchange code for access token
        token_data = {
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code
        }
        
        headers = {"Accept": "application/json"}
        
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            data=token_data,
            headers=headers
        )
        
        if token_response.status_code != 200:
            logger.error(f"GitHub token exchange failed: {token_response.text}")
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        token_json = token_response.json()
        access_token = token_json.get("access_token")
        
        if not access_token:
            logger.error(f"No access token in response: {token_json}")
            raise HTTPException(status_code=400, detail="No access token received")
        
        # Get user info from GitHub
        user_response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/json"
            }
        )
        
        if user_response.status_code != 200:
            logger.error(f"Failed to get GitHub user info: {user_response.text}")
            raise HTTPException(status_code=400, detail="Failed to get user information")
        
        user_info = user_response.json()
        
        # Get user email (if not public)
        email = user_info.get("email")
        if not email:
            email_response = requests.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json"
                }
            )
            if email_response.status_code == 200:
                emails = email_response.json()
                primary_email = next((e for e in emails if e.get("primary")), None)
                if primary_email:
                    email = primary_email.get("email")
        
        # TODO: Integrate with AWS Cognito here
        # For now, just create a simple session
        
        # Create a simple session token
        session_data = {
            "user_id": user_info.get("id"),
            "username": user_info.get("login"),
            "email": email,
            "name": user_info.get("name"),
            "avatar_url": user_info.get("avatar_url"),
            "github_token": access_token,
            "exp": int(time.time()) + 3600  # 1 hour expiry
        }
        
        session_token = jwt.encode(session_data, SESSION_TOKEN_SECRET, algorithm="HS256")
        
        # Redirect back to the frontend with success
        frontend_callback_url = redirect_uri.replace("/auth/callback", "/auth/callback")
        redirect_url = f"{frontend_callback_url}?token={session_token}&next={next_url}&authenticated=true"
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in GitHub callback: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@router.post("/github/verify")
def verify_github_token(token: str):
    """Verify a GitHub session token"""
    try:
        payload = jwt.decode(token, SESSION_TOKEN_SECRET, algorithms=["HS256"])
        return {"valid": True, "user": payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

logger.info("✅ Full GitHub auth routes loaded successfully")
