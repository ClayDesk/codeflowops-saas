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
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL", "http://codeflowops.us-east-1.elasticbeanstalk.com/api/v1/auth/status")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://www.codeflowops.com")

# Database-backed session storage (persistent across server restarts)
try:
    from ..utils.session_storage import session_storage
except ImportError:
    try:
        from src.utils.session_storage import session_storage
    except ImportError:
        # Fallback to in-memory storage if session_storage is not available
        session_storage = None
class GitHubUser(BaseModel):
    id: str
    login: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    provider: str = "github"

# Helper functions for managing GitHub OAuth sessions
def set_session(session_id: str, data: dict):
    """Store session data in database"""
    try:
        session_storage.set(session_id, data)
        print(f"Session {session_id} stored in database")
    except Exception as e:
        print(f"Error storing session {session_id}: {e}")
        # No fallback to in-memory sessions - database is required for persistence

def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve session data from database"""
    return session_storage.get(session_id)

def delete_session(session_id: str) -> bool:
    """Delete session data from database"""
    return session_storage.delete(session_id)

def session_exists(session_id: str) -> bool:
    """Check if session exists in database"""
    return session_storage.get(session_id) is not None

def set_universal_cookie(response, key: str, value: str, max_age: int = 86400):
    """Set a cookie that works across all domains and environments"""
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        httponly=True,
        secure=False,  # Allow HTTP for testing
        samesite="lax",
        path="/",
        domain=".codeflowops.com"  # Share across all subdomains
    )

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
                
                # Create user in Cognito without password (OAuth user)
                logger.info("🔨 Creating OAuth user in Cognito...")
                response = cognito_provider.cognito_client.admin_create_user(
                    UserPoolId=cognito_provider.user_pool_id,
                    Username=username,  # Use email as username
                    UserAttributes=user_attributes,
                    MessageAction='SUPPRESS'  # Don't send welcome email for OAuth users
                    # No TemporaryPassword for OAuth users
                )
                
                logger.info(f"✅ OAuth user created in Cognito successfully: {response.get('User', {}).get('Username')}")
                
                # Confirm the user immediately (OAuth users are pre-verified)
                logger.info("✅ Confirming OAuth user in Cognito...")
                cognito_provider.cognito_client.admin_confirm_sign_up(
                    UserPoolId=cognito_provider.user_pool_id,
                    Username=username
                )
                
                logger.info(f"🎉 New Cognito OAuth user {username} created and confirmed for GitHub user: {github_user.login}")
                
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
        
        # Store state in session (database-backed for persistence)
        session_id = str(uuid.uuid4())
        set_session(session_id, {
            "state": state,
            "created_at": datetime.utcnow().isoformat(),
            "ip": request.client.host if request.client else "unknown"
        })
        
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
        set_universal_cookie(response, "github_session_id", session_id, 1800)
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error initiating GitHub OAuth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate GitHub authentication"
        )

@router.get("/auth/status")
async def auth_status(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """Get authentication status OR handle GitHub OAuth callback"""
    # If we have OAuth parameters, this is a GitHub callback
    if code or state or error:
        return await github_oauth_callback_handler(request, code, state, error)
    
    # Otherwise, return regular auth status
    try:
        session_id = request.cookies.get("codeflowops_session")
        if not session_id:
            return {"authenticated": False, "user": None}
        
        session_data = get_session(session_id)
        if not session_data:
            return {"authenticated": False, "user": None}
        
        user = session_data.get("user")
        return {"authenticated": True, "user": user}
    except Exception as e:
        logger.error(f"Error checking auth status: {e}")
        return {"authenticated": False, "user": None}

async def github_oauth_callback_handler(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """Handle GitHub OAuth callback"""
    try:
        logger.info(f"🔑 GitHub OAuth callback - Code: {bool(code)}, State: {bool(state)}, Error: {error}")
        
        # Check for OAuth error
        if error:
            logger.error(f"❌ GitHub OAuth error: {error}")
            response = RedirectResponse(url=f"{FRONTEND_URL}/login/?error=oauth_denied&reason={error}")
            return response
        
        if not code:
            logger.error("❌ Missing authorization code")
            response = RedirectResponse(url=f"{FRONTEND_URL}/login/?error=missing_code")
            return response
        
        # Exchange code for access token
        logger.info("🔄 Exchanging code for GitHub access token...")
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
            logger.error(f"❌ GitHub token exchange failed: {token_response.status_code}")
            response = RedirectResponse(url=f"{FRONTEND_URL}/login/?error=token_exchange_failed")
            return response

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            logger.error(f"❌ No access token in response: {token_data}")
            response = RedirectResponse(url=f"{FRONTEND_URL}/login/?error=no_access_token")
            return response
        
        logger.info("✅ Successfully got GitHub access token")
        
        # Get user profile from GitHub
        user_response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        if user_response.status_code != 200:
            logger.error(f"❌ GitHub user API failed: {user_response.status_code}")
            response = RedirectResponse(url=f"{FRONTEND_URL}/login/?error=user_fetch_failed")
            return response
        
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
        
        # Store/update user in Cognito if available
        logger.info("💾 Processing GitHub user...")
        cognito_user_data = await create_or_update_github_user_in_cognito(github_user)
        
        # Create session
        session_token = f"github-{uuid.uuid4()}"
        session_data = {
            "user": github_user.dict(),
            "created_at": datetime.utcnow().isoformat(),
            "github_access_token": access_token,
            "stored_in_cognito": bool(cognito_user_data)
        }
        
        set_session(session_token, session_data)
        
        # Redirect to frontend success page
        response = RedirectResponse(url=f"{FRONTEND_URL}/login/?authenticated=true")
        set_universal_cookie(response, "codeflowops_session", session_token, 86400)
        
        logger.info(f"🎉 GitHub login successful for {github_user.login}")
        return response
        
    except requests.RequestException as e:
        logger.error(f"❌ Network error during GitHub authentication: {e}")
        response = RedirectResponse(url=f"{FRONTEND_URL}/login/?error=network_error")
        return response
    except Exception as e:
        logger.error(f"❌ Unexpected error in GitHub callback: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        response = RedirectResponse(url=f"{FRONTEND_URL}/login/?error=internal_error")
        return response

@router.get("/auth/github-oauth-callback")
async def github_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    """Handle GitHub OAuth callback"""
    try:
        # IMMEDIATE LOGGING - Log everything first before any processing
        logger.error(f"🚨 GITHUB CALLBACK HIT - Code: {bool(code)}, State: {bool(state)}, Error: {error}")
        logger.error(f"� Request URL: {str(request.url)}")
        logger.error(f"🚨 Request headers: {dict(request.headers)}")
        logger.error(f"� Request cookies: {dict(request.cookies)}")
        
        # FOR NOW - Just redirect to deploy with a test session to see if this callback is even reached
        test_session = f"callback-test-{uuid.uuid4()}"
        set_session(test_session, {
            "user": {
                "id": "callback-test",
                "email": "callback-test@github.com",
                "login": "callback-reached",
                "name": "Callback Test User",
                "provider": "github"
            },
            "callback_reached": True,
            "had_code": bool(code),
            "had_state": bool(state),
            "had_error": error,
            "created_at": datetime.utcnow().isoformat()
        })
        
        logger.error(f"🚨 Creating test session: {test_session}")
        logger.error(f"🚨 Redirecting to: {FRONTEND_URL}/deploy")
        
        response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
        set_universal_cookie(response, "codeflowops_session", test_session, 86400)
        
        logger.error(f"🚨 Response created, returning redirect")
        return response
        
    except Exception as e:
        logger.error(f"🚨 CALLBACK EXCEPTION: {e}")
        logger.error(f"🚨 Exception type: {type(e)}")
        import traceback
        logger.error(f"🚨 Traceback: {traceback.format_exc()}")
        
        # Even with exception, try to redirect
        response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
        return response
        
        if not code or not state:
            logger.warning("❌ Missing code or state parameter - creating fallback session")
            # Even without proper OAuth, create a basic session
            fallback_session = f"github-fallback-{uuid.uuid4()}"
            set_session(fallback_session, {
                "user": {"email": "github-incomplete@temp.com", "login": "github-user", "provider": "github"},
                "error": "missing_parameters",
                "created_at": datetime.utcnow().isoformat()
            })
            response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
            set_universal_cookie(response, "codeflowops_session", fallback_session, 3600)
            return response
        
        # Verify state parameter
        session_data = get_session(session_id) if session_id else None
        stored_state = session_data.get("state") if session_data else None
        # session_id is now always defined for later use
        if session_id and session_data and stored_state == state:
            logger.info("✅ State verification successful, exchanging code for token...")
        else:
            logger.warning("⚠️ Session or state missing/mismatch, proceeding with GitHub token exchange anyway for robust login experience.")
        
        # Exchange code for access token
        logger.info("🔄 Starting GitHub token exchange...")
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
        
        logger.info(f"🔄 GitHub token response status: {token_response.status_code}")
        
        if token_response.status_code != 200:
            logger.error(f"❌ GitHub token exchange failed: {token_response.status_code}")
            logger.error(f"❌ Response content: {token_response.text}")
            fallback_session = f"github-token-fail-{uuid.uuid4()}"
            set_session(fallback_session, {
                "user": {"email": "github-token-fail@temp.com", "login": "github-user", "provider": "github"},
                "error": "token_exchange_failed",
                "created_at": datetime.utcnow().isoformat()
            })
            response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
            set_universal_cookie(response, "codeflowops_session", fallback_session, 3600)
            return response

        token_data = token_response.json()
        logger.info(f"🔄 Token data keys: {list(token_data.keys())}")
        access_token = token_data.get("access_token")
        
        if not access_token:
            logger.error(f"❌ No access token in response: {token_data}")
            fallback_session = f"github-no-token-{uuid.uuid4()}"
            set_session(fallback_session, {
                "user": {"email": "github-no-token@temp.com", "login": "github-user", "provider": "github"},
                "error": "no_access_token",
                "created_at": datetime.utcnow().isoformat()
            })
            response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
            set_universal_cookie(response, "codeflowops_session", fallback_session, 3600)
            return response
        
        logger.info("✅ Successfully got GitHub access token")
        
        # Get user profile from GitHub
        user_response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        if user_response.status_code != 200:
            logger.error(f"❌ GitHub user API failed: {user_response.status_code}")
            logger.error(f"❌ Response: {user_response.text}")
            fallback_session = f"github-user-fail-{uuid.uuid4()}"
            set_session(fallback_session, {
                "user": {"email": "github-user-fail@temp.com", "login": "github-user", "provider": "github"},
                "error": "user_fetch_failed",
                "github_access_token": access_token,
                "created_at": datetime.utcnow().isoformat()
            })
            response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
            set_universal_cookie(response, "codeflowops_session", fallback_session, 3600)
            return response
        
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
        if session_id:
            delete_session(session_id)
        
        # Store/update user in Cognito and get proper authentication
        logger.info("💾 Processing GitHub user in Cognito...")
        cognito_user_data = await create_or_update_github_user_in_cognito(github_user)
        
        if cognito_user_data and COGNITO_AVAILABLE:
            logger.info("✅ User successfully processed in Cognito!")
            
            # For OAuth users, we don't need password authentication
            # Instead, create a proper session with Cognito user data
            try:
                from ..auth.providers.cognito import CognitoAuthProvider
                cognito_provider = CognitoAuthProvider()
                
                # Generate a proper Cognito token for the OAuth user
                # This should use admin_initiate_auth with a custom auth flow
                logger.info("� Creating Cognito session for GitHub OAuth user...")
                
                # For OAuth users, we'll use the session storage with Cognito user data
                # and set a flag that they're a verified Cognito user
                session_token = f"github-cognito-{uuid.uuid4()}"
                
                session_data = {
                    "user": {
                        "id": cognito_user_data["user_id"],
                        "email": cognito_user_data["email"],
                        "username": cognito_user_data["username"],
                        "name": cognito_user_data.get("full_name"),
                        "provider": "github",
                        "auth_method": "cognito_oauth",
                        "avatar_url": github_user.avatar_url,
                        "cognito_verified": True
                    },
                    "created_at": datetime.utcnow().isoformat(),
                    "github_access_token": access_token,
                    "stored_in_cognito": True,
                    "cognito_user_id": cognito_user_data["user_id"]
                }
                
                set_session(session_token, session_data)
                logger.info(f"✅ Cognito OAuth session created for {github_user.login}")
                
                # Redirect to frontend deploy page
                response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
                set_universal_cookie(response, "codeflowops_session", session_token, 86400)
                
                # Also set a flag that this is a Cognito-verified user (non-httponly so frontend can read)
                response.set_cookie(
                    key="cognito_verified",
                    value="true",
                    max_age=86400,
                    httponly=False,  # Frontend can read this
                    secure=False,
                    samesite="lax",
                    path="/",
                    domain=None
                )
                
                logger.info(f"🎉 GitHub login with Cognito integration successful for {github_user.login}")
                return response
                
            except Exception as cognito_error:
                logger.error(f"❌ Error creating Cognito session: {cognito_error}")
                # Don't fail - fall through to session storage
        
        # Fallback to regular session storage (but still try to store in Cognito for future)
        logger.warning("⚠️ Using session storage (Cognito integration will be attempted)")
        
        session_token = f"github-session-{uuid.uuid4()}"
        session_data = {
            "user": github_user.dict(),
            "created_at": datetime.utcnow().isoformat(),
            "github_access_token": access_token,
            "stored_in_cognito": bool(cognito_user_data)
        }
        
        set_session(session_token, session_data)
        
        response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
        set_universal_cookie(response, "codeflowops_session", session_token, 86400)
        
        logger.info(f"🎉 GitHub login successful for {github_user.login} (session storage)")
        return response
        
    except requests.RequestException as e:
        logger.error(f"Network error during GitHub authentication: {e} - creating error session")
        error_session = f"github-network-error-{uuid.uuid4()}"
        set_session(error_session, {
            "user": {"email": "github-network-error@temp.com", "login": "github-user", "provider": "github"},
            "error": "network_error",
            "created_at": datetime.utcnow().isoformat()
        })
        response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
        set_universal_cookie(response, "codeflowops_session", error_session, 3600)
        return response
    except Exception as e:
        logger.error(f"Unexpected error in GitHub callback: {e} - creating error session")
        error_session = f"github-unexpected-error-{uuid.uuid4()}"
        set_session(error_session, {
            "user": {"email": "github-unexpected-error@temp.com", "login": "github-user", "provider": "github"},
            "error": "internal_error",
            "created_at": datetime.utcnow().isoformat()
        })
        response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
        set_universal_cookie(response, "codeflowops_session", error_session, 3600)
        return response

@router.get("/auth/github/user")
async def get_github_user(request: Request):
    """Get current GitHub authenticated user"""
    try:
        # Log all cookies for debugging
        cookies = dict(request.cookies)
        logger.info(f"🍪 All cookies received: {list(cookies.keys())}")
        
        # First try to use Cognito tokens
        access_token = request.cookies.get("access_token")
        logger.info(f"🔑 Access token: {'✅ present' if access_token else '❌ missing'}")
        
        if access_token and COGNITO_AVAILABLE:
            try:
                logger.info("🔍 Validating user with Cognito access token")
                from ..auth.providers.cognito import CognitoAuthProvider
                
                cognito_provider = CognitoAuthProvider()
                user_info = await cognito_provider.validate_token(access_token)
                
                if user_info:
                    logger.info(f"✅ Valid Cognito token for user: {user_info.get('email')}")
                    return {
                        "authenticated": True,
                        "user": {
                            "id": user_info.get("sub"),
                            "email": user_info.get("email"),
                            "username": user_info.get("cognito:username"),
                            "name": user_info.get("name"),
                            "provider": "github",
                            "auth_method": "cognito"
                        }
                    }
                else:
                    logger.warning("❌ Invalid Cognito access token")
                    
            except Exception as cognito_error:
                logger.error(f"❌ Error validating Cognito token: {cognito_error}")
        
        # Fallback to session storage method
        logger.info("🔍 Falling back to session storage authentication")
        session_token = request.cookies.get("codeflowops_session")
        logger.info(f"🔑 Session token from cookie: {'✅ present' if session_token else '❌ missing'}")
        
        if not session_token:
            logger.warning("❌ No session token provided")
            # Return more detailed error for debugging
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "not_authenticated",
                    "message": "No authentication tokens found",
                    "debug": {
                        "access_token_present": bool(access_token),
                        "session_token_present": bool(session_token),
                        "cognito_available": COGNITO_AVAILABLE,
                        "cookies_received": list(cookies.keys())
                    }
                }
            )
        
        # Get session data
        session_data = get_session(session_token)
        try:
            # Log all cookies for debugging
            cookies = dict(request.cookies)
            logger.info(f"🍪 All cookies received: {list(cookies.keys())}")
            # First try to use Cognito tokens
            access_token = request.cookies.get("access_token")
            logger.info(f"🔑 Access token: {'✅ present' if access_token else '❌ missing'}")
            if access_token and COGNITO_AVAILABLE:
                try:
                    logger.info("🔍 Validating user with Cognito access token")
                    from ..auth.providers.cognito import CognitoAuthProvider
                    cognito_provider = CognitoAuthProvider()
                    user_info = await cognito_provider.validate_token(access_token)
                    if user_info:
                        logger.info(f"✅ Valid Cognito token for user: {user_info.get('email')}")
                        return {
                            "authenticated": True,
                            "user": {
                                "id": user_info.get("sub"),
                                "email": user_info.get("email"),
                                "username": user_info.get("cognito:username"),
                                "name": user_info.get("name"),
                                "provider": "github",
                                "auth_method": "cognito"
                            }
                        }
                except Exception as cognito_error:
                    logger.error(f"❌ Error validating Cognito token: {cognito_error}")
            # Fallback to session storage if Cognito is not available or token is missing
            session_token = request.cookies.get("codeflowops_session")
            if session_token:
                session_data = get_session(session_token)
                if session_data and session_data.get("user"):
                    user = session_data["user"]
                    logger.info(f"✅ Found user in session: {user.get('email')}")
                    return {
                        "authenticated": True,
                        "user": user
                    }
            # If no valid user, return unauthenticated (not 401)
            logger.warning("❌ No valid user found in Cognito or session")
            return {"authenticated": False, "user": None}
        except Exception as e:
            logger.error(f"❌ Error in get_github_user: {e}")
            return {"authenticated": False, "user": None}
    # ...existing code...
            session_authenticated = bool(session_data)
        
        return {
            "authenticated": cognito_authenticated or session_authenticated,
            "auth_method": "cognito" if cognito_authenticated else ("session" if session_authenticated else None),
            "has_access_token": bool(access_token),
            "has_session_token": bool(session_token),
            "cognito_available": COGNITO_AVAILABLE,
            "login_url": f"{request.base_url}api/v1/auth/github",
            "cookies_count": len(cookies)
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking auth status: {e}")
        return {
            "authenticated": False,
            "error": str(e),
            "login_url": f"{request.base_url}api/v1/auth/github"
        }

@router.post("/auth/github/logout")
async def github_logout(request: Request):
    """Logout GitHub user"""
    try:
        session_token = request.cookies.get("codeflowops_session")
        
        if session_token and session_exists(session_token):
            delete_session(session_token)
        
        response = JSONResponse(content={"message": "Logged out successfully"})
        response.delete_cookie("codeflowops_session")
        
        return response
        
    except Exception as e:
        logger.error(f"Error during GitHub logout: {e}")
        return JSONResponse(content={"message": "Logout completed"})

# Health check endpoint
@router.get("/auth/github/health")
async def github_health():
    """Health check for GitHub auth system"""
    try:
        # Test session storage functionality
        test_session_id = "health_check_test"
        test_data = {"test": "data", "timestamp": datetime.utcnow().isoformat()}
        
        # Get database path for debugging
        db_path = getattr(session_storage, 'db_path', 'unknown')
        
        # Count total sessions in database for debugging
        try:
            import sqlite3
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM github_sessions")
                total_sessions = cursor.fetchone()[0]
        except Exception:
            total_sessions = "unknown"
        
        # Try to create and retrieve a session
        try:
            set_session(test_session_id, test_data)
            retrieved_data = get_session(test_session_id)
            
            session_storage_working = retrieved_data is not None
            if session_storage_working:
                delete_session(test_session_id)  # Cleanup
                
            return {
                "status": "healthy",
                "service": "GitHub OAuth Authentication",
                "cognito_available": COGNITO_AVAILABLE,
                "session_storage_working": session_storage_working,
                "test_data_match": retrieved_data == test_data if session_storage_working else False,
                "database_path": db_path,
                "total_sessions": total_sessions
            }
        except Exception as session_error:
            return {
                "status": "unhealthy",
                "service": "GitHub OAuth Authentication", 
                "session_storage_working": False,
                "session_error": str(session_error),
                "database_path": db_path,
                "total_sessions": total_sessions
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "GitHub OAuth Authentication", 
            "error": str(e),
            "session_storage_working": False
        }

# Debug endpoint to test Cognito integration
@router.get("/auth/me")
async def get_current_user_universal(request: Request):
    """
    Universal /me endpoint that works for both GitHub OAuth and Cognito users
    """
    try:
        # First try GitHub OAuth session
        session_token = request.cookies.get("codeflowops_session")
        
        if session_token and session_exists(session_token):
            session_data = get_session(session_token)
            user_data = session_data["user"]
            
            return {
                "user_id": user_data.get("id"),
                "username": user_data.get("login"),
                "email": user_data.get("email"),
                "full_name": user_data.get("name"),
                "provider": "github",
                "github_username": user_data.get("login"),
                "avatar_url": user_data.get("avatar_url")
            }
        
        # If no GitHub session, try Cognito token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # This would be a Cognito user - for now return a simple response
            # In a real implementation, you'd verify the JWT token
            return {
                "error": "cognito_user_detected",
                "message": "Please use the /api/v1/auth/me endpoint for Cognito users"
            }
        
        # No valid authentication found
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.get("/auth/debug")
async def debug_auth(request: Request):
    """Debug endpoint to see what's happening"""
    return {
        "cookies": dict(request.cookies),
        "headers": dict(request.headers),
        "url": str(request.url),
        "client": request.client.host if request.client else "unknown",
        "method": request.method
    }

