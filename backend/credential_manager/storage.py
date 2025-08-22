"""
Secure storage module for AWS credentials.
Handles database operations with encryption and audit logging.
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, LargeBinary, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, and_, or_
import enum
import logging

from .encryption import CredentialEncryption
from .audit import AuditLogger

logger = logging.getLogger(__name__)

Base = declarative_base()

class CredentialType(enum.Enum):
    """Types of AWS credentials supported."""
    ACCESS_KEY = "access_key"
    ROLE_ARN = "role_arn"
    EXTERNAL_ID = "external_id"
    SESSION_TOKEN = "session_token"

class TenantAWSCredential(Base):
    """Model for storing encrypted tenant AWS credentials."""
    
    __tablename__ = "tenant_aws_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    credential_name = Column(String(255), nullable=False)  # User-friendly name
    credential_type = Column(Enum(CredentialType), nullable=False)
    encrypted_data = Column(LargeBinary, nullable=False)  # Encrypted credential data
    encryption_key_id = Column(String(255), nullable=False)
    encryption_method = Column(String(50), nullable=False, default="kms")
    data_hash = Column(String(64), nullable=False)  # SHA256 hash for integrity
    
    # AWS-specific metadata
    aws_region = Column(String(50), nullable=True)
    aws_account_id = Column(String(12), nullable=True)
    permissions_policy = Column(JSON, nullable=True)  # IAM policy document
    
    # Lifecycle management
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    last_rotated = Column(DateTime, nullable=True)
    rotation_schedule = Column(String(50), nullable=True)  # e.g., "30d", "90d"
    expires_at = Column(DateTime, nullable=True)
    
    # Status and validation
    is_active = Column(Boolean, default=True)
    is_validated = Column(Boolean, default=False)
    last_validated = Column(DateTime, nullable=True)
    validation_error = Column(Text, nullable=True)
    
    # Access control
    allowed_ips = Column(JSON, nullable=True)  # List of allowed IP ranges
    mfa_required = Column(Boolean, default=True)
    max_session_duration = Column(String(20), default="1h")
    
    def __repr__(self):
        return f"<TenantAWSCredential(id={self.id}, tenant={self.tenant_id}, name={self.credential_name})>"

class CredentialAccessLog(Base):
    """Model for audit logging of credential access."""
    
    __tablename__ = "credential_access_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    credential_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Action details
    action = Column(String(100), nullable=False)  # CREATE, READ, UPDATE, DELETE, ROTATE
    resource_type = Column(String(50), nullable=False)  # credential, session, policy
    
    # Request context
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Result
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<CredentialAccessLog(id={self.id}, action={self.action}, success={self.success})>"

class CredentialStorage:
    """Handles secure storage and retrieval of AWS credentials."""
    
    def __init__(self, database_url: str, encryption_method: str = "kms"):
        """
        Initialize credential storage.
        
        Args:
            database_url: Database connection string
            encryption_method: Encryption method ('kms' or 'vault')
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.encryption = CredentialEncryption(encryption_method)
        self.audit = AuditLogger()
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
        logger.info("Credential storage initialized")
    
    def get_db_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    def store_credential(
        self,
        tenant_id: str,
        user_id: str,
        credential_name: str,
        credential_type: CredentialType,
        credential_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """
        Store encrypted AWS credentials for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User who is storing the credential
            credential_name: User-friendly name for the credential
            credential_type: Type of credential
            credential_data: Raw credential data
            metadata: Additional metadata
            ip_address: Client IP address for audit
            
        Returns:
            Credential ID
        """
        db = self.get_db_session()
        
        try:
            # Encrypt credential data
            encrypted_result = self.encryption.encrypt_credential(tenant_id, credential_data)
            
            # Create credential record
            credential = TenantAWSCredential(
                tenant_id=uuid.UUID(tenant_id),
                credential_name=credential_name,
                credential_type=credential_type,
                encrypted_data=encrypted_result['encrypted_data'].encode('utf-8'),
                encryption_key_id=encrypted_result['encryption_key_id'],
                encryption_method=encrypted_result['encryption_method'],
                data_hash=encrypted_result['data_hash'],
                created_by=uuid.UUID(user_id),
                aws_region=credential_data.get('region'),
                aws_account_id=credential_data.get('account_id')
            )
            
            # Set metadata if provided
            if metadata:
                credential.permissions_policy = metadata.get('permissions_policy')
                credential.allowed_ips = metadata.get('allowed_ips')
                credential.mfa_required = metadata.get('mfa_required', True)
                credential.max_session_duration = metadata.get('max_session_duration', '1h')
                credential.rotation_schedule = metadata.get('rotation_schedule')
                if metadata.get('expires_at'):
                    credential.expires_at = datetime.fromisoformat(metadata['expires_at'])
            
            db.add(credential)
            db.commit()
            
            credential_id = str(credential.id)
            
            # Log the action
            self.audit.log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                action="CREATE",
                resource_type="credential",
                resource_id=credential_id,
                success=True,
                ip_address=ip_address,
                metadata={'credential_name': credential_name, 'credential_type': credential_type.value}
            )
            
            logger.info(f"Stored credential {credential_id} for tenant {tenant_id}")
            return credential_id
            
        except Exception as e:
            db.rollback()
            
            # Log the error
            self.audit.log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                action="CREATE",
                resource_type="credential",
                success=False,
                error_message=str(e),
                ip_address=ip_address
            )
            
            logger.error(f"Failed to store credential for tenant {tenant_id}: {e}")
            raise
        finally:
            db.close()
    
    def retrieve_credential(
        self,
        tenant_id: str,
        user_id: str,
        credential_id: str,
        ip_address: Optional[str] = None,
        validate_access: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve and decrypt AWS credentials.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User requesting the credential
            credential_id: Credential identifier
            ip_address: Client IP address for audit
            validate_access: Whether to validate access permissions
            
        Returns:
            Decrypted credential data
        """
        db = self.get_db_session()
        
        try:
            # Get credential record
            credential = db.query(TenantAWSCredential).filter(
                and_(
                    TenantAWSCredential.id == uuid.UUID(credential_id),
                    TenantAWSCredential.tenant_id == uuid.UUID(tenant_id),
                    TenantAWSCredential.is_active == True
                )
            ).first()
            
            if not credential:
                raise ValueError("Credential not found or access denied")
            
            # Check if credential has expired
            if credential.expires_at and credential.expires_at < datetime.utcnow():
                raise ValueError("Credential has expired")
            
            # Validate IP access if configured
            if validate_access and credential.allowed_ips and ip_address:
                if not self._validate_ip_access(ip_address, credential.allowed_ips):
                    raise ValueError("IP address not allowed")
            
            # Decrypt credential data
            encrypted_data = {
                'encrypted_data': credential.encrypted_data.decode('utf-8'),
                'encryption_key_id': credential.encryption_key_id,
                'encryption_method': credential.encryption_method,
                'data_hash': credential.data_hash
            }
            
            decrypted_data = self.encryption.decrypt_credential(tenant_id, encrypted_data)
            
            # Add metadata
            decrypted_data.update({
                'credential_id': credential_id,
                'credential_name': credential.credential_name,
                'credential_type': credential.credential_type.value,
                'aws_region': credential.aws_region,
                'aws_account_id': credential.aws_account_id,
                'mfa_required': credential.mfa_required,
                'max_session_duration': credential.max_session_duration
            })
            
            # Log successful access
            self.audit.log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                action="READ",
                resource_type="credential",
                resource_id=credential_id,
                success=True,
                ip_address=ip_address,
                metadata={'credential_name': credential.credential_name}
            )
            
            return decrypted_data
            
        except Exception as e:
            # Log the error
            self.audit.log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                action="READ",
                resource_type="credential",
                resource_id=credential_id,
                success=False,
                error_message=str(e),
                ip_address=ip_address
            )
            
            logger.error(f"Failed to retrieve credential {credential_id} for tenant {tenant_id}: {e}")
            raise
        finally:
            db.close()
    
    def list_credentials(
        self,
        tenant_id: str,
        user_id: str,
        include_inactive: bool = False,
        ip_address: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all credentials for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User making the request
            include_inactive: Whether to include inactive credentials
            ip_address: Client IP address for audit
            
        Returns:
            List of credential metadata (no sensitive data)
        """
        db = self.get_db_session()
        
        try:
            query = db.query(TenantAWSCredential).filter(
                TenantAWSCredential.tenant_id == uuid.UUID(tenant_id)
            )
            
            if not include_inactive:
                query = query.filter(TenantAWSCredential.is_active == True)
            
            credentials = query.all()
            
            result = []
            for cred in credentials:
                result.append({
                    'credential_id': str(cred.id),
                    'credential_name': cred.credential_name,
                    'credential_type': cred.credential_type.value,
                    'aws_region': cred.aws_region,
                    'aws_account_id': cred.aws_account_id,
                    'created_at': cred.created_at.isoformat(),
                    'last_rotated': cred.last_rotated.isoformat() if cred.last_rotated else None,
                    'expires_at': cred.expires_at.isoformat() if cred.expires_at else None,
                    'is_active': cred.is_active,
                    'is_validated': cred.is_validated,
                    'last_validated': cred.last_validated.isoformat() if cred.last_validated else None,
                    'mfa_required': cred.mfa_required,
                    'rotation_schedule': cred.rotation_schedule
                })
            
            # Log the action
            self.audit.log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                action="LIST",
                resource_type="credential",
                success=True,
                ip_address=ip_address,
                metadata={'count': len(result)}
            )
            
            return result
            
        except Exception as e:
            # Log the error
            self.audit.log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                action="LIST",
                resource_type="credential",
                success=False,
                error_message=str(e),
                ip_address=ip_address
            )
            
            logger.error(f"Failed to list credentials for tenant {tenant_id}: {e}")
            raise
        finally:
            db.close()
    
    def update_credential(
        self,
        tenant_id: str,
        user_id: str,
        credential_id: str,
        updates: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Update credential metadata or data.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User making the update
            credential_id: Credential identifier
            updates: Dictionary of fields to update
            ip_address: Client IP address for audit
            
        Returns:
            True if successful
        """
        db = self.get_db_session()
        
        try:
            credential = db.query(TenantAWSCredential).filter(
                and_(
                    TenantAWSCredential.id == uuid.UUID(credential_id),
                    TenantAWSCredential.tenant_id == uuid.UUID(tenant_id)
                )
            ).first()
            
            if not credential:
                raise ValueError("Credential not found")
            
            # Update allowed fields
            if 'credential_name' in updates:
                credential.credential_name = updates['credential_name']
            if 'aws_region' in updates:
                credential.aws_region = updates['aws_region']
            if 'permissions_policy' in updates:
                credential.permissions_policy = updates['permissions_policy']
            if 'allowed_ips' in updates:
                credential.allowed_ips = updates['allowed_ips']
            if 'mfa_required' in updates:
                credential.mfa_required = updates['mfa_required']
            if 'max_session_duration' in updates:
                credential.max_session_duration = updates['max_session_duration']
            if 'rotation_schedule' in updates:
                credential.rotation_schedule = updates['rotation_schedule']
            if 'expires_at' in updates:
                credential.expires_at = datetime.fromisoformat(updates['expires_at']) if updates['expires_at'] else None
            if 'is_active' in updates:
                credential.is_active = updates['is_active']
            
            # If credential data is being updated, re-encrypt
            if 'credential_data' in updates:
                encrypted_result = self.encryption.encrypt_credential(tenant_id, updates['credential_data'])
                credential.encrypted_data = encrypted_result['encrypted_data'].encode('utf-8')
                credential.data_hash = encrypted_result['data_hash']
                credential.last_rotated = datetime.utcnow()
            
            db.commit()
            
            # Log the action
            self.audit.log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                action="UPDATE",
                resource_type="credential",
                resource_id=credential_id,
                success=True,
                ip_address=ip_address,
                metadata={'updates': list(updates.keys())}
            )
            
            logger.info(f"Updated credential {credential_id} for tenant {tenant_id}")
            return True
            
        except Exception as e:
            db.rollback()
            
            # Log the error
            self.audit.log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                action="UPDATE",
                resource_type="credential",
                resource_id=credential_id,
                success=False,
                error_message=str(e),
                ip_address=ip_address
            )
            
            logger.error(f"Failed to update credential {credential_id} for tenant {tenant_id}: {e}")
            raise
        finally:
            db.close()
    
    def delete_credential(
        self,
        tenant_id: str,
        user_id: str,
        credential_id: str,
        ip_address: Optional[str] = None,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete (deactivate) a credential.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User making the deletion
            credential_id: Credential identifier
            ip_address: Client IP address for audit
            hard_delete: Whether to permanently delete the record
            
        Returns:
            True if successful
        """
        db = self.get_db_session()
        
        try:
            credential = db.query(TenantAWSCredential).filter(
                and_(
                    TenantAWSCredential.id == uuid.UUID(credential_id),
                    TenantAWSCredential.tenant_id == uuid.UUID(tenant_id)
                )
            ).first()
            
            if not credential:
                raise ValueError("Credential not found")
            
            if hard_delete:
                db.delete(credential)
            else:
                credential.is_active = False
            
            db.commit()
            
            # Log the action
            self.audit.log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                action="DELETE",
                resource_type="credential",
                resource_id=credential_id,
                success=True,
                ip_address=ip_address,
                metadata={'hard_delete': hard_delete}
            )
            
            logger.info(f"Deleted credential {credential_id} for tenant {tenant_id}")
            return True
            
        except Exception as e:
            db.rollback()
            
            # Log the error
            self.audit.log_access(
                tenant_id=tenant_id,
                user_id=user_id,
                action="DELETE",
                resource_type="credential",
                resource_id=credential_id,
                success=False,
                error_message=str(e),
                ip_address=ip_address
            )
            
            logger.error(f"Failed to delete credential {credential_id} for tenant {tenant_id}: {e}")
            raise
        finally:
            db.close()
    
    def _validate_ip_access(self, ip_address: str, allowed_ips: List[str]) -> bool:
        """
        Validate if IP address is in allowed ranges.
        
        Args:
            ip_address: Client IP address
            allowed_ips: List of allowed IP addresses/ranges
            
        Returns:
            True if access is allowed
        """
        import ipaddress
        
        try:
            client_ip = ipaddress.ip_address(ip_address)
            
            for allowed_ip in allowed_ips:
                if '/' in allowed_ip:
                    # CIDR range
                    if client_ip in ipaddress.ip_network(allowed_ip, strict=False):
                        return True
                else:
                    # Single IP
                    if client_ip == ipaddress.ip_address(allowed_ip):
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating IP access: {e}")
            return False
