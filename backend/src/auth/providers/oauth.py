"""
OAuth2 authentication provider for GitHub, Google, etc.
"""

import httpx
from typing import Dict, Any
from .base import AuthProvider, AuthResult
from ...config.env import get_settings

settings = get_settings()

class OAuthProvider(AuthProvider):
    """OAuth2 authentication provider"""
    
    def __init__(self, provider_type: str = "github"):
        self.provider_type = provider_type
        self.config = self._get_provider_config(provider_type)
    
    def _get_provider_config(self, provider_type: str) -> Dict[str, str]:
        """Get OAuth configuration for provider"""
        configs = {
            "github": {
                "authorize_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "user_url": "https://api.github.com/user",
                "client_id": getattr(settings, 'GITHUB_CLIENT_ID', ''),
                "client_secret": getattr(settings, 'GITHUB_CLIENT_SECRET', ''),
                "scope": "user:email"
            },
            "google": {
                "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "user_url": "https://www.googleapis.com/oauth2/v2/userinfo",
                "client_id": getattr(settings, 'GOOGLE_CLIENT_ID', ''),
                "client_secret": getattr(settings, 'GOOGLE_CLIENT_SECRET', ''),
                "scope": "openid email profile"
            }
        }
        return configs.get(provider_type, {})
    
    @property
    def provider_name(self) -> str:
        return f"oauth_{self.provider_type}"
    
    @property
    def supports_registration(self) -> bool:
        return True  # OAuth can create users on first login
    
    @property
    def supports_password_reset(self) -> bool:
        return False  # Handled by OAuth provider
    
    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        """Get OAuth authorization URL"""
        params = {
            "client_id": self.config["client_id"],
            "redirect_uri": redirect_uri,
            "scope": self.config["scope"],
            "state": state,
            "response_type": "code"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.config['authorize_url']}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.config["token_url"],
                data={
                    "client_id": self.config["client_id"],
                    "client_secret": self.config["client_secret"],
                    "code": code,
                    "redirect_uri": redirect_uri
                },
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.config["user_url"],
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def authenticate(self, username: str, password: str) -> AuthResult:
        """Not supported for OAuth - use authorization flow instead"""
        return AuthResult(
            success=False,
            error_message="Use OAuth authorization flow instead"
        )
    
    async def authenticate_with_code(self, code: str, redirect_uri: str) -> AuthResult:
        """Authenticate user with OAuth authorization code"""
        try:
            # Exchange code for token
            token_data = await self.exchange_code_for_token(code, redirect_uri)
            access_token = token_data.get("access_token")
            
            if not access_token:
                return AuthResult(
                    success=False,
                    error_message="Failed to get access token"
                )
            
            # Get user info
            user_info = await self.get_user_info(access_token)
            
            # Map provider-specific fields to our format
            if self.provider_type == "github":
                email = user_info.get("email")
                username = user_info.get("login")
                full_name = user_info.get("name") or username
                user_id = str(user_info.get("id"))
            elif self.provider_type == "google":
                email = user_info.get("email")
                username = email.split("@")[0] if email else None
                full_name = user_info.get("name")
                user_id = user_info.get("id")
            else:
                return AuthResult(
                    success=False,
                    error_message=f"Unsupported provider: {self.provider_type}"
                )
            
            return AuthResult(
                success=True,
                user_id=user_id,
                email=email,
                username=username,
                full_name=full_name,
                access_token=access_token,
                metadata={
                    "provider": f"oauth_{self.provider_type}",
                    "oauth_user_info": user_info,
                    "oauth_token_data": token_data
                }
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=f"OAuth authentication failed: {str(e)}"
            )
    
    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """Refresh access token (if supported by provider)"""
        return AuthResult(
            success=False,
            error_message="Token refresh not implemented for OAuth"
        )
    
    async def validate_token(self, token: str) -> AuthResult:
        """Validate access token by getting user info"""
        try:
            user_info = await self.get_user_info(token)
            
            # Map user info similar to authenticate_with_code
            if self.provider_type == "github":
                email = user_info.get("email")
                username = user_info.get("login")
                full_name = user_info.get("name") or username
                user_id = str(user_info.get("id"))
            elif self.provider_type == "google":
                email = user_info.get("email")
                username = email.split("@")[0] if email else None
                full_name = user_info.get("name")
                user_id = user_info.get("id")
            else:
                return AuthResult(success=False, error_message="Unsupported provider")
            
            return AuthResult(
                success=True,
                user_id=user_id,
                email=email,
                username=username,
                full_name=full_name,
                metadata={
                    "provider": f"oauth_{self.provider_type}",
                    "oauth_user_info": user_info
                }
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=f"Token validation failed: {str(e)}"
            )
    
    async def logout(self, token: str) -> bool:
        """Logout (OAuth tokens typically can't be revoked)"""
        return True  # OAuth tokens typically expire naturally
    
    async def register(self, user_data: Dict[str, Any]) -> AuthResult:
        """Registration handled through OAuth flow"""
        return AuthResult(
            success=False,
            error_message="Use OAuth authorization flow for registration"
        )
    
    async def reset_password(self, email: str) -> bool:
        """Password reset handled by OAuth provider"""
        return False
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Password change handled by OAuth provider"""
        return False
