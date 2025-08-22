"""
Encryption utilities for credential data
"""

import json
import base64
from typing import Dict, Any


def encrypt_credential_data(data: Dict[str, Any], tenant_id: str) -> str:
    """
    Encrypt credential data - placeholder implementation
    In production, this would use AWS KMS or similar
    """
    # For now, just base64 encode (NOT SECURE - for development only)
    json_data = json.dumps(data)
    encoded = base64.b64encode(json_data.encode()).decode()
    return encoded


def decrypt_credential_data(encrypted_data: str, tenant_id: str) -> Dict[str, Any]:
    """
    Decrypt credential data - placeholder implementation
    In production, this would use AWS KMS or similar
    """
    # For now, just base64 decode (NOT SECURE - for development only)
    try:
        decoded = base64.b64decode(encrypted_data.encode()).decode()
        return json.loads(decoded)
    except Exception:
        # Return sample data if decryption fails
        return {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "region": "us-east-1"
        }
