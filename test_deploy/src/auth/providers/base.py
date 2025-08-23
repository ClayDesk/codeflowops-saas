"""
Base authentication provider interface
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel

class AuthResult(BaseModel):
    """Authentication result"""
    success: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    organization: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}

class AuthProvider(ABC):
    """Base authentication provider"""
    
    @abstractmethod
    async def authenticate(self, username: str, password: str) -> AuthResult:
        """Authenticate user with username/password"""
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """Refresh access token"""
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> AuthResult:
        """Validate access token"""
        pass
    
    @abstractmethod
    async def logout(self, token: str) -> bool:
        """Logout user and invalidate token"""
        pass
    
    @abstractmethod
    async def register(self, user_data: Dict[str, Any]) -> AuthResult:
        """Register new user"""
        pass
    
    @abstractmethod
    async def reset_password(self, email: str) -> bool:
        """Initiate password reset"""
        pass
    
    @abstractmethod
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier"""
        pass
    
    @property
    @abstractmethod
    def supports_registration(self) -> bool:
        """Whether provider supports user registration"""
        pass
    
    @property
    @abstractmethod
    def supports_password_reset(self) -> bool:
        """Whether provider supports password reset"""
        pass
