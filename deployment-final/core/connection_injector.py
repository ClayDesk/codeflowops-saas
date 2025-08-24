# Phase 3: Enhanced Connection String Injector
# backend/core/connection_injector.py

"""
Connection string injection via AWS Secrets Manager
Secure database credential management and environment variable injection
"""

import boto3
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

from .database_provisioner import EnhancedDatabaseInstance

logger = logging.getLogger(__name__)

class EnvironmentType(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class ConnectionConfig:
    """Database connection configuration"""
    instance: EnhancedDatabaseInstance
    application_name: str
    environment: EnvironmentType
    custom_variables: Dict[str, str] = None
    
    def __post_init__(self):
        if self.custom_variables is None:
            self.custom_variables = {}

@dataclass
class InjectionResult:
    """Result of connection string injection"""
    success: bool
    environment_variables: Dict[str, str]
    secrets_manager_arn: str
    connection_string: str
    error_message: Optional[str] = None

class ConnectionInjector:
    """
    ✅ Connection string injection via AWS Secrets Manager
    
    Features:
    - Secure credential storage in AWS Secrets Manager
    - Environment-specific connection strings
    - Multiple format support (DATABASE_URL, individual variables)
    - RDS Proxy integration
    - Connection pooling configuration
    - Framework-specific variable formats
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.secrets_manager = boto3.client('secretsmanager', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
        
        logger.info("🔐 Connection injector initialized")
    
    def inject_connection_variables(self, config: ConnectionConfig) -> InjectionResult:
        """
        Inject database connection variables into application environment
        
        Creates both DATABASE_URL and individual connection variables
        for maximum framework compatibility
        """
        
        logger.info(f"🚀 Injecting connection variables for {config.application_name}")
        
        try:
            # Get database connection details
            instance = config.instance
            endpoint = self._get_connection_endpoint(instance)
            
            # Create connection string
            connection_string = self._create_connection_string(instance, endpoint)
            
            # Create comprehensive environment variables
            env_vars = self._create_environment_variables(instance, endpoint, config)
            
            # Store/update secrets in AWS Secrets Manager
            secrets_arn = self._update_application_secrets(config.application_name, env_vars, config.environment)
            
            # Store configuration in Parameter Store for easy retrieval
            self._store_parameter_store_config(config.application_name, env_vars, config.environment)
            
            result = InjectionResult(
                success=True,
                environment_variables=env_vars,
                secrets_manager_arn=secrets_arn,
                connection_string=connection_string
            )
            
            logger.info(f"✅ Connection variables injected successfully")
            logger.info(f"🔗 Connection endpoint: {endpoint}")
            logger.info(f"🔐 Secrets ARN: {secrets_arn}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Connection injection failed: {e}")
            return InjectionResult(
                success=False,
                environment_variables={},
                secrets_manager_arn="",
                connection_string="",
                error_message=str(e)
            )
    
    def _get_connection_endpoint(self, instance: EnhancedDatabaseInstance) -> str:
        """Get the appropriate connection endpoint (proxy if available)"""
        
        if instance.proxy:
            logger.info("🔗 Using RDS Proxy endpoint for connection pooling")
            return instance.proxy.endpoint
        else:
            logger.info("🔗 Using direct database endpoint")
            return instance.base_instance.endpoint
    
    def _create_connection_string(self, instance: EnhancedDatabaseInstance, endpoint: str) -> str:
        """Create database connection string"""
        
        db_instance = instance.base_instance
        
        # Use placeholder for password (will be replaced at runtime)
        if db_instance.engine.startswith('postgres'):
            return f"postgresql://{db_instance.username}:{{password}}@{endpoint}:{db_instance.port}/{db_instance.database_name}"
        elif db_instance.engine.startswith('mysql'):
            return f"mysql://{db_instance.username}:{{password}}@{endpoint}:{db_instance.port}/{db_instance.database_name}"
        elif db_instance.engine.startswith('docdb'):
            return f"mongodb://{db_instance.username}:{{password}}@{endpoint}:{db_instance.port}/{db_instance.database_name}"
        
        return f"unknown://{endpoint}:{db_instance.port}"
    
    def _create_environment_variables(self, instance: EnhancedDatabaseInstance, 
                                    endpoint: str, config: ConnectionConfig) -> Dict[str, str]:
        """Create comprehensive environment variables for different frameworks"""
        
        db_instance = instance.base_instance
        
        # Base connection variables
        env_vars = {
            # Standard DATABASE_URL (most frameworks)
            'DATABASE_URL': self._create_connection_string(instance, endpoint),
            
            # Individual connection parameters
            'DB_HOST': endpoint,
            'DB_PORT': str(db_instance.port),
            'DB_NAME': db_instance.database_name,
            'DB_DATABASE': db_instance.database_name,  # Alternative name
            'DB_USERNAME': db_instance.username,
            'DB_USER': db_instance.username,  # Alternative name
            'DB_ENGINE': db_instance.engine,
            
            # Framework-specific variables
            **self._get_framework_specific_variables(db_instance, endpoint),
            
            # Connection pool settings (if RDS Proxy is used)
            **self._get_connection_pool_variables(instance),
            
            # Environment-specific settings
            **self._get_environment_specific_variables(config.environment),
            
            # Custom variables
            **config.custom_variables
        }
        
        # Add SSL/TLS settings
        if config.environment == EnvironmentType.PRODUCTION:
            env_vars.update({
                'DB_SSL_MODE': 'require',
                'DB_SSL_REQUIRED': 'true',
                'DATABASE_REQUIRE_SSL': 'true'
            })
        
        return env_vars
    
    def _get_framework_specific_variables(self, db_instance: Any, endpoint: str) -> Dict[str, str]:
        """Get framework-specific environment variables"""
        
        framework_vars = {}
        
        if db_instance.engine.startswith('postgres'):
            # PostgreSQL-specific
            framework_vars.update({
                'POSTGRES_HOST': endpoint,
                'POSTGRES_PORT': str(db_instance.port),
                'POSTGRES_DB': db_instance.database_name,
                'POSTGRES_USER': db_instance.username,
                'PGHOST': endpoint,
                'PGPORT': str(db_instance.port),
                'PGDATABASE': db_instance.database_name,
                'PGUSER': db_instance.username
            })
            
        elif db_instance.engine.startswith('mysql'):
            # MySQL-specific
            framework_vars.update({
                'MYSQL_HOST': endpoint,
                'MYSQL_PORT': str(db_instance.port),
                'MYSQL_DATABASE': db_instance.database_name,
                'MYSQL_USER': db_instance.username
            })
            
        elif db_instance.engine.startswith('docdb'):
            # MongoDB/DocumentDB-specific
            framework_vars.update({
                'MONGO_HOST': endpoint,
                'MONGO_PORT': str(db_instance.port),
                'MONGO_DB': db_instance.database_name,
                'MONGO_USER': db_instance.username,
                'MONGODB_URI': f"mongodb://{db_instance.username}:{{password}}@{endpoint}:{db_instance.port}/{db_instance.database_name}"
            })
        
        return framework_vars
    
    def _get_connection_pool_variables(self, instance: EnhancedDatabaseInstance) -> Dict[str, str]:
        """Get connection pooling configuration variables"""
        
        pool_vars = {}
        
        if instance.proxy:
            # RDS Proxy configuration
            pool_vars.update({
                'DB_PROXY_ENDPOINT': instance.proxy.endpoint,
                'DB_CONNECTION_POOLING': 'true',
                'DB_MAX_CONNECTIONS': '100',
                'DB_IDLE_TIMEOUT': '1800',  # 30 minutes
                'DB_CONNECTION_TIMEOUT': '30'
            })
        else:
            # Direct connection settings
            pool_vars.update({
                'DB_CONNECTION_POOLING': 'false',
                'DB_MAX_CONNECTIONS': '20',  # Conservative limit
                'DB_CONNECTION_TIMEOUT': '30'
            })
        
        return pool_vars
    
    def _get_environment_specific_variables(self, environment: EnvironmentType) -> Dict[str, str]:
        """Get environment-specific configuration variables"""
        
        env_config = {
            EnvironmentType.DEVELOPMENT: {
                'DB_LOG_QUERIES': 'true',
                'DB_DEBUG': 'true',
                'DB_TIMEOUT': '30',
                'DB_RETRY_ATTEMPTS': '3'
            },
            EnvironmentType.STAGING: {
                'DB_LOG_QUERIES': 'false',
                'DB_DEBUG': 'false',
                'DB_TIMEOUT': '30',
                'DB_RETRY_ATTEMPTS': '5'
            },
            EnvironmentType.PRODUCTION: {
                'DB_LOG_QUERIES': 'false',
                'DB_DEBUG': 'false',
                'DB_TIMEOUT': '10',
                'DB_RETRY_ATTEMPTS': '5',
                'DB_STATEMENT_TIMEOUT': '300000',  # 5 minutes
                'DB_IDLE_IN_TRANSACTION_SESSION_TIMEOUT': '60000'  # 1 minute
            }
        }
        
        return env_config.get(environment, {})
    
    def _update_application_secrets(self, application_name: str, env_vars: Dict[str, str], 
                                  environment: EnvironmentType) -> str:
        """Store/update application secrets in AWS Secrets Manager"""
        
        secret_name = f"codeflowops/{application_name}/{environment.value}/database"
        
        # Create secret value (exclude non-sensitive variables)
        sensitive_vars = {
            'DATABASE_URL': env_vars['DATABASE_URL'],
            'DB_HOST': env_vars['DB_HOST'],
            'DB_PORT': env_vars['DB_PORT'],
            'DB_NAME': env_vars['DB_NAME'],
            'DB_USERNAME': env_vars['DB_USERNAME'],
            'DB_ENGINE': env_vars['DB_ENGINE']
        }
        
        # Add framework-specific sensitive variables
        for key, value in env_vars.items():
            if any(pattern in key.lower() for pattern in ['host', 'port', 'database', 'user', 'uri']):
                sensitive_vars[key] = value
        
        secret_description = f"Database connection secrets for {application_name} ({environment.value})"
        
        try:
            # Try to create new secret
            response = self.secrets_manager.create_secret(
                Name=secret_name,
                Description=secret_description,
                SecretString=json.dumps(sensitive_vars),
                Tags=[
                    {'Key': 'Application', 'Value': application_name},
                    {'Key': 'Environment', 'Value': environment.value},
                    {'Key': 'ManagedBy', 'Value': 'CodeFlowOps-Phase3'},
                    {'Key': 'Type', 'Value': 'DatabaseCredentials'}
                ]
            )
            
            logger.info(f"✅ Created new secret: {secret_name}")
            
        except self.secrets_manager.exceptions.ResourceExistsException:
            # Secret exists, update it
            response = self.secrets_manager.update_secret(
                SecretId=secret_name,
                Description=secret_description,
                SecretString=json.dumps(sensitive_vars)
            )
            
            logger.info(f"✅ Updated existing secret: {secret_name}")
        
        return response['ARN']
    
    def _store_parameter_store_config(self, application_name: str, env_vars: Dict[str, str], 
                                    environment: EnvironmentType):
        """Store non-sensitive configuration in Parameter Store"""
        
        # Non-sensitive configuration variables
        non_sensitive_vars = {
            key: value for key, value in env_vars.items()
            if not any(pattern in key.lower() for pattern in ['password', 'secret', 'key', 'token'])
            and not any(pattern in key.lower() for pattern in ['host', 'uri', 'url'])  # These go to secrets
        }
        
        parameter_prefix = f"/codeflowops/{application_name}/{environment.value}/database"
        
        for key, value in non_sensitive_vars.items():
            parameter_name = f"{parameter_prefix}/{key.lower()}"
            
            try:
                self.ssm.put_parameter(
                    Name=parameter_name,
                    Value=value,
                    Type='String',
                    Overwrite=True,
                    Tags=[
                        {'Key': 'Application', 'Value': application_name},
                        {'Key': 'Environment', 'Value': environment.value},
                        {'Key': 'ManagedBy', 'Value': 'CodeFlowOps-Phase3'}
                    ]
                )
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to store parameter {parameter_name}: {e}")
        
        logger.info(f"✅ Stored {len(non_sensitive_vars)} parameters in Parameter Store")
    
    def retrieve_connection_secrets(self, application_name: str, environment: EnvironmentType) -> Dict[str, str]:
        """Retrieve connection secrets from AWS Secrets Manager"""
        
        secret_name = f"codeflowops/{application_name}/{environment.value}/database"
        
        try:
            response = self.secrets_manager.get_secret_value(SecretId=secret_name)
            secrets = json.loads(response['SecretString'])
            
            logger.info(f"✅ Retrieved connection secrets for {application_name}")
            return secrets
            
        except self.secrets_manager.exceptions.ResourceNotFoundException:
            logger.error(f"❌ Connection secrets not found for {application_name}")
            return {}
        except Exception as e:
            logger.error(f"❌ Failed to retrieve connection secrets: {e}")
            return {}
    
    def retrieve_connection_parameters(self, application_name: str, environment: EnvironmentType) -> Dict[str, str]:
        """Retrieve connection parameters from Parameter Store"""
        
        parameter_prefix = f"/codeflowops/{application_name}/{environment.value}/database"
        
        try:
            response = self.ssm.get_parameters_by_path(
                Path=parameter_prefix,
                Recursive=True,
                WithDecryption=True
            )
            
            parameters = {}
            for param in response['Parameters']:
                key = param['Name'].split('/')[-1].upper()
                parameters[key] = param['Value']
            
            logger.info(f"✅ Retrieved {len(parameters)} connection parameters for {application_name}")
            return parameters
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve connection parameters: {e}")
            return {}
    
    def get_runtime_environment_variables(self, application_name: str, 
                                        environment: EnvironmentType, 
                                        include_password: bool = False) -> Dict[str, str]:
        """
        Get complete set of environment variables for runtime use
        
        Args:
            application_name: Name of the application
            environment: Environment type
            include_password: Whether to include actual password (use only for local development)
        """
        
        # Get secrets and parameters
        secrets = self.retrieve_connection_secrets(application_name, environment)
        parameters = self.retrieve_connection_parameters(application_name, environment)
        
        # Combine all variables
        env_vars = {**secrets, **parameters}
        
        if not include_password:
            # Replace password placeholders with environment variable references
            for key, value in env_vars.items():
                if isinstance(value, str) and '{password}' in value:
                    env_vars[key] = value.replace('{password}', '${DB_PASSWORD}')
        
        return env_vars
    
    def generate_docker_env_file(self, application_name: str, environment: EnvironmentType, 
                                output_path: str) -> str:
        """Generate .env file for Docker containers"""
        
        env_vars = self.get_runtime_environment_variables(application_name, environment)
        
        env_content = []
        env_content.append(f"# Database environment variables for {application_name}")
        env_content.append(f"# Generated by CodeFlowOps Phase 3")
        env_content.append(f"# Environment: {environment.value}")
        env_content.append("")
        
        for key, value in sorted(env_vars.items()):
            if '{password}' in str(value):
                env_content.append(f"# {key}={value}")
                env_content.append(f"# Note: Replace {{password}} with actual password from secrets")
            else:
                env_content.append(f"{key}={value}")
        
        env_content.append("")
        env_content.append("# Password should be set separately from AWS Secrets Manager:")
        env_content.append("# DB_PASSWORD=<retrieve from secrets manager>")
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(env_content))
        
        logger.info(f"✅ Docker environment file generated: {output_path}")
        return output_path
    
    def cleanup_application_secrets(self, application_name: str, environment: EnvironmentType):
        """Clean up application secrets and parameters"""
        
        logger.info(f"🧹 Cleaning up secrets for {application_name} ({environment.value})")
        
        try:
            # Delete secrets
            secret_name = f"codeflowops/{application_name}/{environment.value}/database"
            self.secrets_manager.delete_secret(
                SecretId=secret_name,
                ForceDeleteWithoutRecovery=True
            )
            logger.info(f"✅ Deleted secret: {secret_name}")
            
            # Delete parameters
            parameter_prefix = f"/codeflowops/{application_name}/{environment.value}/database"
            parameters_response = self.ssm.get_parameters_by_path(
                Path=parameter_prefix,
                Recursive=True
            )
            
            parameter_names = [param['Name'] for param in parameters_response['Parameters']]
            if parameter_names:
                self.ssm.delete_parameters(Names=parameter_names)
                logger.info(f"✅ Deleted {len(parameter_names)} parameters")
            
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")


# Example usage and testing
if __name__ == "__main__":
    import sys
    from .database_provisioner import DatabaseProvisioner, DatabaseConfig
    
    async def main():
        # Example: Inject connection variables for a provisioned database
        
        # This would normally come from database provisioning
        provisioner = DatabaseProvisioner()
        
        # Example database config
        db_config = DatabaseConfig(
            db_name="example_app",
            username="appuser",
            instance_class="db.t3.micro",
            engine="mysql"
        )
        
        # Provision database (this would be done by the provisioner)
        # enhanced_db = provisioner.provision_database(db_config)
        
        # For demo, create a mock enhanced instance
        # enhanced_db = create_mock_instance()
        
        # Inject connection variables
        injector = ConnectionInjector()
        
        connection_config = ConnectionConfig(
            instance=None,  # enhanced_db,
            application_name="my-web-app",
            environment=EnvironmentType.PRODUCTION,
            custom_variables={'APP_ENV': 'production'}
        )
        
        # result = injector.inject_connection_variables(connection_config)
        
        # if result.success:
        #     print(f"✅ Connection variables injected!")
        #     print(f"Environment variables: {len(result.environment_variables)}")
        #     print(f"Connection string: {result.connection_string}")
        # else:
        #     print(f"❌ Injection failed: {result.error_message}")
        
        print("Connection Injector example (requires actual database instance)")
    
    import asyncio
    asyncio.run(main())
