"""
Authentication manager that handles multiple providers
"""

from typing import Dict, List, Optional, Union
from enum import Enum
from .providers.base import AuthProvider, AuthResult
from .providers.local import LocalAuthProvider
from .providers.cognito import CognitoAuthProvider
from .providers.oauth import OAuthProvider
from ..config.env import get_settings

settings = get_settings()

class AuthProviderType(Enum):
    LOCAL = "local"
    COGNITO = "cognito"
    GITHUB = "github"
    GOOGLE = "google"
    SAML = "saml"

class AuthManager:
    """Central authentication manager"""
    
    def __init__(self):
        self.providers: Dict[str, AuthProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available authentication providers"""
        
        # Always include local auth
        self.providers[AuthProviderType.LOCAL.value] = LocalAuthProvider()
        
        # Add Cognito if configured
        if (hasattr(settings, 'COGNITO_USER_POOL_ID') and 
            getattr(settings, 'COGNITO_USER_POOL_ID')):
            try:
                self.providers[AuthProviderType.COGNITO.value] = CognitoAuthProvider()
            except Exception as e:
                print(f"Cognito provider not available: {e}")
        
        # Add GitHub OAuth if configured
        if (hasattr(settings, 'GITHUB_CLIENT_ID') and 
            getattr(settings, 'GITHUB_CLIENT_ID')):
            self.providers[AuthProviderType.GITHUB.value] = OAuthProvider("github")
        
        # Add Google OAuth if configured
        if (hasattr(settings, 'GOOGLE_CLIENT_ID') and 
            getattr(settings, 'GOOGLE_CLIENT_ID')):
            self.providers[AuthProviderType.GOOGLE.value] = OAuthProvider("google")
    
    def get_available_providers(self) -> List[Dict[str, str]]:
        """Get list of available authentication providers for frontend"""
        providers = []
        
        for provider_type, provider in self.providers.items():
            providers.append({
                "type": provider_type,
                "name": provider.provider_name,
                "supports_registration": provider.supports_registration,
                "supports_password_reset": provider.supports_password_reset,
                "display_name": self._get_display_name(provider_type)
            })
        
        return providers
    
    def _get_display_name(self, provider_type: str) -> str:
        """Get user-friendly display name for provider"""
        names = {
            "local": "Email & Password",
            "cognito": "Company SSO",
            "github": "GitHub",
            "google": "Google",
            "saml": "Enterprise SSO"
        }
        return names.get(provider_type, provider_type.title())
    
    async def authenticate(self, provider_type: str, credentials: Dict[str, str]) -> AuthResult:
        """Authenticate user with specified provider"""
        provider = self.providers.get(provider_type)
        if not provider:
            return AuthResult(
                success=False,
                error_message=f"Provider '{provider_type}' not available"
            )
        
        if provider_type == "local":
            # Email/password authentication
            return await provider.authenticate(
                credentials.get("username", ""),
                credentials.get("password", "")
            )
        elif provider_type in ["github", "google"]:
            # OAuth flow - requires authorization code
            return await provider.authenticate_with_code(
                credentials.get("code", ""),
                credentials.get("redirect_uri", "")
            )
        elif provider_type == "cognito":
            # Cognito authentication
            return await provider.authenticate(
                credentials.get("username", ""),
                credentials.get("password", "")
            )
        else:
            return AuthResult(
                success=False,
                error_message=f"Authentication method not implemented for {provider_type}"
            )
    
    async def validate_token(self, token: str, provider_type: Optional[str] = None) -> AuthResult:
        """Validate token - try all providers if type not specified"""
        if provider_type:
            provider = self.providers.get(provider_type)
            if provider:
                return await provider.validate_token(token)
        
        # Try all providers
        for provider in self.providers.values():
            result = await provider.validate_token(token)
            if result.success:
                return result
        
        return AuthResult(
            success=False,
            error_message="Invalid token"
        )
    
    async def refresh_token(self, refresh_token: str, provider_type: str) -> AuthResult:
        """Refresh access token"""
        provider = self.providers.get(provider_type)
        if not provider:
            return AuthResult(
                success=False,
                error_message=f"Provider '{provider_type}' not available"
            )
        
        return await provider.refresh_token(refresh_token)
    
    async def logout(self, token: str, provider_type: str) -> bool:
        """Logout user"""
        provider = self.providers.get(provider_type)
        if provider:
            return await provider.logout(token)
        return False
    
    async def register(self, provider_type: str, user_data: Dict[str, str]) -> AuthResult:
        """Register new user"""
        provider = self.providers.get(provider_type)
        if not provider:
            return AuthResult(
                success=False,
                error_message=f"Provider '{provider_type}' not available"
            )
        
        if not provider.supports_registration:
            return AuthResult(
                success=False,
                error_message=f"Registration not supported for {provider_type}"
            )
        
        return await provider.register(user_data)
    
    def get_oauth_authorization_url(self, provider_type: str, state: str, redirect_uri: str) -> Optional[str]:
        """Get OAuth authorization URL"""
        provider = self.providers.get(provider_type)
        if isinstance(provider, OAuthProvider):
            return provider.get_authorization_url(state, redirect_uri)
        return None

# Global auth manager instance
auth_manager = AuthManager()
