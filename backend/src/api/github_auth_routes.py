"""
GitHub OAuth Authentication Routes
Simple GitHub login integration for CodeFlowOps with Cognito storage
"""
from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional, Any
import requests
import os
import logging
import uuid
from datetime import datetime

# Import Cognito provider for user storage
try:
    from ..auth.providers.cognito import CognitoAuthProvider
    COGNITO_AVAILABLE = True
except ImportError:
    try:
        from src.auth.providers.cognito import CognitoAuthProvider
        COGNITO_AVAILABLE = True
    except ImportError:
        COGNITO_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()

# GitHub OAuth configuration - Production Ready
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "Ov23li4xEOeDgSAMz2rg")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "65006527de2a3974af1a804b97fd6bcaac62b732")

# Production callback URL - this must match GitHub OAuth app settings
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL", "https://api.codeflowops.com/api/v1/auth/github/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://codeflowops.com")

# In-memory session storage (use Redis/database in production)
_github_sessions = {}

class GitHubUser(BaseModel):
    id: str
    login: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    provider: str = "github"

async def create_or_update_github_user_in_cognito(github_user: GitHubUser) -> Optional[Dict[str, Any]]:
    """Create or update GitHub user in Cognito and return auth tokens"""
    if not COGNITO_AVAILABLE:
        logger.warning("🚫 Cognito not available, falling back to session storage")
        return None
    
    try:
        logger.info(f"🔗 Initializing Cognito provider for user: {github_user.login}")
        cognito_provider = CognitoAuthProvider()
        
        # Check if user already exists in Cognito by email
        try:
            logger.info(f"🔍 Searching for existing user with email: {github_user.email}")
            
            # Try to find existing user by email
            existing_users = cognito_provider.cognito_client.list_users(
                UserPoolId=cognito_provider.user_pool_id,
                Filter=f'email = "{github_user.email}"'
            )
            
            if existing_users['Users']:
                # User exists, just return their info
                existing_user = existing_users['Users'][0]
                username = existing_user['Username']
                logger.info(f"✅ Found existing Cognito user: {username} for GitHub user: {github_user.login}")
                
                return {
                    "user_id": username,
                    "email": github_user.email,
                    "username": github_user.login,
                    "full_name": github_user.name,
                    "provider": "github",
                    "avatar_url": github_user.avatar_url
                }
                
            else:
                # Create new user with email as username (Cognito requirement)
                username = github_user.email  # Use email as username
                logger.info(f"👤 Creating new Cognito user with email as username: {username} for GitHub user: {github_user.login}")
                
                # Basic user attributes that should work in any Cognito setup
                user_attributes = [
                    {'Name': 'email', 'Value': github_user.email},
                    {'Name': 'email_verified', 'Value': 'true'}
                ]
                
                # Add name if available
                if github_user.name:
                    user_attributes.append({'Name': 'name', 'Value': github_user.name})
                
                logger.info(f"📝 User attributes: {user_attributes}")
                
                # Create user in Cognito
                logger.info("🔨 Creating user in Cognito...")
                response = cognito_provider.cognito_client.admin_create_user(
                    UserPoolId=cognito_provider.user_pool_id,
                    Username=username,  # Use email as username
                    UserAttributes=user_attributes,
                    MessageAction='SUPPRESS',  # Don't send welcome email
                    TemporaryPassword='TempPass123!'  # Required for admin creation
                )
                
                logger.info(f"✅ User created in Cognito successfully: {response.get('User', {}).get('Username')}")
                
                # Set permanent password for OAuth users (they won't use this)
                logger.info("� Setting permanent password for OAuth user...")
                cognito_provider.cognito_client.admin_set_user_password(
                    UserPoolId=cognito_provider.user_pool_id,
                    Username=username,
                    Password='GitHubOAuth123!',  # OAuth users won't use this password
                    Permanent=True
                )
                
                logger.info(f"🎉 New Cognito user {username} created and confirmed for GitHub user: {github_user.login}")
                
                return {
                    "user_id": username,
                    "email": github_user.email,
                    "username": github_user.login,
                    "full_name": github_user.name,
                    "provider": "github",
                    "avatar_url": github_user.avatar_url
                }
            
        except Exception as cognito_error:
            logger.error(f"💥 Cognito operation failed: {cognito_error}")
            # Log the specific error for debugging
            import traceback
            logger.error(f"📋 Cognito error traceback: {traceback.format_exc()}")
            return None
            
    except Exception as e:
        logger.error(f"💥 Error initializing Cognito provider: {e}")
        import traceback
        logger.error(f"📋 Cognito provider error traceback: {traceback.format_exc()}")
        return None

