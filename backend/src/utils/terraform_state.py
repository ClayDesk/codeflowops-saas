"""
Terraform State Manager
Handles Terraform state isolation per user and project
"""

import os
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TerraformStateManager:
    """Manages Terraform state files with proper isolation"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.state_bucket = getattr(settings, 'TERRAFORM_STATE_BUCKET', 'codeflowops-terraform-state')
    
    def get_state_key(self, user_id: str, project_name: str, session_id: str) -> str:
        """
        Generate S3 key for Terraform state file
        Format: users/{user_id}/projects/{project_name}/sessions/{session_id}/terraform.tfstate
        """
        # Sanitize inputs for S3 key
        safe_user_id = self._sanitize_for_s3_key(user_id)
        safe_project_name = self._sanitize_for_s3_key(project_name)
        safe_session_id = self._sanitize_for_s3_key(session_id)
        
        return f"users/{safe_user_id}/projects/{safe_project_name}/sessions/{safe_session_id}/terraform.tfstate"
    
    def get_state_lock_key(self, user_id: str, project_name: str, session_id: str) -> str:
        """Generate S3 key for Terraform state lock file"""
        state_key = self.get_state_key(user_id, project_name, session_id)
        return state_key.replace('.tfstate', '.tflock')
    
    def _sanitize_for_s3_key(self, value: str) -> str:
        """Sanitize string for use in S3 key"""
        # Replace invalid characters with hyphens
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9\-_.]', '-', value)
        # Remove consecutive hyphens
        sanitized = re.sub(r'-+', '-', sanitized)
        # Remove leading/trailing hyphens
        return sanitized.strip('-')
    
    async def setup_terraform_backend(
        self, 
        terraform_dir: str, 
        user_id: str, 
        project_name: str, 
        session_id: str
    ) -> Dict[str, str]:
        """
        Setup Terraform backend configuration for state isolation
        
        Args:
            terraform_dir: Directory containing Terraform files
            user_id: User identifier
            project_name: Project name
            session_id: Session identifier
            
        Returns:
            Dict with backend configuration details
        """
        try:
            state_key = self.get_state_key(user_id, project_name, session_id)
            lock_table = getattr(settings, 'TERRAFORM_LOCK_TABLE', 'codeflowops-terraform-locks')
            
            # Create backend configuration
            backend_config = {
                'bucket': self.state_bucket,
                'key': state_key,
                'region': settings.AWS_REGION,
                'dynamodb_table': lock_table,
                'encrypt': 'true'
            }
            
            # Write backend configuration file
            backend_tf_path = Path(terraform_dir) / 'backend.tf'
            backend_content = f'''
terraform {{
  backend "s3" {{
    bucket         = "{self.state_bucket}"
    key            = "{state_key}"
    region         = "{settings.AWS_REGION}"
    dynamodb_table = "{lock_table}"
    encrypt        = true
  }}
}}
'''
            
            with open(backend_tf_path, 'w') as f:
                f.write(backend_content)
            
            logger.info(f"Created Terraform backend config: {backend_tf_path}")
            logger.info(f"State will be stored at: s3://{self.state_bucket}/{state_key}")
            
            return backend_config
            
        except Exception as e:
            logger.error(f"Failed to setup Terraform backend: {e}")
            raise
    
    async def ensure_state_infrastructure(self):
        """Ensure S3 bucket and DynamoDB table exist for state management"""
        try:
            # Check/create S3 bucket
            await self._ensure_state_bucket()
            
            # Check/create DynamoDB table
            await self._ensure_lock_table()
            
        except Exception as e:
            logger.error(f"Failed to ensure state infrastructure: {e}")
            raise
    
    async def _ensure_state_bucket(self):
        """Ensure Terraform state S3 bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.state_bucket)
            logger.info(f"State bucket {self.state_bucket} exists")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                try:
                    if settings.AWS_REGION == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.state_bucket)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.state_bucket,
                            CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
                        )
                    
                    # Enable versioning
                    self.s3_client.put_bucket_versioning(
                        Bucket=self.state_bucket,
                        VersioningConfiguration={'Status': 'Enabled'}
                    )
                    
                    # Enable encryption
                    self.s3_client.put_bucket_encryption(
                        Bucket=self.state_bucket,
                        ServerSideEncryptionConfiguration={
                            'Rules': [{
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': 'AES256'
                                }
                            }]
                        }
                    )
                    
                    logger.info(f"Created state bucket {self.state_bucket}")
                except ClientError as create_error:
                    logger.error(f"Failed to create state bucket: {create_error}")
                    raise
            else:
                logger.error(f"Failed to check state bucket: {e}")
                raise
    
    async def _ensure_lock_table(self):
        """Ensure DynamoDB table for Terraform locking exists"""
        try:
            dynamodb = boto3.client(
                'dynamodb',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            
            lock_table = getattr(settings, 'TERRAFORM_LOCK_TABLE', 'codeflowops-terraform-locks')
            
            try:
                dynamodb.describe_table(TableName=lock_table)
                logger.info(f"Lock table {lock_table} exists")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # Table doesn't exist, create it
                    dynamodb.create_table(
                        TableName=lock_table,
                        KeySchema=[
                            {
                                'AttributeName': 'LockID',
                                'KeyType': 'HASH'
                            }
                        ],
                        AttributeDefinitions=[
                            {
                                'AttributeName': 'LockID',
                                'AttributeType': 'S'
                            }
                        ],
                        BillingMode='PAY_PER_REQUEST'
                    )
                    logger.info(f"Created lock table {lock_table}")
                else:
                    logger.error(f"Failed to check lock table: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Failed to ensure lock table: {e}")
            raise
    
    async def cleanup_state(self, user_id: str, project_name: str, session_id: str):
        """Clean up Terraform state files after destroy"""
        try:
            state_key = self.get_state_key(user_id, project_name, session_id)
            
            # Delete state file
            try:
                self.s3_client.delete_object(Bucket=self.state_bucket, Key=state_key)
                logger.info(f"Deleted state file: s3://{self.state_bucket}/{state_key}")
            except ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchKey':
                    logger.warning(f"Failed to delete state file: {e}")
            
            # Delete any backup/version files
            try:
                # List and delete all versions of the state file
                versions = self.s3_client.list_object_versions(
                    Bucket=self.state_bucket,
                    Prefix=state_key
                )
                
                for version in versions.get('Versions', []):
                    self.s3_client.delete_object(
                        Bucket=self.state_bucket,
                        Key=version['Key'],
                        VersionId=version['VersionId']
                    )
                
                for delete_marker in versions.get('DeleteMarkers', []):
                    self.s3_client.delete_object(
                        Bucket=self.state_bucket,
                        Key=delete_marker['Key'],
                        VersionId=delete_marker['VersionId']
                    )
                    
            except ClientError as e:
                logger.warning(f"Failed to cleanup state versions: {e}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup state: {e}")
            # Don't raise - this is cleanup, not critical
    
    async def get_terraform_init_args(
        self, 
        user_id: str, 
        project_name: str, 
        session_id: str
    ) -> list:
        """Get terraform init arguments for proper backend configuration"""
        backend_config = {
            'bucket': self.state_bucket,
            'key': self.get_state_key(user_id, project_name, session_id),
            'region': settings.AWS_REGION,
            'dynamodb_table': getattr(settings, 'TERRAFORM_LOCK_TABLE', 'codeflowops-terraform-locks'),
            'encrypt': 'true'
        }
        
        init_args = ['init']
        for key, value in backend_config.items():
            init_args.extend(['-backend-config', f'{key}={value}'])
        
        return init_args


# Global state manager instance
terraform_state_manager = TerraformStateManager()
