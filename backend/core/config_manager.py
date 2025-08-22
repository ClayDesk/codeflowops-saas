# Phase 1: Configuration Management
# backend/core/config_manager.py

"""
Centralized configuration management with environment support
This is a NEW component that manages configuration without affecting existing systems
"""

import os
import json
import logging
import boto3
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    engine: str  # mysql, postgresql, mongodb
    host: str
    port: int
    database_name: str
    username: str
    password_secret_arn: str  # AWS Secrets Manager ARN
    connection_pool_size: int = 10
    ssl_required: bool = True
    proxy_enabled: bool = False
    proxy_endpoint: Optional[str] = None

@dataclass
class SecurityConfig:
    """Security configuration"""
    vpc_id: Optional[str] = None
    subnet_ids: List[str] = field(default_factory=list)
    security_group_ids: List[str] = field(default_factory=list)
    enable_vpc_endpoints: bool = True
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
    iam_role_arn: Optional[str] = None

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    enable_cloudwatch: bool = True
    enable_xray: bool = True
    log_level: str = "INFO"
    custom_metrics_namespace: str = "CodeFlowOps"
    health_check_interval_minutes: int = 5
    alert_sns_topic_arn: Optional[str] = None

@dataclass 
class DeploymentConfig:
    """Deployment-specific configuration"""
    region: str
    environment: Environment
    project_name: str
    stack_name: str
    domain_name: Optional[str] = None
    certificate_arn: Optional[str] = None
    enable_blue_green: bool = False
    rollback_on_failure: bool = True

