"""
User model
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class User:
    """User model placeholder"""
    id: str
    email: str
    tenant_id: str
    is_active: bool = True
    is_superuser: bool = False
    
    def __init__(self, id: str, email: str, tenant_id: str, **kwargs):
        self.id = id
        self.email = email
        self.tenant_id = tenant_id
        self.is_active = kwargs.get('is_active', True)
        self.is_superuser = kwargs.get('is_superuser', False)
