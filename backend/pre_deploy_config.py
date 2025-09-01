#!/usr/bin/env python3
"""
Pre-deployment configuration script
Sets up AWS Parameter Store configuration before deploying to Elastic Beanstalk
"""

import os
import sys
import boto3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_aws_parameters():
    """Setup AWS Parameter Store parameters for production"""
    
    region = 'us-east-1'
    app_name = 'codeflowops'
    environment = 'production'
    
    try:
        ssm = boto3.client('ssm', region_name=region)
        
        # Configuration parameters
        parameters = {
            'GITHUB_CLIENT_ID': {
                'value': 'Ov23li4xEOeDgSAMz2rg',
                'type': 'String',
                'description': 'GitHub OAuth Client ID'
            },
            'GITHUB_CLIENT_SECRET': {
                'value': 'b112410a2cd2fd6c8f395673cfb1f26503edbed7',
                'type': 'SecureString',
                'description': 'GitHub OAuth Client Secret'
            },
            'COGNITO_USER_POOL_ID': {
                'value': 'us-east-1_lWcaQdyeZ',
                'type': 'String',
                'description': 'AWS Cognito User Pool ID'
            },
            'COGNITO_CLIENT_ID': {
                'value': '3d0gm6gtv4ia8vonloc38q8nkt',
                'type': 'String',
                'description': 'AWS Cognito Client ID'
            },
            'FRONTEND_URL': {
                'value': 'https://main.d3f9i8qr0q8s2a.amplifyapp.com',
                'type': 'String',
                'description': 'Frontend URL for CORS and redirects'
            },
            'API_BASE_URL': {
                'value': 'https://api.codeflowops.com',
                'type': 'String',
                'description': 'Backend API base URL'
            },
            'CORS_ORIGINS': {
                'value': 'https://main.d3f9i8qr0q8s2a.amplifyapp.com,https://codeflowops.com,https://www.codeflowops.com',
                'type': 'String',
                'description': 'Allowed CORS origins'
            },
            'ENVIRONMENT': {
                'value': 'production',
                'type': 'String',
                'description': 'Application environment'
            },
            'DEBUG': {
                'value': 'False',
                'type': 'String',
                'description': 'Debug mode setting'
            },
            'LOG_LEVEL': {
                'value': 'INFO',
                'type': 'String',
                'description': 'Logging level'
            }
        }
        
        logger.info(f"Setting up AWS Parameter Store configuration...")
        
        for key, config in parameters.items():
            parameter_name = f"/{app_name}/{environment}/{key}"
            
            try:
                ssm.put_parameter(
                    Name=parameter_name,
                    Value=config['value'],
                    Type=config['type'],
                    Description=config['description'],
                    Overwrite=True
                )
                
                logger.info(f"✅ Set parameter: {key}")
                
            except Exception as e:
                logger.error(f"❌ Failed to set parameter {key}: {e}")
                return False
        
        logger.info("🎉 All parameters configured successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error setting up AWS parameters: {e}")
        return False


def verify_configuration():
    """Verify the configuration is accessible"""
    try:
        logger.info("Verifying configuration access...")
        
        # Try to import and use our config manager
        sys.path.insert(0, os.path.dirname(__file__))
        from src.config.aws_config import config_manager
        
        # Test getting a parameter
        github_client_id = config_manager.get_parameter('GITHUB_CLIENT_ID')
        
        if github_client_id:
            logger.info(f"✅ Configuration verification successful")
            logger.info(f"   GitHub Client ID: {github_client_id[:10]}...")
            return True
        else:
            logger.error("❌ Configuration verification failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Configuration verification error: {e}")
        return False


if __name__ == "__main__":
    logger.info("🔧 CodeFlowOps Pre-deployment Configuration")
    logger.info("=" * 50)
    
    # Setup parameters
    if setup_aws_parameters():
        # Verify configuration
        if verify_configuration():
            logger.info("✅ Pre-deployment configuration completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Configuration verification failed")
            sys.exit(1)
    else:
        logger.error("❌ Parameter setup failed")
        sys.exit(1)