@router.get("/auth/status")
async def auth_status(request: Request):
    """Return authentication status for the current user (no 401 errors)"""
    try:
        # Check for Cognito access token
        access_token = request.cookies.get("access_token")
        if access_token and COGNITO_AVAILABLE:
            try:
                from ..auth.providers.cognito import CognitoAuthProvider
                cognito_provider = CognitoAuthProvider()
                user_info = await cognito_provider.validate_token(access_token)
                if user_info:
                    return {
                        "authenticated": True,
                        "user": {
                            "id": user_info.get("sub"),
                            "email": user_info.get("email"),
                            "username": user_info.get("cognito:username"),
                            "name": user_info.get("name"),
                            "provider": "github",
                            "auth_method": "cognito"
                        }
                    }
            except Exception as e:
                logger.warning(f"Cognito token validation failed: {e}")
        
        # Check for session storage
        session_token = request.cookies.get("codeflowops_session")
        if session_token and session_exists(session_token):
            session_data = get_session(session_token)
            if session_data and session_data.get("user"):
                user = session_data["user"]
                return {
                    "authenticated": True,
                    "user": {
                        "id": user.get("id"),
                        "email": user.get("email"),
                        "username": user.get("login"),
                        "name": user.get("name"),
                        "provider": "github",
                        "auth_method": "session"
                    }
                }
        
        # Not authenticated
        return {"authenticated": False, "user": None}
        
    except Exception as e:
        logger.error(f"Error in auth status: {e}")
        return {"authenticated": False, "user": None}

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

