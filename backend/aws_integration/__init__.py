"""
AWS Integration module for secure credential usage.
Handles role assumption, session management, and permission validation.
"""

import boto3
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session
import logging

logger = logging.getLogger(__name__)

class AWSSessionManager:
    """Manages AWS sessions with temporary credentials."""
    
    def __init__(self):
        """Initialize AWS session manager."""
        self.active_sessions = {}  # Store active sessions
        self.session_timeout = 3600  # 1 hour default
    
    def create_session(
        self,
        tenant_id: str,
        user_id: str,
        credentials: Dict[str, Any],
        session_duration: int = 3600,
        session_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create AWS session with temporary credentials.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            credentials: AWS credentials
            session_duration: Session duration in seconds
            session_name: Optional session name
            
        Returns:
            Session information with temporary credentials
        """
        try:
            session_id = str(uuid.uuid4())
            session_name = session_name or f"CodeFlowOps-{tenant_id}-{user_id}"
            
            if credentials.get('credential_type') == 'role_arn':
                # Use role assumption for cross-account access
                temp_creds = self._assume_role(
                    role_arn=credentials['role_arn'],
                    external_id=credentials.get('external_id'),
                    session_name=session_name,
                    duration_seconds=session_duration
                )
            else:
                # Use access keys to create STS session
                temp_creds = self._create_sts_session(
                    access_key_id=credentials['access_key_id'],
                    secret_access_key=credentials['secret_access_key'],
                    session_name=session_name,
                    duration_seconds=session_duration
                )
            
            # Store session information
            session_info = {
                'session_id': session_id,
                'tenant_id': tenant_id,
                'user_id': user_id,
                'credentials': temp_creds,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(seconds=session_duration),
                'last_used': datetime.utcnow(),
                'region': credentials.get('aws_region', 'us-east-1')
            }
            
            self.active_sessions[session_id] = session_info
            
            logger.info(f"Created AWS session {session_id} for tenant {tenant_id}")
            
            return {
                'session_id': session_id,
                'access_key_id': temp_creds['AccessKeyId'],
                'secret_access_key': temp_creds['SecretAccessKey'],
                'session_token': temp_creds['SessionToken'],
                'expires_at': session_info['expires_at'].isoformat(),
                'region': session_info['region']
            }
            
        except Exception as e:
            logger.error(f"Failed to create AWS session for tenant {tenant_id}: {e}")
            raise
    
    def _assume_role(
        self,
        role_arn: str,
        external_id: Optional[str] = None,
        session_name: str = "CodeFlowOpsSession",
        duration_seconds: int = 3600
    ) -> Dict[str, str]:
        """Assume AWS IAM role and return temporary credentials."""
        try:
            sts_client = boto3.client('sts')
            
            assume_role_params = {
                'RoleArn': role_arn,
                'RoleSessionName': session_name,
                'DurationSeconds': duration_seconds
            }
            
            if external_id:
                assume_role_params['ExternalId'] = external_id
            
            response = sts_client.assume_role(**assume_role_params)
            
            return response['Credentials']
            
        except ClientError as e:
            logger.error(f"Failed to assume role {role_arn}: {e}")
            raise
    
    def _create_sts_session(
        self,
        access_key_id: str,
        secret_access_key: str,
        session_name: str = "CodeFlowOpsSession",
        duration_seconds: int = 3600
    ) -> Dict[str, str]:
        """Create STS session token from access keys."""
        try:
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key
            )
            
            response = sts_client.get_session_token(
                DurationSeconds=duration_seconds
            )
            
            return response['Credentials']
            
        except ClientError as e:
            logger.error(f"Failed to create STS session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get active session by ID."""
        session = self.active_sessions.get(session_id)
        
        if not session:
            return None
        
        # Check if session has expired
        if datetime.utcnow() > session['expires_at']:
            self.revoke_session(session_id)
            return None
        
        # Update last used timestamp
        session['last_used'] = datetime.utcnow()
        
        return session
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke (delete) an active session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Revoked AWS session {session_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions from memory."""
        current_time = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if current_time > session['expires_at']
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def list_active_sessions(self, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List active sessions with optional filtering."""
        sessions = []
        
        for session_id, session in self.active_sessions.items():
            if tenant_id and session['tenant_id'] != tenant_id:
                continue
            if user_id and session['user_id'] != user_id:
                continue
            
            sessions.append({
                'session_id': session_id,
                'tenant_id': session['tenant_id'],
                'user_id': session['user_id'],
                'created_at': session['created_at'].isoformat(),
                'expires_at': session['expires_at'].isoformat(),
                'last_used': session['last_used'].isoformat(),
                'region': session['region']
            })
        
        return sessions

class CrossAccountRoleManager:
    """Manages cross-account IAM roles for tenant isolation."""
    
    def __init__(self):
        """Initialize cross-account role manager."""
        self.iam_client = boto3.client('iam')
        self.sts_client = boto3.client('sts')
    
    def create_tenant_role(
        self,
        tenant_id: str,
        trusted_account_id: str,
        external_id: str,
        permissions: List[str]
    ) -> str:
        """
        Create IAM role for tenant with cross-account trust.
        
        Args:
            tenant_id: Tenant identifier
            trusted_account_id: AWS account ID that can assume this role
            external_id: External ID for additional security
            permissions: List of IAM permissions
            
        Returns:
            Role ARN
        """
        try:
            role_name = f"CodeFlowOps-Tenant-{tenant_id}"
            
            # Create trust policy
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": f"arn:aws:iam::{trusted_account_id}:root"
                        },
                        "Action": "sts:AssumeRole",
                        "Condition": {
                            "StringEquals": {
                                "sts:ExternalId": external_id
                            }
                        }
                    }
                ]
            }
            
            # Create role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"CodeFlowOps tenant role for {tenant_id}",
                Tags=[
                    {"Key": "Application", "Value": "CodeFlowOps"},
                    {"Key": "TenantId", "Value": tenant_id},
                    {"Key": "Purpose", "Value": "TenantAccess"}
                ]
            )
            
            role_arn = response['Role']['Arn']
            
            # Create and attach permission policy
            if permissions:
                self._create_tenant_policy(tenant_id, role_name, permissions)
            
            logger.info(f"Created tenant role {role_arn} for tenant {tenant_id}")
            return role_arn
            
        except Exception as e:
            logger.error(f"Failed to create tenant role for {tenant_id}: {e}")
            raise
    
    def _create_tenant_policy(self, tenant_id: str, role_name: str, permissions: List[str]):
        """Create and attach policy to tenant role."""
        try:
            policy_name = f"CodeFlowOps-Tenant-{tenant_id}-Policy"
            
            # Create policy document
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": permissions,
                        "Resource": "*"
                    }
                ]
            }
            
            # Create policy
            self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description=f"Permissions for CodeFlowOps tenant {tenant_id}"
            )
            
            # Attach policy to role
            policy_arn = f"arn:aws:iam::{self._get_account_id()}:policy/{policy_name}"
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            
            logger.info(f"Created and attached policy {policy_arn} to role {role_name}")
            
        except Exception as e:
            logger.error(f"Failed to create tenant policy: {e}")
            raise
    
    def _get_account_id(self) -> str:
        """Get current AWS account ID."""
        try:
            return self.sts_client.get_caller_identity()['Account']
        except Exception as e:
            logger.error(f"Failed to get AWS account ID: {e}")
            raise

