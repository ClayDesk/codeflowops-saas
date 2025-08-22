"""
Local authentication provider using our database
"""

from typing import Dict, Any
from .base import AuthProvider, AuthResult
from ..auth_utils import UserManager, verify_password, hash_password, create_access_token, create_refresh_token
from ...models.auth_models import UserRole

class LocalAuthProvider(AuthProvider):
    """Local database authentication provider"""
    
    def __init__(self):
        self.user_manager = UserManager()
    
    @property
    def provider_name(self) -> str:
        return "local"
    
    @property
    def supports_registration(self) -> bool:
        return True
    
    @property
    def supports_password_reset(self) -> bool:
        return True
    
    async def authenticate(self, username: str, password: str) -> AuthResult:
        """Authenticate user with username/password"""
        try:
            # Try to get user by email or username
            user = await self.user_manager.get_user_by_email(username)
            if not user:
                user = await self.user_manager.get_user_by_username(username)
            
            if not user:
                return AuthResult(
                    success=False,
                    error_message="Invalid credentials"
                )
            
            if not user.is_active:
                return AuthResult(
                    success=False,
                    error_message="Account is disabled"
                )
            
            if not verify_password(password, user.hashed_password):
                return AuthResult(
                    success=False,
                    error_message="Invalid credentials"
                )
            
            # Create tokens
            access_token = create_access_token(user.id)
            refresh_token = create_refresh_token(user.id)
            
            return AuthResult(
                success=True,
                user_id=str(user.id),
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                role=user.role.value,
                organization=user.organization,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=1800,  # 30 minutes
                metadata={
                    "provider": "local",
                    "last_login": user.last_login_at.isoformat() if user.last_login_at else None
                }
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=f"Authentication failed: {str(e)}"
            )
    
    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """Refresh access token"""
        try:
            # Validate refresh token and get user
            user_id = await self.user_manager.validate_refresh_token(refresh_token)
            if not user_id:
                return AuthResult(
                    success=False,
                    error_message="Invalid refresh token"
                )
            
            user = await self.user_manager.get_user_by_id(user_id)
            if not user or not user.is_active:
                return AuthResult(
                    success=False,
                    error_message="User not found or inactive"
                )
            
            # Create new access token
            access_token = create_access_token(user.id)
            
            return AuthResult(
                success=True,
                user_id=str(user.id),
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                role=user.role.value,
                organization=user.organization,
                access_token=access_token,
                expires_in=1800,
                metadata={"provider": "local"}
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=f"Token refresh failed: {str(e)}"
            )
    
    async def validate_token(self, token: str) -> AuthResult:
        """Validate access token"""
        try:
            user_id = await self.user_manager.validate_access_token(token)
            if not user_id:
                return AuthResult(
                    success=False,
                    error_message="Invalid token"
                )
            
            user = await self.user_manager.get_user_by_id(user_id)
            if not user or not user.is_active:
                return AuthResult(
                    success=False,
                    error_message="User not found or inactive"
                )
            
            return AuthResult(
                success=True,
                user_id=str(user.id),
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                role=user.role.value,
                organization=user.organization,
                metadata={"provider": "local"}
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=f"Token validation failed: {str(e)}"
            )
    
    async def logout(self, token: str) -> bool:
        """Logout user and invalidate token"""
        try:
            return await self.user_manager.revoke_token(token)
        except Exception:
            return False
    
    async def register(self, user_data: Dict[str, Any]) -> AuthResult:
        """Register new user"""
        try:
            hashed_password = hash_password(user_data["password"])
            
            user = await self.user_manager.create_user(
                email=user_data["email"],
                username=user_data.get("username", user_data["email"]),
                full_name=user_data.get("full_name", ""),
                hashed_password=hashed_password,
                role=UserRole(user_data.get("role", "user")),
                organization=user_data.get("organization")
            )
            
            # Create tokens
            access_token = create_access_token(user.id)
            refresh_token = create_refresh_token(user.id)
            
            return AuthResult(
                success=True,
                user_id=str(user.id),
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                role=user.role.value,
                organization=user.organization,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=1800,
                metadata={"provider": "local"}
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=f"Registration failed: {str(e)}"
            )
    
    async def reset_password(self, email: str) -> bool:
        """Initiate password reset"""
        try:
            return await self.user_manager.initiate_password_reset(email)
        except Exception:
            return False
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            user = await self.user_manager.get_user_by_id(user_id)
            if not user:
                return False
            
            if not verify_password(old_password, user.hashed_password):
                return False
            
            hashed_password = hash_password(new_password)
            return await self.user_manager.update_password(user_id, hashed_password)
            
        except Exception:
            return False