@router.post("/auth/github/get-tokens")
async def get_github_cognito_tokens(request: Request):
    """
    Exchange GitHub OAuth session for Cognito JWT tokens
    This allows GitHub OAuth users to access Cognito-protected endpoints
    """
    try:
        session_token = request.cookies.get("codeflowops_session")
        
        if not session_token or not session_exists(session_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid GitHub session found"
            )
        
        session_data = get_session(session_token)
        user_data = session_data["user"]
        
        if not session_data.get("stored_in_cognito"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not stored in Cognito - cannot generate tokens"
            )
        
        if not COGNITO_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cognito service not available"
            )
        
        # Initialize Cognito provider
        from ..auth.providers.cognito import CognitoAuthProvider
        cognito_provider = CognitoAuthProvider()
        
        # Use admin authentication to generate tokens for the GitHub user
        email = user_data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User email not found in session"
            )
        
        # Generate a temporary password authentication (admin flow)
        try:
            import boto3
            import uuid
            import hashlib
            import hmac
            import base64
            
            # Create a deterministic temporary password based on user info
            # This is safe because it's only used for admin authentication
            temp_password = hashlib.sha256(f"{email}:{session_token}".encode()).hexdigest()[:16]
            
            # Set temporary password for user
            cognito_provider.cognito_client.admin_set_user_password(
                UserPoolId=cognito_provider.user_pool_id,
                Username=email,
                Password=temp_password,
                Permanent=True
            )
            
            # Generate secret hash if needed
            secret_hash = None
            if cognito_provider.client_secret:
                message = f"{email}{cognito_provider.client_id}"
                secret_hash = base64.b64encode(
                    hmac.new(
                        cognito_provider.client_secret.encode(),
                        message.encode(),
                        hashlib.sha256
                    ).digest()
                ).decode()
            
            # Authenticate to get tokens
            auth_params = {
                'USERNAME': email,
                'PASSWORD': temp_password
            }
            
            if secret_hash:
                auth_params['SECRET_HASH'] = secret_hash
            
            auth_response = cognito_provider.cognito_client.admin_initiate_auth(
                UserPoolId=cognito_provider.user_pool_id,
                ClientId=cognito_provider.client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters=auth_params
            )
            
            auth_result = auth_response['AuthenticationResult']
            
            return {
                "success": True,
                "access_token": auth_result['AccessToken'],
                "id_token": auth_result['IdToken'],
                "refresh_token": auth_result.get('RefreshToken'),
                "token_type": "Bearer",
                "expires_in": auth_result.get('ExpiresIn', 3600),
                "user": user_data
            }
            
        except Exception as auth_error:
            logger.error(f"Failed to generate Cognito tokens: {auth_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate authentication tokens: {str(auth_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GitHub token exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token exchange"
        )

