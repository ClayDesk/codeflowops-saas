# Phase 2: MongoDB Database Provider
# backend/providers/mongodb_provider.py

"""
MongoDB database provider using Amazon DocumentDB
Production-ready MongoDB-compatible deployment with best practices
"""

import boto3
import json
import logging
import secrets
import string
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_database_provider import (
    BaseDatabaseProvider, DatabaseConfig, DatabaseInstance, 
    DatabaseEngine, DatabaseStatus
)

logger = logging.getLogger(__name__)

class MongoDBProvider(BaseDatabaseProvider):
    """
    MongoDB database provider using Amazon DocumentDB
    ✅ Production-ready MongoDB-compatible with DocumentDB
    """
    
    def __init__(self, region: str = 'us-east-1'):
        super().__init__(region)
        self.engine = DatabaseEngine.MONGODB
    
    def create_database(self, config: DatabaseConfig) -> DatabaseInstance:
        """
        Create DocumentDB cluster (MongoDB-compatible)
        ✅ Amazon DocumentDB with MongoDB compatibility
        """
        
        # Generate secure master password
        master_password = self._generate_secure_password()
        
        # Create master password secret
        secret_arn = self.create_master_password_secret(
            config.db_name, 
            config.username, 
            master_password
        )
        
        # DocumentDB requires cluster architecture
        cluster_identifier = f"{config.db_name}-cluster"
        
        # Prepare DocumentDB cluster parameters
        cluster_params = {
            'DBClusterIdentifier': cluster_identifier,
            'Engine': 'docdb',
            'MasterUsername': config.username,
            'MasterUserPassword': master_password,
            'BackupRetentionPeriod': config.backup_retention,
            'StorageEncrypted': config.enable_encryption,
            'EngineVersion': '5.0.0',  # Latest DocumentDB version with MongoDB 5.0 compatibility
            'DeletionProtection': True,
            'EnableCloudwatchLogsExports': ['audit', 'profiler'],
            'Tags': [
                {'Key': 'Name', 'Value': cluster_identifier},
                {'Key': 'Project', 'Value': 'CodeFlowOps'},
                {'Key': 'Engine', 'Value': 'DocumentDB-MongoDB'},
                {'Key': 'ManagedBy', 'Value': 'MongoDBProvider'},
                {'Key': 'Environment', 'Value': config.tags.get('Environment', 'development') if config.tags else 'development'}
            ]
        }
        
        # Add VPC configuration if provided
        if config.vpc_security_group_ids:
            cluster_params['VpcSecurityGroupIds'] = config.vpc_security_group_ids
        
        if config.subnet_group_name:
            cluster_params['DBSubnetGroupName'] = config.subnet_group_name
        
        # Add custom tags if provided
        if config.tags:
            for key, value in config.tags.items():
                cluster_params['Tags'].append({'Key': key, 'Value': value})
        
        try:
            logger.info(f"🍃 Creating DocumentDB cluster: {cluster_identifier}")
            
            # Create DocumentDB cluster
            cluster_response = self.docdb.create_db_cluster(**cluster_params)
            
            # Create primary instance
            instance_identifier = f"{cluster_identifier}-primary"
            instance_params = {
                'DBInstanceIdentifier': instance_identifier,
                'DBInstanceClass': config.instance_class,
                'Engine': 'docdb',
                'DBClusterIdentifier': cluster_identifier,
                'Tags': [
                    {'Key': 'Name', 'Value': instance_identifier},
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'Role', 'Value': 'Primary'}
                ]
            }
            
            self.docdb.create_db_instance(**instance_params)
            
            cluster = cluster_response['DBCluster']
            
            # Create database instance object
            instance = DatabaseInstance(
                identifier=cluster_identifier,
                engine=self.engine,
                status=DatabaseStatus.CREATING,
                endpoint=cluster.get('Endpoint', ''),
                port=cluster.get('Port', 27017),
                db_name=config.db_name,
                username=config.username,
                created_at=datetime.now(),
                backup_retention=config.backup_retention,
                multi_az=True,  # DocumentDB clusters are inherently multi-AZ
                encryption_enabled=config.enable_encryption,
                secret_arn=secret_arn
            )
            
            logger.info(f"✅ DocumentDB cluster created: {cluster_identifier}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create DocumentDB cluster: {e}")
            raise
    
    def get_database_info(self, identifier: str) -> DatabaseInstance:
        """Get DocumentDB cluster information"""
        
        try:
            response = self.docdb.describe_db_clusters(DBClusterIdentifier=identifier)
            db_cluster = response['DBClusters'][0]
            
            # Map DocumentDB status to our enum
            status_map = {
                'creating': DatabaseStatus.CREATING,
                'available': DatabaseStatus.AVAILABLE,
                'modifying': DatabaseStatus.MODIFYING,
                'backing-up': DatabaseStatus.BACKING_UP,
                'deleting': DatabaseStatus.DELETING,
                'failed': DatabaseStatus.FAILED
            }
            
            status = status_map.get(db_cluster['Status'], DatabaseStatus.FAILED)
            
            # Get secret ARN
            secret_arn = None
            try:
                secret_name = f"codeflowops/database/{identifier}/master"
                secret_response = self.secrets_manager.describe_secret(SecretId=secret_name)
                secret_arn = secret_response['ARN']
            except:
                pass  # Secret doesn't exist
            
            return DatabaseInstance(
                identifier=identifier,
                engine=self.engine,
                status=status,
                endpoint=db_cluster.get('Endpoint', ''),
                port=db_cluster.get('Port', 27017),
                db_name=db_cluster.get('DatabaseName', identifier),
                username=db_cluster.get('MasterUsername', ''),
                created_at=db_cluster.get('ClusterCreateTime', datetime.now()),
                backup_retention=db_cluster.get('BackupRetentionPeriod', 0),
                multi_az=True,  # DocumentDB clusters are always multi-AZ
                encryption_enabled=db_cluster.get('StorageEncrypted', False),
                secret_arn=secret_arn
            )
            
        except Exception as e:
            logger.error(f"Failed to get DocumentDB cluster info: {e}")
            raise
    
    def delete_database(self, identifier: str, skip_snapshot: bool = False) -> bool:
        """Delete DocumentDB cluster"""
        
        try:
            logger.info(f"🗑️ Deleting DocumentDB cluster: {identifier}")
            
            # Delete cluster instances first
            try:
                instances_response = self.docdb.describe_db_instances(
                    Filters=[
                        {'Name': 'db-cluster-id', 'Values': [identifier]}
                    ]
                )
                
                for instance in instances_response['DBInstances']:
                    instance_id = instance['DBInstanceIdentifier']
                    self.docdb.delete_db_instance(
                        DBInstanceIdentifier=instance_id
                    )
                    logger.info(f"✅ Deleted DocumentDB instance: {instance_id}")
            
            except Exception as e:
                logger.warning(f"Error deleting cluster instances: {e}")
            
            # Delete cluster
            delete_params = {
                'DBClusterIdentifier': identifier,
                'SkipFinalSnapshot': skip_snapshot
            }
            
            if not skip_snapshot:
                delete_params['FinalDBSnapshotIdentifier'] = f"{identifier}-final-snapshot-{int(datetime.now().timestamp())}"
            
            self.docdb.delete_db_cluster(**delete_params)
            
            # Clean up secrets
            try:
                secret_name = f"codeflowops/database/{identifier}/master"
                self.secrets_manager.delete_secret(
                    SecretId=secret_name,
                    ForceDeleteWithoutRecovery=True
                )
                logger.info(f"✅ Deleted master password secret")
            except:
                pass  # Secret doesn't exist
            
            logger.info(f"✅ DocumentDB cluster deletion initiated: {identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete DocumentDB cluster: {e}")
            return False
    
    def get_connection_string(self, identifier: str) -> str:
        """
        Get MongoDB connection string for DocumentDB
        ✅ DocumentDB-compatible connection string
        """
        
        try:
            db_info = self.get_database_info(identifier)
            
            # Get credentials from Secrets Manager
            secret_name = f"codeflowops/database/{identifier}/master"
            secret_response = self.secrets_manager.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(secret_response['SecretString'])
            
            username = secret_data['username']
            password = secret_data['password']
            
            # DocumentDB connection string format
            connection_string = (
                f"mongodb://{username}:{password}@{db_info.endpoint}:{db_info.port}/"
                f"?ssl=true&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
            )
            
            return connection_string
            
        except Exception as e:
            logger.error(f"Failed to get DocumentDB connection string: {e}")
            raise
    
    def create_database_user(self, identifier: str, username: str, password: str, permissions: List[str]) -> bool:
        """
        Create DocumentDB database user with specific permissions
        ✅ Application-specific user management for DocumentDB
        """
        
        try:
            import pymongo
            from pymongo import MongoClient
            
            # Get admin connection string
            admin_connection_string = self.get_connection_string(identifier)
            
            # Connect as admin user with SSL settings for DocumentDB
            client = MongoClient(
                admin_connection_string,
                ssl=True,
                ssl_ca_certs='/opt/docdb-ca-bundle.pem',  # DocumentDB CA bundle
                retryWrites=False
            )
            
            # Switch to admin database
            admin_db = client.admin
            
            # Create user with roles
            roles = []
            for permission in permissions:
                if permission == 'read':
                    roles.append({"role": "read", "db": identifier})
                elif permission == 'write':
                    roles.append({"role": "readWrite", "db": identifier})
                elif permission == 'admin':
                    roles.append({"role": "dbAdmin", "db": identifier})
                    roles.append({"role": "userAdmin", "db": identifier})
            
            admin_db.command("createUser", username, pwd=password, roles=roles)
            
            client.close()
            
            logger.info(f"✅ Created DocumentDB user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create DocumentDB user: {e}")
            return False
    
    def create_replica_set_member(self, cluster_identifier: str, instance_class: str = None) -> bool:
        """
        Add replica set member to DocumentDB cluster
        ✅ Scale DocumentDB cluster for better performance
        """
        
        if not instance_class:
            instance_class = 'db.t3.medium'
        
        try:
            # Get existing instances count
            instances_response = self.docdb.describe_db_instances(
                Filters=[
                    {'Name': 'db-cluster-id', 'Values': [cluster_identifier]}
                ]
            )
            
            instance_count = len(instances_response['DBInstances'])
            instance_identifier = f"{cluster_identifier}-replica-{instance_count + 1}"
            
            instance_params = {
                'DBInstanceIdentifier': instance_identifier,
                'DBInstanceClass': instance_class,
                'Engine': 'docdb',
                'DBClusterIdentifier': cluster_identifier,
                'Tags': [
                    {'Key': 'Name', 'Value': instance_identifier},
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'Role', 'Value': 'Replica'}
                ]
            }
            
            self.docdb.create_db_instance(**instance_params)
            
            logger.info(f"✅ Created DocumentDB replica: {instance_identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create DocumentDB replica: {e}")
            return False
    
    def _get_engine_string(self) -> str:
        """Get engine string for AWS services"""
        return "docdb"
    
    def _get_proxy_engine_family(self) -> str:
        """DocumentDB doesn't support RDS Proxy"""
        return None
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """Generate secure random password for DocumentDB"""
        
        # DocumentDB has specific password requirements
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Ensure password meets DocumentDB requirements
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.islower() for c in password):
            password = password[:-2] + secrets.choice(string.ascii_lowercase) + password[-1]
        if not any(c.isdigit() for c in password):
            password = password[:-3] + secrets.choice(string.digits) + password[-2:]
        
        return password
    
    def create_backup(self, identifier: str, backup_name: str = None) -> str:
        """
        Create manual backup of DocumentDB cluster
        ✅ On-demand backup support
        """
        
        if not backup_name:
            backup_name = f"{identifier}-manual-{int(datetime.now().timestamp())}"
        
        try:
            response = self.docdb.create_db_cluster_snapshot(
                DBClusterSnapshotIdentifier=backup_name,
                DBClusterIdentifier=identifier,
                Tags=[
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'BackupType', 'Value': 'Manual'},
                    {'Key': 'SourceCluster', 'Value': identifier}
                ]
            )
            
            snapshot_arn = response['DBClusterSnapshot']['DBClusterSnapshotArn']
            logger.info(f"✅ Created DocumentDB backup: {backup_name}")
            return snapshot_arn
            
        except Exception as e:
            logger.error(f"Failed to create DocumentDB backup: {e}")
            raise
    
    def restore_from_backup(self, backup_identifier: str, new_cluster_identifier: str, instance_class: str = 'db.t3.medium') -> DatabaseInstance:
        """
        Restore DocumentDB cluster from backup
        ✅ Point-in-time recovery support
        """
        
        try:
            logger.info(f"🔄 Restoring DocumentDB cluster from backup: {backup_identifier}")
            
            restore_params = {
                'DBClusterIdentifier': new_cluster_identifier,
                'SnapshotIdentifier': backup_identifier,
                'Engine': 'docdb',
                'EngineVersion': '5.0.0',
                'Tags': [
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'RestoredFrom', 'Value': backup_identifier},
                    {'Key': 'ManagedBy', 'Value': 'MongoDBProvider'}
                ]
            }
            
            cluster_response = self.docdb.restore_db_cluster_from_snapshot(**restore_params)
            
            # Create primary instance for restored cluster
            instance_identifier = f"{new_cluster_identifier}-primary"
            instance_params = {
                'DBInstanceIdentifier': instance_identifier,
                'DBInstanceClass': instance_class,
                'Engine': 'docdb',
                'DBClusterIdentifier': new_cluster_identifier
            }
            
            self.docdb.create_db_instance(**instance_params)
            
            cluster = cluster_response['DBCluster']
            
            return DatabaseInstance(
                identifier=new_cluster_identifier,
                engine=self.engine,
                status=DatabaseStatus.CREATING,
                endpoint=cluster.get('Endpoint', ''),
                port=cluster.get('Port', 27017),
                db_name=cluster.get('DatabaseName', new_cluster_identifier),
                username=cluster.get('MasterUsername', ''),
                created_at=datetime.now(),
                backup_retention=cluster.get('BackupRetentionPeriod', 0),
                multi_az=True,
                encryption_enabled=cluster.get('StorageEncrypted', False)
            )
            
        except Exception as e:
            logger.error(f"Failed to restore DocumentDB cluster: {e}")
            raise
    
    def optimize_for_workload(self, identifier: str, workload_type: str) -> bool:
        """
        Optimize DocumentDB cluster for specific workloads
        ✅ Workload-specific optimization for DocumentDB
        """
        
        try:
            optimization_params = {}
            
            if workload_type == "analytics":
                # DocumentDB parameter group for analytics workload
                optimization_params = {
                    'profiler': '2',  # Profile slow operations
                    'profiler_threshold_ms': '100'
                }
            elif workload_type == "transactional":
                # Optimized for transactional workload
                optimization_params = {
                    'profiler': '1',  # Profile only slow operations
                    'profiler_threshold_ms': '50'
                }
            
            if optimization_params:
                # Create parameter group
                param_group_name = f"{identifier}-optimized-{workload_type}"
                
                try:
                    self.docdb.create_db_cluster_parameter_group(
                        DBClusterParameterGroupName=param_group_name,
                        DBParameterGroupFamily='docdb5.0',
                        Description=f"Optimized parameters for {workload_type} workload"
                    )
                    
                    # Modify parameters
                    parameters = [
                        {'ParameterName': key, 'ParameterValue': value, 'ApplyMethod': 'pending-reboot'}
                        for key, value in optimization_params.items()
                    ]
                    
                    self.docdb.modify_db_cluster_parameter_group(
                        DBClusterParameterGroupName=param_group_name,
                        Parameters=parameters
                    )
                    
                    # Apply parameter group to cluster
                    self.docdb.modify_db_cluster(
                        DBClusterIdentifier=identifier,
                        DBClusterParameterGroupName=param_group_name,
                        ApplyImmediately=False  # Apply during next maintenance window
                    )
                    
                    logger.info(f"✅ Applied {workload_type} optimization to {identifier}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Failed to optimize cluster: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to optimize DocumentDB cluster: {e}")
            return False
