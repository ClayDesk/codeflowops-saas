#!/usr/bin/env python3
"""
AWS Configuration Setup Script
Easily set up all production configuration in AWS Parameter Store

Usage:
  python setup_aws_config.py          # Setup production config
  python setup_aws_config.py --list   # List current parameters
  python setup_aws_config.py --test   # Test configuration
"""

import argparse
import asyncio
import sys
import os

# Add the backend root to the path
backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from src.config.aws_config import config_manager, setup_aws_config


def setup_config():
    """Setup all production configuration in AWS Parameter Store"""
    print("🔧 Setting up production configuration in AWS Parameter Store...")
    print("=" * 60)
    
    try:
        config_manager.setup_production_config()
        print("\n✅ Configuration setup completed successfully!")
        print("\nThe following parameters have been configured:")
        print("- GitHub OAuth Client ID and Secret")
        print("- AWS Cognito User Pool settings")
        print("- Frontend and API URLs")
        print("- CORS settings")
        print("- Environment configuration")
        
    except Exception as e:
        print(f"❌ Error setting up configuration: {e}")
        sys.exit(1)


def list_parameters():
    """List all current parameters in AWS Parameter Store"""
    print("📋 Current AWS Parameter Store configuration:")
    print("=" * 60)
    
    try:
        import boto3
        
        ssm = boto3.client('ssm', region_name='us-east-1')
        
        # List all parameters for our app
        response = ssm.get_parameters_by_path(
            Path='/codeflowops/production/',
            Recursive=True,
            WithDecryption=False  # Don't decrypt secure strings for listing
        )
        
        if not response['Parameters']:
            print("No parameters found. Run setup first.")
            return
        
        for param in response['Parameters']:
            name = param['Name'].replace('/codeflowops/production/', '')
            param_type = param['Type']
            value = param['Value'] if param_type != 'SecureString' else '***SECURE***'
            
            print(f"  {name:25} = {value} ({param_type})")
        
        print(f"\nTotal parameters: {len(response['Parameters'])}")
        
    except Exception as e:
        print(f"❌ Error listing parameters: {e}")


def test_configuration():
    """Test the current configuration"""
    print("🧪 Testing production configuration...")
    print("=" * 60)
    
    try:
        # Test configuration loading
        config = config_manager.get_all_config()
        
        required_keys = [
            'GITHUB_CLIENT_ID',
            'GITHUB_CLIENT_SECRET', 
            'COGNITO_USER_POOL_ID',
            'COGNITO_CLIENT_ID',
            'FRONTEND_URL'
        ]
        
        print("Configuration test results:")
        all_good = True
        
        for key in required_keys:
            value = config.get(key)
            if value:
                # Show partial value for security
                display_value = value[:10] + "..." if len(value) > 10 else value
                print(f"  ✅ {key:25} = {display_value}")
            else:
                print(f"  ❌ {key:25} = NOT SET")
                all_good = False
        
        print("\nOptional configuration:")
        optional_keys = [
            'API_BASE_URL',
            'CORS_ORIGINS',
            'ENVIRONMENT',
            'LOG_LEVEL'
        ]
        
        for key in optional_keys:
            value = config.get(key)
            if value:
                print(f"  ✅ {key:25} = {value}")
            else:
                print(f"  ⚠️  {key:25} = NOT SET (optional)")
        
        if all_good:
            print("\n🎉 All required configuration is set!")
        else:
            print("\n⚠️  Some required configuration is missing. Run setup.")
            
        # Test AWS Parameter Store access
        print("\nTesting AWS Parameter Store access...")
        test_param = config_manager.get_parameter('GITHUB_CLIENT_ID')
        if test_param:
            print("  ✅ AWS Parameter Store access working")
        else:
            print("  ❌ AWS Parameter Store access failed")
        
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")


async def test_oauth_integration():
    """Test the OAuth integration"""
    print("🔐 Testing OAuth integration...")
    print("=" * 60)
    
    try:
        from src.services.oauth_cognito_integration import oauth_cognito_service
        
        # Test authorization URL generation
        auth_url = await oauth_cognito_service.get_oauth_authorization_url(
            provider="github",
            redirect_uri="https://api.codeflowops.com/api/v1/auth/github",
            state="test-state"
        )
        
        print("  ✅ Authorization URL generation successful")
        print(f"     URL: {auth_url[:80]}...")
        
        print("\n🎉 OAuth integration test passed!")
        
    except Exception as e:
        print(f"❌ OAuth integration test failed: {e}")


def main():
    parser = argparse.ArgumentParser(description='Setup AWS configuration for CodeFlowOps')
    parser.add_argument('--list', action='store_true', help='List current parameters')
    parser.add_argument('--test', action='store_true', help='Test configuration')
    parser.add_argument('--test-oauth', action='store_true', help='Test OAuth integration')
    
    args = parser.parse_args()
    
    if args.list:
        list_parameters()
    elif args.test:
        test_configuration()
    elif args.test_oauth:
        asyncio.run(test_oauth_integration())
    else:
        setup_config()


if __name__ == "__main__":
    main()
