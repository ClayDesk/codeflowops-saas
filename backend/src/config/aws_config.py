"""
Production Configuration Manager
Automatically loads configuration from multiple sources:
1. AWS Systems Manager Parameter Store (recommended)
2. AWS Secrets Manager
3. Environment variables (fallback)
4. .env files (development)
"""

import os
import json
import boto3
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ProductionConfigManager:
    """Manages configuration for production deployment"""
    
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.environment = os.getenv('ENVIRONMENT', 'production')
        self.app_name = 'codeflowops'
        
        # Initialize AWS clients
        try:
            self.ssm_client = boto3.client('ssm', region_name=self.region)
            self.secrets_client = boto3.client('secretsmanager', region_name=self.region)
            self.aws_available = True
        except Exception as e:
            logger.warning(f"AWS clients not available: {e}")
            self.aws_available = False
        
        self._config_cache = {}
    
    def get_parameter(self, key: str, default: Any = None, secure: bool = False) -> Any:
        """
        Get configuration parameter from multiple sources
        Priority: SSM Parameter Store > Secrets Manager > Environment > Default
        """
        
        # Check cache first
        cache_key = f"{key}_{secure}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        value = None
        
        # 1. Try AWS Systems Manager Parameter Store
        if self.aws_available:
            value = self._get_from_ssm(key, secure)
        
        # 2. Try AWS Secrets Manager (for sensitive data)
        if value is None and self.aws_available and secure:
            value = self._get_from_secrets_manager(key)
        
        # 3. Try environment variables
        if value is None:
            value = os.getenv(key)
        
        # 4. Use default
        if value is None:
            value = default
        
        # Cache the result
        if value is not None:
            self._config_cache[cache_key] = value
        
        return value
    
    def _get_from_ssm(self, key: str, secure: bool = False) -> Optional[str]:
        """Get parameter from AWS Systems Manager Parameter Store"""
        try:
            parameter_name = f"/{self.app_name}/{self.environment}/{key}"
            
            response = self.ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=secure
            )
            
            value = response['Parameter']['Value']
            logger.debug(f"Retrieved {key} from SSM Parameter Store")
            return value
            
        except self.ssm_client.exceptions.ParameterNotFound:
            logger.debug(f"Parameter {key} not found in SSM")
            return None
        except Exception as e:
            logger.warning(f"Error getting {key} from SSM: {e}")
            return None
    
    def _get_from_secrets_manager(self, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        try:
            secret_name = f"{self.app_name}/{self.environment}/{key}"
            
            response = self.secrets_client.get_secret_value(SecretId=secret_name)
            
            if 'SecretString' in response:
                secret_data = json.loads(response['SecretString'])
                # If it's a JSON secret, try to get the key
                if isinstance(secret_data, dict):
                    value = secret_data.get(key) or secret_data.get('value')
                else:
                    value = secret_data
            else:
                value = response['SecretBinary']
            
            logger.debug(f"Retrieved {key} from Secrets Manager")
            return value
            
        except self.secrets_client.exceptions.ResourceNotFoundException:
            logger.debug(f"Secret {key} not found in Secrets Manager")
            return None
        except Exception as e:
            logger.warning(f"Error getting {key} from Secrets Manager: {e}")
            return None
    
    def set_parameter(self, key: str, value: str, secure: bool = False, description: str = ""):
        """Set parameter in AWS Systems Manager Parameter Store"""
        if not self.aws_available:
            logger.warning("AWS not available, cannot set parameter")
            return False
        
        try:
            parameter_name = f"/{self.app_name}/{self.environment}/{key}"
            
            self.ssm_client.put_parameter(
                Name=parameter_name,
                Value=value,
                Type='SecureString' if secure else 'String',
                Description=description or f"{key} for {self.app_name} {self.environment}",
                Overwrite=True
            )
            
            logger.info(f"Set parameter {key} in SSM Parameter Store")
            
            # Update cache
            cache_key = f"{key}_{secure}"
            self._config_cache[cache_key] = value
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting {key} in SSM: {e}")
            return False
    
    def setup_production_config(self):
        """Setup all production configuration parameters"""
        logger.info("Setting up production configuration in AWS Parameter Store...")
        
        # GitHub OAuth configuration
        self.set_parameter('GITHUB_CLIENT_ID', 'Ov23li4xEOeDgSAMz2rg', secure=False, 
                          description='GitHub OAuth Client ID')
        self.set_parameter('GITHUB_CLIENT_SECRET', 'b112410a2cd2fd6c8f395673cfb1f26503edbed7', secure=True,
                          description='GitHub OAuth Client Secret')
        
        # AWS Cognito configuration
        self.set_parameter('COGNITO_USER_POOL_ID', 'us-east-1_lWcaQdyeZ', secure=False,
                          description='AWS Cognito User Pool ID')
        self.set_parameter('COGNITO_CLIENT_ID', '3d0gm6gtv4ia8vonloc38q8nkt', secure=False,
                          description='AWS Cognito Client ID')
        
        # URLs
        self.set_parameter('FRONTEND_URL', 'https://main.d3f9i8qr0q8s2a.amplifyapp.com', secure=False,
                          description='Frontend URL for CORS and redirects')
        self.set_parameter('API_BASE_URL', 'https://api.codeflowops.com', secure=False,
                          description='Backend API base URL')
        
        # CORS settings
        self.set_parameter('CORS_ORIGINS', 
                          'https://main.d3f9i8qr0q8s2a.amplifyapp.com,https://codeflowops.com,https://www.codeflowops.com', 
                          secure=False, description='Allowed CORS origins')
        
        # Environment settings
        self.set_parameter('ENVIRONMENT', 'production', secure=False,
                          description='Application environment')
        self.set_parameter('DEBUG', 'False', secure=False,
                          description='Debug mode setting')
        self.set_parameter('LOG_LEVEL', 'INFO', secure=False,
                          description='Logging level')
        
        logger.info("Production configuration setup complete!")
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary"""
        config = {
            # GitHub OAuth
            'GITHUB_CLIENT_ID': self.get_parameter('GITHUB_CLIENT_ID'),
            'GITHUB_CLIENT_SECRET': self.get_parameter('GITHUB_CLIENT_SECRET', secure=True),
            
            # AWS Cognito
            'AWS_REGION': self.get_parameter('AWS_REGION', default='us-east-1'),
            'COGNITO_USER_POOL_ID': self.get_parameter('COGNITO_USER_POOL_ID'),
            'COGNITO_CLIENT_ID': self.get_parameter('COGNITO_CLIENT_ID'),
            
            # URLs
            'FRONTEND_URL': self.get_parameter('FRONTEND_URL'),
            'API_BASE_URL': self.get_parameter('API_BASE_URL'),
            
            # CORS
            'CORS_ORIGINS': self.get_parameter('CORS_ORIGINS'),
            
            # Environment
            'ENVIRONMENT': self.get_parameter('ENVIRONMENT', default='production'),
            'DEBUG': self.get_parameter('DEBUG', default='False').lower() == 'true',
            'LOG_LEVEL': self.get_parameter('LOG_LEVEL', default='INFO'),
        }
        
        return {k: v for k, v in config.items() if v is not None}


# Global instance
config_manager = ProductionConfigManager()


def get_production_settings():
    """Get production settings from AWS Parameter Store"""
    return config_manager.get_all_config()


def setup_aws_config():
    """Setup AWS Parameter Store configuration (run once)"""
    config_manager.setup_production_config()
