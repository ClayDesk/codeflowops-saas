"""
Authentication providers for CodeFlowOps
Supports multiple authentication backends
"""

from .base import AuthProvider
from .local import LocalAuthProvider
from .cognito import CognitoAuthProvider
from .oauth import OAuthProvider

__all__ = [
    "AuthProvider",
    "LocalAuthProvider", 
    "CognitoAuthProvider",
    "OAuthProvider"
]
