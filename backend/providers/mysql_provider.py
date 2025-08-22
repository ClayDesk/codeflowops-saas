# Phase 2: MySQL Database Provider
# backend/providers/mysql_provider.py

"""
MySQL database provider with RDS and Aurora support
Production-ready MySQL deployment with best practices
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

class MySQLProvider(BaseDatabaseProvider):
    """
    MySQL database provider with RDS/Aurora support
    ✅ Production-ready MySQL with RDS Proxy integration
    """
    
    def __init__(self, region: str = 'us-east-1'):
        super().__init__(region)
        self.engine = DatabaseEngine.MYSQL
    
    def create_database(self, config: DatabaseConfig) -> DatabaseInstance:
        """
        Create MySQL RDS instance with best practices
        ✅ Supports both single-instance RDS and Aurora clusters
        """
        
        # Generate secure master password
        master_password = self._generate_secure_password()
        
        # Create master password secret
        secret_arn = self.create_master_password_secret(
            config.db_name, 
            config.username, 
            master_password
        )
        
        # Prepare RDS parameters
        db_params = {
            'DBInstanceIdentifier': config.db_name,
            'DBInstanceClass': config.instance_class,
            'Engine': 'mysql',
            'MasterUsername': config.username,
            'MasterUserPassword': master_password,
            'AllocatedStorage': config.allocated_storage,
            'StorageType': 'gp3',  # Latest generation storage
            'StorageEncrypted': config.enable_encryption,
            'BackupRetentionPeriod': config.backup_retention,
            'MultiAZ': config.multi_az,
            'EngineVersion': '8.0.35',  # Latest stable MySQL version
            'AutoMinorVersionUpgrade': True,
            'PubliclyAccessible': False,  # Security best practice
            'CopyTagsToSnapshot': True,
            'DeletionProtection': True,  # Prevent accidental deletion
            'EnablePerformanceInsights': True,
            'PerformanceInsightsRetentionPeriod': 7,
            'MonitoringInterval': 60,
            'EnableCloudwatchLogsExports': ['error', 'general', 'slow-query'],
            'Tags': [
                {'Key': 'Name', 'Value': config.db_name},
                {'Key': 'Project', 'Value': 'CodeFlowOps'},
                {'Key': 'Engine', 'Value': 'MySQL'},
                {'Key': 'ManagedBy', 'Value': 'MySQLProvider'},
                {'Key': 'Environment', 'Value': config.tags.get('Environment', 'development') if config.tags else 'development'}
            ]
        }
        
        # Add VPC configuration if provided
        if config.vpc_security_group_ids:
            db_params['VpcSecurityGroupIds'] = config.vpc_security_group_ids
        
        if config.subnet_group_name:
            db_params['DBSubnetGroupName'] = config.subnet_group_name
        
        # Add custom tags if provided
        if config.tags:
            for key, value in config.tags.items():
                db_params['Tags'].append({'Key': key, 'Value': value})
        
        try:
            logger.info(f"🐬 Creating MySQL database: {config.db_name}")
            
            response = self.rds.create_db_instance(**db_params)
            db_instance = response['DBInstance']
            
            # Wait for database to be available if proxy is requested
            if config.enable_proxy:
                logger.info("⏳ Waiting for database to become available before creating proxy...")
                self.wait_for_database_available(config.db_name, timeout_minutes=25)
            
            # Create RDS Proxy if enabled
            proxy_endpoint = None
            if config.enable_proxy and config.vpc_security_group_ids:
                try:
                    # Get VPC subnet IDs from subnet group
                    subnet_response = self.rds.describe_db_subnet_groups(
                        DBSubnetGroupName=config.subnet_group_name
                    )
                    subnet_ids = [subnet['SubnetIdentifier'] for subnet in 
                                subnet_response['DBSubnetGroups'][0]['Subnets']]
                    
                    proxy_arn = self.create_rds_proxy(
                        config.db_name, 
                        config.db_name, 
                        secret_arn, 
                        subnet_ids
                    )
                    proxy_endpoint = f"{config.db_name}-proxy.proxy-{self.region}.rds.amazonaws.com"
                    
                except Exception as e:
                    logger.warning(f"Failed to create RDS Proxy: {e}")
            
            # Create database instance object
            instance = DatabaseInstance(
                identifier=config.db_name,
                engine=self.engine,
                status=DatabaseStatus.CREATING,
                endpoint=db_instance['Endpoint']['Address'] if 'Endpoint' in db_instance else '',
                port=db_instance.get('DbInstancePort', 3306),
                db_name=config.db_name,
                username=config.username,
                created_at=datetime.now(),
                backup_retention=config.backup_retention,
                multi_az=config.multi_az,
                encryption_enabled=config.enable_encryption,
                proxy_endpoint=proxy_endpoint,
                secret_arn=secret_arn
            )
            
            logger.info(f"✅ MySQL database created: {config.db_name}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create MySQL database: {e}")
            raise
    
    def get_database_info(self, identifier: str) -> DatabaseInstance:
        """Get MySQL database instance information"""
        
        try:
            response = self.rds.describe_db_instances(DBInstanceIdentifier=identifier)
            db_instance = response['DBInstances'][0]
            
            # Map RDS status to our enum
            status_map = {
                'creating': DatabaseStatus.CREATING,
                'available': DatabaseStatus.AVAILABLE,
                'modifying': DatabaseStatus.MODIFYING,
                'backing-up': DatabaseStatus.BACKING_UP,
                'deleting': DatabaseStatus.DELETING,
                'failed': DatabaseStatus.FAILED
            }
            
            status = status_map.get(db_instance['DBInstanceStatus'], DatabaseStatus.FAILED)
            
            # Check for RDS Proxy
            proxy_endpoint = None
            try:
                proxy_response = self.rds.describe_db_proxies(
                    DBProxyName=f"{identifier}-proxy"
                )
                if proxy_response['DBProxies']:
                    proxy = proxy_response['DBProxies'][0]
                    proxy_endpoint = proxy['Endpoint']
            except:
                pass  # Proxy doesn't exist
            
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
                endpoint=db_instance.get('Endpoint', {}).get('Address', ''),
                port=db_instance.get('Endpoint', {}).get('Port', 3306),
                db_name=db_instance.get('DBName', identifier),
                username=db_instance.get('MasterUsername', ''),
                created_at=db_instance.get('InstanceCreateTime', datetime.now()),
                backup_retention=db_instance.get('BackupRetentionPeriod', 0),
                multi_az=db_instance.get('MultiAZ', False),
                encryption_enabled=db_instance.get('StorageEncrypted', False),
                proxy_endpoint=proxy_endpoint,
                secret_arn=secret_arn
            )
            
        except Exception as e:
            logger.error(f"Failed to get MySQL database info: {e}")
            raise
    
    def delete_database(self, identifier: str, skip_snapshot: bool = False) -> bool:
        """Delete MySQL database instance"""
        
        try:
            logger.info(f"🗑️ Deleting MySQL database: {identifier}")
            
            # Delete RDS Proxy first if it exists
            try:
                self.rds.delete_db_proxy(DBProxyName=f"{identifier}-proxy")
                logger.info(f"✅ Deleted RDS Proxy: {identifier}-proxy")
            except:
                pass  # Proxy doesn't exist
            
            # Delete database instance
            delete_params = {
                'DBInstanceIdentifier': identifier,
                'SkipFinalSnapshot': skip_snapshot,
                'DeleteAutomatedBackups': True
            }
            
            if not skip_snapshot:
                delete_params['FinalDBSnapshotIdentifier'] = f"{identifier}-final-snapshot-{int(datetime.now().timestamp())}"
            
            self.rds.delete_db_instance(**delete_params)
            
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
            
            logger.info(f"✅ MySQL database deletion initiated: {identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete MySQL database: {e}")
            return False
    
    def get_connection_string(self, identifier: str) -> str:
        """
        Get MySQL connection string with proxy support
        ✅ Supports both direct and proxy connections
        """
        
        try:
            db_info = self.get_database_info(identifier)
            
            # Get credentials from Secrets Manager
            secret_name = f"codeflowops/database/{identifier}/master"
            secret_response = self.secrets_manager.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(secret_response['SecretString'])
            
            username = secret_data['username']
            password = secret_data['password']
            
            # Use proxy endpoint if available, otherwise direct endpoint
            endpoint = db_info.proxy_endpoint if db_info.proxy_endpoint else db_info.endpoint
            port = 3306  # Standard MySQL port
            
            connection_string = (
                f"mysql://{username}:{password}@{endpoint}:{port}/{db_info.db_name}"
                "?ssl=true&charset=utf8mb4"
            )
            
            return connection_string
            
        except Exception as e:
            logger.error(f"Failed to get MySQL connection string: {e}")
            raise
    
    def create_database_user(self, identifier: str, username: str, password: str, permissions: List[str]) -> bool:
        """
        Create MySQL database user with specific permissions
        ✅ Application-specific user management
        """
        
        try:
            import pymysql
            
            # Get admin connection info
            db_info = self.get_database_info(identifier)
            
            # Get admin credentials
            secret_name = f"codeflowops/database/{identifier}/master"
            secret_response = self.secrets_manager.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(secret_response['SecretString'])
            
            admin_username = secret_data['username']
            admin_password = secret_data['password']
            
            # Connect as admin user
            endpoint = db_info.proxy_endpoint if db_info.proxy_endpoint else db_info.endpoint
            
            connection = pymysql.connect(
                host=endpoint,
                port=3306,
                user=admin_username,
                password=admin_password,
                database=db_info.db_name,
                ssl={'ssl': True}
            )
            
            with connection.cursor() as cursor:
                # Create user
                cursor.execute(f"CREATE USER %s@'%' IDENTIFIED BY %s", (username, password))
                
                # Grant permissions
                for permission in permissions:
                    if permission == 'read':
                        cursor.execute(f"GRANT SELECT ON {db_info.db_name}.* TO %s@'%'", (username,))
                    elif permission == 'write':
                        cursor.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {db_info.db_name}.* TO %s@'%'", (username,))
                    elif permission == 'admin':
                        cursor.execute(f"GRANT ALL PRIVILEGES ON {db_info.db_name}.* TO %s@'%'", (username,))
                
                cursor.execute("FLUSH PRIVILEGES")
                connection.commit()
            
            connection.close()
            
            logger.info(f"✅ Created MySQL user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create MySQL user: {e}")
            return False
    
    def create_aurora_cluster(self, config: DatabaseConfig, cluster_size: int = 2) -> DatabaseInstance:
        """
        Create MySQL Aurora cluster for high availability
        ✅ Aurora cluster support for production workloads
        """
        
        cluster_identifier = f"{config.db_name}-cluster"
        
        # Generate secure master password
        master_password = self._generate_secure_password()
        
        # Create master password secret
        secret_arn = self.create_master_password_secret(
            cluster_identifier, 
            config.username, 
            master_password
        )
        
        try:
            logger.info(f"🚀 Creating MySQL Aurora cluster: {cluster_identifier}")
            
            # Create Aurora cluster
            cluster_params = {
                'DBClusterIdentifier': cluster_identifier,
                'Engine': 'aurora-mysql',
                'EngineVersion': '8.0.mysql_aurora.3.04.0',
                'MasterUsername': config.username,
                'MasterUserPassword': master_password,
                'DatabaseName': config.db_name,
                'BackupRetentionPeriod': config.backup_retention,
                'StorageEncrypted': config.enable_encryption,
                'EnableCloudwatchLogsExports': ['audit', 'error', 'general', 'slowquery'],
                'DeletionProtection': True,
                'Tags': [
                    {'Key': 'Name', 'Value': cluster_identifier},
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'Engine', 'Value': 'Aurora-MySQL'},
                    {'Key': 'ManagedBy', 'Value': 'MySQLProvider'}
                ]
            }
            
            # Add VPC configuration
            if config.vpc_security_group_ids:
                cluster_params['VpcSecurityGroupIds'] = config.vpc_security_group_ids
            
            if config.subnet_group_name:
                cluster_params['DBSubnetGroupName'] = config.subnet_group_name
            
            cluster_response = self.rds.create_db_cluster(**cluster_params)
            
            # Create cluster instances
            for i in range(cluster_size):
                instance_identifier = f"{cluster_identifier}-{i+1}"
                instance_params = {
                    'DBInstanceIdentifier': instance_identifier,
                    'DBInstanceClass': config.instance_class,
                    'Engine': 'aurora-mysql',
                    'DBClusterIdentifier': cluster_identifier,
                    'PubliclyAccessible': False,
                    'Tags': [
                        {'Key': 'Name', 'Value': instance_identifier},
                        {'Key': 'Project', 'Value': 'CodeFlowOps'},
                        {'Key': 'Role', 'Value': 'writer' if i == 0 else 'reader'}
                    ]
                }
                
                self.rds.create_db_instance(**instance_params)
            
            cluster = cluster_response['DBCluster']
            
            return DatabaseInstance(
                identifier=cluster_identifier,
                engine=self.engine,
                status=DatabaseStatus.CREATING,
                endpoint=cluster.get('Endpoint', ''),
                port=cluster.get('Port', 3306),
                db_name=config.db_name,
                username=config.username,
                created_at=datetime.now(),
                backup_retention=config.backup_retention,
                multi_az=True,  # Aurora is inherently multi-AZ
                encryption_enabled=config.enable_encryption,
                secret_arn=secret_arn
            )
            
        except Exception as e:
            logger.error(f"Failed to create Aurora cluster: {e}")
            raise
    
    def _get_engine_string(self) -> str:
        """Get engine string for AWS services"""
        return "mysql"
    
    def _get_proxy_engine_family(self) -> str:
        """Get proxy engine family"""
        return "MYSQL"
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """Generate secure random password"""
        
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # Ensure password meets RDS requirements
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.islower() for c in password):
            password = password[:-2] + secrets.choice(string.ascii_lowercase) + password[-1]
        if not any(c.isdigit() for c in password):
            password = password[:-3] + secrets.choice(string.digits) + password[-2:]
        
        return password
    
    def optimize_for_workload(self, identifier: str, workload_type: str) -> bool:
        """
        Optimize MySQL configuration for specific workloads
        ✅ Workload-specific optimization
        """
        
        try:
            optimization_params = {}
            
            if workload_type == "oltp":  # Online Transaction Processing
                optimization_params = {
                    'max_connections': '100',
                    'innodb_buffer_pool_size': '{DBInstanceClassMemory*3/4}',
                    'innodb_log_file_size': '256M',
                    'innodb_flush_log_at_trx_commit': '1',
                    'sync_binlog': '1',
                    'query_cache_size': '0',  # Disabled for better performance
                    'query_cache_type': '0'
                }
            elif workload_type == "analytics":  # Analytical workload
                optimization_params = {
                    'max_connections': '50',
                    'innodb_buffer_pool_size': '{DBInstanceClassMemory*7/8}',
                    'innodb_log_file_size': '512M',
                    'innodb_flush_log_at_trx_commit': '2',
                    'sync_binlog': '0',
                    'read_buffer_size': '2M',
                    'sort_buffer_size': '4M',
                    'join_buffer_size': '8M'
                }
            elif workload_type == "mixed":  # Mixed workload
                optimization_params = {
                    'max_connections': '80',
                    'innodb_buffer_pool_size': '{DBInstanceClassMemory*3/4}',
                    'innodb_log_file_size': '512M',
                    'innodb_flush_log_at_trx_commit': '1',
                    'sync_binlog': '1',
                    'query_cache_size': '128M',
                    'query_cache_type': '1'
                }
            
            if optimization_params:
                # Create parameter group
                param_group_name = f"{identifier}-optimized-{workload_type}"
                
                try:
                    self.rds.create_db_parameter_group(
                        DBParameterGroupName=param_group_name,
                        DBParameterGroupFamily='mysql8.0',
                        Description=f"Optimized parameters for {workload_type} workload"
                    )
                    
                    # Modify parameters
                    parameters = [
                        {'ParameterName': key, 'ParameterValue': value, 'ApplyMethod': 'pending-reboot'}
                        for key, value in optimization_params.items()
                    ]
                    
                    self.rds.modify_db_parameter_group(
                        DBParameterGroupName=param_group_name,
                        Parameters=parameters
                    )
                    
                    # Apply parameter group to database
                    self.rds.modify_db_instance(
                        DBInstanceIdentifier=identifier,
                        DBParameterGroupName=param_group_name,
                        ApplyImmediately=False  # Apply during next maintenance window
                    )
                    
                    logger.info(f"✅ Applied {workload_type} optimization to {identifier}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Failed to optimize database: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to optimize MySQL database: {e}")
            return False
    
    def setup_replication(self, master_identifier: str, replica_identifier: str, region: str = None) -> bool:
        """
        Setup MySQL read replica for scaling
        ✅ Read replica support for read scaling
        """
        
        try:
            replica_region = region or self.region
            
            replica_params = {
                'DBInstanceIdentifier': replica_identifier,
                'SourceDBInstanceIdentifier': master_identifier,
                'DBInstanceClass': 'db.t3.micro',  # Can be different from master
                'PubliclyAccessible': False,
                'AutoMinorVersionUpgrade': True,
                'Tags': [
                    {'Key': 'Name', 'Value': replica_identifier},
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'Role', 'Value': 'ReadReplica'},
                    {'Key': 'MasterDB', 'Value': master_identifier}
                ]
            }
            
            # For cross-region replica
            if replica_region != self.region:
                replica_params['SourceDBInstanceIdentifier'] = f"arn:aws:rds:{self.region}:123456789012:db:{master_identifier}"
            
            self.rds.create_db_instance_read_replica(**replica_params)
            
            logger.info(f"✅ Created MySQL read replica: {replica_identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create MySQL read replica: {e}")
            return False