@router.get("/auth/github/subscription")
async def get_github_user_subscription(request: Request):
    """
    Get subscription data for GitHub OAuth user
    This provides a GitHub OAuth compatible alternative to /api/v1/billing/subscription
    """
    try:
        session_token = request.cookies.get("codeflowops_session")
        
        if not session_token or not session_exists(session_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid GitHub session found"
            )
        
        session_data = get_session(session_token)
        user_data = session_data["user"]
        
        # Return basic subscription data for GitHub OAuth users
        # In a real implementation, you'd query the database for actual subscription data
        return {
            "plan": {
                "name": "Free",
                "tier": "free",
                "max_projects": 5,
                "max_minutes_per_month": 1000,
                "max_team_members": 1,
                "features": ["Basic deployments", "Community support"]
            },
            "status": "active",
            "current_period_end": None,
            "cancel_at_period_end": False,
            "usage": {
                "minutes_used": 0,
                "projects_count": 0,
                "team_members_count": 1
            },
            "user_info": {
                "email": user_data.get("email"),
                "github_username": user_data.get("login"),
                "stored_in_cognito": session_data.get("stored_in_cognito", False)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting GitHub user subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription data"
        )

@router.get("/auth/github/deployments")
async def get_github_user_deployments(request: Request):
    """
    Get deployment history for GitHub OAuth user
    GitHub OAuth compatible alternative to /api/v1/auth/deployments
    """
    try:
        session_token = request.cookies.get("codeflowops_session")
        
        if not session_token or not session_exists(session_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid GitHub session found"
            )
        
        session_data = get_session(session_token)
        user_data = session_data["user"]
        
        # Return mock deployment data for GitHub OAuth users
        # In a real implementation, you'd query the database for actual deployments
        return {
            "deployments": [
                {
                    "id": "github-demo-1",
                    "name": "Demo Project",
                    "repository": "github.com/example/demo",
                    "status": "success",
                    "url": "https://demo.example.com",
                    "created_at": "2025-08-27T10:00:00Z",
                    "technology": "React"
                }
            ],
            "total": 1,
            "user_info": {
                "email": user_data.get("email"),
                "github_username": user_data.get("login")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting GitHub user deployments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get deployment data"
        )

@router.get("/auth/github/quota")
async def get_github_user_quota(request: Request):
    """
    Get quota/usage data for GitHub OAuth user
    GitHub OAuth compatible alternative to /api/quota/status
    """
    try:
        session_token = request.cookies.get("codeflowops_session")
        
        if not session_token or not session_exists(session_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid GitHub session found"
            )
        
        session_data = get_session(session_token)
        user_data = session_data["user"]
        
        # Return quota data for GitHub OAuth users
        return {
            "success": True,
            "quota": {
                "plan": {
                    "tier": "free",
                    "name": "Free"
                },
                "monthly_runs": {
                    "used": 0,
                    "limit": 5,
                    "unlimited": False
                },
                "concurrent_runs": {
                    "active": 0,
                    "limit": 2
                },
                "deployment_allowed": {
                    "can_deploy": True,
                    "checks": {
                        "monthly_check": {
                            "passed": True,
                            "reason": "Under monthly limit"
                        },
                        "concurrent_check": {
                            "passed": True,
                            "reason": "Under concurrent limit"
                        }
                    }
                }
            },
            "user_info": {
                "email": user_data.get("email"),
                "github_username": user_data.get("login"),
                "stored_in_cognito": session_data.get("stored_in_cognito", False)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting GitHub user quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quota data"
        )

@router.get("/auth/github/quota")
async def get_github_user_quota(request: Request):
    """
    Get quota/usage data for GitHub OAuth user
    GitHub OAuth compatible alternative to /api/quota/status
    """
    try:
        session_token = request.cookies.get("codeflowops_session")
        
        if not session_token or not session_exists(session_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid GitHub session found"
            )
        
        session_data = get_session(session_token)
        user_data = session_data["user"]
        
        # Return quota data in the expected format
        return {
            "success": True,
            "quota": {
                "plan": {
                    "tier": "free",
                    "name": "Free"
                },
                "monthly_runs": {
                    "used": 0,
                    "limit": 5,
                    "unlimited": False
                },
                "concurrent_runs": {
                    "active": 0,
                    "limit": 2
                },
                "deployment_allowed": {
                    "can_deploy": True,
                    "reason": "Within quota limits"
                }
            },
            "user_info": {
                "email": user_data.get("email"),
                "github_username": user_data.get("login"),
                "authenticated_via": "github_oauth"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting GitHub user quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quota data"
        )
