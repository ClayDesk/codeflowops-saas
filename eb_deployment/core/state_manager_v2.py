# Phase 1: Foundation + Quick Wins Implementation
# backend/core/state_manager_v2.py

"""
Enhanced state management with DynamoDB and concurrency safety
This is a NEW component that coexists with existing deployment tracking
"""

import boto3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class DeploymentStatus(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    BUILDING = "building"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"

@dataclass
class DeploymentState:
    """Enhanced deployment state with full observability"""
    deployment_id: str
    status: DeploymentStatus
    stack_type: str
    primary_stack: str
    secondary_stacks: List[str]
    resources: Dict[str, Any]
    health_checks: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    version: int = 1

class ConcurrentDeploymentError(Exception):
    """Raised when concurrent deployment operations conflict"""
    pass

class ConcurrentUpdateError(Exception):
    """Raised when deployment update conflicts with another process"""
    pass

class StateManagerV2:
    """
    Enhanced DynamoDB-based deployment state tracking with concurrency control
    This is a NEW component that doesn't interfere with existing deployment tracking
    """
    
    def __init__(self, table_name: str = 'codeflowops-deployments-v2'):
        """
        Initialize with separate table to avoid conflicts with existing system
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name
        self.table = None
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create DynamoDB table if it doesn't exist"""
        try:
            # Check if table exists
            self.table = self.dynamodb.Table(self.table_name)
            self.table.meta.client.describe_table(TableName=self.table_name)
            logger.info(f"Using existing DynamoDB table: {self.table_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.info(f"Creating new DynamoDB table: {self.table_name}")
                self._create_table()
            else:
                raise
    
    def _create_table(self):
        """Create the DynamoDB table with proper configuration"""
        self.table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {
                    'AttributeName': 'deployment_id',
                    'KeyType': 'HASH'
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'deployment_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST',
            Tags=[
                {
                    'Key': 'Project',
                    'Value': 'CodeFlowOps'
                },
                {
                    'Key': 'Component', 
                    'Value': 'StateManagement'
                },
                {
                    'Key': 'Version',
                    'Value': 'v2'
                }
            ]
        )
        
        # Wait for table to be ready
        self.table.meta.client.get_waiter('table_exists').wait(TableName=self.table_name)
        logger.info(f"Successfully created DynamoDB table: {self.table_name}")
    
    def track_deployment(self, deployment_state: DeploymentState) -> Dict[str, Any]:
        """
        Track deployment lifecycle with optimistic concurrency control
        ✅ DynamoDB concurrency safety with ConditionExpression
        """
        timestamp = datetime.utcnow().isoformat()
        deployment_state.created_at = timestamp
        deployment_state.updated_at = timestamp
        deployment_state.version = 1
        
        try:
            # Convert dataclass to dict for DynamoDB
            item = asdict(deployment_state)
            item['status'] = item['status'].value  # Convert enum to string
            
            response = self.table.put_item(
                Item=item,
                ConditionExpression='attribute_not_exists(deployment_id)',  # Prevent duplicates
                ReturnValues='ALL_OLD'
            )
            
            logger.info(f"✅ Successfully tracked deployment: {deployment_state.deployment_id}")
            return item
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Concurrent deployment creation detected for {deployment_state.deployment_id}")
                raise ConcurrentDeploymentError(f"Deployment {deployment_state.deployment_id} already exists")
            else:
                logger.error(f"Failed to track deployment {deployment_state.deployment_id}: {e}")
                raise
    
    def update_deployment_status(self, deployment_id: str, new_status: DeploymentStatus, 
                               current_version: int, additional_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Update deployment with optimistic concurrency control
        ✅ Optimistic locking prevents race conditions
        """
        timestamp = datetime.utcnow().isoformat()
        
        try:
            update_expression = 'SET #status = :status, updated_at = :timestamp, version = version + :inc'
            expression_values = {
                ':status': new_status.value,
                ':timestamp': timestamp,
                ':current_version': current_version,
                ':inc': 1
            }
            expression_names = {'#status': 'status'}
            
            # Add additional data if provided
            if additional_data:
                for key, value in additional_data.items():
                    safe_key = key.replace('-', '_').replace('.', '_')
                    update_expression += f', #{safe_key} = :{safe_key}'
                    expression_names[f'#{safe_key}'] = key
                    expression_values[f':{safe_key}'] = value
            
            response = self.table.update_item(
                Key={'deployment_id': deployment_id},
                UpdateExpression=update_expression,
                ConditionExpression='version = :current_version',  # ✅ Optimistic locking
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            logger.info(f"✅ Successfully updated deployment {deployment_id} to {new_status.value}")
            return response['Attributes']
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.warning(f"Concurrent update detected for deployment {deployment_id}")
                raise ConcurrentUpdateError(f"Deployment {deployment_id} was modified by another process")
            else:
                logger.error(f"Failed to update deployment {deployment_id}: {e}")
                raise
    
    def get_deployment(self, deployment_id: str) -> Optional[DeploymentState]:
        """Get deployment state by ID"""
        try:
            response = self.table.get_item(Key={'deployment_id': deployment_id})
            
            if 'Item' in response:
                item = response['Item']
                # Convert status string back to enum
                item['status'] = DeploymentStatus(item['status'])
                return DeploymentState(**item)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to get deployment {deployment_id}: {e}")
            raise
    
    def list_deployments(self, limit: int = 50, status_filter: Optional[DeploymentStatus] = None) -> List[DeploymentState]:
        """List recent deployments with optional status filtering"""
        try:
            scan_kwargs = {'Limit': limit}
            
            if status_filter:
                scan_kwargs['FilterExpression'] = boto3.dynamodb.conditions.Attr('status').eq(status_filter.value)
            
            response = self.table.scan(**scan_kwargs)
            
            deployments = []
            for item in response.get('Items', []):
                item['status'] = DeploymentStatus(item['status'])
                deployments.append(DeploymentState(**item))
            
            # Sort by created_at descending
            deployments.sort(key=lambda x: x.created_at, reverse=True)
            return deployments
            
        except Exception as e:
            logger.error(f"Failed to list deployments: {e}")
            raise
    
    def cleanup_old_deployments(self, retention_days: int = 30):
        """Clean up old deployment records"""
        # Implementation for cleanup based on retention policy
        pass
