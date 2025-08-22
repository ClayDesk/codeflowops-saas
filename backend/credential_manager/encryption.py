"""
Encryption module for secure AWS credential storage.
Handles tenant-specific encryption using AWS KMS or HashiCorp Vault.
"""

import os
import json
import base64
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import boto3
from botocore.exceptions import ClientError
import hashlib
import logging

logger = logging.getLogger(__name__)

class CredentialEncryption:
    """Handles encryption/decryption of AWS credentials with tenant isolation."""
    
    def __init__(self, encryption_method: str = "kms"):
        """
        Initialize encryption service.
        
        Args:
            encryption_method: 'kms' for AWS KMS or 'vault' for HashiCorp Vault
        """
        self.encryption_method = encryption_method
        self.kms_client = None
        self.vault_client = None
        
        if encryption_method == "kms":
            self._init_kms()
        elif encryption_method == "vault":
            self._init_vault()
        else:
            raise ValueError("Unsupported encryption method")
    
    def _init_kms(self):
        """Initialize AWS KMS client."""
        try:
            self.kms_client = boto3.client('kms')
            logger.info("AWS KMS client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize KMS client: {e}")
            raise
    
    def _init_vault(self):
        """Initialize HashiCorp Vault client."""
        # TODO: Implement Vault integration
        logger.warning("Vault integration not yet implemented")
        pass
    
    def get_tenant_encryption_key(self, tenant_id: str) -> str:
        """
        Get or create tenant-specific encryption key.
        
        Args:
            tenant_id: Unique tenant identifier
            
        Returns:
            KMS key ID or Vault key path
        """
        if self.encryption_method == "kms":
            return self._get_kms_key(tenant_id)
        elif self.encryption_method == "vault":
            return self._get_vault_key(tenant_id)
    
    def _get_kms_key(self, tenant_id: str) -> str:
        """Get or create KMS key for tenant."""
        key_alias = f"alias/codeflowops-tenant-{tenant_id}"
        
        try:
            # Try to get existing key
            response = self.kms_client.describe_key(KeyId=key_alias)
            return response['KeyMetadata']['KeyId']
        except ClientError as e:
            if e.response['Error']['Code'] == 'NotFoundException':
                # Create new key for tenant
                return self._create_kms_key(tenant_id)
            else:
                logger.error(f"Error accessing KMS key: {e}")
                raise
    
    def _create_kms_key(self, tenant_id: str) -> str:
        """Create new KMS key for tenant."""
        try:
            # Create KMS key
            response = self.kms_client.create_key(
                Description=f"CodeFlowOps AWS credential encryption key for tenant {tenant_id}",
                Usage='ENCRYPT_DECRYPT',
                KeySpec='SYMMETRIC_DEFAULT',
                Policy=json.dumps({
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "Enable IAM User Permissions",
                            "Effect": "Allow",
                            "Principal": {"AWS": f"arn:aws:iam::{self._get_account_id()}:root"},
                            "Action": "kms:*",
                            "Resource": "*"
                        },
                        {
                            "Sid": "Allow use of the key for tenant operations",
                            "Effect": "Allow",
                            "Principal": {"AWS": f"arn:aws:iam::{self._get_account_id()}:role/CodeFlowOps-CredentialManager"},
                            "Action": [
                                "kms:Encrypt",
                                "kms:Decrypt",
                                "kms:ReEncrypt*",
                                "kms:GenerateDataKey*",
                                "kms:DescribeKey"
                            ],
                            "Resource": "*",
                            "Condition": {
                                "StringEquals": {
                                    "kms:ViaService": f"rds.{os.getenv('AWS_REGION', 'us-east-1')}.amazonaws.com"
                                }
                            }
                        }
                    ]
                }),
                Tags=[
                    {"TagKey": "Application", "TagValue": "CodeFlowOps"},
                    {"TagKey": "TenantId", "TagValue": tenant_id},
                    {"TagKey": "Purpose", "TagValue": "CredentialEncryption"}
                ]
            )
            
            key_id = response['KeyMetadata']['KeyId']
            
            # Create alias
            alias_name = f"alias/codeflowops-tenant-{tenant_id}"
            self.kms_client.create_alias(
                AliasName=alias_name,
                TargetKeyId=key_id
            )
            
            logger.info(f"Created KMS key {key_id} for tenant {tenant_id}")
            return key_id
            
        except Exception as e:
            logger.error(f"Failed to create KMS key for tenant {tenant_id}: {e}")
            raise
    
    def _get_account_id(self) -> str:
        """Get current AWS account ID."""
        try:
            sts = boto3.client('sts')
            return sts.get_caller_identity()['Account']
        except Exception as e:
            logger.error(f"Failed to get AWS account ID: {e}")
            raise
    
    def encrypt_credential(self, tenant_id: str, credential_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Encrypt AWS credential data for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            credential_data: Dictionary containing AWS credentials
            
        Returns:
            Dictionary with encrypted data and metadata
        """
        try:
            # Serialize credential data
            plaintext = json.dumps(credential_data, sort_keys=True)
            
            if self.encryption_method == "kms":
                return self._encrypt_with_kms(tenant_id, plaintext)
            elif self.encryption_method == "vault":
                return self._encrypt_with_vault(tenant_id, plaintext)
                
        except Exception as e:
            logger.error(f"Failed to encrypt credentials for tenant {tenant_id}: {e}")
            raise
    
    def _encrypt_with_kms(self, tenant_id: str, plaintext: str) -> Dict[str, str]:
        """Encrypt data using AWS KMS."""
        key_id = self.get_tenant_encryption_key(tenant_id)
        
        try:
            response = self.kms_client.encrypt(
                KeyId=key_id,
                Plaintext=plaintext.encode('utf-8'),
                EncryptionContext={
                    'tenant_id': tenant_id,
                    'application': 'codeflowops',
                    'data_type': 'aws_credentials'
                }
            )
            
            return {
                'encrypted_data': base64.b64encode(response['CiphertextBlob']).decode('utf-8'),
                'encryption_key_id': key_id,
                'encryption_method': 'kms',
                'data_hash': hashlib.sha256(plaintext.encode('utf-8')).hexdigest()
            }
            
        except Exception as e:
            logger.error(f"KMS encryption failed for tenant {tenant_id}: {e}")
            raise
    
    def decrypt_credential(self, tenant_id: str, encrypted_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Decrypt AWS credential data for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            encrypted_data: Dictionary with encrypted data and metadata
            
        Returns:
            Decrypted credential data
        """
        try:
            if encrypted_data['encryption_method'] == "kms":
                return self._decrypt_with_kms(tenant_id, encrypted_data)
            elif encrypted_data['encryption_method'] == "vault":
                return self._decrypt_with_vault(tenant_id, encrypted_data)
                
        except Exception as e:
            logger.error(f"Failed to decrypt credentials for tenant {tenant_id}: {e}")
            raise
    
    def _decrypt_with_kms(self, tenant_id: str, encrypted_data: Dict[str, str]) -> Dict[str, Any]:
        """Decrypt data using AWS KMS."""
        try:
            ciphertext_blob = base64.b64decode(encrypted_data['encrypted_data'])
            
            response = self.kms_client.decrypt(
                CiphertextBlob=ciphertext_blob,
                EncryptionContext={
                    'tenant_id': tenant_id,
                    'application': 'codeflowops',
                    'data_type': 'aws_credentials'
                }
            )
            
            plaintext = response['Plaintext'].decode('utf-8')
            
            # Verify data integrity
            if hashlib.sha256(plaintext.encode('utf-8')).hexdigest() != encrypted_data['data_hash']:
                raise ValueError("Data integrity check failed")
            
            return json.loads(plaintext)
            
        except Exception as e:
            logger.error(f"KMS decryption failed for tenant {tenant_id}: {e}")
            raise
    
    def _encrypt_with_vault(self, tenant_id: str, plaintext: str) -> Dict[str, str]:
        """Encrypt data using HashiCorp Vault."""
        # TODO: Implement Vault encryption
        raise NotImplementedError("Vault encryption not yet implemented")
    
    def _decrypt_with_vault(self, tenant_id: str, encrypted_data: Dict[str, str]) -> Dict[str, Any]:
        """Decrypt data using HashiCorp Vault."""
        # TODO: Implement Vault decryption
        raise NotImplementedError("Vault decryption not yet implemented")
    
    def rotate_encryption_key(self, tenant_id: str) -> str:
        """
        Rotate encryption key for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            New key ID
        """
        if self.encryption_method == "kms":
            return self._rotate_kms_key(tenant_id)
        elif self.encryption_method == "vault":
            return self._rotate_vault_key(tenant_id)
    
    def _rotate_kms_key(self, tenant_id: str) -> str:
        """Rotate KMS key for tenant."""
        try:
            key_id = self.get_tenant_encryption_key(tenant_id)
            
            # KMS automatically rotates keys, but we can force rotation
            response = self.kms_client.enable_key_rotation(KeyId=key_id)
            
            logger.info(f"Enabled key rotation for tenant {tenant_id}")
            return key_id
            
        except Exception as e:
            logger.error(f"Failed to rotate KMS key for tenant {tenant_id}: {e}")
            raise
    
    def _rotate_vault_key(self, tenant_id: str) -> str:
        """Rotate Vault key for tenant."""
        # TODO: Implement Vault key rotation
        raise NotImplementedError("Vault key rotation not yet implemented")
