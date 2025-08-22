"""
Credential model
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Credential:
    """Credential model placeholder"""
    id: str
    tenant_id: str
    credential_name: str
    credential_type: str
    credential_data: Dict[str, Any]
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    def __init__(self, id: str, tenant_id: str, credential_name: str, 
                 credential_type: str, credential_data: Dict[str, Any], **kwargs):
        self.id = id
        self.tenant_id = tenant_id
        self.credential_name = credential_name
        self.credential_type = credential_type
        self.credential_data = credential_data
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', datetime.utcnow())
