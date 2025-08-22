"""
Database migration for AWS credential management tables.

Revision ID: 001_credential_management
Revises: 
Create Date: 2025-08-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = '001_credential_management'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Create tables for secure AWS credential management."""
    
    # Create enum for credential types
    credential_type_enum = postgresql.ENUM(
        'access_key', 'role_arn', 'external_id', 'session_token',
        name='credentialtype'
    )
    credential_type_enum.create(op.get_bind())
    
    # Create tenant_aws_credentials table
    op.create_table(
        'tenant_aws_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('credential_name', sa.String(255), nullable=False),
        sa.Column('credential_type', credential_type_enum, nullable=False),
        sa.Column('encrypted_data', sa.LargeBinary, nullable=False),
        sa.Column('encryption_key_id', sa.String(255), nullable=False),
        sa.Column('encryption_method', sa.String(50), nullable=False, default='kms'),
        sa.Column('data_hash', sa.String(64), nullable=False),
        
        # AWS-specific metadata
        sa.Column('aws_region', sa.String(50), nullable=True),
        sa.Column('aws_account_id', sa.String(12), nullable=True),
        sa.Column('permissions_policy', postgresql.JSON, nullable=True),
        
        # Lifecycle management
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('last_rotated', sa.DateTime, nullable=True),
        sa.Column('rotation_schedule', sa.String(50), nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        
        # Status and validation
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_validated', sa.Boolean, default=False),
        sa.Column('last_validated', sa.DateTime, nullable=True),
        sa.Column('validation_error', sa.Text, nullable=True),
        
        # Access control
        sa.Column('allowed_ips', postgresql.JSON, nullable=True),
        sa.Column('mfa_required', sa.Boolean, default=True),
        sa.Column('max_session_duration', sa.String(20), default='1h'),
    )
    
    # Create indexes for tenant_aws_credentials
    op.create_index('idx_tenant_credentials_tenant_id', 'tenant_aws_credentials', ['tenant_id'])
    op.create_index('idx_tenant_credentials_active', 'tenant_aws_credentials', ['is_active'])
    op.create_index('idx_tenant_credentials_expires', 'tenant_aws_credentials', ['expires_at'])
    
    # Create credential_access_log table
    op.create_table(
        'credential_access_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('credential_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Action details
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        
        # Request context
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        
        # Result
        sa.Column('success', sa.Boolean, nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        
        # Additional metadata
        sa.Column('metadata', postgresql.JSON, nullable=True),
        sa.Column('timestamp', sa.DateTime, default=sa.func.now(), index=True),
    )
    
    # Create indexes for credential_access_log
    op.create_index('idx_access_log_tenant_id', 'credential_access_log', ['tenant_id'])
    op.create_index('idx_access_log_user_id', 'credential_access_log', ['user_id'])
    op.create_index('idx_access_log_timestamp', 'credential_access_log', ['timestamp'])
    op.create_index('idx_access_log_action', 'credential_access_log', ['action'])
    op.create_index('idx_access_log_success', 'credential_access_log', ['success'])
    
    # Create ip_whitelist table
    op.create_table(
        'tenant_ip_whitelist',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=False),  # IPv4/IPv6
        sa.Column('ip_range', sa.String(50), nullable=True),     # CIDR notation
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
    )
    
    # Create indexes for ip_whitelist
    op.create_index('idx_ip_whitelist_tenant_id', 'tenant_ip_whitelist', ['tenant_id'])
    op.create_index('idx_ip_whitelist_active', 'tenant_ip_whitelist', ['is_active'])
    
    # Create mfa_settings table
    op.create_table(
        'user_mfa_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('totp_secret', sa.String(32), nullable=True),  # Base32 encoded
        sa.Column('backup_codes', postgresql.JSON, nullable=True),  # Array of backup codes
        sa.Column('used_backup_codes', postgresql.JSON, nullable=True),  # Array of used codes
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('email_verified', sa.Boolean, default=False),
        sa.Column('phone_verified', sa.Boolean, default=False),
        sa.Column('totp_enabled', sa.Boolean, default=False),
        sa.Column('sms_enabled', sa.Boolean, default=False),
        sa.Column('email_enabled', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create aws_sessions table for tracking active sessions
    op.create_table(
        'aws_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('session_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('credential_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aws_access_key_id', sa.String(128), nullable=False),
        sa.Column('aws_session_token', sa.Text, nullable=False),
        sa.Column('aws_region', sa.String(50), nullable=False),
        sa.Column('session_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=False, index=True),
        sa.Column('last_used', sa.DateTime, default=sa.func.now()),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('revoked_at', sa.DateTime, nullable=True),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    
    # Create indexes for aws_sessions
    op.create_index('idx_aws_sessions_expires', 'aws_sessions', ['expires_at'])
    op.create_index('idx_aws_sessions_active', 'aws_sessions', ['is_active'])
    op.create_index('idx_aws_sessions_tenant', 'aws_sessions', ['tenant_id'])

def downgrade():
    """Drop tables for AWS credential management."""
    
    # Drop tables in reverse order
    op.drop_table('aws_sessions')
    op.drop_table('user_mfa_settings')
    op.drop_table('tenant_ip_whitelist')
    op.drop_table('credential_access_log')
    op.drop_table('tenant_aws_credentials')
    
    # Drop enum type
    credential_type_enum = postgresql.ENUM(name='credentialtype')
    credential_type_enum.drop(op.get_bind())
