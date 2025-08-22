# Phase 2: Base Database Provider
# backend/providers/base_database_provider.py

"""
Base database provider interface for Phase 2 implementation
Defines common interface for PostgreSQL, MySQL, and MongoDB providers
"""

import boto3
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseEngine(Enum):
    POSTGRESQL = "postgres"
    MYSQL = "mysql" 
    MONGODB = "docdb"  # Amazon DocumentDB for MongoDB compatibility

class DatabaseStatus(Enum):
    CREATING = "creating"
    AVAILABLE = "available"
    MODIFYING = "modifying"
    BACKING_UP = "backing-up"
    DELETING = "deleting"
    FAILED = "failed"

@dataclass
class DatabaseConfig:
    """Database configuration parameters"""
    db_name: str
    username: str
    engine: DatabaseEngine
    instance_class: str = "db.t3.micro"
    allocated_storage: int = 20
    multi_az: bool = False
    backup_retention: int = 7
    vpc_security_group_ids: List[str] = None
    subnet_group_name: Optional[str] = None
    enable_encryption: bool = True
    enable_proxy: bool = True
    tags: Dict[str, str] = None

@dataclass
class DatabaseInstance:
    """Database instance information"""
    identifier: str
    engine: DatabaseEngine
    status: DatabaseStatus
    endpoint: str
    port: int
    db_name: str
    username: str
    created_at: datetime
    backup_retention: int
    multi_az: bool
    encryption_enabled: bool
    proxy_endpoint: Optional[str] = None
    secret_arn: Optional[str] = None