class ConfigManager:
    """
    Centralized configuration management for CodeFlowOps
    ✅ Environment-aware configuration with AWS integration
    """
    
    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.ssm = boto3.client('ssm')
        self.secrets_manager = boto3.client('secretsmanager')
        
        # ✅ Load configuration hierarchy
        self.config = self._load_configuration()
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Load configuration from multiple sources with precedence:
        1. Environment variables (highest)
        2. AWS Parameter Store
        3. Local config files
        4. Default values (lowest)
        """
        
        config = {}
        
        # 1. Load defaults
        config.update(self._get_default_config())
        
        # 2. Load from local config files
        config.update(self._load_local_config())
        
        # 3. Load from AWS Parameter Store
        config.update(self._load_aws_parameters())
        
        # 4. Override with environment variables
        config.update(self._load_env_variables())
        
        logger.info(f"✅ Loaded configuration for {self.environment.value} environment")
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration values"""
        return {
            'deployment': {
                'region': 'us-east-1',
                'environment': self.environment.value,
                'project_name': 'codeflowops',
                'enable_blue_green': False,
                'rollback_on_failure': True
            },
            'security': {
                'enable_vpc_endpoints': True,
                'encryption_at_rest': True,
                'encryption_in_transit': True
            },
            'monitoring': {
                'enable_cloudwatch': True,
                'enable_xray': False,  # Disabled by default for cost
                'log_level': 'INFO',
                'custom_metrics_namespace': 'CodeFlowOps',
                'health_check_interval_minutes': 5
            },
            'database': {
                'connection_pool_size': 10,
                'ssl_required': True,
                'proxy_enabled': False
            }
        }
    
    def _load_local_config(self) -> Dict[str, Any]:
        """Load configuration from local JSON files"""
        
        config = {}
        config_dir = Path(__file__).parent.parent / 'config'
        
        # Load base config
        base_config_file = config_dir / 'base.json'
        if base_config_file.exists():
            try:
                with open(base_config_file, 'r') as f:
                    config.update(json.load(f))
            except Exception as e:
                logger.warning(f"Failed to load base config: {e}")
        
        # Load environment-specific config
        env_config_file = config_dir / f'{self.environment.value}.json'
        if env_config_file.exists():
            try:
                with open(env_config_file, 'r') as f:
                    env_config = json.load(f)
                    config = self._deep_merge(config, env_config)
            except Exception as e:
                logger.warning(f"Failed to load {self.environment.value} config: {e}")
        
        return config
    
    def _load_aws_parameters(self) -> Dict[str, Any]:
        """Load configuration from AWS Systems Manager Parameter Store"""
        
        config = {}
        parameter_prefix = f'/codeflowops/{self.environment.value}'
        
        try:
            paginator = self.ssm.get_paginator('get_parameters_by_path')
            
            for page in paginator.paginate(
                Path=parameter_prefix,
                Recursive=True,
                WithDecryption=True
            ):
                for param in page['Parameters']:
                    # Convert parameter name to nested dict key
                    key_path = param['Name'].replace(parameter_prefix, '').strip('/').split('/')
                    self._set_nested_value(config, key_path, param['Value'])
            
            logger.info(f"✅ Loaded parameters from AWS Parameter Store: {parameter_prefix}")
            
        except Exception as e:
            logger.warning(f"Failed to load AWS parameters: {e}")
        
        return config
    
    def _load_env_variables(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        
        config = {}
        
        # Environment variable mappings
        env_mappings = {
            'CODEFLOWOPS_REGION': ['deployment', 'region'],
            'CODEFLOWOPS_PROJECT_NAME': ['deployment', 'project_name'],
            'CODEFLOWOPS_LOG_LEVEL': ['monitoring', 'log_level'],
            'CODEFLOWOPS_ENABLE_XRAY': ['monitoring', 'enable_xray'],
            'CODEFLOWOPS_VPC_ID': ['security', 'vpc_id'],
            'CODEFLOWOPS_DB_HOST': ['database', 'host'],
            'CODEFLOWOPS_DB_PORT': ['database', 'port'],
            'CODEFLOWOPS_DB_NAME': ['database', 'database_name'],
        }
        
        for env_var, key_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Convert string values to appropriate types
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                
                self._set_nested_value(config, key_path, value)
        
        return config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _set_nested_value(self, dictionary: Dict[str, Any], key_path: List[str], value: Any):
        """Set a nested dictionary value using a list of keys"""
        
        current = dictionary
        for key in key_path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[key_path[-1]] = value
    
    def get_deployment_config(self) -> DeploymentConfig:
        """Get deployment configuration"""
        
        deployment_data = self.config.get('deployment', {})
        
        return DeploymentConfig(
            region=deployment_data.get('region', 'us-east-1'),
            environment=Environment(deployment_data.get('environment', 'development')),
            project_name=deployment_data.get('project_name', 'codeflowops'),
            stack_name=deployment_data.get('stack_name', f"codeflowops-{self.environment.value}"),
            domain_name=deployment_data.get('domain_name'),
            certificate_arn=deployment_data.get('certificate_arn'),
            enable_blue_green=deployment_data.get('enable_blue_green', False),
            rollback_on_failure=deployment_data.get('rollback_on_failure', True)
        )
    
    def get_database_config(self, stack_name: str) -> Optional[DatabaseConfig]:
        """Get database configuration for a specific stack"""
        
        db_data = self.config.get('stacks', {}).get(stack_name, {}).get('database', {})
        
        if not db_data:
            return None
        
        return DatabaseConfig(
            engine=db_data.get('engine', 'postgresql'),
            host=db_data.get('host', ''),
            port=db_data.get('port', 5432),
            database_name=db_data.get('database_name', stack_name),
            username=db_data.get('username', 'app_user'),
            password_secret_arn=db_data.get('password_secret_arn', ''),
            connection_pool_size=db_data.get('connection_pool_size', 10),
            ssl_required=db_data.get('ssl_required', True),
            proxy_enabled=db_data.get('proxy_enabled', False),
            proxy_endpoint=db_data.get('proxy_endpoint')
        )
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        
        security_data = self.config.get('security', {})
        
        return SecurityConfig(
            vpc_id=security_data.get('vpc_id'),
            subnet_ids=security_data.get('subnet_ids', []),
            security_group_ids=security_data.get('security_group_ids', []),
            enable_vpc_endpoints=security_data.get('enable_vpc_endpoints', True),
            encryption_at_rest=security_data.get('encryption_at_rest', True),
            encryption_in_transit=security_data.get('encryption_in_transit', True),
            iam_role_arn=security_data.get('iam_role_arn')
        )
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        
        monitoring_data = self.config.get('monitoring', {})
        
        return MonitoringConfig(
            enable_cloudwatch=monitoring_data.get('enable_cloudwatch', True),
            enable_xray=monitoring_data.get('enable_xray', False),
            log_level=monitoring_data.get('log_level', 'INFO'),
            custom_metrics_namespace=monitoring_data.get('custom_metrics_namespace', 'CodeFlowOps'),
            health_check_interval_minutes=monitoring_data.get('health_check_interval_minutes', 5),
            alert_sns_topic_arn=monitoring_data.get('alert_sns_topic_arn')
        )
    
    def store_parameter(self, parameter_name: str, value: str, secure: bool = False):
        """Store parameter in AWS Parameter Store"""
        
        full_parameter_name = f'/codeflowops/{self.environment.value}/{parameter_name}'
        
        try:
            self.ssm.put_parameter(
                Name=full_parameter_name,
                Value=value,
                Type='SecureString' if secure else 'String',
                Overwrite=True,
                Tags=[
                    {'Key': 'Project', 'Value': 'CodeFlowOps'},
                    {'Key': 'Environment', 'Value': self.environment.value},
                    {'Key': 'ManagedBy', 'Value': 'ConfigManager'}
                ]
            )
            
            logger.info(f"✅ Stored parameter: {full_parameter_name}")
            
        except Exception as e:
            logger.error(f"Failed to store parameter {parameter_name}: {e}")
            raise
    
    def get_connection_string(self, stack_name: str) -> Optional[str]:
        """
        Get database connection string with secret resolution
        ✅ Secure connection string with AWS Secrets Manager integration
        """
        
        db_config = self.get_database_config(stack_name)
        if not db_config:
            return None
        
        try:
            # Get password from Secrets Manager
            secret_response = self.secrets_manager.get_secret_value(
                SecretId=db_config.password_secret_arn
            )
            
            secret_data = json.loads(secret_response['SecretString'])
            password = secret_data.get('password', '')
            
            # Build connection string based on engine
            if db_config.engine == 'postgresql':
                connection_string = (
                    f"postgresql://{db_config.username}:{password}@"
                    f"{db_config.host}:{db_config.port}/{db_config.database_name}"
                )
                if db_config.ssl_required:
                    connection_string += "?sslmode=require"
                    
            elif db_config.engine == 'mysql':
                connection_string = (
                    f"mysql://{db_config.username}:{password}@"
                    f"{db_config.host}:{db_config.port}/{db_config.database_name}"
                )
                if db_config.ssl_required:
                    connection_string += "?ssl=true"
            
            else:
                logger.warning(f"Unsupported database engine: {db_config.engine}")
                return None
            
            return connection_string
            
        except Exception as e:
            logger.error(f"Failed to get connection string for {stack_name}: {e}")
            return None
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """
        Validate configuration completeness and correctness
        ✅ Configuration validation with error reporting
        """
        
        errors = {}
        
        # Validate deployment config
        deployment_errors = []
        deployment_config = self.get_deployment_config()
        
        if not deployment_config.region:
            deployment_errors.append("Missing region")
        
        if not deployment_config.project_name:
            deployment_errors.append("Missing project_name")
        
        if deployment_errors:
            errors['deployment'] = deployment_errors
        
        # Validate security config
        security_errors = []
        security_config = self.get_security_config()
        
        if self.environment == Environment.PRODUCTION:
            if not security_config.vpc_id:
                security_errors.append("VPC ID required for production")
            
            if not security_config.encryption_at_rest:
                security_errors.append("Encryption at rest required for production")
        
        if security_errors:
            errors['security'] = security_errors
        
        logger.info(f"✅ Configuration validation complete: {len(errors)} error categories found")
        return errors