@router.get("/auth/github")
async def github_login(request: Request):
    """Initiate GitHub OAuth login"""
    try:
        logger.info("🚀 GitHub OAuth login initiated")
        
        # Generate state parameter for security
        state = str(uuid.uuid4())
        
        # Store state in session (in production, use secure session storage)
        session_id = str(uuid.uuid4())
        _github_sessions[session_id] = {
            "state": state,
            "created_at": datetime.utcnow(),
            "ip": request.client.host if request.client else "unknown"
        }
        
        # Build GitHub OAuth URL
        github_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={GITHUB_CLIENT_ID}"
            f"&redirect_uri={GITHUB_CALLBACK_URL}"
            f"&scope=read:user user:email"
            f"&state={state}"
        )
        
        logger.info(f"🔗 Redirecting to GitHub OAuth for session {session_id}")
        
        # Redirect to GitHub
        response = RedirectResponse(url=github_url)
        response.set_cookie(
            key="github_session_id", 
            value=session_id,
            max_age=600,  # 10 minutes
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error initiating GitHub OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate GitHub authentication"
        )

@router.get("/auth/github/callback")
async def github_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """Handle GitHub OAuth callback"""
    try:
        logger.info("🔄 GitHub OAuth callback received")
        logger.info(f"   Code: {'✅ present' if code else '❌ missing'}")
        logger.info(f"   State: {'✅ present' if state else '❌ missing'}")
        logger.info(f"   Error: {error if error else 'None'}")
        
        # Check for OAuth error
        if error:
            logger.warning(f"❌ GitHub OAuth error: {error}")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=github_oauth_error&message={error}"
            )
        
        if not code or not state:
            logger.warning("❌ Missing code or state parameter in GitHub callback")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=missing_parameters"
            )
        
        # Verify state parameter
        session_id = request.cookies.get("github_session_id")
        logger.info(f"🔑 Session ID from cookie: {'✅ present' if session_id else '❌ missing'}")
        
        if not session_id or session_id not in _github_sessions:
            logger.warning("❌ Invalid or missing session in GitHub callback")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=invalid_session"
            )
        
        session_data = _github_sessions[session_id]
        if session_data["state"] != state:
            logger.warning("❌ State parameter mismatch in GitHub callback")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=state_mismatch"
            )
        
        logger.info("✅ State verification successful, exchanging code for token...")
        
        # Exchange code for access token
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_CALLBACK_URL,
            },
            headers={"Accept": "application/json"},
            timeout=10
        )
        
        if token_response.status_code != 200:
            logger.error(f"GitHub token exchange failed: {token_response.status_code}")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=token_exchange_failed"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            logger.error("No access token received from GitHub")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=no_access_token"
            )
        
        # Get user profile from GitHub
        user_response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        if user_response.status_code != 200:
            logger.error(f"GitHub user API failed: {user_response.status_code}")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=user_fetch_failed"
            )
        
        user_data = user_response.json()
        
        # Get user's primary email
        email_response = requests.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        primary_email = None
        if email_response.status_code == 200:
            emails = email_response.json()
            primary_email = next(
                (email["email"] for email in emails if email.get("primary")),
                user_data.get("email")
            )
        else:
            primary_email = user_data.get("email")
        
        # Create user object
        github_user = GitHubUser(
            id=str(user_data["id"]),
            login=user_data["login"],
            email=primary_email or f"{user_data['login']}@github.user",
            name=user_data.get("name"),
            avatar_url=user_data.get("avatar_url"),
            provider="github"
        )
        
        # Clean up OAuth session
        del _github_sessions[session_id]
        
        # Try to store/update user in Cognito
        logger.info("💾 Attempting to store user in Cognito...")
        cognito_user_data = await create_or_update_github_user_in_cognito(github_user)
        
        if cognito_user_data:
            logger.info("✅ User successfully stored in Cognito!")
        else:
            logger.warning("⚠️ Failed to store user in Cognito, using session storage")
        
        # Create a session token
        session_token = f"github-session-{uuid.uuid4()}"
        
        # Store user session with Cognito data if available
        session_data = {
            "user": cognito_user_data if cognito_user_data else github_user.dict(),
            "created_at": datetime.utcnow(),
            "github_access_token": access_token,  # Store for potential API calls
            "stored_in_cognito": bool(cognito_user_data)
        }
        
        _github_sessions[session_token] = session_data
        
        if cognito_user_data:
            logger.info(f"🎉 GitHub authentication complete - user {github_user.login} stored in Cognito")
        else:
            logger.info(f"🎉 GitHub authentication complete - user {github_user.login} using session storage")
        
        # Redirect to frontend homepage with session token
        response = RedirectResponse(url=f"{FRONTEND_URL}/")
        response.set_cookie(
            key="codeflowops_session",
            value=session_token,
            max_age=86400,  # 24 hours
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return response
        
    except requests.RequestException as e:
        logger.error(f"Network error during GitHub authentication: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=network_error"
        )
    except Exception as e:
        logger.error(f"Unexpected error in GitHub callback: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?error=internal_error"
        )

@router.get("/auth/github/user")
async def get_github_user(request: Request):
    """Get current GitHub authenticated user"""
    try:
        session_token = request.cookies.get("codeflowops_session")
        
        if not session_token or session_token not in _github_sessions:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        
        session_data = _github_sessions[session_token]
        user_data = session_data["user"]
        
        return {
            "user": user_data,
            "authenticated": True,
            "provider": "github"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting GitHub user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.post("/auth/github/logout")
async def github_logout(request: Request):
    """Logout GitHub user"""
    try:
        session_token = request.cookies.get("codeflowops_session")
        
        if session_token and session_token in _github_sessions:
            del _github_sessions[session_token]
        
        response = JSONResponse(content={"message": "Logged out successfully"})
        response.delete_cookie("codeflowops_session")
        
        return response
        
    except Exception as e:
        logger.error(f"Error during GitHub logout: {e}")
        return JSONResponse(content={"message": "Logout completed"})

# Health check endpoint
@router.get("/auth/github/health")
async def github_auth_health():
    """Health check for GitHub auth service"""
    return {
        "status": "healthy",
        "service": "github_auth",
        "github_client_configured": bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET),
        "callback_url": GITHUB_CALLBACK_URL,
        "cognito_available": COGNITO_AVAILABLE
    }

# Debug endpoint to test Cognito integration
@router.get("/auth/github/test-cognito")
async def test_cognito_integration():
    """Test endpoint to verify Cognito integration"""
    if not COGNITO_AVAILABLE:
        return {"error": "Cognito not available", "details": "CognitoAuthProvider could not be imported"}
    
    try:
        cognito_provider = CognitoAuthProvider()
        
        # Test basic Cognito connection
        response = cognito_provider.cognito_client.describe_user_pool(
            UserPoolId=cognito_provider.user_pool_id
        )
        
        return {
            "status": "cognito_connected",
            "user_pool_name": response['UserPool']['Name'],
            "user_pool_id": cognito_provider.user_pool_id,
            "region": cognito_provider.region
        }
        
    except Exception as e:
        return {
            "error": "cognito_connection_failed",
            "details": str(e)
        }