class BaseDatabaseProvider(ABC):
    """
    Base database provider interface
    ✅ Common interface for all database engines
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.rds = boto3.client('rds', region_name=region)
        self.docdb = boto3.client('docdb', region_name=region)
        self.secrets_manager = boto3.client('secretsmanager', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
    
    @abstractmethod
    def create_database(self, config: DatabaseConfig) -> DatabaseInstance:
        """Create a new database instance"""
        pass
    
    @abstractmethod
    def get_database_info(self, identifier: str) -> DatabaseInstance:
        """Get database instance information"""
        pass
    
    @abstractmethod
    def delete_database(self, identifier: str, skip_snapshot: bool = False) -> bool:
        """Delete database instance"""
        pass
    
    @abstractmethod
    def get_connection_string(self, identifier: str) -> str:
        """Get database connection string"""
        pass
    
    @abstractmethod
    def create_database_user(self, identifier: str, username: str, password: str, permissions: List[str]) -> bool:
        """Create database user with specific permissions"""
        pass
    
    def create_db_subnet_group(self, group_name: str, subnet_ids: List[str], description: str = None) -> str:
        """
        Create DB subnet group for VPC deployment
        ✅ Required for VPC database deployment
        """
        
        if not description:
            description = f"Subnet group for {group_name}"
        
        try:
            response = self.rds.create_db_subnet_group(
                DBSubnetGroupName=group_name,
                DBSubnetGroupDescription=description,
                SubnetIds=subnet_ids,
                Tags=[
                    {'Key': 'Name', 'Value': group_name},
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'ManagedBy', 'Value': 'DatabaseProvider'}
                ]
            )
            
            logger.info(f"✅ Created DB subnet group: {group_name}")
            return response['DBSubnetGroup']['DBSubnetGroupName']
            
        except Exception as e:
            if 'DBSubnetGroupAlreadyExistsFault' in str(e):
                logger.info(f"DB subnet group {group_name} already exists")
                return group_name
            else:
                logger.error(f"Failed to create DB subnet group: {e}")
                raise
    
    def create_db_security_group(self, vpc_id: str, group_name: str, port: int) -> str:
        """
        Create security group for database access
        ✅ Least-privilege database security
        """
        
        try:
            response = self.ec2.create_security_group(
                GroupName=group_name,
                Description=f"Security group for {group_name} database",
                VpcId=vpc_id,
                TagSpecifications=[
                    {
                        'ResourceType': 'security-group',
                        'Tags': [
                            {'Key': 'Name', 'Value': group_name},
                            {'Key': 'Project', 'Value': 'CodeFlowOps'}
                        ]
                    }
                ]
            )
            
            security_group_id = response['GroupId']
            
            # Add inbound rule for database port from VPC CIDR
            vpc_response = self.ec2.describe_vpcs(VpcIds=[vpc_id])
            vpc_cidr = vpc_response['Vpcs'][0]['CidrBlock']
            
            self.ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': port,
                        'ToPort': port,
                        'IpRanges': [{'CidrIp': vpc_cidr, 'Description': 'Database access from VPC'}]
                    }
                ]
            )
            
            logger.info(f"✅ Created database security group: {security_group_id}")
            return security_group_id
            
        except Exception as e:
            logger.error(f"Failed to create database security group: {e}")
            raise
    
    def create_master_password_secret(self, identifier: str, username: str, password: str) -> str:
        """
        Create master password in AWS Secrets Manager
        ✅ Secure password management
        """
        
        secret_name = f"codeflowops/database/{identifier}/master"
        
        secret_value = {
            'username': username,
            'password': password,
            'engine': self._get_engine_string(),
            'host': f"{identifier}.{self.region}.rds.amazonaws.com",
            'dbname': identifier
        }
        
        try:
            response = self.secrets_manager.create_secret(
                Name=secret_name,
                Description=f"Master credentials for {identifier} database",
                SecretString=json.dumps(secret_value),
                Tags=[
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'DatabaseId', 'Value': identifier},
                    {'Key': 'ManagedBy', 'Value': 'DatabaseProvider'}
                ]
            )
            
            logger.info(f"✅ Created master password secret: {secret_name}")
            return response['ARN']
            
        except Exception as e:
            if 'ResourceExistsException' in str(e):
                # Secret already exists, get ARN
                response = self.secrets_manager.describe_secret(SecretId=secret_name)
                return response['ARN']
            else:
                logger.error(f"Failed to create master password secret: {e}")
                raise
    
    def create_rds_proxy(self, identifier: str, db_instance_identifier: str, secret_arn: str, vpc_subnet_ids: List[str]) -> str:
        """
        Create RDS Proxy for connection pooling and security
        ✅ Production-grade connection management
        """
        
        proxy_name = f"{identifier}-proxy"
        
        try:
            response = self.rds.create_db_proxy(
                DBProxyName=proxy_name,
                EngineFamily=self._get_proxy_engine_family(),
                Auth=[
                    {
                        'AuthScheme': 'SECRETS',
                        'SecretArn': secret_arn,
                        'IAMAuth': 'DISABLED'  # Start with username/password auth
                    }
                ],
                RoleArn=self._get_proxy_role_arn(),
                VpcSubnetIds=vpc_subnet_ids,
                RequireTLS=True,
                IdleClientTimeout=1800,  # 30 minutes
                MaxConnectionsPercent=100,
                MaxIdleConnectionsPercent=50,
                Tags=[
                    {'Key': 'Name', 'Value': proxy_name},
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'DatabaseId', 'Value': identifier}
                ]
            )
            
            proxy_arn = response['DBProxy']['DBProxyArn']
            
            # Register database targets
            self.rds.register_db_proxy_targets(
                DBProxyName=proxy_name,
                DBInstanceIdentifiers=[db_instance_identifier]
            )
            
            logger.info(f"✅ Created RDS Proxy: {proxy_name}")
            return proxy_arn
            
        except Exception as e:
            logger.error(f"Failed to create RDS Proxy: {e}")
            raise
    
    def wait_for_database_available(self, identifier: str, timeout_minutes: int = 20) -> bool:
        """
        Wait for database to become available
        ✅ Deployment orchestration support
        """
        
        import time
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                db_info = self.get_database_info(identifier)
                if db_info.status == DatabaseStatus.AVAILABLE:
                    logger.info(f"✅ Database {identifier} is now available")
                    return True
                
                logger.info(f"Database {identifier} status: {db_info.status.value}")
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.warning(f"Error checking database status: {e}")
                time.sleep(30)
        
        logger.error(f"Database {identifier} did not become available within {timeout_minutes} minutes")
        return False
    
    @abstractmethod
    def _get_engine_string(self) -> str:
        """Get engine string for AWS services"""
        pass
    
    @abstractmethod
    def _get_proxy_engine_family(self) -> str:
        """Get proxy engine family"""
        pass
    
    def _get_proxy_role_arn(self) -> str:
        """Get IAM role ARN for RDS Proxy (placeholder)"""
        # This would need to be created separately or retrieved from configuration
        return f"arn:aws:iam::123456789012:role/codeflowops-rds-proxy-role"
    
    def get_database_metrics(self, identifier: str, hours: int = 1) -> Dict[str, Any]:
        """
        Get database performance metrics
        ✅ Monitoring integration
        """
        
        import boto3
        from datetime import datetime, timedelta
        
        cloudwatch = boto3.client('cloudwatch', region_name=self.region)
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = {}
        
        # Common metrics for all database engines
        metric_queries = [
            ('CPUUtilization', 'Percent'),
            ('DatabaseConnections', 'Count'),
            ('FreeableMemory', 'Bytes'),
            ('ReadLatency', 'Seconds'),
            ('WriteLatency', 'Seconds')
        ]
        
        for metric_name, unit in metric_queries:
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName=metric_name,
                    Dimensions=[
                        {'Name': 'DBInstanceIdentifier', 'Value': identifier}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,  # 5-minute intervals
                    Statistics=['Average', 'Maximum']
                )
                
                if response['Datapoints']:
                    latest = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                    metrics[metric_name] = {
                        'average': latest.get('Average', 0),
                        'maximum': latest.get('Maximum', 0),
                        'unit': unit,
                        'timestamp': latest['Timestamp'].isoformat()
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to get {metric_name} metric: {e}")
        
        return metrics
