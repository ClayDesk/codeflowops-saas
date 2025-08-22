"""
Tenant model
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class Tenant:
    """Tenant model placeholder"""
    id: str
    name: str
    is_active: bool = True
    
    def __init__(self, id: str, name: str, **kwargs):
        self.id = id
        self.name = name
        self.is_active = kwargs.get('is_active', True)
