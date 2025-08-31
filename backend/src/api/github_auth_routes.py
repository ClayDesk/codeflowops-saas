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
        response.set_cookie(
            key="github_session_id", 
            value=session_id,
            max_age=1800,  # 30 minutes (extended from 10 minutes)
            httponly=True,
            secure=True,  # Set to True in production with HTTPS
            samesite="lax",
            domain=".codeflowops.com"  # Allow cookie to work across subdomains
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
        
        if not session_id:
            logger.warning("❌ No github_session_id cookie found")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=invalid_session&reason=no_cookie"
            )
            
        if not session_exists(session_id):
            logger.warning(f"❌ Session {session_id} does not exist in database")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=invalid_session&reason=session_not_found"
            )
        
        session_data = get_session(session_id)
        if not session_data:
            logger.warning(f"❌ Could not retrieve session data for {session_id}")
            return RedirectResponse(
                url=f"{FRONTEND_URL}/login?error=invalid_session&reason=session_data_missing"
            )
            
        stored_state = session_data.get("state")
        if stored_state != state:
            logger.warning(f"❌ State parameter mismatch: stored={stored_state}, received={state}")
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
        delete_session(session_id)
        
        # Try to store/update user in Cognito
        logger.info("💾 Attempting to store user in Cognito...")
        cognito_user_data = await create_or_update_github_user_in_cognito(github_user)
        
        if cognito_user_data and COGNITO_AVAILABLE:
            logger.info("✅ User successfully stored in Cognito!")
            
            # Now authenticate the user with Cognito to get proper tokens
            try:
                logger.info("🔐 Authenticating user with Cognito to get tokens...")
                from ..auth.providers.cognito import CognitoAuthProvider
                
                cognito_provider = CognitoAuthProvider()
                auth_result = await cognito_provider.authenticate(
                    username=github_user.email,  # Cognito username is email
                    password='GitHubOAuth123!'    # Password we set for OAuth users
                )
                
                if auth_result.success:
                    logger.info(f"🎉 Cognito authentication successful for {github_user.login}")
                    
                    # Use Cognito tokens instead of manual session
                    response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
                    
                    # Set Cognito tokens as secure cookies
                    response.set_cookie(
                        key="access_token",
                        value=auth_result.access_token,
                        max_age=auth_result.expires_in,
                        httponly=True,
                        secure=True,
                        samesite="lax",
                        domain=".codeflowops.com"
                    )
                    
                    if auth_result.refresh_token:
                        response.set_cookie(
                            key="refresh_token", 
                            value=auth_result.refresh_token,
                            max_age=86400 * 30,  # 30 days
                            httponly=True,
                            secure=True,
                            samesite="lax",
                            domain=".codeflowops.com"
                        )
                    
                    # Also store user info for convenience
                    response.set_cookie(
                        key="user_info",
                        value=f"{auth_result.email}|{auth_result.username}",
                        max_age=auth_result.expires_in,
                        httponly=False,  # Allow frontend to read user info
                        secure=True,
                        samesite="lax",
                        domain=".codeflowops.com"
                    )
                    
                    return response
                    
                else:
                    logger.error(f"❌ Cognito authentication failed: {auth_result.error_message}")
                    # Fall back to session storage
                    
            except Exception as cognito_auth_error:
                logger.error(f"❌ Error during Cognito authentication: {cognito_auth_error}")
                # Fall back to session storage
        
        # Fallback to session storage if Cognito is not available or authentication failed
        logger.warning("⚠️ Using session storage fallback")
        
        # Create a session token
        session_token = f"github-session-{uuid.uuid4()}"
        
        # Store user session with Cognito data if available
        session_data = {
            "user": cognito_user_data if cognito_user_data else github_user.dict(),
            "created_at": datetime.utcnow(),
            "github_access_token": access_token,  # Store for potential API calls
            "stored_in_cognito": bool(cognito_user_data)
        }
        
        set_session(session_token, session_data)
        
        # Redirect to frontend deploy page after successful authentication
        response = RedirectResponse(url=f"{FRONTEND_URL}/deploy")
        response.set_cookie(
            key="codeflowops_session",
            value=session_token,
            max_age=86400,  # 24 hours
            httponly=True,
            secure=True,  # Set to True in production with HTTPS
            samesite="lax",
            domain=".codeflowops.com"  # Allow cookie to work across subdomains
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
        if not session_data:
            logger.warning(f"❌ Session {session_token} not found or expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "session_not_found",
                    "message": "Session not found or expired", 
                    "session_token": session_token[:10] + "..." if len(session_token) > 10 else session_token
                }
            )
        
        user_data = session_data.get("user", {})
        logger.info(f"✅ Valid session for user: {user_data.get('email', 'unknown')}")
        
        return {
            "authenticated": True,
            "user": {
                "id": user_data.get("user_id") or user_data.get("id"),
                "email": user_data.get("email"),
                "username": user_data.get("username") or user_data.get("login"),
                "name": user_data.get("full_name") or user_data.get("name"),
                "avatar_url": user_data.get("avatar_url"),
                "provider": user_data.get("provider", "github"),
                "auth_method": "session"
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (401 Unauthorized)
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in get_github_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/auth/status")
async def get_auth_status(request: Request):
    """Get authentication status (public endpoint)"""
    try:
        # Check authentication without throwing 401
        cookies = dict(request.cookies)
        access_token = request.cookies.get("access_token")
        session_token = request.cookies.get("codeflowops_session")
        
        # Try Cognito first
        cognito_authenticated = False
        if access_token and COGNITO_AVAILABLE:
            try:
                from ..auth.providers.cognito import CognitoAuthProvider
                cognito_provider = CognitoAuthProvider()
                user_info = await cognito_provider.validate_token(access_token)
                cognito_authenticated = bool(user_info)
            except:
                cognito_authenticated = False
        
        # Try session storage
        session_authenticated = False
        if session_token:
            session_data = get_session(session_token)
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