class PermissionValidator:
    """Validates AWS IAM permissions and policies."""
    
    def __init__(self):
        """Initialize permission validator."""
        self.iam_client = boto3.client('iam')
        self.dangerous_permissions = [
            'iam:*',
            'sts:AssumeRole',
            '*:*',
            'iam:CreateRole',
            'iam:DeleteRole',
            'iam:AttachRolePolicy',
            'iam:DetachRolePolicy',
            'iam:PutRolePolicy',
            'iam:DeleteRolePolicy',
            'ec2:TerminateInstances',
            'rds:DeleteDBInstance',
            's3:DeleteBucket'
        ]
    
    def validate_credentials(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate AWS credentials and check permissions.
        
        Args:
            credentials: AWS credentials to validate
            
        Returns:
            Validation result with permissions and warnings
        """
        try:
            if credentials.get('credential_type') == 'role_arn':
                return self._validate_role_arn(credentials['role_arn'])
            else:
                return self._validate_access_keys(
                    credentials['access_key_id'],
                    credentials['secret_access_key']
                )
                
        except Exception as e:
            logger.error(f"Failed to validate credentials: {e}")
            return {
                'valid': False,
                'error': str(e),
                'permissions': [],
                'warnings': []
            }
    
    def _validate_access_keys(self, access_key_id: str, secret_access_key: str) -> Dict[str, Any]:
        """Validate access keys and check permissions."""
        try:
            # Test credentials by making a simple API call
            sts_client = boto3.client(
                'sts',
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key
            )
            
            identity = sts_client.get_caller_identity()
            
            # Get user/role permissions
            iam_client = boto3.client(
                'iam',
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key
            )
            
            permissions = self._get_user_permissions(iam_client, identity)
            warnings = self._check_dangerous_permissions(permissions)
            
            return {
                'valid': True,
                'identity': identity,
                'permissions': permissions,
                'warnings': warnings
            }
            
        except ClientError as e:
            return {
                'valid': False,
                'error': str(e),
                'permissions': [],
                'warnings': []
            }
    
    def _validate_role_arn(self, role_arn: str) -> Dict[str, Any]:
        """Validate role ARN and check permissions."""
        try:
            # Check if role exists and get its policies
            role_name = role_arn.split('/')[-1]
            
            response = self.iam_client.get_role(RoleName=role_name)
            role = response['Role']
            
            # Get role permissions
            permissions = self._get_role_permissions(role_name)
            warnings = self._check_dangerous_permissions(permissions)
            
            return {
                'valid': True,
                'role': role,
                'permissions': permissions,
                'warnings': warnings
            }
            
        except ClientError as e:
            return {
                'valid': False,
                'error': str(e),
                'permissions': [],
                'warnings': []
            }
    
    def _get_user_permissions(self, iam_client, identity: Dict[str, str]) -> List[str]:
        """Get permissions for IAM user."""
        permissions = []
        
        try:
            arn = identity['Arn']
            if ':user/' in arn:
                user_name = arn.split('/')[-1]
                
                # Get user policies
                policies = iam_client.list_attached_user_policies(UserName=user_name)
                for policy in policies['AttachedPolicies']:
                    perms = self._get_policy_permissions(iam_client, policy['PolicyArn'])
                    permissions.extend(perms)
                
                # Get inline policies
                inline_policies = iam_client.list_user_policies(UserName=user_name)
                for policy_name in inline_policies['PolicyNames']:
                    policy_doc = iam_client.get_user_policy(UserName=user_name, PolicyName=policy_name)
                    perms = self._extract_permissions_from_document(policy_doc['PolicyDocument'])
                    permissions.extend(perms)
                
        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
        
        return list(set(permissions))  # Remove duplicates
    
    def _get_role_permissions(self, role_name: str) -> List[str]:
        """Get permissions for IAM role."""
        permissions = []
        
        try:
            # Get role policies
            policies = self.iam_client.list_attached_role_policies(RoleName=role_name)
            for policy in policies['AttachedPolicies']:
                perms = self._get_policy_permissions(self.iam_client, policy['PolicyArn'])
                permissions.extend(perms)
            
            # Get inline policies
            inline_policies = self.iam_client.list_role_policies(RoleName=role_name)
            for policy_name in inline_policies['PolicyNames']:
                policy_doc = self.iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
                perms = self._extract_permissions_from_document(policy_doc['PolicyDocument'])
                permissions.extend(perms)
                
        except Exception as e:
            logger.error(f"Failed to get role permissions: {e}")
        
        return list(set(permissions))  # Remove duplicates
    
    def _get_policy_permissions(self, iam_client, policy_arn: str) -> List[str]:
        """Get permissions from a managed policy."""
        try:
            policy = iam_client.get_policy(PolicyArn=policy_arn)
            version_id = policy['Policy']['DefaultVersionId']
            
            policy_version = iam_client.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=version_id
            )
            
            return self._extract_permissions_from_document(policy_version['PolicyVersion']['Document'])
            
        except Exception as e:
            logger.error(f"Failed to get policy permissions for {policy_arn}: {e}")
            return []
    
    def _extract_permissions_from_document(self, policy_document: Dict[str, Any]) -> List[str]:
        """Extract permission actions from policy document."""
        permissions = []
        
        try:
            statements = policy_document.get('Statement', [])
            if not isinstance(statements, list):
                statements = [statements]
            
            for statement in statements:
                if statement.get('Effect') == 'Allow':
                    actions = statement.get('Action', [])
                    if isinstance(actions, str):
                        actions = [actions]
                    permissions.extend(actions)
                    
        except Exception as e:
            logger.error(f"Failed to extract permissions from policy document: {e}")
        
        return permissions
    
    def _check_dangerous_permissions(self, permissions: List[str]) -> List[str]:
        """Check for dangerous permissions."""
        warnings = []
        
        for permission in permissions:
            for dangerous in self.dangerous_permissions:
                if permission == dangerous or (dangerous.endswith('*') and permission.startswith(dangerous[:-1])):
                    warnings.append(f"Dangerous permission detected: {permission}")
        
        return warnings
